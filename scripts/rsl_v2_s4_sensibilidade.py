# -*- coding: utf-8 -*-
"""S4 (RQ1.4) e analise de sensibilidade sobre os 18 estudos da camada de profundidade.

Protocolo, secao 9. Fontes:
  planilhas/v2/extracao.csv        primeira extracao (Tabela 3b)
  full_leitura_artigos/<id>.json   segunda extracao, independente e cega (so as notas QA)

Um campo de custo conta como reportado apenas quando traz valor; `nao_informado`,
mesmo seguido de comentario entre parenteses, nao conta.
"""
import csv
import io
import json
import os

RAIZ = os.path.join(os.path.dirname(__file__), "..", "revisao_sistematica")

with io.open(os.path.join(RAIZ, "planilhas", "v2", "extracao.csv"), encoding="utf-8") as f:
    linhas = list(csv.DictReader(f))


def qa_segunda(i):
    with io.open(os.path.join(RAIZ, "full_leitura_artigos", i + ".json"), encoding="utf-8") as f:
        d = json.load(f)
    return sum(float(d.get("qa%d" % k, 0)) for k in range(1, 7))


def informado(v):
    v = v.strip().lower()
    return bool(v) and not v.startswith("nao_informado")


def freq_borda(r):
    return "borda" in r["quais_combinadas"] and "frequencia" in r["quais_combinadas"]


qa2 = {r["id"]: qa_segunda(r["id"]) for r in linhas}
qa1 = {r["id"]: float(r["qa_total"]) for r in linhas}


def linha(nome, sub):
    n = len(sub)
    pct = lambda k: "{} ({:.0f}%)".format(k, 100.0 * k / n)
    fb = [r for r in sub if freq_borda(r)]
    sim = sorted(r["id"] for r in fb if r["avalia_interacao"] == "sim")
    print("| {} | {} | {} | {} ({}) | {} | {} | {} |".format(
        nome, n, len(fb), len(sim), ", ".join(sim) or "nenhum",
        pct(sum(r["cross_dataset"] == "sim" for r in sub)),
        pct(sum(informado(r["custo_params"]) for r in sub)),
        pct(sum(informado(r["custo_latencia"]) for r in sub))))


print("| Subconjunto | n | Freq.+borda | Precedentes sim | Entre datasets | Parametros | Latencia |")
print("|---|---|---|---|---|---|---|")
linha("Todos", linhas)
linha("So periodicos", [r for r in linhas if r["tipo_publicacao"] == "periodico"])
linha("QA >= 5,5 nas duas extracoes", [r for r in linhas if qa1[r["id"]] >= 5.5 and qa2[r["id"]] >= 5.5])
linha("QA = 6, primeira extracao", [r for r in linhas if qa1[r["id"]] == 6])
linha("QA = 6, segunda extracao", [r for r in linhas if qa2[r["id"]] == 6])
print()
print("FLOPs reportados: {}".format(sum(informado(r["custo_flops"]) for r in linhas)))
print("QA media {:.2f}; distribuicao {}".format(
    sum(qa1.values()) / len(qa1), sorted(qa1.values())))
