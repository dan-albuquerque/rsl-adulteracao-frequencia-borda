# -*- coding: utf-8 -*-
"""Fase 4, coleta: busca os metadados dos candidatos de snowballing e deduplica.

Roda depois de rsl_fase4_snowballing.py --medir, que ja gravou os identificadores
das referencias para tras. Aqui:

  1. busca metadados das referencias para tras, com filtro de janela e tipo
  2. busca os trabalhos que citam cada semente (para frente)
  3. deduplica entre si e contra o corpus de 1.413 da busca primaria
  4. grava os candidatos que precisam passar pelas fases 1 e 2

Referencia: protocolo secao 6 (Fase 4) e secao 6, gestao de referencias
(limiar de similaridade de 95% com coincidencia de ano; ver desvio 8).
"""
import csv
import datetime as dt
import difflib
import io
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DADOS = os.path.join(RAIZ, "revisao_sistematica", "dados")
EMAIL = "dam@cesar.school"
UA = {"User-Agent": "mailto:" + EMAIL}
API = "https://api.openalex.org/works"

JANELA_MIN, JANELA_MAX = 2020, 2026
TIPOS_OK = "article|review|conference-paper|book-chapter"
SELECT = ("id,doi,title,display_name,publication_year,type,primary_location,"
          "authorships,abstract_inverted_index,cited_by_count")


def get(url, tentativas=4):
    for k in range(tentativas):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503):
                time.sleep(2 * (k + 1))
                continue
            return None
        except Exception:
            time.sleep(2 * (k + 1))
    return None


def norm_titulo(t):
    t = (t or "").lower()
    t = re.sub(r"[^a-z0-9 ]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def norm_doi(d):
    d = (d or "").lower().strip()
    return d.replace("https://doi.org/", "").replace("http://dx.doi.org/", "")


def resumo(inv):
    if not inv:
        return ""
    pos = {}
    for palavra, idxs in inv.items():
        for i in idxs:
            pos[i] = palavra
    return " ".join(pos[k] for k in sorted(pos))


def simplifica(w):
    loc = w.get("primary_location") or {}
    src = loc.get("source") or {}
    return {
        "openalex": w.get("id", ""),
        "doi": norm_doi(w.get("doi")),
        "titulo": w.get("title") or w.get("display_name") or "",
        "ano": w.get("publication_year"),
        "tipo": w.get("type", ""),
        "veiculo": src.get("display_name", "") or "",
        "editora": src.get("host_organization_name", "") or "",
        "autores": "; ".join(
            (a.get("author") or {}).get("display_name", "")
            for a in (w.get("authorships") or [])[:8]),
        "resumo": resumo(w.get("abstract_inverted_index")),
        "citacoes": w.get("cited_by_count", 0),
    }


def busca_por_ids(ids):
    """Metadados em lote, ja filtrados por janela e tipo no servidor."""
    out = []
    for i in range(0, len(ids), 50):
        lote = [x.rsplit("/", 1)[-1] for x in ids[i:i + 50]]
        filtro = ("ids.openalex:" + "|".join(lote)
                  + ",type:" + TIPOS_OK
                  + ",from_publication_date:%d-01-01,to_publication_date:%d-12-31"
                  % (JANELA_MIN, JANELA_MAX))
        url = (API + "?filter=" + urllib.parse.quote(filtro, safe=":|/.,-")
               + "&per-page=50&select=" + SELECT)
        d = get(url)
        if d:
            out.extend(simplifica(w) for w in d.get("results", []))
        if (i // 50) % 10 == 0:
            print("    lote %d/%d, acumulado %d" % (i // 50 + 1, (len(ids) + 49) // 50, len(out)))
        time.sleep(0.2)
    return out


def busca_citantes(seed_ids):
    out = []
    for k, wid in enumerate(seed_ids):
        filtro = ("cites:%s,type:%s,from_publication_date:%d-01-01,to_publication_date:%d-12-31"
                  % (wid, TIPOS_OK, JANELA_MIN, JANELA_MAX))
        cursor = "*"
        while cursor:
            url = (API + "?filter=" + urllib.parse.quote(filtro, safe=":|/.,-")
                   + "&per-page=200&cursor=" + cursor + "&select=" + SELECT)
            d = get(url)
            if not d:
                break
            out.extend(simplifica(w) for w in d.get("results", []))
            cursor = (d.get("meta") or {}).get("next_cursor")
            if not d.get("results"):
                break
        if (k + 1) % 25 == 0:
            print("    %d/%d sementes, acumulado %d citantes" % (k + 1, len(seed_ids), len(out)))
        time.sleep(0.15)
    return out


def main():
    regs = list(csv.DictReader(io.open(os.path.join(DADOS, "triagem.csv"), encoding="utf-8")))
    corpus_doi = {norm_doi(r["doi"]) for r in regs if r.get("doi")}
    corpus_tit = {norm_titulo(r["titulo"]): r.get("ano", "") for r in regs}

    medicao = json.load(io.open(os.path.join(DADOS, "fase4_medicao.json"), encoding="utf-8"))
    seed_ids = list(medicao["citantes_por_semente"].keys())
    para_tras_ids = json.load(io.open(os.path.join(DADOS, "fase4_para_tras_ids.json"),
                                      encoding="utf-8"))

    print("1) metadados das %d referencias para tras (com filtro de janela/tipo)"
          % len(para_tras_ids))
    tras = busca_por_ids(para_tras_ids)
    print("   sobreviveram a janela 2020-2026 e ao filtro de tipo: %d" % len(tras))

    print("2) trabalhos citantes das %d sementes" % len(seed_ids))
    frente = busca_citantes(seed_ids)
    print("   citantes recuperados (com repeticao): %d" % len(frente))

    # ---- uniao e deduplicacao
    for r in tras:
        r["origem_snowballing"] = "para_tras"
    for r in frente:
        r["origem_snowballing"] = "para_frente"

    vistos_oa, unicos = set(), []
    for r in tras + frente:
        if r["openalex"] in vistos_oa:
            continue
        vistos_oa.add(r["openalex"])
        unicos.append(r)
    print("3) unicos apos remover repeticao interna: %d" % len(unicos))

    novos, ja_no_corpus = [], 0
    for r in unicos:
        nt = norm_titulo(r["titulo"])
        if r["doi"] and r["doi"] in corpus_doi:
            ja_no_corpus += 1
            continue
        if nt in corpus_tit:
            ja_no_corpus += 1
            continue
        # similaridade >= 95% com mesmo ano (protocolo, desvio 8)
        dup = False
        for ct, ca in corpus_tit.items():
            if abs(len(ct) - len(nt)) > 25:
                continue
            if str(ca) == str(r["ano"]) and difflib.SequenceMatcher(None, ct, nt).ratio() >= 0.95:
                dup = True
                break
        if dup:
            ja_no_corpus += 1
            continue
        novos.append(r)

    print("4) ja presentes no corpus de 1.413: %d" % ja_no_corpus)
    print("   CANDIDATOS NOVOS para fases 1 e 2: %d" % len(novos))

    novos.sort(key=lambda r: (-(r.get("citacoes") or 0), r["titulo"]))
    for i, r in enumerate(novos, 1):
        r["id"] = "N%04d" % i

    json.dump(novos, io.open(os.path.join(DADOS, "fase4_candidatos.json"), "w", encoding="utf-8"),
              indent=1, ensure_ascii=False)
    with io.open(os.path.join(DADOS, "fase4_candidatos.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "origem_snowballing", "ano", "titulo", "veiculo", "tipo",
                    "doi", "citacoes", "tem_resumo"])
        for r in novos:
            w.writerow([r["id"], r["origem_snowballing"], r["ano"], r["titulo"], r["veiculo"],
                        r["tipo"], r["doi"], r["citacoes"], "sim" if r["resumo"] else "nao"])

    resumo_exec = {
        "data": dt.date.today().isoformat(),
        "para_tras_brutos": len(para_tras_ids),
        "para_tras_na_janela": len(tras),
        "para_frente_brutos": len(frente),
        "unicos": len(unicos),
        "ja_no_corpus": ja_no_corpus,
        "candidatos_novos": len(novos),
    }
    json.dump(resumo_exec, io.open(os.path.join(DADOS, "fase4_execucao.json"), "w",
                                   encoding="utf-8"), indent=1, ensure_ascii=False)
    print("\ngravado: fase4_candidatos.{json,csv} e fase4_execucao.json")


if __name__ == "__main__":
    main()
