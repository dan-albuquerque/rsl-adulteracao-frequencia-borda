# -*- coding: utf-8 -*-
"""S1: taxonomia de estrategia de customizacao (protocolo_rsl.md, secao 9), construida
por leitura indutiva do campo `estrategia_customizacao` dos 87 estudos da camada de
profundidade.

Cobertura: 87 de 2.442 estudos incluidos no corpus (3,6%). Isto e uma TAXONOMIA
PROVISORIA — quando a camada de mapeamento (2.355 estudos) for extraida, cada novo
estudo precisa ser encaixado nestas categorias (ou provocar uma nova, se nao couber),
nao redefinir o esquema do zero.

CINCO CATEGORIAS, aplicadas nesta ordem de prioridade (a primeira que valer decide):

  D  Nao-arquitetural     A contribuicao nao e uma arquitetura de deteccao: estrategia
                          de treino, geracao de dado, marca d'agua ativa, ataque ou
                          evasao contra detectores
  E  Ensemble             Fusao de dois ou mais BACKBONES INTEIROS, publicados e
                          treinados independentemente, combinados prontos (nao
                          customizacoes sobre um backbone compartilhado)
  C  Classico, sem rede   Sem grafo computacional aprendido por descida de gradiente:
                          estatistica, SVM, KNN, arvore de decisao sobre atributos
                          manuais
  A  Multi-ramo paralelo  Dois ou mais encoders com peso proprio, cada um dedicado a
                          um dominio de representacao, fundidos em algum ponto
  B  Modulo unico /       Um backbone continuo unico; a customizacao e um ou poucos
     transformacao        modulos plugados nele, OU uma transformacao/aumento da
     de entrada           entrada (canais extras, decomposicao em bandas) que
                          alimenta esse backbone unico

Referencia cruzada: cada id tambem carrega o `ponto_intervencao` e `dominio_aplicacao`
ja extraidos em planilhas/extracao.csv, nao repetidos aqui.

ACHADOS DE INTEGRIDADE feitos durante esta leitura (nao estavam nas sinalizacoes
anteriores, ver dados/_SINALIZACOES_FASE3.md, secao K):

  S0578  qa1 estava com 1 (equivocado). O metodo classifica por KNN sobre um vetor de
         79 dimensoes de atributos manuais (DFT do histograma + filtro passa-alta).
         NENHUMA rede neural. Mesmo padrao do EC2 ja descrito no CLAUDE.md: extrator
         anterior pontuou customizacao arquitetural onde nao havia. Candidato a EC2.
         AFETA A SINTESE S3: contava como um dos 6 precedentes com avalia_interacao=sim
         no par frequencia+borda; se excluido, o par cai para 5.

  S1301  qa1 ja estava corretamente em 0. Pipeline de purificacao adversarial que
         ATACA detectores (substitui deconvolucao por upsampling+blur, suprime
         alta frequencia, alinha distribuicao latente via DINO-v2), mesmo padrao do
         S0683 (DeepNotch) ja sinalizado. Nao afeta S3 (avalia_interacao=nao).
"""
import csv
import io
import json
import os
import collections

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RSL = os.path.join(RAIZ, 'revisao_sistematica')
CSV = os.path.join(RSL, 'planilhas', 'extracao.csv')
DADOS = os.path.join(RSL, 'dados')

CATEGORIAS = {
    'A': 'multi_ramo_paralelo',
    'B': 'modulo_ou_transformacao_entrada',
    'C': 'classico_sem_rede',
    'D': 'nao_arquitetural',
    'E': 'ensemble_entre_modelos',
}

TAXONOMIA = {
    'N1198': 'A', 'N1211': 'A', 'N1338': 'A', 'N2147': 'A',
    'S0020': 'A', 'S0043': 'A', 'S0057': 'A', 'S0059': 'A', 'S0074': 'A',
    'S0094': 'D', 'S0122': 'B', 'S0195': 'A', 'S0200': 'B',
    'S0225': 'B', 'S0231': 'B', 'S0240': 'D', 'S0255': 'C', 'S0272': 'B',
    'S0280': 'B', 'S0290': 'C', 'S0334': 'A', 'S0336': 'C',
    'S0341': 'A', 'S0358': 'C', 'S0387': 'C', 'S0390': 'A', 'S0393': 'B',
    'S0404': 'A', 'S0427': 'A', 'S0447': 'B', 'S0449': 'A', 'S0453': 'B',
    'S0456': 'A', 'S0465': 'C', 'S0467': 'B', 'S0521': 'A', 'S0523': 'A',
    'S0588': 'A', 'S0591': 'B', 'S0594': 'B', 'S0608': 'A',
    'S0614': 'A', 'S0621': 'D', 'S0622': 'B', 'S0626': 'B', 'S0656': 'B',
    'S0677': 'B', 'S0678': 'A', 'S0689': 'B', 'S0701': 'B',
    'S0702': 'B', 'S0724': 'A', 'S0727': 'A', 'S0734': 'A', 'S0747': 'B',
    'S0795': 'B', 'S0799': 'B', 'S0842': 'D', 'S0856': 'B', 'S0868': 'B',
    'S0876': 'A', 'S0889': 'B', 'S0913': 'C', 'S0941': 'A', 'S1011': 'A',
    'S1028': 'E', 'S1063': 'A', 'S1066': 'A', 'S1075': 'A', 'S1095': 'A',
    'S1118': 'A', 'S1128': 'C', 'S1149': 'A', 'S1152': 'A', 'S1222': 'A',
    'S1265': 'A', 'S1291': 'A', 'S1320': 'A',
    'S1322': 'A', 'S1374': 'E', 'S1400': 'A',
}


def main():
    regs = {r['id']: r for r in csv.DictReader(io.open(CSV, encoding='utf-8'))}
    faltando = set(regs) - set(TAXONOMIA)
    sobrando = set(TAXONOMIA) - set(regs)
    assert not faltando, 'sem categoria: %s' % faltando
    assert not sobrando, 'id nao existe em extracao.csv: %s' % sobrando

    cont = collections.Counter(TAXONOMIA.values())
    por_categoria = collections.defaultdict(list)
    for i, c in TAXONOMIA.items():
        por_categoria[c].append(i)

    # cruzamento categoria x dominio_aplicacao
    cruz = collections.defaultdict(collections.Counter)
    for i, c in TAXONOMIA.items():
        cruz[c][regs[i]['dominio_aplicacao']] += 1

    resumo = {
        'n': len(TAXONOMIA),
        'cobertura_pct': round(100.0 * len(TAXONOMIA) / 2442, 1),
        'contagem': {CATEGORIAS[k]: v for k, v in cont.items()},
        'ids_por_categoria': {CATEGORIAS[k]: sorted(v) for k, v in por_categoria.items()},
        'cruzamento_categoria_dominio_aplicacao': {
            CATEGORIAS[k]: dict(v) for k, v in cruz.items()
        },
    }
    destino = os.path.join(DADOS, 'sintese_s1_taxonomia.json')
    json.dump(resumo, io.open(destino, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)

    print('=== S1: taxonomia de estrategia de customizacao (provisoria, %.1f%% do corpus) ===' % resumo['cobertura_pct'])
    for k in ['A', 'B', 'C', 'D', 'E']:
        print('%-32s %3d' % (CATEGORIAS[k], cont[k]))
    print('\ngravado:', destino)


if __name__ == '__main__':
    main()
