"""Deduplica registros da revisao sistematica.

Referencia: revisao_sistematica/protocolo_rsl.md, secao 6 (Gestao de referencias).
Criterio do protocolo: DOI normalizado + similaridade de titulo acima de 85%.

Serve para dois cenarios:
  1. corpus vindo do rsl_search.py (dedup ja feito por id, este script confirma
     por DOI e titulo, que e o criterio declarado no protocolo);
  2. exports BibTeX/RIS baixados manualmente das bases, que precisam de dedup
     cross-base antes da triagem.

Uso:
    python scripts/rsl_dedup.py revisao_sistematica/dados/triagem.csv
    python scripts/rsl_dedup.py export_ieee.bib export_acm.bib export_sd.ris
"""

import csv
import difflib
import os
import re
import sys

# Limiar de similaridade de titulo. O protocolo v0.4 declarava 0.85; a execucao
# mostrou que titulos desta area sao formulaicos demais para esse valor
# ("An improved BLOCK based copy-move..." x "An improved REDUCED FEATURE based
# copy-move..." passam de 0.85 e sao artigos distintos), produzindo 12 falsos
# positivos em 71. Elevado para 0.95 com exigencia adicional de mesmo ano.
# Registrado na Tabela 6 do protocolo.
LIMIAR = 0.95
EXIGIR_MESMO_ANO = True


def norm_doi(d):
    if not d:
        return ""
    d = d.strip().lower()
    d = re.sub(r"^https?://(dx\.)?doi\.org/", "", d)
    return d.strip()


def norm_titulo(t):
    t = (t or "").lower()
    t = re.sub(r"[^a-z0-9 ]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def ler_csv(caminho):
    with open(caminho, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def ler_bib(caminho):
    """Parser minimo de BibTeX: so precisa de title e doi para deduplicar."""
    txt = open(caminho, encoding="utf-8", errors="replace").read()
    regs = []
    for bloco in re.split(r"\n@", txt)[0 if txt.startswith("@") else 1:]:
        def campo(nome):
            m = re.search(nome + r"\s*=\s*[{\"](.+?)[}\"]\s*,?\s*\n", bloco,
                          re.I | re.S)
            return re.sub(r"\s+", " ", m.group(1)).strip() if m else ""
        t = campo("title")
        if t:
            regs.append({"titulo": t, "doi": campo("doi"), "ano": campo("year"),
                         "autores": campo("author"), "_origem": os.path.basename(caminho)})
    return regs


def ler_ris(caminho):
    txt = open(caminho, encoding="utf-8", errors="replace").read()
    regs, cur = [], {}
    for linha in txt.splitlines():
        m = re.match(r"^([A-Z][A-Z0-9])  - (.*)$", linha)
        if not m:
            continue
        tag, val = m.group(1), m.group(2).strip()
        if tag == "TI":
            cur["titulo"] = val
        elif tag == "DO":
            cur["doi"] = val
        elif tag == "PY":
            cur["ano"] = val
        elif tag == "AU":
            cur["autores"] = cur.get("autores", "") + ("; " if cur.get("autores") else "") + val
        elif tag == "ER":
            if cur.get("titulo"):
                cur["_origem"] = os.path.basename(caminho)
                regs.append(cur)
            cur = {}
    if cur.get("titulo"):
        cur["_origem"] = os.path.basename(caminho)
        regs.append(cur)
    return regs


def carregar(caminhos):
    regs = []
    for c in caminhos:
        ext = os.path.splitext(c)[1].lower()
        if ext == ".csv":
            regs += ler_csv(c)
        elif ext == ".bib":
            regs += ler_bib(c)
        elif ext in (".ris", ".txt", ".nbib"):
            regs += ler_ris(c)
        else:
            sys.exit("extensao nao suportada: " + c)
    return regs


def deduplicar(regs):
    """Devolve (unicos, duplicatas). Duplicata guarda o id do registro retido."""
    unicos, dups = [], []
    por_doi = {}
    titulos = []  # (titulo_norm, indice_em_unicos)

    for r in regs:
        doi = norm_doi(r.get("doi"))
        tn = norm_titulo(r.get("titulo"))

        if doi and doi in por_doi:
            dups.append((r, unicos[por_doi[doi]], "DOI identico"))
            continue

        achou = None
        for tn2, idx in titulos:
            if not tn or not tn2:
                continue
            # atalho de custo: comparar so titulos de comprimento proximo
            if abs(len(tn) - len(tn2)) > 0.3 * max(len(tn), len(tn2)):
                continue
            if difflib.SequenceMatcher(None, tn, tn2).ratio() >= LIMIAR:
                if EXIGIR_MESMO_ANO and str(r.get("ano", "")) != str(unicos[idx].get("ano", "")):
                    continue
                achou = idx
                break
        if achou is not None:
            dups.append((r, unicos[achou], "titulo similar >= {:.0%}".format(LIMIAR)))
            continue

        if doi:
            por_doi[doi] = len(unicos)
        titulos.append((tn, len(unicos)))
        unicos.append(r)

    return unicos, dups


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    caminhos = sys.argv[1:]
    regs = carregar(caminhos)
    print("carregados: {} registros de {} arquivo(s)".format(len(regs), len(caminhos)))

    unicos, dups = deduplicar(regs)
    print("unicos    : {}".format(len(unicos)))
    print("duplicatas: {}  (EC8 no protocolo)".format(len(dups)))

    if dups:
        print("\n--- duplicatas removidas ---")
        for r, retido, motivo in dups[:40]:
            print("  [{}] {:50s}".format(motivo, (r.get("titulo") or "")[:50]))
            print("      retido: {:50s}".format((retido.get("titulo") or "")[:50]))
        if len(dups) > 40:
            print("  ... e outras {}".format(len(dups) - 40))

    base = os.path.dirname(os.path.abspath(caminhos[0]))
    saida = os.path.join(base, "corpus_dedup.csv")
    cols = list(unicos[0].keys()) if unicos else []
    with open(saida, "w", encoding="utf-8", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=cols)
        wr.writeheader()
        wr.writerows(unicos)
    print("\nGravado: {}".format(saida))
    print("Registrar a contagem de duplicatas em EC8 da Tabela 2 do protocolo.")


if __name__ == "__main__":
    main()
