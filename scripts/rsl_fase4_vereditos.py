# -*- coding: utf-8 -*-
"""Fase 3 aplicada aos 16 estudos de profundidade vindos do snowballing (fase 4).

Referencia: revisao_sistematica/protocolo_rsl.md, secao 6 (Fase 3) e secao 5 (EC6).
Espelha scripts/rsl_fase3_vereditos.py, mas opera sobre dados/fase4_triagem.csv
(planilha propria do snowballing, nao fundida em triagem.csv) e restrito aos ids
listados em dados/fase4_profundidade.csv.

Regra, igual a fase 3 do corpus primario:

  extracao/<id>.json existe          -> incluir        (lido, extraido, QA pontuado)
  pdfs/<id>.INDISPONIVEL existe      -> excluir, EC6   (texto completo inacessivel)
  nenhum dos dois                    -> PENDENTE, nao decide, so reporta
"""
import csv
import io
import json
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RSL = os.path.join(RAIZ, 'revisao_sistematica')
DADOS = os.path.join(RSL, 'dados')
CSV_F4 = os.path.join(DADOS, 'fase4_triagem.csv')
CSV_PROF = os.path.join(DADOS, 'fase4_profundidade.csv')


def main():
    with io.open(CSV_PROF, encoding='utf-8', newline='') as f:
        prof_ids = {r['id'] for r in csv.DictReader(f)}

    with io.open(CSV_F4, encoding='utf-8', newline='') as f:
        leitor = csv.DictReader(f)
        campos = list(leitor.fieldnames)
        regs = list(leitor)

    if 'fase3_fulltext_veredito' not in campos:
        campos += ['fase3_fulltext_veredito', 'fase3_codigo_ec']

    incluidos, ec6, pendentes = [], [], []
    for r in regs:
        r.setdefault('fase3_fulltext_veredito', '')
        r.setdefault('fase3_codigo_ec', '')
        if r['id'] not in prof_ids:
            continue
        rid = r['id']
        tem_extracao = os.path.exists(os.path.join(DADOS, 'extracao', rid + '.json'))
        tem_indisp = os.path.exists(os.path.join(RSL, 'pdfs', rid + '.INDISPONIVEL'))

        if tem_extracao:
            r['fase3_fulltext_veredito'] = 'incluir'
            r['fase3_codigo_ec'] = ''
            incluidos.append(rid)
        elif tem_indisp:
            r['fase3_fulltext_veredito'] = 'excluir'
            r['fase3_codigo_ec'] = 'EC6'
            ec6.append(rid)
        else:
            pendentes.append(rid)

    with io.open(CSV_F4, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(regs)

    resumo = {
        'profundidade_snowballing': len(prof_ids),
        'incluidos_fase3': len(incluidos),
        'excluidos_ec6': len(ec6),
        'pendentes': len(pendentes),
        'ids_pendentes': pendentes,
    }
    json.dump(resumo, io.open(os.path.join(DADOS, 'fase4_profundidade_vereditos.json'), 'w',
                              encoding='utf-8'), indent=1, ensure_ascii=False)

    print('profundidade (snowballing) : %d' % resumo['profundidade_snowballing'])
    print('  incluidos (extraidos)     : %d %s' % (len(incluidos), incluidos))
    print('  excluidos por EC6         : %d %s' % (len(ec6), ec6))
    print('  PENDENTES                 : %d %s' % (len(pendentes), pendentes))
    print('\ngravado: fase4_triagem.csv e fase4_profundidade_vereditos.json')
    return 1 if pendentes else 0


if __name__ == '__main__':
    sys.exit(main())
