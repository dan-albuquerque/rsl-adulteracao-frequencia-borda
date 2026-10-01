# -*- coding: utf-8 -*-
"""Calibracao de variantes mais restritas da string de busca (feedback do orientador,
2026-09-22: string atual "muito abrangente"). Testa cada variante contra o OpenAlex
e contra o conjunto quasi-gold (protocolo secao 4.4), sem gravar nada em disco.

So faz consultas de contagem (per_page=1) e, para o quasi-gold, uma busca por
titulo restrita ao filtro da variante. Nao reexecuta a busca completa nem
sobrescreve triagem.csv: isso so acontece depois que o autor escolher uma opcao.

Uso:
    python scripts/rsl_calibra_string.py
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request

EMAIL = "dam@cesar.school"
UA = {"User-Agent": "mailto:" + EMAIL}
API_KEY = os.environ.get("OPENALEX_API_KEY", "")

JANELA = "from_publication_date:2020-01-01,to_publication_date:2026-12-31"
TIPOS = "type:article|review|conference-paper"

# bloco de tarefa, igual ao atual (nao mexido nesta rodada de calibracao)
BLOCO_DOC = (
    '("image forgery" OR "image tampering" OR "image manipulation detection" '
    'OR "document forgery" OR "document tampering" OR "tampered text" '
    'OR "splicing detection" OR "copy-move" OR "image forensics")'
)
BLOCO_FACE = '("deepfake detection" OR "face forgery")'

# ----------------------------------------------------------------------------
# Variantes do bloco de customizacao, da mais ampla (atual, baseline) a mais
# restrita. Cada uma remove termos genericos candidatos a causar volume sem
# precisao: "feature fusion" e "attention module" aparecem em qualquer artigo
# de visao computacional com mecanismo de atencao, nao so em customizacao
# arquitetural para deteccao de adulteracao.
# ----------------------------------------------------------------------------
CUST_ENXUTO = (
    '("frequency" OR "discrete cosine transform" OR "DCT" OR "high-frequency" '
    'OR "edge attention" OR "two-stream" OR "dual-stream")'
)
BLOCO_DOC_ESTREITO = (
    '("image forgery" OR "image tampering" OR "document forgery" '
    'OR "document tampering" OR "tampered text" '
    'OR "splicing detection" OR "copy-move")'
)
BLOCO_ARQ = '("network" OR "model" OR "module" OR "branch" OR "architecture" OR "backbone")'

VARIANTES = {
    "baseline (atual)": {
        "doc": BLOCO_DOC,
        "cust": (
            '("frequency" OR "discrete cosine transform" OR "DCT" OR "high-frequency" '
            'OR "edge attention" OR "attention module" OR "plug-in module" '
            'OR "two-stream" OR "dual-stream" OR "feature fusion" OR "backbone modification")'
        ),
        "extra": None,
    },
    "sem termos genericos de atencao/fusao": {
        "doc": BLOCO_DOC,
        "cust": (
            '("frequency" OR "discrete cosine transform" OR "DCT" OR "high-frequency" '
            'OR "edge attention" OR "plug-in module" '
            'OR "two-stream" OR "dual-stream" OR "backbone modification")'
        ),
        "extra": None,
    },
    "so termos de dominio de representacao": {
        "doc": BLOCO_DOC, "cust": CUST_ENXUTO, "extra": None,
    },
    "frequency exige contexto (frase composta)": {
        "doc": BLOCO_DOC,
        "cust": (
            '("frequency domain" OR "frequency-aware" OR "discrete cosine transform" OR "DCT" '
            'OR "high-frequency" OR "edge attention" OR "plug-in module" '
            'OR "two-stream" OR "dual-stream" OR "backbone modification")'
        ),
        "extra": None,
    },
    "+ bloco de arquitetura obrigatorio (3 blocos)": {
        "doc": BLOCO_DOC, "cust": CUST_ENXUTO, "extra": BLOCO_ARQ,
    },
    "tarefa mais restrita + customizacao enxuta": {
        "doc": BLOCO_DOC_ESTREITO, "cust": CUST_ENXUTO, "extra": None,
    },
    "tarefa restrita + arquitetura obrigatoria": {
        "doc": BLOCO_DOC_ESTREITO, "cust": CUST_ENXUTO, "extra": BLOCO_ARQ,
    },
    # pedido do usuario 2026-09-22: focar em customizacao de rede + documento + fraude,
    # em vez do bloco generico de imagem que hoje domina o volume.
    "documento+fraude estrito": {
        "doc": (
            '("document forgery" OR "document tampering" OR "document fraud" '
            'OR "tampered text" OR "document forensics" OR "document image forensics")'
        ),
        "cust": CUST_ENXUTO,
        "extra": None,
    },
    "customizacao de rede explicita (bloco extra)": {
        "doc": BLOCO_DOC,
        "cust": CUST_ENXUTO,
        "extra": (
            '("network architecture" OR "novel architecture" OR "proposed module" '
            'OR "proposed branch" OR "customized network" OR "network design" '
            'OR "architectural design")'
        ),
    },
    "documento+fraude estrito + customizacao de rede explicita": {
        "doc": (
            '("document forgery" OR "document tampering" OR "document fraud" '
            'OR "tampered text" OR "document forensics" OR "document image forensics")'
        ),
        "cust": CUST_ENXUTO,
        "extra": (
            '("network architecture" OR "novel architecture" OR "proposed module" '
            'OR "proposed branch" OR "customized network" OR "network design" '
            'OR "architectural design")'
        ),
    },
    # pedido do usuario 2026-09-23: sinal de rede neural mais amplo que o bloco de C1
    # (que so tinha 3 termos e derrubava Guo et al. 2023); testar se um bloco mais
    # generoso de vocabulario de rede neural ainda recupera o quasi-gold.
    "+ sinal de rede neural amplo (3 blocos)": {
        "doc": BLOCO_DOC,
        "cust": CUST_ENXUTO,
        "extra": (
            '("neural network" OR "convolutional" OR "CNN" OR "deep learning" '
            'OR "backbone" OR "encoder")'
        ),
    },
    "cust sem high-frequency (termo colide com outras areas)": {
        "doc": BLOCO_DOC,
        "cust": (
            '("frequency" OR "discrete cosine transform" OR "DCT" '
            'OR "edge attention" OR "two-stream" OR "dual-stream")'
        ),
        "extra": None,
    },
    "sinal de rede amplo + cust sem high-frequency": {
        "doc": BLOCO_DOC,
        "cust": (
            '("frequency" OR "discrete cosine transform" OR "DCT" '
            'OR "edge attention" OR "two-stream" OR "dual-stream")'
        ),
        "extra": (
            '("neural network" OR "convolutional" OR "CNN" OR "deep learning" '
            'OR "backbone" OR "encoder")'
        ),
    },
    # pedido do usuario 2026-09-23: 3o AND exigindo sinal de deteccao/classificacao
    # empirica, em vez de sinal de rede neural (que ja reprovou 2x). Baixo risco
    # esperado: os 4 ancoras do quasi-gold propoem deteccao explicitamente.
    "+ sinal de deteccao obrigatorio (3 blocos)": {
        "doc": BLOCO_DOC,
        "cust": CUST_ENXUTO,
        "extra": '("detection" OR "detecting" OR "classification")',
    },
    "cust enxuto + sinal de deteccao (sem attention/plugin/backbonemod)": {
        "doc": BLOCO_DOC,
        "cust": (
            '("frequency" OR "discrete cosine transform" OR "DCT" OR "high-frequency" '
            'OR "edge attention" OR "plug-in module" '
            'OR "two-stream" OR "dual-stream" OR "backbone modification")'
        ),
        "extra": '("detection" OR "detecting" OR "classification")',
    },
    # pedido do usuario 2026-09-23: mais opcoes de 3o/4o AND em cima da variante
    # ja vencedora (doc + cust enxuto + deteccao obrigatoria, 405/712, 4/4).
    "B: tirar classification (so detection/detecting)": {
        "doc": BLOCO_DOC, "cust": CUST_ENXUTO,
        "extra": '("detection" OR "detecting")',
    },
    "A: + 4o AND propose/novel": {
        "doc": BLOCO_DOC, "cust": CUST_ENXUTO,
        "extra": ('("detection" OR "detecting" OR "classification") '
                   'AND ("propose" OR "novel" OR "we present" OR "introduce")'),
    },
    "C: + 4o AND avaliacao empirica": {
        "doc": BLOCO_DOC, "cust": CUST_ENXUTO,
        "extra": ('("detection" OR "detecting" OR "classification") '
                   'AND ("dataset" OR "accuracy" OR "AUC" OR "F1")'),
    },
    "B+A combinado": {
        "doc": BLOCO_DOC, "cust": CUST_ENXUTO,
        "extra": ('("detection" OR "detecting") '
                   'AND ("propose" OR "novel" OR "we present" OR "introduce")'),
    },
    "C+B combinado": {
        "doc": BLOCO_DOC, "cust": CUST_ENXUTO,
        "extra": ('("detection" OR "detecting") '
                   'AND ("dataset" OR "accuracy" OR "AUC" OR "F1")'),
    },
    "MAX: B+A+C combinado": {
        "doc": BLOCO_DOC, "cust": CUST_ENXUTO,
        "extra": ('("detection" OR "detecting") '
                   'AND ("propose" OR "novel" OR "we present" OR "introduce") '
                   'AND ("dataset" OR "accuracy" OR "AUC" OR "F1")'),
    },
}

QUASI_GOLD = [
    ("V1", "Bae et al. (2025)", "edge-focused deep learning"),
    ("V2", "Guo et al. (2023)", "space-frequency interactive"),
    ("V3", "Qu et al. (2023)", "tampered text detection in document"),
    ("V4", "Qian et al. (2020)", "thinking in frequency"),
]


def _filtro(bloco_tarefa, bloco_cust, bloco_extra=None):
    busca = "{} AND {}".format(bloco_tarefa, bloco_cust)
    if bloco_extra:
        busca += " AND {}".format(bloco_extra)
    return "title_and_abstract.search:{},{},{}".format(busca, JANELA, TIPOS)


def _contagem(filtro, pausa=1.0, tentativas=6):
    url = "https://api.openalex.org/works?filter=" + urllib.parse.quote(filtro, safe=":,|") + "&per_page=1"
    if API_KEY:
        url += "&api_key=" + API_KEY
    espera = 3.0
    for tentativa in range(tentativas):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                d = json.load(r)
            time.sleep(pausa)
            return d["meta"]["count"]
        except urllib.error.HTTPError as e:
            if e.code == 429 and tentativa < tentativas - 1:
                sys.stderr.write("    429, aguardando {:.0f}s...\n".format(espera))
                time.sleep(espera)
                espera *= 2
                continue
            raise


def _quasi_gold_ok(bloco_doc, bloco_cust, bloco_extra, frag_titulo, pausa=1.0):
    """Verifica se um estudo especifico do quasi-gold sobrevive ao filtro da variante,
    restringindo por titulo em vez de baixar o corpus inteiro. _contagem faz a
    codificacao de URL uma unica vez sobre o filtro completo; nao pre-codificar aqui."""
    filtro_doc = _filtro(bloco_doc, bloco_cust, bloco_extra) + ',title.search:"{}"'.format(frag_titulo)
    n1 = _contagem(filtro_doc, pausa)
    if n1 > 0:
        return True
    filtro_face = _filtro(BLOCO_FACE, bloco_cust, bloco_extra) + ',title.search:"{}"'.format(frag_titulo)
    n2 = _contagem(filtro_face, pausa)
    return n2 > 0


def main():
    if len(sys.argv) > 1:
        alvo = set(sys.argv[1:])
        ativos = {k: v for k, v in VARIANTES.items() if k in alvo}
    else:
        ativos = VARIANTES

    print("=== Calibracao de variantes mais restritas (feedback do orientador) ===\n")
    if not API_KEY:
        sys.stderr.write("aguardando 120s para respeitar o limite do OpenAlex (sem api_key)...\n")
        time.sleep(120)
    else:
        sys.stderr.write("usando OPENALEX_API_KEY (orcamento proprio, sem espera longa)\n")
    resultados = []
    for nome, blocos in ativos.items():
        bloco_doc = blocos["doc"]
        bloco_cust = blocos["cust"]
        bloco_extra = blocos["extra"]
        sys.stderr.write("testando: {}\n".format(nome))
        n_doc = _contagem(_filtro(bloco_doc, bloco_cust, bloco_extra))
        n_face = _contagem(_filtro(BLOCO_FACE, bloco_cust, bloco_extra))
        total_bruto = n_doc + n_face  # sem remover sobreposicao; estimativa por cima

        gold_ok = []
        for vid, ref, frag in QUASI_GOLD:
            ok = _quasi_gold_ok(bloco_doc, bloco_cust, bloco_extra, frag)
            gold_ok.append((vid, ref, ok))
            sys.stderr.write("  {} {} {}\n".format(vid, ref, "OK" if ok else "AUSENTE"))

        n_gold_ok = sum(1 for _, _, ok in gold_ok if ok)
        resultados.append((nome, n_doc, n_face, total_bruto, n_gold_ok, gold_ok))

    print("\n{:38s} {:>8s} {:>8s} {:>10s}  {}".format(
        "variante", "primaria", "secund.", "~total", "quasi-gold"))
    print("-" * 90)
    for nome, n_doc, n_face, total, n_gold_ok, gold_ok in resultados:
        marca = "{}/4".format(n_gold_ok)
        if n_gold_ok < 4:
            faltando = [vid for vid, _, ok in gold_ok if not ok]
            marca += "  FALTAM: {}".format(",".join(faltando))
        print("{:38s} {:>8d} {:>8d} {:>10d}  {}".format(nome, n_doc, n_face, total, marca))

    print("\nNota: '~total' e primaria+secundaria SEM remover sobreposicao entre")
    print("consultas (a baseline real, 1.413, ja tem sobreposicao de 23 removida).")
    print("Serve para comparar a ORDEM DE GRANDEZA entre variantes, nao o numero final.")
    print("So uma variante com quasi-gold 4/4 pode ser adotada (regra da secao 4.4).")


if __name__ == "__main__":
    main()
