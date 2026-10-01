# -*- coding: utf-8 -*-
"""Fase 4 (snowballing) sob a configuracao v2.

As sementes mudaram: a camada de profundidade caiu de 142 para 35, entao a
colheita de referencias e de citantes precisa ser refeita (o registro de
2026-09-21 guardou so a direcao, para_tras/para_frente, nao qual semente gerou
cada candidato).

O que NAO se refaz: os vereditos. Candidato ja triado em fase4_triagem.csv tem
seu veredito transportado; so o que nunca foi visto entra em triagem nova.
A atribuicao de camada e recalculada com o regex corrigido (C5) e a regra do
par exato (D9').
"""
import csv
import io
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DADOS = os.path.join(RAIZ, "revisao_sistematica", "dados")
V2 = os.path.join(DADOS, "v2")

UA = {"User-Agent": "mailto:dam@cesar.school"}
KEY = os.environ.get("OPENALEX_API_KEY", "")
JANELA = ("from_publication_date:2020-01-01,to_publication_date:2026-12-31,"
          "type:article|review|conference-paper")

FREQ = r"frequenc|\bdct\b|discrete cosine|wavelet|fourier|spectral|spectrum|high-frequency|high frequency"
EDGE = (r"\bedge[- ](attention|aware|guid|enhanc|detect|extract|branch|module|featur|map|prior|inform|supervis)"
        r"|edge[- ]?net|boundary|contour|sobel|canny|laplacian|\bedge loss")
RUIDO = r"\bnoise|\bsrm\b|prnu|steganalytic|constrained conv|noiseprint|noise residual"

CAMPOS = "id,doi,title,publication_year,type,primary_location,authorships,abstract_inverted_index,cited_by_count,referenced_works"


def get(url, tent=6):
    for i in range(tent):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and i < tent - 1:
                time.sleep(5 * (i + 1))
                continue
            raise
        except Exception:
            # RemoteDisconnected, timeout, reset de conexao: transitorios
            if i < tent - 1:
                time.sleep(5 * (i + 1))
                continue
            raise


def pagina(filtro, campos=CAMPOS, pausa=0.2):
    out, cur = [], "*"
    while cur:
        u = ("https://api.openalex.org/works?filter=" + urllib.parse.quote(filtro, safe=":,|")
             + "&per-page=200&cursor=" + cur + "&select=" + campos)
        if KEY:
            u += "&api_key=" + KEY
        d = get(u)
        if not d["results"]:
            break
        out += d["results"]
        cur = d["meta"].get("next_cursor")
        time.sleep(pausa)
    return out


def lotes(xs, n):
    xs = list(xs)
    for i in range(0, len(xs), n):
        yield xs[i:i + n]


def abstract(w):
    inv = w.get("abstract_inverted_index") or {}
    if not inv:
        return ""
    pos = {}
    for tok, idxs in inv.items():
        for i in idxs:
            pos[i] = tok
    return " ".join(pos[i] for i in sorted(pos))


def dominios(t):
    return {n for n, p in (("frequencia", FREQ), ("borda", EDGE), ("ruido", RUIDO)) if re.search(p, t)}


def main():
    with io.open(os.path.join(DADOS, "corpus_bruto.json"), encoding="utf-8") as f:
        bruto1 = json.load(f)
    sid2oa = {"S{:04d}".format(i + 1): w["id"] for i, w in enumerate(bruto1)}
    with io.open(os.path.join(V2, "corpus_bruto.json"), encoding="utf-8") as f:
        corpus_v2 = {w["id"] for w in json.load(f)}

    tri = list(csv.DictReader(io.open(os.path.join(V2, "triagem.csv"), encoding="utf-8")))
    prof = [r["id"] for r in tri if r.get("fase2_camada") == "profundidade"]
    ec4 = [r["id"] for r in tri if r.get("fase1_codigo_ec") == "EC4" or r.get("fase2_codigo_ec") == "EC4"]
    sementes = [sid2oa[s] for s in (prof + ec4) if s in sid2oa]
    print("sementes: {} profundidade + {} EC4 = {}".format(len(prof), len(ec4), len(sementes)))

    # --- para tras: referencias das sementes ---
    refs = set()
    for lote in lotes(sementes, 50):
        f = "openalex_id:" + "|".join(x.rsplit("/", 1)[-1] for x in lote)
        for w in pagina(f, campos="id,referenced_works"):
            refs.update(w.get("referenced_works") or [])
        sys.stderr.write("\r  para_tras: {} refs".format(len(refs)))
    sys.stderr.write("\n")

    # --- para frente: citantes das sementes ---
    cit = {}
    for lote in lotes(sementes, 25):
        f = "cites:" + "|".join(x.rsplit("/", 1)[-1] for x in lote) + "," + JANELA
        for w in pagina(f):
            cit[w["id"]] = w
        sys.stderr.write("\r  para_frente: {} citantes".format(len(cit)))
    sys.stderr.write("\n")

    novos_ids = (refs | set(cit)) - corpus_v2
    print("unicos apos remover o que ja esta no corpus v2: {}".format(len(novos_ids)))

    # metadados dos que vieram so por referencia. Lote pequeno: URL longa derruba
    # a conexao. Falha de lote nao aborta a colheita, so e contabilizada.
    cache = os.path.join(V2, "_f4_meta_cache.json")
    meta = dict(cit)
    if os.path.exists(cache):
        with io.open(cache, encoding="utf-8") as f:
            meta.update(json.load(f))
    faltam = [i for i in novos_ids if i not in meta]
    falhas = 0
    for k, lote in enumerate(lotes(faltam, 20)):
        f = "openalex_id:" + "|".join(x.rsplit("/", 1)[-1] for x in lote) + "," + JANELA
        try:
            for w in pagina(f):
                meta[w["id"]] = w
        except Exception:
            falhas += len(lote)
        if k % 10 == 0:
            with io.open(cache, "w", encoding="utf-8") as fh:
                json.dump({i: w for i, w in meta.items() if i in novos_ids}, fh, ensure_ascii=False)
        sys.stderr.write("\r  metadados: {}/{} (lotes falhos: {})".format(len(meta), len(novos_ids), falhas))
    sys.stderr.write("\n")
    with io.open(cache, "w", encoding="utf-8") as fh:
        json.dump({i: w for i, w in meta.items() if i in novos_ids}, fh, ensure_ascii=False)
    cands = {i: meta[i] for i in novos_ids if i in meta}
    print("candidatos dentro da janela e do tipo: {}".format(len(cands)))

    # --- transporte de vereditos da fase 4 v1 ---
    cand_v1 = json.load(io.open(os.path.join(DADOS, "fase4_candidatos.json"), encoding="utf-8"))
    oa2nid = {c["openalex"]: c["id"] for c in cand_v1 if c.get("openalex")}
    tri_v1 = {r["id"]: r for r in csv.DictReader(io.open(os.path.join(DADOS, "fase4_triagem.csv"), encoding="utf-8"))}

    linhas, transportados, inediots = [], 0, 0
    for oa, w in cands.items():
        nid = oa2nid.get(oa)
        base = tri_v1.get(nid) if nid else None
        tit = w.get("title") or ""
        res = abstract(w)
        if base:
            transportados += 1
            r = dict(base)
            r["resumo"] = r.get("resumo") or res
        else:
            inediots += 1
            r = {"id": nid or ("X%04d" % (inediots,)), "origem_snowballing": "v2",
                 "ano": w.get("publication_year") or "", "titulo": tit,
                 "veiculo": ((w.get("primary_location") or {}).get("source") or {}).get("display_name", ""),
                 "tipo": w.get("type") or "", "doi": (w.get("doi") or "").replace("https://doi.org/", ""),
                 "citacoes": w.get("cited_by_count") or 0, "autores": "", "resumo": res,
                 "fase1_titulo_veredito": "", "fase1_codigo_ec": "",
                 "fase2_resumo_veredito": "", "fase2_codigo_ec": "", "fase2_camada": "",
                 "dominios_detectados": "", "observacoes": "inedito na colheita v2, sem veredito",
                 "fase3_fulltext_veredito": "", "fase3_codigo_ec": ""}
        # camada recalculada (C5 + D9')
        if r.get("fase1_titulo_veredito") == "incluir" and r.get("fase2_codigo_ec") != "EC2":
            doms = dominios((r["titulo"] + " " + (r.get("resumo") or "")).lower())
            r["dominios_detectados"] = "+".join(sorted(doms))
            r["fase2_camada"] = "profundidade" if {"frequencia", "borda"} <= doms else "mapeamento"
        linhas.append(r)

    prof4 = [r for r in linhas if r.get("fase2_camada") == "profundidade"]
    mape4 = [r for r in linhas if r.get("fase2_camada") == "mapeamento"]
    sem_ver = [r for r in linhas if not r.get("fase1_titulo_veredito")]
    extr = {r["id"] for r in csv.DictReader(
        io.open(os.path.join(RAIZ, "revisao_sistematica", "planilhas", "extracao.csv"), encoding="utf-8"))}

    cols = list(linhas[0].keys())
    with io.open(os.path.join(V2, "fase4_triagem.csv"), "w", encoding="utf-8", newline="") as f:
        w_ = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w_.writeheader()
        w_.writerows(linhas)

    print("\n=== Fase 4 v2 ===")
    print("  candidatos              : {}".format(len(linhas)))
    print("    veredito transportado : {}".format(transportados))
    print("    ineditos (sem triagem): {}".format(inediots))
    print("  camada de mapeamento    : {}".format(len(mape4)))
    print("  camada de profundidade  : {}".format(len(prof4)))
    print("    com extracao pronta   : {}".format(sum(1 for r in prof4 if r["id"] in extr)))
    print("  sem veredito de fase 1  : {}".format(len(sem_ver)))
    print("\nGravado: dados/v2/fase4_triagem.csv")


if __name__ == "__main__":
    main()
