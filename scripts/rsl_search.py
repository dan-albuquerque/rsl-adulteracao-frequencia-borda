"""Executa a busca da revisao sistematica no OpenAlex e grava o corpus bruto.

Referencia: revisao_sistematica/protocolo_rsl.md (secao 4 e apendice A).

A busca e reprodutivel: a string, a janela e os filtros de tipo estao codificados
aqui, e o script grava junto ao resultado a URL literalmente submetida e a data de
execucao, que sao o dado exigido pela Tabela 4 do protocolo.

Uso:
    python scripts/rsl_search.py                 # busca primaria + secundaria
    python scripts/rsl_search.py --so-primaria
    python scripts/rsl_search.py --validar       # so checa o conjunto quasi-gold
"""

import argparse
import csv
import datetime as dt
import json
import os
import sys
import time
import urllib.parse
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAIDA = os.path.join(RAIZ, "revisao_sistematica", "dados")
EMAIL = "dam@cesar.school"  # OpenAlex pede identificacao; entra no polite pool
UA = {"User-Agent": "mailto:" + EMAIL}

# ----------------------------------------------------------------------------
# Blocos da string. Ver protocolo secao 4.3 e o registro de desvios (Tabela 6).
# ----------------------------------------------------------------------------
BLOCO_DOC = (
    '("image forgery" OR "image tampering" OR "image manipulation detection" '
    'OR "document forgery" OR "document tampering" OR "tampered text" '
    'OR "splicing detection" OR "copy-move" OR "image forensics")'
)
BLOCO_FACE = '("deepfake detection" OR "face forgery")'

# Bloco de customizacao. "frequency" entra solto, e nao como "frequency domain":
# a calibracao mostrou que Qu et al. (2023) usa "Frequency Perception Head" e
# Qian et al. (2020) usa "Frequency-Aware", e ambos escapavam da forma composta.
BLOCO_CUST = (
    '("frequency" OR "discrete cosine transform" OR "DCT" OR "high-frequency" '
    'OR "edge attention" OR "attention module" OR "plug-in module" '
    'OR "two-stream" OR "dual-stream" OR "feature fusion" OR "backbone modification")'
)

JANELA = "from_publication_date:2020-01-01,to_publication_date:2026-12-31"
# conference-paper e obrigatorio: em ciencia da computacao a conferencia e o
# veiculo principal, e CVPR/ECCV/ICCV entram por esse tipo.
TIPOS = "type:article|review|conference-paper"

CAMPOS = (
    "id,doi,title,publication_year,type,primary_location,authorships,"
    "abstract_inverted_index,cited_by_count,referenced_works_count"
)

# Conjunto quasi-gold (protocolo secao 4.4). Somente estudos PRIMARIOS: surveys
# foram removidos do conjunto porque EC4 os excluiria do corpus, e um conjunto de
# validacao nao pode conter estudo que os proprios critérios rejeitam.
QUASI_GOLD = [
    ("V1", "Bae et al. (2025)", "edge-focused deep learning"),
    ("V2", "Guo et al. (2023)", "space-frequency interactive"),
    ("V3", "Qu et al. (2023)", "tampered text detection in document"),
    ("V4", "Qian et al. (2020)", "thinking in frequency"),
]


def _filtro(bloco_tarefa):
    return "title_and_abstract.search:{} AND {},{},{}".format(
        bloco_tarefa, BLOCO_CUST, JANELA, TIPOS
    )


def _url(filtro, cursor=None, per_page=200):
    p = "https://api.openalex.org/works?filter=" + urllib.parse.quote(filtro, safe=":,|")
    if cursor:
        p += "&per-page={}&cursor={}&select={}".format(per_page, cursor, CAMPOS)
    else:
        p += "&per_page=1"
    return p


def buscar(nome, bloco_tarefa, pausa=0.3):
    """Pagina o resultado completo de uma consulta. Devolve (registros, metadados)."""
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
    meta = {
        "consulta": nome,
        "filtro_submetido": filtro,
        "url_contagem": _url(filtro),
        "data_execucao": dt.date.today().isoformat(),
        "retornados": len(registros),
        "paginas": paginas,
    }
    return registros, meta


def abstract(w):
    """Reconstitui o resumo a partir do indice invertido do OpenAlex."""
    inv = w.get("abstract_inverted_index") or {}
    if not inv:
        return ""
    pos = {}
    for tok, idxs in inv.items():
        for i in idxs:
            pos[i] = tok
    return " ".join(pos[i] for i in sorted(pos))


def veiculo(w):
    loc = w.get("primary_location") or {}
    src = loc.get("source") or {}
    return src.get("display_name") or ""


def editora(w):
    loc = w.get("primary_location") or {}
    src = loc.get("source") or {}
    return src.get("host_organization_name") or src.get("publisher") or ""


def autores(w, limite=6):
    nomes = []
    for a in (w.get("authorships") or [])[:limite]:
        au = a.get("author") or {}
        if au.get("display_name"):
            nomes.append(au["display_name"])
    return "; ".join(nomes)


def validar(registros):
    """Checa o conjunto quasi-gold. Protocolo secao 4.4: a regra de decisao exige
    que a busca recupere todos os quatro estudos primarios do conjunto."""
    titulos = [(w.get("title") or "").lower() for w in registros]
    linhas = []
    for vid, ref, frag in QUASI_GOLD:
        achou = next((t for t in titulos if frag in t), None)
        linhas.append((vid, ref, bool(achou), achou or ""))
    return linhas


def gravar(registros, metadados):
    os.makedirs(SAIDA, exist_ok=True)

    # corpus bruto, para auditoria
    with open(os.path.join(SAIDA, "corpus_bruto.json"), "w", encoding="utf-8") as f:
        json.dump(registros, f, ensure_ascii=False)

    # metadados de execucao -> alimenta a Tabela 4 do protocolo
    with open(os.path.join(SAIDA, "execucao_busca.json"), "w", encoding="utf-8") as f:
        json.dump(metadados, f, ensure_ascii=False, indent=2)

    # semente da planilha de triagem
    cols = [
        "id", "base", "consulta", "autores", "ano", "titulo", "veiculo", "editora",
        "doi", "tipo", "citacoes", "resumo",
        "fase1_titulo_veredito", "fase1_codigo_ec", "fase1_avaliador",
        "fase2_resumo_veredito", "fase2_codigo_ec", "fase2_avaliador",
        "amostra_calibracao", "fase3_fulltext_veredito", "fase3_codigo_ec",
        "origem_snowballing", "observacoes",
    ]
    caminho = os.path.join(SAIDA, "triagem.csv")
    with open(caminho, "w", encoding="utf-8", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=cols)
        wr.writeheader()
        for i, w in enumerate(registros, 1):
            wr.writerow({
                "id": "S{:04d}".format(i),
                "base": "OpenAlex",
                "consulta": w.get("_consulta", ""),
                "autores": autores(w),
                "ano": w.get("publication_year") or "",
                "titulo": w.get("title") or "",
                "veiculo": veiculo(w),
                "editora": editora(w),
                "doi": (w.get("doi") or "").replace("https://doi.org/", ""),
                "tipo": w.get("type") or "",
                "citacoes": w.get("cited_by_count") or 0,
                "resumo": abstract(w),
            })
    return caminho


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--so-primaria", action="store_true",
                    help="busca apenas o bloco documento/forense geral")
    ap.add_argument("--validar", action="store_true",
                    help="executa e reporta so a validacao quasi-gold")
    args = ap.parse_args()

    consultas = [("primaria_documento", BLOCO_DOC)]
    if not args.so_primaria:
        consultas.append(("secundaria_face", BLOCO_FACE))

    todos, metas = [], []
    for nome, bloco in consultas:
        regs, meta = buscar(nome, bloco)
        for w in regs:
            w["_consulta"] = nome
        todos += regs
        metas.append(meta)

    # deduplicacao interna por OpenAlex id
    vistos, unicos = set(), []
    for w in todos:
        if w["id"] in vistos:
            continue
        vistos.add(w["id"])
        unicos.append(w)
    dups = len(todos) - len(unicos)

    print("\n=== Execucao da busca ===")
    for m in metas:
        print("  {:22s} {:5d} registros  ({})".format(
            m["consulta"], m["retornados"], m["data_execucao"]))
    print("  {:22s} {:5d}".format("sobreposicao removida", dups))
    print("  {:22s} {:5d}".format("CORPUS UNICO", len(unicos)))

    print("\n=== Validacao quasi-gold (protocolo 4.4) ===")
    linhas = validar(unicos)
    for vid, ref, ok, tit in linhas:
        print("  {} {:22s} {}  {}".format(vid, ref, "OK " if ok else "AUSENTE", tit[:58]))
    n_ok = sum(1 for _, _, ok, _ in linhas)
    print("  recuperados: {}/{}".format(n_ok, len(linhas)))
    if n_ok < len(linhas):
        print("  ATENCAO: regra de decisao da secao 4.4 nao satisfeita.")
        print("  A string deve ser revisada antes da execucao definitiva,")
        print("  e a revisao registrada na Tabela 6 do protocolo.")

    if args.validar:
        return

    caminho = gravar(unicos, {"consultas": metas, "corpus_unico": len(unicos),
                              "sobreposicao_removida": dups,
                              "quasi_gold": [{"id": v, "ref": r, "recuperado": o}
                                             for v, r, o, _ in linhas]})
    print("\nGravado: {}".format(caminho))
    print("Proximo passo: triagem fase 1 (titulo). Ver protocolo secao 6.")


if __name__ == "__main__":
    main()
