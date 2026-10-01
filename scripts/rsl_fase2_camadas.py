# -*- coding: utf-8 -*-
"""Fase 2: atribui cada sobrevivente a uma camada de sintese.

Referencia: revisao_sistematica/protocolo_rsl.md, secoes 3.1 (decisao D9) e 6.

Tres destinos possiveis:
  excluir      -> EC2, o estudo nao propoe customizacao arquitetural
  mapeamento   -> entra na sintese ampla (RQ1.1 e RQ1.2), extracao reduzida
  profundidade -> sobe para leitura de texto completo (RQ1.3 e RQ1.4)

CRITERIO DE PROMOCAO A PROFUNDIDADE
-----------------------------------
O estudo combina customizacao no dominio da FREQUENCIA com customizacao no
dominio da BORDA ou do RUIDO, que sao os pares de dominios distintos relevantes
para a RQ1.3 e exatamente o par que o estudo primario associado combina
(ramo DCT + modulos de borda).

A ablacao NAO entra como filtro de triagem, e sim como campo de extracao
preenchido a partir do texto completo. Motivo medido: apenas 6% dos resumos do
corpus mencionam ablacao. Filtrar por ela na triagem selecionaria convencao de
escrita de resumo, nao rigor metodologico, e descartaria sistematicamente
estudos que fizeram ablacao sem anuncia-la no resumo.

EC2 NA FASE 2
-------------
Exclui-se quando a contribuicao e de dados, treinamento ou pos-processamento e
o grafo computacional e o de um backbone publicado: metodo classico sem rede
neural, ensemble de modelos prontos, estudo comparativo de arquiteturas
existentes, artigo de dataset ou benchmark.
"""
import csv
import io
import json
import os
import re

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DADOS = os.path.join(RAIZ, 'revisao_sistematica', 'dados')
CSV = os.path.join(DADOS, 'triagem.csv')

FREQ = r"frequenc|\bdct\b|discrete cosine|wavelet|fourier|spectral|spectrum|high-frequency|high frequency"
EDGE = r"\bedge|boundary|contour|sobel|gradient"
RUIDO = r"\bnoise|\bsrm\b|residual|prnu|steganalytic|constrained conv"

# Marcadores de ausencia de customizacao arquitetural (EC2). Aplicados sobre
# titulo e resumo, e sempre conferidos contra a presenca de proposta de rede.
EC2_SINAIS = [
    r"\bsurvey\b", r"\breview\b", r"comparative (study|analysis|evaluation)",
    r"we (compare|evaluate) (the )?(performance of )?(several|three|four|multiple|various)",
    r"\bbenchmark\b.*\b(dataset|suite)\b", r"we (introduce|present|construct) a (large-scale )?dataset",
    r"ensemble of (pre-?trained|existing|multiple) (models|architectures|cnns)",
    r"transfer learning (with|using) (pre-?trained)",
]
# Marcadores de proposta arquitetural. Presentes, vetam a exclusao por EC2.
ARQ_SINAIS = [
    r"we propose (a|an|the) [a-z\- ]*(network|net\b|module|branch|stream|architecture|framework|layer|block|encoder|decoder|transformer)",
    r"propose[sd]? (a|an) novel [a-z\- ]*(network|module|branch|stream|architecture)",
    r"\b(dual|two|three|tri|multi)[- ](stream|branch|domain|path)\b",
    r"attention (module|mechanism|block)", r"plug-?in", r"backbone",
    r"we design (a|an)", r"-net\b", r"net:\b",
]


def tem(txt, p):
    return bool(re.search(p, txt))


def dominios(txt):
    return {n for n, p in (("frequencia", FREQ), ("borda", EDGE), ("ruido", RUIDO)) if tem(txt, p)}


def classificar(r):
    """Devolve (camada, codigo_ec, dominios_detectados)."""
    txt = (r['titulo'] + " " + r['resumo']).lower()
    doms = dominios(txt)

    if r['resumo'].strip():
        arq = any(tem(txt, p) for p in ARQ_SINAIS)
        ec2 = any(tem(txt, p) for p in EC2_SINAIS)
        if ec2 and not arq:
            return 'excluir', 'EC2', doms

    # promocao por sinal positivo: frequencia combinada com borda ou ruido
    if 'frequencia' in doms and ({'borda', 'ruido'} & doms):
        return 'profundidade', '', doms
    return 'mapeamento', '', doms


def main():
    regs = list(csv.DictReader(io.open(CSV, encoding='utf-8')))
    cols = list(regs[0].keys())
    if 'fase2_camada' not in cols:
        cols.insert(cols.index('fase2_codigo_ec') + 1, 'fase2_camada')
        cols.insert(cols.index('fase2_camada') + 1, 'dominios_detectados')

    cont = {'excluir': 0, 'mapeamento': 0, 'profundidade': 0}
    sem_resumo_prof = 0
    for r in regs:
        r.setdefault('fase2_camada', '')
        r.setdefault('dominios_detectados', '')
        if r['fase1_titulo_veredito'] != 'incluir':
            continue
        camada, ec, doms = classificar(r)
        r['fase2_resumo_veredito'] = 'excluir' if camada == 'excluir' else 'incluir'
        r['fase2_codigo_ec'] = ec
        r['fase2_camada'] = '' if camada == 'excluir' else camada
        r['fase2_avaliador'] = 'IA-assistida'
        r['dominios_detectados'] = "+".join(sorted(doms))
        cont[camada] += 1
        if camada == 'profundidade' and not r['resumo'].strip():
            sem_resumo_prof += 1

    with io.open(CSV, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(regs)

    print("=== Fase 2: atribuicao de camadas ===")
    print("  entraram na fase 2       : %d" % sum(cont.values()))
    print("  excluidos por EC2        : %d" % cont['excluir'])
    print("  camada de MAPEAMENTO     : %d" % cont['mapeamento'])
    print("  camada de PROFUNDIDADE   : %d" % cont['profundidade'])
    print("    destes, sem resumo     : %d  (promovidos so pelo titulo)" % sem_resumo_prof)

    prof = [r for r in regs if r.get('fase2_camada') == 'profundidade']
    json.dump([{'id': r['id'], 'titulo': r['titulo'], 'ano': r['ano'],
                'dominios': r['dominios_detectados'], 'doi': r['doi']} for r in prof],
              io.open(os.path.join(DADOS, 'camada_profundidade.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print("\n  Lista da camada de profundidade: %s" %
          os.path.join(DADOS, 'camada_profundidade.json'))


if __name__ == '__main__':
    main()
