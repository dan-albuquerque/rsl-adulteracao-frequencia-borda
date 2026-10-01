# -*- coding: utf-8 -*-
"""S2 (RQ1.2) sobre a camada de mapeamento, com o vocabulario final (protocolo, secao 3.1).

Dominio de cada estudo = regra mecanica final (`dominios_detectados` em dados/v2/triagem.csv
e dados/v2/fase4_triagem.csv), que cobre frequencia, borda e ruido em todo o corpus,
unida aos dominios atribuidos por leitura de titulo e resumo nos 391 estudos lidos
(`lido_por_ia == sim`), unica fonte de espacial, textura e temporal.

Regrava a coluna `dominios` de planilhas/v2/mapeamento.csv com esse valor e imprime S2.
"""
import collections
import csv
import io
import os

RAIZ = os.path.join(os.path.dirname(__file__), "..", "revisao_sistematica")
MAPA = os.path.join(RAIZ, "planilhas", "v2", "mapeamento.csv")

mec = {}
for nome in ("triagem.csv", "fase4_triagem.csv"):
    with io.open(os.path.join(RAIZ, "dados", "v2", nome), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            mec[r["id"]] = {t for t in r.get("dominios_detectados", "").split("+") if t}

with io.open(MAPA, encoding="utf-8") as f:
    leitor = csv.DictReader(f)
    campos = leitor.fieldnames
    linhas = list(leitor)

cont = collections.Counter()
for r in linhas:
    lido = set()
    if r["lido_por_ia"] == "sim":
        lido = {t for t in r["dominios"].split("+") if t and t != "nao_informado"}
    doms = mec[r["id"]] | lido
    r["dominios"] = "+".join(sorted(doms)) if doms else "nao_informado"
    for t in doms:
        cont[t] += 1

with io.open(MAPA, "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=campos)
    w.writeheader()
    w.writerows(linhas)

print("estudos: {}".format(len(linhas)))
for dom, n in cont.most_common():
    print("  {:<10} {}".format(dom, n))
print("  sem dominio: {}".format(sum(1 for r in linhas if r["dominios"] == "nao_informado")))
