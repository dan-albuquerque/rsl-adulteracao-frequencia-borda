# -*- coding: utf-8 -*-
"""Fase 4: triagem dos candidatos do snowballing pelas fases 1 e 2.

Referencia: revisao_sistematica/protocolo_rsl.md, secao 6 (Fase 4). Os
candidatos passam exatamente pelos mesmos criterios do corpus primario:

  fase 1  titulo -> exclusoes EC1, EC3, EC4, EC7 decididas por leitura,
          registradas em dados/_f4_triagem_lote*.json (registro auditavel,
          criterios em dados/_INSTRUCOES_TRIAGEM_F4.md). Na duvida, inclui.
  fase 2  mesma funcao classificar() de rsl_fase2_camadas.py: EC2 lexico e
          atribuicao de camada (frequencia + borda ou ruido -> profundidade).
          Exclusoes adicionais por EC2 decididas por leitura de resumo ficam em
          dados/fase4_ec2_revisado.json, se existir.

Saida: dados/fase4_triagem.csv e dados/fase4_triagem_resumo.json.
Nao altera triagem.csv: o corpus do snowballing fica em planilha propria ate
o autor revisar, e so entao e fundido.
"""
import collections
import csv
import glob
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rsl_fase2_camadas import classificar  # noqa: E402  mesma regra do corpus primario

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DADOS = os.path.join(RAIZ, 'revisao_sistematica', 'dados')


def main():
    cands = json.load(io.open(os.path.join(DADOS, 'fase4_candidatos.json'), encoding='utf-8'))

    exc1 = {}
    lotes = sorted(glob.glob(os.path.join(DADOS, '_f4_triagem_lote*.json')))
    for p in lotes:
        for k, v in json.load(io.open(p, encoding='utf-8')).items():
            exc1[k] = v.strip().upper()
    # correcoes do revisor sobre o triador, com motivo; sobrescrevem os lotes
    p_cor = os.path.join(DADOS, '_f4_triagem_correcoes.json')
    correcoes = {}
    if os.path.exists(p_cor):
        for k, v in json.load(io.open(p_cor, encoding='utf-8')).items():
            if k.startswith('_'):
                continue
            codigo, motivo = v
            correcoes[k] = motivo
            if codigo.lower() == 'incluir':
                exc1.pop(k, None)
            else:
                exc1[k] = codigo.strip().upper()
    validos = {c['id'] for c in cands}
    desconhecidos = sorted(set(exc1) - validos)
    if desconhecidos:
        print('AVISO: ids inexistentes nas exclusoes: %s' % desconhecidos)

    p_ec2 = os.path.join(DADOS, 'fase4_ec2_revisado.json')
    ec2_lido = json.load(io.open(p_ec2, encoding='utf-8')) if os.path.exists(p_ec2) else {}

    linhas = []
    for c in cands:
        r = {
            'id': c['id'], 'origem_snowballing': c['origem_snowballing'],
            'ano': c['ano'], 'titulo': c['titulo'], 'veiculo': c['veiculo'],
            'tipo': c['tipo'], 'doi': c['doi'], 'citacoes': c['citacoes'],
            'autores': c.get('autores', ''), 'resumo': c.get('resumo') or '',
            'fase1_titulo_veredito': '', 'fase1_codigo_ec': '',
            'fase2_resumo_veredito': '', 'fase2_codigo_ec': '', 'fase2_camada': '',
            'dominios_detectados': '', 'observacoes': '',
        }
        if c['id'] in correcoes:
            r['observacoes'] = 'correcao do revisor na fase 1: ' + correcoes[c['id']]
        if c['id'] in exc1:
            r['fase1_titulo_veredito'] = 'excluir'
            r['fase1_codigo_ec'] = exc1[c['id']]
        else:
            r['fase1_titulo_veredito'] = 'incluir'
            camada, ec, doms = classificar(r)
            r['dominios_detectados'] = '+'.join(sorted(doms))
            if c['id'] in ec2_lido:
                # valor 'EC2: motivo' exclui; 'INCLUIR: motivo' resgata falso positivo lexico
                decisao = ec2_lido[c['id']]
                if decisao.upper().startswith('INCLUIR'):
                    r['_resgate'] = camada == 'excluir'
                    if camada == 'excluir':
                        camada = 'profundidade' if ('frequencia' in doms and ({'borda', 'ruido'} & doms)) else 'mapeamento'
                    ec = ''
                    r['observacoes'] = (('resgatado do EC2 lexico' if r['_resgate'] else 'inclusao confirmada')
                                        + ' por leitura do resumo: ' + decisao)
                else:
                    camada, ec = 'excluir', 'EC2'
                    r['observacoes'] = 'EC2 por leitura do resumo: ' + decisao
            elif c['id'] in correcoes:
                pass
            r['fase2_resumo_veredito'] = 'excluir' if camada == 'excluir' else 'incluir'
            r['fase2_codigo_ec'] = ec
            r['fase2_camada'] = '' if camada == 'excluir' else camada
            if not r['resumo'].strip():
                r['observacoes'] = (r['observacoes'] + ' ' if r['observacoes'] else '') + \
                    'sem resumo indexado: fase 2 so pelo titulo'
        linhas.append(r)

    campos = [k for k in linhas[0].keys() if not k.startswith('_')]
    with io.open(os.path.join(DADOS, 'fase4_triagem.csv'), 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=campos, extrasaction='ignore')
        w.writeheader()
        w.writerows(linhas)

    f1 = collections.Counter(r['fase1_codigo_ec'] for r in linhas if r['fase1_titulo_veredito'] == 'excluir')
    passam1 = [r for r in linhas if r['fase1_titulo_veredito'] == 'incluir']
    ec2 = [r for r in passam1 if r['fase2_codigo_ec'] == 'EC2']
    mapa = [r for r in passam1 if r['fase2_camada'] == 'mapeamento']
    prof = [r for r in passam1 if r['fase2_camada'] == 'profundidade']
    resumo = {
        'candidatos': len(linhas),
        'fase1_excluidos': dict(f1), 'fase1_total_excluidos': sum(f1.values()),
        'fase1_sobreviventes': len(passam1),
        'fase2_ec2_lexico': sum(1 for r in ec2 if r['id'] not in ec2_lido),
        'fase2_ec2_leitura': sum(1 for r in ec2 if r['id'] in ec2_lido),
        'fase2_resgatados_do_lexico': sum(1 for r in passam1 if r.get('_resgate')),
        'fase2_profundidade_confirmada_por_leitura': sum(1 for r in passam1 if r['observacoes'].startswith('inclusao confirmada')),
        'camada_mapeamento': len(mapa), 'camada_profundidade': len(prof),
        'profundidade_sem_resumo': sum(1 for r in prof if not r['resumo'].strip()),
        'profundidade_ids': [r['id'] for r in prof],
        'lotes_de_triagem_lidos': [os.path.basename(p) for p in lotes],
        'correcoes_do_revisor': len(correcoes),
    }
    json.dump(resumo, io.open(os.path.join(DADOS, 'fase4_triagem_resumo.json'), 'w',
                              encoding='utf-8'), indent=1, ensure_ascii=False)
    for k, v in resumo.items():
        if k != 'profundidade_ids':
            print('%-26s %s' % (k, v))


if __name__ == '__main__':
    main()
