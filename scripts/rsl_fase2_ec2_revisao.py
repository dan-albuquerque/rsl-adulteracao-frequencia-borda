# -*- coding: utf-8 -*-
"""Revisao humana-assistida das exclusoes por EC2 na fase 2.

Referencia: protocolo_rsl.md, secao 10.2 (pendencia declarada) e ameaca V7.

A atribuicao inicial de camadas (scripts/rsl_fase2_camadas.py) aplicou EC2 por
regra lexica e excluiu apenas 35 de 1.151, numero incompativel com a amostragem
manual, que indicava cerca de 40% na subpopulacao com resumo.

O diagnostico confirmou que a regra nao serve para EC2: "ausencia de sinal de
rede neural no resumo" produz falsos positivos (ObjectFormer e Proposal
Contrastive Learning foram sinalizados sendo redes), pela mesma razao da
correcao C1 da secao 4.3.1: artigos da area nao anunciam no resumo que usam rede
neural. EC2 exige leitura.

Este arquivo registra as exclusoes por EC2 decididas por LEITURA dos resumos dos
169 candidatos levantados. Cada identificador abaixo foi lido individualmente.

CATEGORIAS APLICADAS
  classico   metodo sem rede neural: DCT/DWT com casamento de blocos, SIFT,
             SURF, BRISK, Zernike, k-means, algoritmos de otimizacao, SVM sobre
             atributos manuais, modelagem estatistica, marca d'agua
  extrator   rede pre-treinada usada como extrator fixo de atributos, com
             classificador classico acoplado; grafo inalterado
  treino     a contribuicao e estrategia de treino, aumento de dados ou
             pre-processamento; grafo inalterado
  ensemble   combinacao de modelos prontos, votacao, fusao em nivel de escore
  estudo     estudo comparativo, investigacao ou analise, sem arquitetura propria
  ataque     ataque adversarial a detectores ou defesa, sem detector proprio
  dataset    contribuicao e conjunto de dados ou benchmark
"""
import csv
import io
import json
import os

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DADOS = os.path.join(RAIZ, 'revisao_sistematica', 'dados')
CSV = os.path.join(DADOS, 'triagem.csv')

EC2 = {}


def marcar(cat, ids):
    for i in ids.split():
        assert i not in EC2, "repetido: " + i
        EC2[i] = cat


marcar("classico", """
S0028 S0031 S0048 S0068 S0070 S0071 S0073 S0075 S0078 S0088 S0091 S0096
S0100 S0102 S0106 S0114 S0115 S0144 S0160 S0172 S0177 S0179 S0185 S0188 S0192
S0201 S0216 S0232 S0271 S0276 S0493 S0514 S0537
""")

marcar("extrator", "S0182 S0252 S0259 S0545 S0641")

marcar("treino", "S0757 S0765 S0808 S0999")

marcar("ensemble", "S0956 S1234")

marcar("estudo", "S0081 S0150 S0234 S0498 S0699 S0829 S0850 S1183 S1330 S1335 S1365")

marcar("ataque", "S0602 S0923 S1131 S1313 S1334")

marcar("dataset", "S0107 S1061")

marcar("marcadagua", "S0250 S0485 S1015")


def main():
    regs = list(csv.DictReader(io.open(CSV, encoding='utf-8')))
    cols = list(regs[0].keys())
    ids = {r['id'] for r in regs}
    orfaos = [i for i in EC2 if i not in ids]
    assert not orfaos, "identificadores inexistentes: %s" % orfaos

    prof_afetados, novos = [], 0
    for r in regs:
        if r['id'] not in EC2:
            continue
        if r['fase1_titulo_veredito'] != 'incluir':
            continue
        if r.get('fase2_camada') == 'profundidade':
            prof_afetados.append(r['id'])
        if r['fase2_resumo_veredito'] != 'excluir':
            novos += 1
        r['fase2_resumo_veredito'] = 'excluir'
        r['fase2_codigo_ec'] = 'EC2'
        r['fase2_camada'] = ''
        r['fase2_avaliador'] = 'IA-assistida, resumo lido'
        r['observacoes'] = 'EC2: ' + EC2[r['id']]

    with io.open(CSV, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(regs)

    json.dump(EC2, io.open(os.path.join(DADOS, 'fase2_ec2_revisado.json'), 'w',
                           encoding='utf-8'), indent=1, sort_keys=True)

    import collections
    c = collections.Counter(EC2.values())
    print("=== Revisao das exclusoes por EC2 ===")
    print("  exclusoes por EC2 apos revisao : %d" % len(EC2))
    for k in sorted(c):
        print("    %-12s %3d" % (k, c[k]))
    print("  novas nesta revisao            : %d" % novos)
    print("  afetavam a camada de profundidade: %d %s" % (len(prof_afetados), prof_afetados))

    vivos = [r for r in regs if r['fase1_titulo_veredito'] == 'incluir'
             and r['fase2_resumo_veredito'] == 'incluir']
    mapa = [r for r in vivos if r.get('fase2_camada') == 'mapeamento']
    prof = [r for r in vivos if r.get('fase2_camada') == 'profundidade']
    print("\n  mapeamento   : %d" % len(mapa))
    print("  profundidade : %d" % len(prof))


if __name__ == '__main__':
    main()
