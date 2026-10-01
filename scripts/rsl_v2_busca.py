# -*- coding: utf-8 -*-
"""Busca v2: executa a string calibrada em 2026-09-23 (correcao C4) e mede o que
ela preserva do corpus v1, SEM sobrescrever nada do v1.

String v2 (correcao C4, validada 4/4 contra o quasi-gold, ver protocolo secao 4.3.1):
  tarefa AND customizacao_enxuta

A calibracao de 2026-09-23 testou 11 variantes medindo nao so o volume cortado, mas a
evidencia preservada (quantos dos 77 extraidos sobrevivem, quantos dos 5 precedentes do
achado central da RQ1.3). Resultado: qualquer bloco AND adicional (deteccao, contribuicao
ou avaliacao empirica), mesmo isolado, derruba pelo menos um precedente. A unica reducao
sem perda de evidencia e a poda dos termos redundantes do bloco de customizacao.

Hipotese a verificar: a string v2 e um subconjunto logico estrito da v1 (o bloco de
tarefa e identico, o de customizacao so perdeu termos do OR, e tres blocos AND foram
acrescentados). Se a hipotese vale, nenhum estudo novo aparece, e a "reexecucao" da
revisao e uma filtragem sobre julgamentos ja registrados, nao uma nova triagem.

Saida: revisao_sistematica/dados/v2/ (corpus_bruto.json, execucao_busca.json,
sobrevivencia.json). Nada em dados/ e tocado.
"""
import csv
import io
import json
import os
import sys
import time
import urllib.parse
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DADOS = os.path.join(RAIZ, "revisao_sistematica", "dados")
SAIDA = os.path.join(DADOS, "v2")
PLANILHAS = os.path.join(RAIZ, "revisao_sistematica", "planilhas")

EMAIL = "dam@cesar.school"
UA = {"User-Agent": "mailto:" + EMAIL}
API_KEY = os.environ.get("OPENALEX_API_KEY", "")

JANELA = "from_publication_date:2020-01-01,to_publication_date:2026-12-31"
TIPOS = "type:article|review|conference-paper"

BLOCO_DOC = (
    '("image forgery" OR "image tampering" OR "image manipulation detection" '
    'OR "document forgery" OR "document tampering" OR "tampered text" '
    'OR "splicing detection" OR "copy-move" OR "image forensics")'
)
BLOCO_FACE = '("deepfake detection" OR "face forgery")'
# C4a: removidos "attention module", "plug-in module", "feature fusion" e
# "backbone modification" — a calibracao mostrou que nao recuperavam nada de unico.
BLOCO_CUST = (
    '("frequency" OR "discrete cosine transform" OR "DCT" OR "high-frequency" '
    'OR "edge attention" OR "two-stream" OR "dual-stream")'
)
# Blocos AND adicionais testados e REJEITADOS na calibracao (cada um derruba
# precedente do achado central, ver scripts/rsl_v2_comparacao.py). Mantidos aqui
# como registro do que foi testado, nao entram na string.
_REJEITADO_DETECCAO = '("detection" OR "detecting")'
_REJEITADO_CONTRIB = '("propose" OR "novel" OR "we present" OR "introduce")'
_REJEITADO_AVALIACAO = '("dataset" OR "accuracy" OR "AUC" OR "F1")'

CAMPOS = (
    "id,doi,title,publication_year,type,primary_location,authorships,"
    "abstract_inverted_index,cited_by_count,referenced_works_count"
)


def _filtro(bloco_tarefa):
    busca = " AND ".join([bloco_tarefa, BLOCO_CUST])
    return "title_and_abstract.search:{},{},{}".format(busca, JANELA, TIPOS)


def _url(filtro, cursor=None, per_page=200):
    p = "https://api.openalex.org/works?filter=" + urllib.parse.quote(filtro, safe=":,|")
    if cursor:
        p += "&per-page={}&cursor={}&select={}".format(per_page, cursor, CAMPOS)
    else:
        p += "&per_page=1"
    if API_KEY:
        p += "&api_key=" + API_KEY
    return p


def buscar(nome, bloco_tarefa, pausa=0.3):
    filtro = _filtro(bloco_tarefa)
    registros, cursor, paginas = [], "*", 0
    while cursor:
        url = _url(filtro, cursor)
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
            d = json.load(r)
        registros += d["results"]
        cursor = d["meta"].get("next_cursor")
        paginas += 1
        if not d["results"]:
            break
        sys.stderr.write("\r  {}: {} registros".format(nome, len(registros)))
        time.sleep(pausa)
    sys.stderr.write("\n")
    return registros, {"consulta": nome, "filtro_submetido": filtro,
                       "retornados": len(registros), "paginas": paginas}


def carrega_v1():
    """Mapa id OpenAlex -> id do estudo (S####). O S#### foi atribuido por ordem de
    enumeracao sobre a lista unica salva em corpus_bruto.json (ver rsl_search.gravar)."""
    with io.open(os.path.join(DADOS, "corpus_bruto.json"), encoding="utf-8") as f:
        bruto = json.load(f)
    return {w["id"]: "S{:04d}".format(i + 1) for i, w in enumerate(bruto)}, bruto


def carrega_triagem():
    linhas = {}
    with io.open(os.path.join(DADOS, "triagem.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            linhas[r["id"]] = r
    return linhas


def carrega_extraidos():
    ids = set()
    caminho = os.path.join(PLANILHAS, "extracao.csv")
    with io.open(caminho, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            ids.add(r["id"])
    return ids


def main():
    if not os.path.isdir(SAIDA):
        os.makedirs(SAIDA)

    todos, metas = [], []
    for nome, bloco in [("primaria_documento", BLOCO_DOC), ("secundaria_face", BLOCO_FACE)]:
        regs, meta = buscar(nome, bloco)
        for w in regs:
            w["_consulta"] = nome
        todos += regs
        metas.append(meta)

    vistos, unicos = set(), []
    for w in todos:
        if w["id"] in vistos:
            continue
        vistos.add(w["id"])
        unicos.append(w)
    dups = len(todos) - len(unicos)

    print("\n=== Busca v2 (string C4) ===")
    for m in metas:
        print("  {:22s} {:5d}".format(m["consulta"], m["retornados"]))
    print("  {:22s} {:5d}".format("sobreposicao removida", dups))
    print("  {:22s} {:5d}".format("CORPUS UNICO v2", len(unicos)))

    # --- hipotese do subconjunto ---
    mapa_v1, bruto_v1 = carrega_v1()
    ids_v2 = set(w["id"] for w in unicos)
    ids_v1 = set(mapa_v1)
    novos = ids_v2 - ids_v1
    print("\n=== Hipotese do subconjunto ===")
    print("  corpus v1: {}   corpus v2: {}".format(len(ids_v1), len(ids_v2)))
    print("  estudos v2 que NAO estavam no v1: {}".format(len(novos)))
    if novos:
        print("  ATENCAO: hipotese falhou, ha estudo novo a triar. Exemplos:")
        for w in unicos:
            if w["id"] in novos:
                print("    - {} ({})".format((w.get("title") or "")[:70], w.get("publication_year")))
                if sum(1 for x in unicos if x["id"] in novos) > 5:
                    break

    # --- o que sobrevive do funil v1 ---
    sids_v2 = set(mapa_v1[i] for i in (ids_v2 & ids_v1))
    triagem = carrega_triagem()
    extraidos = carrega_extraidos()

    def conta(filtro_fn):
        dentro = [s for s, r in triagem.items() if filtro_fn(r)]
        sobrev = [s for s in dentro if s in sids_v2]
        return len(dentro), len(sobrev), sorted(set(dentro) - set(sobrev))

    print("\n=== Sobrevivencia do funil v1 sob a string v2 ===")
    n1, s1, _ = conta(lambda r: r["fase1_titulo_veredito"] == "incluir")
    print("  incluidos na fase 1 (titulo):        {} -> {} ({} perdidos)".format(n1, s1, n1 - s1))
    n2, s2, _ = conta(lambda r: r["fase2_resumo_veredito"] == "incluir")
    print("  incluidos na fase 2 (resumo):        {} -> {} ({} perdidos)".format(n2, s2, n2 - s2))
    n3, s3, perd_map = conta(lambda r: r.get("fase2_camada") == "mapeamento"
                             and r["fase2_resumo_veredito"] == "incluir")
    print("  camada de mapeamento:                {} -> {} ({} perdidos)".format(n3, s3, n3 - s3))
    n4, s4, perd_prof = conta(lambda r: r.get("fase2_camada") == "profundidade")
    print("  camada de profundidade:              {} -> {} ({} perdidos)".format(n4, s4, n4 - s4))

    ext_primario = sorted(i for i in extraidos if i.startswith("S"))
    ext_sobrev = [i for i in ext_primario if i in sids_v2]
    ext_perdidos = [i for i in ext_primario if i not in sids_v2]
    print("  extraidos do corpus primario:        {} -> {} ({} perdidos)".format(
        len(ext_primario), len(ext_sobrev), len(ext_perdidos)))
    if ext_perdidos:
        print("\n  EXTRAIDOS QUE CAEM COM A STRING NOVA:")
        for sid in ext_perdidos:
            r = triagem.get(sid, {})
            print("    {}  {}  ({}, {})".format(
                sid, (r.get("titulo") or "")[:62], r.get("ano", "?"),
                (r.get("veiculo") or "?")[:28]))

    with io.open(os.path.join(SAIDA, "corpus_bruto.json"), "w", encoding="utf-8") as f:
        json.dump(unicos, f, ensure_ascii=False)
    with io.open(os.path.join(SAIDA, "execucao_busca.json"), "w", encoding="utf-8") as f:
        json.dump({"consultas": metas, "corpus_unico": len(unicos),
                   "sobreposicao_removida": dups}, f, ensure_ascii=False, indent=2)
    with io.open(os.path.join(SAIDA, "sobrevivencia.json"), "w", encoding="utf-8") as f:
        json.dump({"ids_v2_como_sid": sorted(sids_v2),
                   "novos_sem_equivalente_v1": sorted(novos),
                   "extraidos_perdidos": ext_perdidos,
                   "profundidade_perdidos": perd_prof}, f, ensure_ascii=False, indent=2)
    print("\nGravado em dados/v2/ (v1 intacto).")


if __name__ == "__main__":
    main()
