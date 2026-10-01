# -*- coding: utf-8 -*-
"""Fase 3: registra em triagem.csv o veredito de cada estudo da camada de profundidade.

Referencia: revisao_sistematica/protocolo_rsl.md, secao 6 (Fase 3) e secao 5 (EC6).

Regra, aplicada so a quem tem fase2_camada == profundidade:

  extracao/<id>.json existe          -> incluir        (lido, extraido, QA pontuado)
  pdfs/<id>.INDISPONIVEL existe      -> excluir, EC6   (texto completo inacessivel)
  nenhum dos dois                    -> PENDENTE, nao decide, so reporta

O terceiro caso nao e silenciado de proposito: um veredito atribuido por
ausencia de arquivo seria um estudo marcado como resolvido sem que ninguem
tenha decidido nada. O script falha barulhento e deixa a decisao com o autor.
"""
import csv
import io
import json
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RSL = os.path.join(RAIZ, 'revisao_sistematica')
DADOS = os.path.join(RSL, 'dados')
CSV = os.path.join(DADOS, 'triagem.csv')


def main():
    with io.open(CSV, encoding='utf-8', newline='') as f:
        leitor = csv.DictReader(f)
        campos = leitor.fieldnames
        regs = list(leitor)

    incluidos, ec6, pendentes = [], [], []
    for r in regs:
        if (r.get('fase2_camada') or '').strip().lower() != 'profundidade':
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

    with io.open(CSV, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(regs)

    resumo = {
        'camada_profundidade': len(incluidos) + len(ec6) + len(pendentes),
        'incluidos_fase3': len(incluidos),
        'excluidos_ec6': len(ec6),
        'pendentes': len(pendentes),
        'ids_pendentes': pendentes,
    }
    json.dump(resumo, io.open(os.path.join(DADOS, 'fase3_vereditos.json'), 'w',
                              encoding='utf-8'), indent=1, ensure_ascii=False)

    print('camada de profundidade : %d' % resumo['camada_profundidade'])
    print('  incluidos (extraidos): %d' % len(incluidos))
    print('  excluidos por EC6    : %d' % len(ec6))
    print('  PENDENTES            : %d %s' % (len(pendentes), ' '.join(pendentes)))
    print('\ngravado: triagem.csv e fase3_vereditos.json')
    return 1 if pendentes else 0


if __name__ == '__main__':
    sys.exit(main())
