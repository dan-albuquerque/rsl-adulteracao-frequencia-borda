# -*- coding: utf-8 -*-
"""Camada de mapeamento: consolida a extracao reduzida (Tabela 3a) e calcula S1 e S2.

Referencia: revisao_sistematica/protocolo_rsl.md, secoes 8 (Tabela 3a) e 9 (S1, S2).

DECISAO DE 2026-09-21 (custo de token): a extracao por leitura via subagentes Sonnet
bateu no rate limit do servidor depois de 6 dos 20 lotes (703 de 2.355 estudos).
Decisao do autor: NAO reenviar os 14 lotes restantes. Tratamento hibrido:

  - 703 estudos (lotes 01, 04, 06, 09, 17, 20) tem TAXONOMIA S1 completa, lida por IA
    a partir de titulo e resumo (`estrategia`, `ponto_intervencao`, `operador_fusao`).
  - Os demais 1.652 estudos entram so com o campo `dominios_detectados`, que ja existia
    de graca desde a fase 2 (regex deterministica em rsl_fase2_camadas.py /
    rsl_fase4_triagem.py, sem custo de token). `estrategia`, `ponto_intervencao` e
    `operador_fusao` ficam `nao_informado` para eles: NAO FORAM LIDOS, e nao ha
    tentativa de inferir.

Consequencia declarada: S1 (taxonomia de estrategia) tem amostra de 703 do mapeamento,
nao censo dos 2.355 -- soma-se aos 81 da profundidade. S2 (dominio) tem cobertura do
corpus quase inteiro, porque dominio vem do campo mecanico, mas com vocabulario mais
estreito (a regra so detecta frequencia/borda/ruido, nao espacial/textura/metadados/
temporal) -- ameaca a favor de V9, mesma natureza.

Entrada:
  dados/mapeamento_lotes/lote_NN.jsonl   (o que foi enviado aos extratores)
  dados/mapeamento/lote_NN.json          (o que eles devolveram; so 6 de 20 existem)
  dados/triagem.csv, dados/fase4_triagem.csv (dominios_detectados mecanico, todos)
  planilhas/extracao.csv                 (camada de profundidade, 81 estudos)
  scripts/rsl_sintese_s1_taxonomia.py    (categoria S1 dos 81 da profundidade)

Saida:
  planilhas/mapeamento.csv          Tabela 3a consolidada, 2.355 linhas
  dados/sintese_s1_s2_completa.json S1 (amostra) e S2 (quase censo) sobre as duas camadas
  dados/mapeamento_alertas.csv      estudos que os 6 lotes lidos sinalizaram fora de criterio
"""
import collections
import csv
import glob
import io
import json
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RSL = os.path.join(RAIZ, 'revisao_sistematica')
DADOS = os.path.join(RSL, 'dados')
ENTRADA = os.path.join(DADOS, 'mapeamento_lotes')
SAIDA_LOTES = os.path.join(DADOS, 'mapeamento')

sys.path.insert(0, os.path.join(RAIZ, 'scripts'))
from rsl_sintese_s1_taxonomia import TAXONOMIA  # noqa: E402

DOMINIOS = {'espacial', 'frequencia', 'borda', 'ruido', 'textura', 'metadados', 'temporal'}
VOCAB = {
    'dominio_aplicacao': {'documento', 'face', 'imagem_natural', 'misto',
                          'sensoriamento_remoto', 'medico', 'nao_informado'},
    'estrategia': {'A', 'B', 'C', 'D', 'E', 'nao_informado'},
    'ponto_intervencao': {'entrada_bruta', 'camadas_iniciais', 'corpo', 'camadas_finais',
                          'cabeca', 'transversal', 'nao_informado'},
    'operador_fusao': {'concatenacao', 'soma', 'atencao', 'gate_aprendivel',
                       'canais_entrada', 'ausente', 'nao_informado'},
    'fonte': {'resumo', 'titulo'},
}
NOME_CATEGORIA = {
    'A': 'multi_ramo_paralelo', 'B': 'modulo_ou_transformacao_entrada',
    'C': 'classico_sem_rede', 'D': 'nao_arquitetural', 'E': 'ensemble_entre_modelos',
    'nao_informado': 'nao_informado',
}
CAMPOS = ['id', 'origem', 'ano', 'titulo', 'dominio_aplicacao', 'estrategia',
          'ponto_intervencao', 'dominios', 'operador_fusao', 'fonte', 'lido_por_ia', 'alerta']


def dominios_validos(s):
    if s in ('nao_informado', ''):
        return True
    partes = s.split('+')
    return bool(partes) and all(p in DOMINIOS for p in partes)


def carrega_mecanico():
    """dominios_detectados de todo o corpus, calculado de graca na fase 2/4."""
    m = {}
    for r in csv.DictReader(io.open(os.path.join(DADOS, 'triagem.csv'), encoding='utf-8')):
        m[r['id']] = r.get('dominios_detectados', '')
    for r in csv.DictReader(io.open(os.path.join(DADOS, 'fase4_triagem.csv'), encoding='utf-8')):
        m[r['id']] = r.get('dominios_detectados', '')
    return m


def main():
    problemas = []
    linhas = []
    lidos_por_ia = set()
    dominio_mecanico = carrega_mecanico()

    lotes_lidos, lotes_faltando = [], []
    for caminho_in in sorted(glob.glob(os.path.join(ENTRADA, 'lote_*.jsonl'))):
        nome = os.path.basename(caminho_in).replace('.jsonl', '')
        entrada = [json.loads(l) for l in io.open(caminho_in, encoding='utf-8') if l.strip()]
        caminho_out = os.path.join(SAIDA_LOTES, nome + '.json')

        if not os.path.exists(caminho_out):
            lotes_faltando.append(nome)
            for e in entrada:
                fonte_real = 'resumo' if e['resumo'].strip() else 'titulo'
                dom = dominio_mecanico.get(e['id'], '') or 'nao_informado'
                linhas.append({
                    'id': e['id'], 'origem': e['origem'], 'ano': e['ano'], 'titulo': e['titulo'],
                    'dominio_aplicacao': 'nao_informado', 'estrategia': 'nao_informado',
                    'ponto_intervencao': 'nao_informado', 'dominios': dom,
                    'operador_fusao': 'nao_informado', 'fonte': fonte_real,
                    'lido_por_ia': 'nao', 'alerta': '',
                })
            continue

        lotes_lidos.append(nome)
        saida = json.load(io.open(caminho_out, encoding='utf-8'))
        ids_in = [e['id'] for e in entrada]
        ids_out = [s.get('id') for s in saida]
        if ids_in != ids_out:
            perdidos = sorted(set(ids_in) - set(ids_out))
            extras = sorted(set(ids_out) - set(ids_in))
            problemas.append((nome, 'ids', 'perdidos=%s extras=%s ordem_ok=%s'
                              % (perdidos, extras, sorted(ids_in) == sorted(ids_out))))

        por_id = {s.get('id'): s for s in saida}
        for e in entrada:
            s = por_id.get(e['id'])
            if s is None:
                fonte_real = 'resumo' if e['resumo'].strip() else 'titulo'
                dom = dominio_mecanico.get(e['id'], '') or 'nao_informado'
                linhas.append({
                    'id': e['id'], 'origem': e['origem'], 'ano': e['ano'], 'titulo': e['titulo'],
                    'dominio_aplicacao': 'nao_informado', 'estrategia': 'nao_informado',
                    'ponto_intervencao': 'nao_informado', 'dominios': dom,
                    'operador_fusao': 'nao_informado', 'fonte': fonte_real,
                    'lido_por_ia': 'nao', 'alerta': '',
                })
                continue
            for campo, permitidos in VOCAB.items():
                if s.get(campo) not in permitidos:
                    problemas.append((e['id'], campo, repr(s.get(campo))))
            if not dominios_validos(s.get('dominios', '')):
                problemas.append((e['id'], 'dominios', repr(s.get('dominios'))))
            fonte_real = 'resumo' if e['resumo'].strip() else 'titulo'
            lidos_por_ia.add(e['id'])
            linhas.append({
                'id': e['id'], 'origem': e['origem'], 'ano': e['ano'], 'titulo': e['titulo'],
                'dominio_aplicacao': s.get('dominio_aplicacao'),
                'estrategia': s.get('estrategia'),
                'ponto_intervencao': s.get('ponto_intervencao'),
                'dominios': s.get('dominios'),
                'operador_fusao': s.get('operador_fusao'),
                'fonte': fonte_real,
                'lido_por_ia': 'sim',
                'alerta': (s.get('alerta') or '').strip(),
            })

    print('lotes lidos por IA: %s' % lotes_lidos)
    print('lotes NAO lidos (fallback mecanico): %s' % lotes_faltando)
    print('estudos consolidados: %d  (lidos por IA: %d, so mecanico: %d)'
          % (len(linhas), len(lidos_por_ia), len(linhas) - len(lidos_por_ia)))
    if problemas:
        print('\nPROBLEMAS (%d):' % len(problemas))
        for p in problemas[:60]:
            print('  %s | %s | %s' % p)
        if len(problemas) > 60:
            print('  ... +%d' % (len(problemas) - 60))

    if not os.path.isdir(os.path.join(RSL, 'planilhas')):
        os.makedirs(os.path.join(RSL, 'planilhas'))
    with io.open(os.path.join(RSL, 'planilhas', 'mapeamento.csv'), 'w',
                 encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS)
        w.writeheader()
        w.writerows(linhas)

    alertas = [l for l in linhas if l['alerta']]
    with io.open(os.path.join(DADOS, 'mapeamento_alertas.csv'), 'w',
                 encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['id', 'origem', 'fonte', 'estrategia', 'titulo', 'alerta'])
        w.writeheader()
        for l in alertas:
            w.writerow({k: l[k] for k in ['id', 'origem', 'fonte', 'estrategia', 'titulo', 'alerta']})

    # ---------------- S1: estrategia sobre as duas camadas (amostra no mapeamento) ----------------
    prof = list(csv.DictReader(io.open(os.path.join(RSL, 'planilhas', 'extracao.csv'), encoding='utf-8')))
    s1 = collections.defaultdict(lambda: {'profundidade': 0, 'mapeamento_lido_resumo': 0,
                                          'mapeamento_lido_titulo': 0, 'mapeamento_nao_lido': 0})
    for r in prof:
        s1[NOME_CATEGORIA[TAXONOMIA[r['id']]]]['profundidade'] += 1
    for l in linhas:
        if l['lido_por_ia'] == 'sim':
            s1[NOME_CATEGORIA[l['estrategia']]]['mapeamento_lido_' + l['fonte']] += 1
        else:
            s1['nao_informado']['mapeamento_nao_lido'] += 1

    pi = collections.defaultdict(lambda: {'profundidade': 0, 'mapeamento': 0})
    for r in prof:
        pi[r['ponto_intervencao']]['profundidade'] += 1
    for l in linhas:
        if l['lido_por_ia'] == 'sim':
            pi[l['ponto_intervencao']]['mapeamento'] += 1

    # ---------------- S2: dominio x operador (dominio quase censo, operador so onde lido) --
    def doms(s):
        return [] if s in ('nao_informado', 'nao_aplica', '') else s.split('+')

    freq_dominio_censo = collections.Counter()  # profundidade (leitura) + mapeamento (mecanico + lido)
    s2_operador = collections.defaultdict(collections.Counter)  # so onde ha operador lido
    for r in prof:
        for d in doms(r['dominio_representacao']):
            freq_dominio_censo[d] += 1
            s2_operador[d][r['operador_fusao']] += 1
    for l in linhas:
        for d in doms(l['dominios']):
            freq_dominio_censo[d] += 1
            if l['lido_por_ia'] == 'sim':
                s2_operador[d][l['operador_fusao']] += 1

    resumo = {
        'n_mapeamento': len(linhas),
        'n_mapeamento_lido_por_ia': len(lidos_por_ia),
        'n_mapeamento_so_mecanico': len(linhas) - len(lidos_por_ia),
        'n_profundidade': len(prof),
        'n_total': len(linhas) + len(prof),
        'lotes_lidos': lotes_lidos,
        'lotes_nao_lidos_fallback_mecanico': lotes_faltando,
        'mapeamento_dominio_aplicacao_amostra_lida': dict(collections.Counter(
            l['dominio_aplicacao'] for l in linhas if l['lido_por_ia'] == 'sim').most_common()),
        's1_estrategia': {k: dict(v) for k, v in s1.items()},
        's1_ponto_intervencao_amostra': {k: dict(v) for k, v in pi.items()},
        's2_frequencia_dominio_quase_censo': dict(freq_dominio_censo.most_common()),
        's2_dominio_x_operador_amostra_lida': {d: dict(c) for d, c in s2_operador.items()},
        'alertas': len(alertas),
        'alertas_por_estrategia': dict(collections.Counter(l['estrategia'] for l in alertas)),
        'problemas_validacao': len(problemas),
    }
    json.dump(resumo, io.open(os.path.join(DADOS, 'sintese_s1_s2_completa.json'), 'w', encoding='utf-8'),
              indent=1, ensure_ascii=False)

    print('\n=== S1: estrategia de customizacao (profundidade lida + mapeamento amostra lida + resto nao lido) ===')
    print('%-34s %6s %10s %10s %10s' % ('categoria', 'prof', 'map_res', 'map_tit', 'map_naolido'))
    for k in ['multi_ramo_paralelo', 'modulo_ou_transformacao_entrada', 'classico_sem_rede',
              'nao_arquitetural', 'ensemble_entre_modelos', 'nao_informado']:
        v = s1[k]
        print('%-34s %6d %10d %10d %10d' % (k, v['profundidade'], v['mapeamento_lido_resumo'],
                                             v['mapeamento_lido_titulo'], v['mapeamento_nao_lido']))
    print('\nS2, frequencia de dominio (quase censo, mecanico+lido):', dict(freq_dominio_censo.most_common()))
    print('alertas do extrator (so nos 6 lotes lidos): %d  (por estrategia: %s)'
          % (len(alertas), resumo['alertas_por_estrategia']))


if __name__ == '__main__':
    main()
