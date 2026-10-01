# -*- coding: utf-8 -*-
"""Compara variantes de string pelo que elas PRESERVAM da evidencia ja extraida,
nao so pelo volume que cortam.

Para cada variante, executa a busca completa (primaria + secundaria) e mede:
  - tamanho do corpus
  - quantos dos 77 extraidos do corpus primario sobrevivem
  - quantos dos 26 com avalia_interacao=sim sobrevivem
  - o par frequencia+borda: quantos estudos e quantos com ablacao cruzada genuina
  - quais dos 5 precedentes do achado central sobrevivem

Exige OPENALEX_API_KEY no ambiente. Nao grava nada em dados/, so imprime a tabela.
"""
import collections
import csv
import io
import json
import os
import sys
import time
import urllib.parse
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DADOS = os.path.join(RAIZ, "revisao_sistematica", "dados")
PLANILHAS = os.path.join(RAIZ, "revisao_sistematica", "planilhas")

UA = {"User-Agent": "mailto:dam@cesar.school"}
API_KEY = os.environ.get("OPENALEX_API_KEY", "")
JANELA = "from_publication_date:2020-01-01,to_publication_date:2026-12-31"
TIPOS = "type:article|review|conference-paper"

DOC = ('("image forgery" OR "image tampering" OR "image manipulation detection" '
       'OR "document forgery" OR "document tampering" OR "tampered text" '
       'OR "splicing detection" OR "copy-move" OR "image forensics")')
FACE = '("deepfake detection" OR "face forgery")'
CUST_BASE = ('("frequency" OR "discrete cosine transform" OR "DCT" OR "high-frequency" '
             'OR "edge attention" OR "attention module" OR "plug-in module" '
             'OR "two-stream" OR "dual-stream" OR "feature fusion" OR "backbone modification")')
CUST_ENX = ('("frequency" OR "discrete cosine transform" OR "DCT" OR "high-frequency" '
            'OR "edge attention" OR "two-stream" OR "dual-stream")')
DET_FULL = '("detection" OR "detecting" OR "classification")'
DET_B = '("detection" OR "detecting")'
PROPOSE = '("propose" OR "novel" OR "we present" OR "introduce")'
AVAL = '("dataset" OR "accuracy" OR "AUC" OR "F1")'

VARIANTES = [
    ("v1 baseline (atual)",            CUST_BASE, []),
    ("cust enxuto",                    CUST_ENX,  []),
    ("cust + deteccao(full)",          CUST_ENX,  [DET_FULL]),
    ("cust + deteccao(B)",             CUST_ENX,  [DET_B]),
    ("cust + propose  (isolado)",      CUST_ENX,  [PROPOSE]),
    ("cust + avaliacao (isolado)",     CUST_ENX,  [AVAL]),
    ("A: cust+det(full)+propose",      CUST_ENX,  [DET_FULL, PROPOSE]),
    ("C: cust+det(full)+aval",         CUST_ENX,  [DET_FULL, AVAL]),
    ("B+A: cust+det(B)+propose",       CUST_ENX,  [DET_B, PROPOSE]),
    ("C+B: cust+det(B)+aval",          CUST_ENX,  [DET_B, AVAL]),
    ("MAX: cust+det(B)+propose+aval",  CUST_ENX,  [DET_B, PROPOSE, AVAL]),
]

PRECEDENTES = ["S0467", "S0280", "S0876", "S0272", "S0059"]


def _filtro(tarefa, cust, extras):
    busca = " AND ".join([tarefa, cust] + list(extras))
    return "title_and_abstract.search:{},{},{}".format(busca, JANELA, TIPOS)


def busca_ids(tarefa, cust, extras, pausa=0.2):
    filtro = _filtro(tarefa, cust, extras)
    ids, cursor = set(), "*"
    while cursor:
        url = ("https://api.openalex.org/works?filter="
               + urllib.parse.quote(filtro, safe=":,|")
               + "&per-page=200&cursor=" + cursor + "&select=id")
        if API_KEY:
            url += "&api_key=" + API_KEY
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
            d = json.load(r)
        if not d["results"]:
            break
        ids.update(w["id"] for w in d["results"])
        cursor = d["meta"].get("next_cursor")
        time.sleep(pausa)
    return ids


def par_norm(s):
    xs = sorted(x.strip() for x in (s or "").replace(" e ", ",").replace("+", ",").split(",") if x.strip())
    return xs


def main():
    with io.open(os.path.join(DADOS, "corpus_bruto.json"), encoding="utf-8") as f:
        bruto = json.load(f)
    oa2sid = {w["id"]: "S{:04d}".format(i + 1) for i, w in enumerate(bruto)}

    extr = {r["id"]: r for r in csv.DictReader(io.open(os.path.join(PLANILHAS, "extracao.csv"), encoding="utf-8"))}
    prim = {i: r for i, r in extr.items() if i.startswith("S")}

    print("extraidos do corpus primario: {}".format(len(prim)))
    print("\n{:30s} {:>6s} {:>8s} {:>7s} {:>10s}  {}".format(
        "variante", "corpus", "extr/77", "sim/26", "freq+borda", "precedentes perdidos"))
    print("-" * 108)

    for nome, cust, extras in VARIANTES:
        try:
            ids = busca_ids(DOC, cust, extras) | busca_ids(FACE, cust, extras)
        except Exception as e:
            print("{:30s}  ERRO: {}".format(nome, e))
            continue
        sids = set(oa2sid[i] for i in ids if i in oa2sid)
        viv = [r for i, r in prim.items() if i in sids]
        n_sim = sum(1 for r in viv if r["avalia_interacao"] == "sim")
        fb = [r for r in viv if {"frequencia", "borda"} <= set(par_norm(r["quais_combinadas"]))
              and r["id"] != "S1028"]
        fb_sim = sum(1 for r in fb if r["avalia_interacao"] == "sim")
        perd = [p for p in PRECEDENTES if p not in sids]
        print("{:30s} {:>6d} {:>8s} {:>7d} {:>10s}  {}".format(
            nome, len(ids), "{}/{}".format(len(viv), len(prim)), n_sim,
            "{}({})".format(len(fb), fb_sim), ",".join(perd) if perd else "nenhum"))
        sys.stdout.flush()

    print("\nLegenda: 'freq+borda' = estudos que combinam frequencia e borda (inclui triplas),")
    print("com o numero de ablacao cruzada genuina entre parenteses. Corpus atual: 18(5).")


if __name__ == "__main__":
    main()
