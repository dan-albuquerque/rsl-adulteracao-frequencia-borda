"""Calcula o Cohen Kappa da amostra de calibracao da triagem.

Referencia: revisao_sistematica/protocolo_rsl.md, fase 2 da secao 6 e ameaca V2.
O protocolo exige Kappa >= 0,8 antes de liberar a triagem em volume.

Espera um CSV com uma linha por registro da amostra e duas colunas de veredito,
uma por avaliador. Vereditos aceitos: incluir, excluir, duvida.

Uso:
    python scripts/rsl_kappa.py calibracao.csv
    python scripts/rsl_kappa.py calibracao.csv --a aval_danilo --b aval_eduardo
    python scripts/rsl_kappa.py calibracao.csv --binario   # duvida conta como incluir
"""

import argparse
import collections
import csv
import sys

LIMIAR_PROTOCOLO = 0.80


def kappa(pares):
    """Cohen Kappa para duas categorizacoes nominais."""
    n = len(pares)
    if n == 0:
        return None, None, None
    cats = sorted({c for p in pares for c in p})
    obs = sum(1 for a, b in pares if a == b) / n
    ca = collections.Counter(a for a, _ in pares)
    cb = collections.Counter(b for _, b in pares)
    esp = sum((ca[c] / n) * (cb[c] / n) for c in cats)
    if esp == 1.0:
        return 1.0, obs, esp  # concordancia total e sem variacao
    return (obs - esp) / (1 - esp), obs, esp


def interpretar(k):
    # Landis & Koch (1977), a escala usual na literatura
    if k < 0:
        return "pior que o acaso"
    if k < 0.20:
        return "ligeira"
    if k < 0.40:
        return "razoavel"
    if k < 0.60:
        return "moderada"
    if k < 0.80:
        return "substancial"
    return "quase perfeita"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--a", default=None, help="coluna do avaliador A")
    ap.add_argument("--b", default=None, help="coluna do avaliador B")
    ap.add_argument("--binario", action="store_true",
                    help="colapsa 'duvida' em 'incluir' (o protocolo faz duvida avancar)")
    args = ap.parse_args()

    with open(args.csv, encoding="utf-8") as f:
        regs = list(csv.DictReader(f))
    if not regs:
        sys.exit("planilha vazia")

    cols = list(regs[0].keys())
    ca, cb = args.a, args.b
    if not ca or not cb:
        cands = [c for c in cols if "aval" in c.lower() or "veredito" in c.lower()]
        if len(cands) < 2:
            sys.exit("informe --a e --b. Colunas disponiveis: " + ", ".join(cols))
        ca, cb = cands[0], cands[1]
        print("colunas inferidas: A={}  B={}".format(ca, cb))

    pares, ignorados = [], 0
    for r in regs:
        a = (r.get(ca) or "").strip().lower()
        b = (r.get(cb) or "").strip().lower()
        if not a or not b:
            ignorados += 1
            continue
        if args.binario:
            a = "incluir" if a in ("incluir", "duvida") else "excluir"
            b = "incluir" if b in ("incluir", "duvida") else "excluir"
        pares.append((a, b))

    if not pares:
        sys.exit("nenhum par completo de vereditos")

    k, obs, esp = kappa(pares)
    print("\n=== Cohen Kappa ===")
    print("  pares avaliados       : {}".format(len(pares)))
    if ignorados:
        print("  linhas incompletas    : {} (ignoradas)".format(ignorados))
    print("  concordancia observada: {:.4f}".format(obs))
    print("  concordancia esperada : {:.4f}".format(esp))
    print("  KAPPA                 : {:.4f}  ({})".format(k, interpretar(k)))

    print("\n--- matriz de confusao ---")
    cats = sorted({c for p in pares for c in p})
    m = collections.Counter(pares)
    print("        " + "".join("{:>10s}".format("B:" + c[:8]) for c in cats))
    for a in cats:
        print("{:>8s}".format("A:" + a[:6]) + "".join(
            "{:>10d}".format(m.get((a, b), 0)) for b in cats))

    print("\n--- veredito do protocolo ---")
    if k >= LIMIAR_PROTOCOLO:
        print("  Kappa >= {:.2f}: criterios calibrados.".format(LIMIAR_PROTOCOLO))
        print("  Liberada a triagem em volume (fase 2, secao 6).")
    else:
        print("  Kappa < {:.2f}: NAO liberado.".format(LIMIAR_PROTOCOLO))
        print("  O protocolo exige revisar a redacao dos criterios IC/EC e")
        print("  repetir a calibracao antes de triar o restante. Divergencias")
        print("  concentradas indicam qual criterio esta ambiguo: veja a matriz.")

    disc = [(a, b) for a, b in pares if a != b]
    if disc:
        print("\n  discordancias: {} de {} ({:.1%})".format(
            len(disc), len(pares), len(disc) / len(pares)))


if __name__ == "__main__":
    main()
