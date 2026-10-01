# -*- coding: utf-8 -*-
"""Fase 4 da revisao sistematica: snowballing para tras e para frente.

Referencia: revisao_sistematica/protocolo_rsl.md, secao 6 (Fase 4) e 4.1.1.
O snowballing e OBRIGATORIO por causa do desvio D8: a busca correu sobre o
OpenAlex em vez de IEEE/ACM/ScienceDirect, e o snowballing e a mitigacao
declarada para a cobertura incompleta que isso gera (ameaca V1).

Procedimento, conforme Wohlin (2014):
  - para tras: listas de referencia dos estudos da camada de profundidade
  - para frente: trabalhos que citam esses estudos
  - pontos de partida adicionais: os estudos secundarios retidos por EC4

Uso:
    python scripts/rsl_fase4_snowballing.py --medir     # so conta o volume
    python scripts/rsl_fase4_snowballing.py             # executa e grava
"""
import argparse
import csv
import datetime as dt
import io
import json
import os
import re
import sys
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
TIPOS_OK = {"article", "review", "conference-paper", "book-chapter"}


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
            raise
        except Exception:
            time.sleep(2 * (k + 1))
    return None


def norm_titulo(t):
    t = (t or "").lower()
    t = re.sub(r"[^a-z0-9 ]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def norm_doi(d):
    d = (d or "").lower().strip()
    d = d.replace("https://doi.org/", "").replace("http://dx.doi.org/", "")
    return d


def carrega_triagem():
    p = os.path.join(DADOS, "triagem.csv")
    return list(csv.DictReader(io.open(p, encoding="utf-8")))


def sementes(regs):
    """Camada de profundidade + secundarios excluidos por EC4 (protocolo, fase 4)."""
    prof = [r for r in regs
            if (r.get("fase2_camada") or "").strip().lower() == "profundidade"
            and (r.get("fase2_resumo_veredito") or "").strip().lower() == "incluir"]
    ec4 = [r for r in regs if (r.get("fase1_codigo_ec") or "").strip().upper() == "EC4"]
    return prof, ec4


def resolve_openalex(regs):
    """Mapeia cada semente ao work id do OpenAlex, em lotes por DOI."""
    por_doi = {}
    dois = [norm_doi(r["doi"]) for r in regs if r.get("doi")]
    for i in range(0, len(dois), 40):
        lote = dois[i:i + 40]
        filtro = "doi:" + "|".join("https://doi.org/" + d for d in lote)
        url = (API + "?filter=" + urllib.parse.quote(filtro, safe=":|/.,")
               + "&per-page=200&select=id,doi,title,publication_year,referenced_works,cited_by_count")
        d = get(url)
        if not d:
            continue
        for w in d.get("results", []):
            por_doi[norm_doi(w.get("doi"))] = w
        time.sleep(0.2)
    return por_doi


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--medir", action="store_true", help="so conta o volume, nao busca metadados")
    args = ap.parse_args()

    regs = carrega_triagem()
    prof, ec4 = sementes(regs)
    print("sementes: %d da camada de profundidade + %d secundarios EC4" % (len(prof), len(ec4)))

    todas = prof + ec4
    resolvidas = resolve_openalex(todas)
    print("resolvidas no OpenAlex por DOI: %d de %d" % (len(resolvidas), len(todas)))

    # ---- para tras: referencias citadas pelas sementes
    para_tras = set()
    for w in resolvidas.values():
        for ref in (w.get("referenced_works") or []):
            para_tras.add(ref)
    print("para tras, referencias unicas: %d" % len(para_tras))

    # ---- para frente: quem cita as sementes (so conta, na medicao)
    ids = [w["id"].rsplit("/", 1)[-1] for w in resolvidas.values()]
    total_citantes = 0
    citantes_por_semente = {}
    for k, wid in enumerate(ids):
        filtro = ("cites:%s,type:%s,from_publication_date:%d-01-01,to_publication_date:%d-12-31"
                  % (wid, "|".join(sorted(TIPOS_OK)), JANELA_MIN, JANELA_MAX))
        url = (API + "?filter=" + urllib.parse.quote(filtro, safe=":|/.,-")
               + "&per-page=1&select=id")
        d = get(url)
        n = (d or {}).get("meta", {}).get("count", 0)
        citantes_por_semente[wid] = n
        total_citantes += n
        if (k + 1) % 25 == 0:
            print("  ... %d/%d sementes consultadas, %d citantes acumulados"
                  % (k + 1, len(ids), total_citantes))
        time.sleep(0.15)

    print("para frente, citacoes (com repeticao entre sementes): %d" % total_citantes)

    medicao = {
        "data": dt.date.today().isoformat(),
        "sementes_profundidade": len(prof),
        "sementes_ec4": len(ec4),
        "resolvidas": len(resolvidas),
        "para_tras_unicas": len(para_tras),
        "para_frente_com_repeticao": total_citantes,
        "citantes_por_semente": citantes_por_semente,
    }
    json.dump(medicao, io.open(os.path.join(DADOS, "fase4_medicao.json"), "w", encoding="utf-8"),
              indent=1, ensure_ascii=False)
    json.dump(sorted(para_tras), io.open(os.path.join(DADOS, "fase4_para_tras_ids.json"), "w",
                                         encoding="utf-8"), indent=1)
    print("\ngravado: fase4_medicao.json e fase4_para_tras_ids.json")


if __name__ == "__main__":
    main()
