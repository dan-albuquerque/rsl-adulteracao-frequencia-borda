# -*- coding: utf-8 -*-
"""Fase 3: consolida os JSON de extracao numa planilha unica (Tabela 3b do protocolo).

Referencia: revisao_sistematica/protocolo_rsl.md, secao 8.

Faz tres coisas alem de juntar:

  1. Preenche autores, ano e veiculo a partir da triagem.csv quando o extrator
     nao conseguiu le-los do texto. O metadado bibliografico e do registro da
     busca, nao do PDF: varios PDFs sao copias de preprint ou nao trazem o
     cabecalho do periodico, e deixar o extrator adivinhar isso produziria
     veiculo errado num campo que a sintese usa para estratificar.
  2. Valida os vocabularios fechados e reporta violacoes, sem corrigi-las.
  3. Calcula qa_total e grava tambem um resumo agregado.

Uso:
    python scripts/rsl_fase3_consolida.py
"""
import csv
import io
import json
import os
import collections

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RSL = os.path.join(RAIZ, 'revisao_sistematica')
DADOS = os.path.join(RSL, 'dados')
EXTRACAO = os.path.join(DADOS, 'extracao')
SAIDA = os.path.join(RSL, 'planilhas')

CAMPOS = [
    'id', 'autores', 'ano', 'veiculo', 'tipo_publicacao', 'tipo_veiculo',
    'dominio_aplicacao', 'tipo_adulteracao', 'backbone_base',
    'estrategia_customizacao', 'ponto_intervencao', 'dominio_representacao',
    'operador_fusao', 'fusao_condicional', 'combina_multiplas', 'quais_combinadas',
    'avalia_interacao', 'datasets', 'metricas', 'protocolo_validacao',
    'resultado_principal', 'ganho_sobre_baseline', 'cross_dataset',
    'queda_cross_dataset', 'custo_params', 'custo_flops', 'custo_latencia',
    'hardware_reportado', 'ablacao', 'escopo_ablacao', 'limitacoes_declaradas',
    'qa1', 'qa2', 'qa3', 'qa4', 'qa5', 'qa6', 'qa_total',
    'extracao_origem', 'falha_leitura', 'observacao_extrator',
]

VOCAB = {
    'ponto_intervencao': {'entrada_bruta', 'camadas_iniciais', 'corpo',
                          'camadas_finais', 'cabeca', 'transversal'},
    'operador_fusao': {'concatenacao', 'soma', 'atencao', 'gate_aprendivel',
                       'canais_entrada', 'ausente'},
    'avalia_interacao': {'sim', 'nao', 'parcial'},
    'combina_multiplas': {'sim', 'nao'},
    'fusao_condicional': {'sim', 'nao'},
    'cross_dataset': {'sim', 'nao'},
    'ablacao': {'sim', 'nao'},
    'tipo_publicacao': {'periodico', 'conferencia'},
    'dominio_aplicacao': {'documento', 'face', 'imagem_natural', 'misto',
                          'sensoriamento_remoto', 'medico'},
}
# 'nao_informado' e 'nao_aplica' sao sempre aceitos: sao a regra de ouro.
NEUTROS = {'nao_informado', 'nao_aplica'}


def main():
    triagem = {r['id']: r for r in csv.DictReader(
        io.open(os.path.join(DADOS, 'triagem.csv'), encoding='utf-8'))}

    linhas, violacoes, backfill = [], [], collections.Counter()
    for nome in sorted(os.listdir(EXTRACAO)):
        if not nome.endswith('.json'):
            continue
        j = json.load(io.open(os.path.join(EXTRACAO, nome), encoding='utf-8'))
        rid = j.get('id') or nome[:-5]
        t = triagem.get(rid, {})

        # metadado bibliografico vem do registro da busca, nao do PDF
        for campo, origem in (('autores', 'autores'), ('ano', 'ano'), ('veiculo', 'veiculo')):
            atual = str(j.get(campo) or '').strip()
            if (not atual or atual in NEUTROS) and t.get(origem, '').strip():
                j[campo] = t[origem].strip()
                backfill[campo] += 1

        total = 0.0
        for k in range(1, 7):
            try:
                total += float(j.get('qa%d' % k) or 0)
            except (TypeError, ValueError):
                violacoes.append((rid, 'qa%d' % k, repr(j.get('qa%d' % k))))
        j['qa_total'] = total

        for campo, permitido in VOCAB.items():
            v = str(j.get(campo) or '').strip().lower()
            if v and v not in permitido and v not in NEUTROS:
                violacoes.append((rid, campo, v))

        linhas.append({c: j.get(c, '') for c in CAMPOS})

    if not os.path.isdir(SAIDA):
        os.makedirs(SAIDA)
    destino = os.path.join(SAIDA, 'extracao.csv')
    with io.open(destino, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS)
        w.writeheader()
        w.writerows(linhas)

    def conta(campo):
        return dict(collections.Counter(l[campo] for l in linhas).most_common())

    qas = sorted(l['qa_total'] for l in linhas)
    n = len(qas)
    resumo = {
        'estudos': n,
        'qa_media': round(sum(qas) / n, 3) if n else 0,
        'qa_mediana': (qas[n // 2] if n % 2 else (qas[n // 2 - 1] + qas[n // 2]) / 2) if n else 0,
        'avalia_interacao': conta('avalia_interacao'),
        'combina_multiplas': conta('combina_multiplas'),
        'operador_fusao': conta('operador_fusao'),
        'ponto_intervencao': conta('ponto_intervencao'),
        'dominio_aplicacao': conta('dominio_aplicacao'),
        'ablacao': conta('ablacao'),
        'cross_dataset': conta('cross_dataset'),
        'com_falha_leitura': [l['id'] for l in linhas if l['falha_leitura']],
        'violacoes_vocabulario': violacoes,
        'metadado_preenchido_da_triagem': dict(backfill),
    }
    json.dump(resumo, io.open(os.path.join(DADOS, 'fase3_resumo.json'), 'w',
                              encoding='utf-8'), indent=1, ensure_ascii=False)

    print('estudos consolidados : %d -> %s' % (n, destino))
    print('qa media %.2f | mediana %.2f' % (resumo['qa_media'], resumo['qa_mediana']))
    print('avalia_interacao     : %s' % resumo['avalia_interacao'])
    print('metadado da triagem  : %s' % dict(backfill))
    print('falha de leitura     : %s' % (resumo['com_falha_leitura'] or 'nenhuma'))
    if violacoes:
        print('\nVIOLACOES DE VOCABULARIO (%d), corrigir a mao:' % len(violacoes))
        for rid, campo, v in violacoes:
            print('  %s  %-22s %s' % (rid, campo, v))


if __name__ == '__main__':
    main()
