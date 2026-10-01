# -*- coding: utf-8 -*-
"""Camada de mapeamento: prepara os lotes de entrada para a extracao reduzida (Tabela 3a).

Referencia: revisao_sistematica/protocolo_rsl.md, secoes 3.1 e 8 (Tabela 3a).

Universo: 2.355 estudos
  - 909 do corpus primario  (triagem.csv,       fase2_camada == mapeamento)
  - 1.446 do snowballing     (fase4_triagem.csv, fase2_camada == mapeamento)

Saida: revisao_sistematica/dados/mapeamento_lotes/lote_NN.jsonl, um estudo por linha,
com id, origem, ano, veiculo, titulo e resumo. O resumo e truncado em 3.000 caracteres
(afeta menos de 2% dos registros; o que importa para a Tabela 3a esta no inicio).
"""
import csv
import io
import json
import os

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DADOS = os.path.join(RAIZ, 'revisao_sistematica', 'dados')
SAIDA = os.path.join(DADOS, 'mapeamento_lotes')
TAM_LOTE = 118
MAX_RESUMO = 3000


def carrega():
    regs = []
    for r in csv.DictReader(io.open(os.path.join(DADOS, 'triagem.csv'), encoding='utf-8')):
        if (r.get('fase2_camada') == 'mapeamento' and r['fase1_titulo_veredito'] == 'incluir'
                and r['fase2_resumo_veredito'] == 'incluir'):
            regs.append((r, 'primario'))
    for r in csv.DictReader(io.open(os.path.join(DADOS, 'fase4_triagem.csv'), encoding='utf-8')):
        if r.get('fase2_camada') == 'mapeamento':
            regs.append((r, 'snowballing'))
    return regs


def main():
    regs = carrega()
    if not os.path.isdir(SAIDA):
        os.makedirs(SAIDA)
    for f in os.listdir(SAIDA):
        os.remove(os.path.join(SAIDA, f))

    n_lotes = 0
    for i in range(0, len(regs), TAM_LOTE):
        n_lotes += 1
        caminho = os.path.join(SAIDA, 'lote_%02d.jsonl' % n_lotes)
        with io.open(caminho, 'w', encoding='utf-8') as f:
            for r, origem in regs[i:i + TAM_LOTE]:
                f.write(json.dumps({
                    'id': r['id'],
                    'origem': origem,
                    'ano': r['ano'],
                    'veiculo': r.get('veiculo', ''),
                    'titulo': r['titulo'],
                    'resumo': r['resumo'].strip()[:MAX_RESUMO],
                }, ensure_ascii=False) + '\n')

    sem = sum(1 for r, _ in regs if not r['resumo'].strip())
    print('estudos: %d (sem resumo: %d) em %d lotes de ate %d'
          % (len(regs), sem, n_lotes, TAM_LOTE))


if __name__ == '__main__':
    main()
