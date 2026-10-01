# -*- coding: utf-8 -*-
"""Procura a configuracao (string x regra de promocao) que deixa a camada de
PROFUNDIDADE abaixo de 20 estudos, que e o que o autor precisa ler.

Duas alavancas independentes:
  1. a string de busca, que define o corpus
  2. a regra de promocao a profundidade (protocolo, secao 3.1 / D9), hoje
     "frequencia E (borda OU ruido)"

A regra alternativa "frequencia E borda" e o par exato que o estudo primario
combina (ramo DCT + modulos de borda), portanto um estreitamento alinhado a RQ1.3,
nao arbitrario.

Restricao: manter pelo menos 1 dos 5 precedentes do achado central.
"""
import csv
import io
import json
import os
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
DET_B = '("detection" OR "detecting")'
PROPOSE = '("propose" OR "novel" OR "we present" OR "introduce")'
AVAL = '("dataset" OR "accuracy" OR "AUC" OR "F1")'

STRINGS = [
    ("v1 baseline", CUST_BASE, []),
    ("C4 cust enxuto", CUST_ENX, []),
    ("MAX (4 blocos)", CUST_ENX, [DET_B, PROPOSE, AVAL]),
]

REGRAS = [
    ("atual: freq E (borda OU ruido)", lambda d: "frequencia" in d and ({"borda", "ruido"} & d)),
    ("estrita: freq E borda", lambda d: {"frequencia", "borda"} <= d),
    ("estritissima: freq E borda E ruido", lambda d: {"frequencia", "borda", "ruido"} <= d),
]

PRECEDENTES = ["S0467", "S0280", "S0876", "S0272", "S0059"]


def busca_ids(tarefa, cust, extras, pausa=0.2):
    busca = " AND ".join([tarefa, cust] + list(extras))
    filtro = "title_and_abstract.search:{},{},{}".format(busca, JANELA, TIPOS)
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


def main():
    with io.open(os.path.join(DADOS, "corpus_bruto.json"), encoding="utf-8") as f:
        bruto = json.load(f)
    oa2sid = {w["id"]: "S{:04d}".format(i + 1) for i, w in enumerate(bruto)}

    tri = {r["id"]: r for r in csv.DictReader(io.open(os.path.join(DADOS, "triagem.csv"), encoding="utf-8"))}
    extr = {r["id"] for r in csv.DictReader(io.open(os.path.join(PLANILHAS, "extracao.csv"), encoding="utf-8"))}

    corpora = {}
    for nome, cust, extras in STRINGS:
        ids = busca_ids(DOC, cust, extras) | busca_ids(FACE, cust, extras)
        corpora[nome] = (len(ids), set(oa2sid[i] for i in ids if i in oa2sid))
        print("{:18s} corpus = {}".format(nome, len(ids)))

    print("\n{:18s} {:34s} {:>6s} {:>9s} {:>9s}  {}".format(
        "string", "regra de promocao", "prof.", "ja extr.", "a ler", "precedentes mantidos"))
    print("-" * 112)
    for nome_s, (n_corpus, sids) in corpora.items():
        for nome_r, regra in REGRAS:
            prof = []
            for sid in sids:
                r = tri.get(sid)
                if not r or r["fase1_titulo_veredito"] != "incluir":
                    continue
                if r.get("fase2_codigo_ec") == "EC2":
                    continue
                doms = set(x for x in (r.get("dominios_detectados") or "").split("+") if x)
                if regra(doms):
                    prof.append(sid)
            ja = [s for s in prof if s in extr]
            prec = [p for p in PRECEDENTES if p in prof]
            print("{:18s} {:34s} {:>6d} {:>9d} {:>9d}  {} ({})".format(
                nome_s, nome_r, len(prof), len(ja), len(prof) - len(ja),
                ",".join(prec) if prec else "NENHUM", len(prec)))

    print("\n'a ler' = estudos da profundidade que ainda nao tem extracao pronta.")
    print("'ja extr.' = ja foram lidos e extraidos no v1, aproveitaveis sem retrabalho.")


if __name__ == "__main__":
    main()
