# -*- coding: utf-8 -*-
"""Figura do fluxo de selecao (duas camadas), no formato PRISMA 2020.

Contagens lidas de dados/v2/triagem.csv (corpus primario) e dados/v2/fase4_triagem.csv
(snowballing). As contagens de coleta do snowballing (sementes, referencias, citantes,
unicos) sao as da Tabela 1b do protocolo.

Saida: revisao_sistematica/relatorio_final/figuras/fluxo_selecao.{pdf,png}
"""
import collections
import csv
import io
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

RAIZ = os.path.join(os.path.dirname(__file__), "..", "revisao_sistematica")
SAIDA = os.path.join(RAIZ, "relatorio_final", "figuras", "fluxo_selecao")
COLETA_F4 = {"sementes": 86, "sem_prof": 35, "sem_ec4": 51, "refs": 1416, "citantes": 214, "unicos": 1492}


def ler(nome):
    with io.open(os.path.join(RAIZ, "dados", "v2", nome), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def fmt(n):
    return "{:,}".format(n).replace(",", ".")


prim, f4 = ler("triagem.csv"), ler("fase4_triagem.csv")
ec1 = collections.Counter(r["fase1_codigo_ec"] for r in prim if r["fase1_titulo_veredito"] == "excluir")
ec2 = sum(1 for r in prim if r["fase2_codigo_ec"] == "EC2")
mape = sum(1 for r in prim if r["fase2_camada"] == "mapeamento")
prof = [r for r in prim if r["fase2_camada"] == "profundidade"]
ec3 = collections.Counter(r["fase3_codigo_ec"] for r in prof if r["fase3_fulltext_veredito"] == "excluir")
extr = sum(1 for r in prof if r["fase3_fulltext_veredito"] == "incluir")
f4ec1 = collections.Counter(r["fase1_codigo_ec"] for r in f4 if r["fase1_titulo_veredito"] == "excluir")
f4ec2 = sum(1 for r in f4 if r["fase2_codigo_ec"] == "EC2")
f4map = sum(1 for r in f4 if r["fase2_camada"] == "mapeamento")
f4prof = sum(1 for r in f4 if r["fase2_camada"] == "profundidade")

AZUL, CINZA, VERDE = ("#e8eef5", "#5a7896"), ("#f3f3f3", "#8a8a8a"), ("#e6f2e8", "#4f8a5b")
fig, ax = plt.subplots(figsize=(11, 10.5))
ax.set_xlim(0, 103)
ax.set_ylim(0, 105)
ax.axis("off")


def caixa(x, y, w, h, texto, cor, tam=8.5, peso="normal"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.2",
                                facecolor=cor[0], edgecolor=cor[1], linewidth=1.1))
    ax.text(x + w / 2, y + h / 2, texto, ha="center", va="center", fontsize=tam, weight=peso, linespacing=1.35)


def seta(x1, y1, x2, y2):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color="#5a6b7c", lw=1.1, mutation_scale=12))


for y, rot in ((91, "Identificação"), (62, "Triagem"), (34, "Leitura completa"), (8, "Incluídos")):
    ax.text(0.5, y, rot, rotation=90, va="center", ha="left", fontsize=9.5, weight="bold", color="#40566b")

# colunas: snowballing S (5-29), corpus primario P (35-71), exclusoes E (77-101)
caixa(35, 91, 36, 10, "Busca no OpenAlex (2026-09-23)\nconsulta primária: 462\n"
      "consulta secundária (faces): 714\nsobreposição removida: 22", AZUL)
caixa(35, 78, 36, 6, "Registros únicos\nn = {}".format(fmt(len(prim))), AZUL, peso="bold")
caixa(77, 76, 24, 10, "Excluídos na fase 1 (título)\nn = {}\nEC1 {}, EC3 {}, EC4 {},\nEC7 {}, EC8 {}".format(
    sum(ec1.values()), ec1["EC1"], ec1["EC3"], ec1["EC4"], ec1["EC7"], ec1["EC8"]), CINZA, tam=8)
caixa(35, 64, 36, 6, "Após a fase 1\nn = {}".format(fmt(len(prim) - sum(ec1.values()))), AZUL)
caixa(77, 64, 24, 6, "Excluídos na fase 2 (resumo)\nEC2, n = {}".format(ec2), CINZA, tam=8)
caixa(35, 46, 16, 10, "Camada de\nmapeamento\nn = {}".format(mape), AZUL)
caixa(55, 46, 16, 10, "Camada de\nprofundidade\nn = {}\n(frequência + borda)".format(len(prof)), AZUL, tam=8)
caixa(55, 29, 16, 9, "Texto completo\navaliado\nn = {}".format(len(prof)), AZUL)
caixa(77, 29, 24, 9, "Excluídos na fase 3\nn = {}\nEC6 (sem texto completo) {}\nEC2 {}".format(
    sum(ec3.values()), ec3["EC6"], ec3["EC2"]), CINZA, tam=8)
seta(53, 91, 53, 84.6)
seta(71, 81, 76.4, 81)
seta(53, 78, 53, 70.6)
seta(71, 67, 76.4, 67)
seta(47, 64, 43, 56.6)
seta(59, 64, 63, 56.6)
seta(63, 46, 63, 38.6)
seta(71, 33.5, 76.4, 33.5)

caixa(5, 91, 24, 10, "Snowballing (fase 4)\nsementes: {}\n({} da profundidade +\n{} secundários retidos por EC4)".format(
    COLETA_F4["sementes"], COLETA_F4["sem_prof"], COLETA_F4["sem_ec4"]), AZUL, tam=8)
caixa(5, 76, 24, 10, "Referências únicas: {}\ncitantes: {}\nfora do corpus primário: {}\nna janela e no tipo: n = {}".format(
    fmt(COLETA_F4["refs"]), COLETA_F4["citantes"], fmt(COLETA_F4["unicos"]), len(f4)), AZUL, tam=8)
caixa(5, 60, 24, 10, "Excluídos, n = {}\nfase 1: EC1 {}, EC4 {}, EC3 {}\nfase 2: EC2 {}".format(
    sum(f4ec1.values()) + f4ec2, f4ec1["EC1"], f4ec1["EC4"], f4ec1["EC3"], f4ec2), CINZA, tam=8)
caixa(5, 46, 24, 10, "Snowballing\nmapeamento: n = {}\nprofundidade: n = {}".format(f4map, f4prof), AZUL)
seta(17, 91, 17, 86.6)
seta(17, 76, 17, 70.6)
seta(17, 60, 17, 56.6)

caixa(5, 3, 46, 10, "Camada de mapeamento\nn = {}\n({} do corpus primário + {} do snowballing)".format(
    fmt(mape + f4map), mape, f4map), VERDE, peso="bold")
caixa(55, 3, 16, 10, "Estudos\nextraídos\nn = {}".format(extr), VERDE, peso="bold")
seta(17, 46, 17, 13.6)
seta(43, 46, 43, 13.6)
seta(63, 29, 63, 13.6)

plt.tight_layout()
for ext in ("pdf", "png"):
    fig.savefig(SAIDA + "." + ext, dpi=200, bbox_inches="tight")
print("mapeamento {} + {}; profundidade {}; extraidos {}".format(mape, f4map, len(prof), extr))
