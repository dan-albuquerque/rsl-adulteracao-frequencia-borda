# -*- coding: utf-8 -*-
"""Reexecucao da revisao sob a configuracao v2 (2026-09-23).

Tres mudancas de metodo, todas registradas na Tabela 6 do protocolo:
  C4  string podada: saem "attention module", "plug-in module", "feature fusion"
      e "backbone modification" do bloco de customizacao. A calibracao de 11
      variantes mostrou que nao recuperavam nada de unico (corpus 1.413 -> 1.154)
  C5  regex de dominio corrigido: "borda" casava com "gradient" (gradiente
      descendente, otimizador) e "ruido" casava com "residual" (conexao residual,
      padrao arquitetural). Dos 69 promovidos pelo par frequencia+borda sob o
      regex antigo, 34 eram falso positivo lexico
  D9' promocao a profundidade pelo par EXATO frequencia+borda, que e o par que o
      estudo primario combina (ramo DCT + modulos de borda), em vez de
      "frequencia E (borda OU ruido)"

O corpus v2 e subconjunto do v1 salvo 10 registros indexados no OpenAlex depois
de 2026-09-16. Por isso a reexecucao NAO refaz julgamentos: ela transporta os
vereditos ja registrados e tria apenas os 10 novos. Os vereditos de fase 1 dos 10
estao em NOVOS_FASE1, decididos por leitura de titulo e resumo.

Escreve em dados/v2/ e planilhas/v2/. Nada do v1 e tocado.
"""
import csv
import io
import json
import os
import re

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DADOS = os.path.join(RAIZ, "revisao_sistematica", "dados")
V2 = os.path.join(DADOS, "v2")
PLAN = os.path.join(RAIZ, "revisao_sistematica", "planilhas")
PLAN_V2 = os.path.join(PLAN, "v2")

# --- C5: regex de dominio corrigido ---------------------------------------
FREQ = r"frequenc|\bdct\b|discrete cosine|wavelet|fourier|spectral|spectrum|high-frequency|high frequency"
EDGE = (r"\bedge[- ](attention|aware|guid|enhanc|detect|extract|branch|module|featur|map|prior|inform|supervis)"
        r"|edge[- ]?net|boundary|contour|sobel|canny|laplacian|\bedge loss")
RUIDO = r"\bnoise|\bsrm\b|prnu|steganalytic|constrained conv|noiseprint|noise residual"

# Fase 1 dos 10 registros novos (indexados apos 2026-09-16), por leitura.
NOVOS_FASE1 = {
    "Image Forgery Detection using Noise Residual and Frequency Domain Analysis": ("incluir", ""),
    "A Lightweight Spatial–Frequency Fusion Framework with Self-Supervised Learning for Image Forgery Detection and Localization": ("incluir", ""),
    "FAS-MSSA: Frequency-Aware Sampling with Multi-Scale Spectral Attention for Video Face Forgery Detection": ("incluir", ""),
    "M3D-net: Multi-modal 3D facial feature reconstruction network for deepfake detection": ("incluir", ""),
    "BEAT2AASIST: BEATs Feature Splitting with Dual-Branch AASIST for Environmental Sound Deepfake Detection": ("excluir", "EC3"),
    "MDFF-Net++: A Compression-Aware Multimodal Deepfake Detection Framework for Real-Time Social-Media Streams": ("incluir", ""),
    "SWIM-Conv-FFT: A Dual-Domain Hybrid Framework for Robust Deepfake Detection Across Social Media Platforms": ("incluir", ""),
    "Deep Learning-Based Pre-Processing Pipeline and Hybrid Vision Transformer Model for Deepfake Video Detection": ("incluir", ""),
    "Hybrid Deep Learning Model for Fake Image Detection with Advanced Face Object Segmentation Method": ("incluir", ""),
    "Deepfake Face Detection from GAN to Diffusion Model": ("incluir", ""),
}

EC2_SINAIS = [
    r"\bsurvey\b", r"\breview\b", r"comparative (study|analysis|evaluation)",
    r"we (compare|evaluate) (the )?(performance of )?(several|three|four|multiple|various)",
    r"\bbenchmark\b.*\b(dataset|suite)\b", r"we (introduce|present|construct) a (large-scale )?dataset",
    r"ensemble of (pre-?trained|existing|multiple) (models|architectures|cnns)",
    r"transfer learning (with|using) (pre-?trained)",
]
ARQ_SINAIS = [
    r"we propose (a|an|the) [a-z\- ]*(network|net\b|module|branch|stream|architecture|framework|layer|block|encoder|decoder|transformer)",
    r"propose[sd]? (a|an) novel [a-z\- ]*(network|module|branch|stream|architecture)",
    r"\b(dual|two|three|tri|multi)[- ](stream|branch|domain|path)\b",
    r"attention (module|mechanism|block)", r"plug-?in", r"backbone",
    r"we design (a|an)", r"-net\b", r"net:\b",
]


def abstract(w):
    inv = w.get("abstract_inverted_index") or {}
    if not inv:
        return ""
    pos = {}
    for tok, idxs in inv.items():
        for i in idxs:
            pos[i] = tok
    return " ".join(pos[i] for i in sorted(pos))


def veiculo(w):
    src = (w.get("primary_location") or {}).get("source") or {}
    return src.get("display_name") or ""


def editora(w):
    src = (w.get("primary_location") or {}).get("source") or {}
    return src.get("host_organization_name") or src.get("publisher") or ""


def autores(w, limite=6):
    return "; ".join((a.get("author") or {}).get("display_name", "")
                     for a in (w.get("authorships") or [])[:limite]
                     if (a.get("author") or {}).get("display_name"))


def dominios(txt):
    return {n for n, p in (("frequencia", FREQ), ("borda", EDGE), ("ruido", RUIDO))
            if re.search(p, txt)}


def main():
    for d in (V2, PLAN_V2):
        if not os.path.isdir(d):
            os.makedirs(d)

    with io.open(os.path.join(DADOS, "corpus_bruto.json"), encoding="utf-8") as f:
        bruto_v1 = json.load(f)
    oa2sid = {w["id"]: "S{:04d}".format(i + 1) for i, w in enumerate(bruto_v1)}
    with io.open(os.path.join(V2, "corpus_bruto.json"), encoding="utf-8") as f:
        bruto_v2 = json.load(f)
    tri_v1 = {r["id"]: r for r in csv.DictReader(io.open(os.path.join(DADOS, "triagem.csv"), encoding="utf-8"))}
    cols = list(next(iter(tri_v1.values())).keys())

    linhas, n_novos, prox_novo = [], 0, 1
    for w in bruto_v2:
        sid = oa2sid.get(w["id"])
        if sid and sid in tri_v1:
            r = dict(tri_v1[sid])
        else:
            n_novos += 1
            tit = w.get("title") or ""
            ver, ec = NOVOS_FASE1.get(tit, ("incluir", ""))
            r = {c: "" for c in cols}
            r.update({
                "id": "V{:04d}".format(prox_novo), "base": "OpenAlex",
                "consulta": w.get("_consulta", ""), "autores": autores(w),
                "ano": w.get("publication_year") or "", "titulo": tit,
                "veiculo": veiculo(w), "editora": editora(w),
                "doi": (w.get("doi") or "").replace("https://doi.org/", ""),
                "tipo": w.get("type") or "", "citacoes": w.get("cited_by_count") or 0,
                "resumo": abstract(w),
                "fase1_titulo_veredito": ver, "fase1_codigo_ec": ec,
                "fase1_avaliador": "autor",
                "observacoes": "indexado no OpenAlex apos 2026-09-16; triado na reexecucao v2",
            })
            prox_novo += 1
        linhas.append(r)

    # --- fase 2 sob o regex corrigido (C5) e a regra do par exato (D9') ---
    # O EC2 da fase 2 e julgamento por estudo (regra lexica + leitura dos 169
    # candidatos de fronteira no v1) e independe da string: e transportado.
    # So a atribuicao de camada, que e mecanica, e recalculada com o regex novo.
    cont = {"excluir": 0, "mapeamento": 0, "profundidade": 0}
    ec2_transportado = 0
    for r in linhas:
        if r["fase1_titulo_veredito"] != "incluir":
            r["fase2_resumo_veredito"] = r["fase2_codigo_ec"] = r["fase2_camada"] = ""
            r["dominios_detectados"] = ""
            continue
        txt = (r["titulo"] + " " + r["resumo"]).lower()
        doms = dominios(txt)
        camada, ec = "mapeamento", ""
        if r.get("fase2_codigo_ec") == "EC2":
            camada, ec = "excluir", "EC2"
            ec2_transportado += 1
        elif r["id"].startswith("V") and r["resumo"].strip():
            arq = any(re.search(p, txt) for p in ARQ_SINAIS)
            ec2 = any(re.search(p, txt) for p in EC2_SINAIS)
            if ec2 and not arq:
                camada, ec = "excluir", "EC2"
        if camada != "excluir" and {"frequencia", "borda"} <= doms:
            camada = "profundidade"
        r["fase2_resumo_veredito"] = "excluir" if camada == "excluir" else "incluir"
        r["fase2_codigo_ec"] = ec
        r["fase2_camada"] = "" if camada == "excluir" else camada
        r["fase2_avaliador"] = "IA-assistida"
        r["dominios_detectados"] = "+".join(sorted(doms))
        cont[camada] += 1

    # A fase 3 so se aplica a camada de profundidade. Vereditos de fase 3 que vieram
    # da execucao de calibracao para estudos hoje no mapeamento sao descartados.
    for r in linhas:
        if r.get("fase2_camada") != "profundidade":
            r["fase3_fulltext_veredito"] = r["fase3_codigo_ec"] = ""

    with io.open(os.path.join(V2, "triagem.csv"), "w", encoding="utf-8", newline="") as f:
        w_ = csv.DictWriter(f, fieldnames=cols)
        w_.writeheader()
        w_.writerows(linhas)

    prof = [r for r in linhas if r.get("fase2_camada") == "profundidade"]
    mape = [r for r in linhas if r.get("fase2_camada") == "mapeamento"]
    extr = {r["id"] for r in csv.DictReader(io.open(os.path.join(PLAN, "extracao.csv"), encoding="utf-8"))}
    com_ext = [r for r in prof if r["id"] in extr]
    sem_ext = [r for r in prof if r["id"] not in extr]

    print("=== Reexecucao v2 ===")
    print("  corpus v2                    : {}".format(len(linhas)))
    print("  registros novos (pos 16/09)  : {}".format(n_novos))
    print("  fase 1 incluidos             : {}".format(sum(1 for r in linhas if r["fase1_titulo_veredito"] == "incluir")))
    print("  fase 2 excluidos por EC2     : {} (transportados do v1: {})".format(cont["excluir"], ec2_transportado))
    print("  camada de MAPEAMENTO         : {}".format(len(mape)))
    print("  camada de PROFUNDIDADE       : {}".format(len(prof)))
    print("    com extracao ja pronta     : {}   <- carga de revisao do autor".format(len(com_ext)))
    print("    sem extracao               : {}".format(len(sem_ext)))
    from collections import Counter
    c = Counter((r.get("fase3_fulltext_veredito") or "sem veredito") + "/" + (r.get("fase3_codigo_ec") or "-")
                for r in sem_ext)
    for k, v in c.most_common():
        print("      {:24s} {}".format(k, v))

    json.dump([{"id": r["id"], "titulo": r["titulo"], "ano": r["ano"],
                "dominios": r["dominios_detectados"], "doi": r["doi"],
                "tem_extracao": r["id"] in extr} for r in prof],
              io.open(os.path.join(V2, "camada_profundidade.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("\nGravado: dados/v2/triagem.csv e dados/v2/camada_profundidade.json")


if __name__ == "__main__":
    main()
