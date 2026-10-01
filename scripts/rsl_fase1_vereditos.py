# -*- coding: utf-8 -*-
"""Aplica os vereditos da fase 1 (triagem por titulo) a triagem.csv.

Referencia: revisao_sistematica/protocolo_rsl.md, secao 6, fase 1.

Regra: so se exclui o CLARAMENTE fora de escopo. Tudo que nao aparece no
dicionario abaixo avanca para a fase 2, conforme o principio "na duvida, inclui"
(Kitchenham e Charters, 2007, secao 6.2.2).

Este arquivo e o registro auditavel da fase 1: cada exclusao tem identificador de
estudo e codigo de criterio de exclusao. Para revisar uma decisao, basta procurar
o identificador aqui.

Codigos usados nesta fase:
  EC1  fora do dominio forense de adulteracao de imagem
  EC3  exclusivamente audio, fala, musica ou texto
  EC4  estudo secundario (survey, review, overview, bibliometria)
  EC7  idioma fora de ingles e portugues
EC8 (duplicatas) nao e aplicado aqui: fica a cargo de scripts/rsl_dedup.py, que
usa o criterio declarado no protocolo (DOI normalizado + similaridade de titulo).
"""
import collections
import csv
import io
import json
import os

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV = os.path.join(RAIZ, 'revisao_sistematica', 'dados', 'triagem.csv')
LOG = os.path.join(RAIZ, 'revisao_sistematica', 'dados', 'fase1_exclusoes.json')

EXCLUSOES = {}


def marcar(codigo, ids):
    for i in ids:
        assert i not in EXCLUSOES, "identificador repetido: " + i
        EXCLUSOES[i] = codigo


# ---------------------------------------------------------------------------
# EC3  audio, fala, musica, texto. Sem componente de imagem estatica.
# ---------------------------------------------------------------------------
marcar("EC3", """
S0011 S0045 S0072 S0079 S0117 S0149 S0162 S0166 S0184 S0190 S0215 S0222 S0316
S0346 S0378 S0438 S0452 S0470
S0583 S0638
S0669 S0673 S0679 S0682 S0684 S0693 S0706 S0714 S0722 S0746 S0756 S0793 S0819
S0821 S0824 S0832
S0837 S0839 S0841 S0844 S0888 S0894 S0895 S0900 S0901 S0902 S0909 S0911 S0912
S0914 S0917 S0924 S0947 S0977 S0982 S1003
S1058 S1065 S1074 S1085 S1100 S1103 S1105 S1119 S1121 S1127 S1135 S1140 S1142
S1159 S1160 S1164 S1171 S1178 S1184 S1186 S1187 S1194 S1199
S1221 S1224 S1225 S1229 S1242 S1243 S1247 S1250 S1252 S1253 S1255 S1261 S1281
S1286 S1290 S1294 S1295 S1298 S1299 S1300 S1308 S1310 S1316 S1317 S1318 S1319
S1345 S1348 S1359 S1360 S1364 S1376 S1379 S1383 S1384 S1386 S1394 S1395 S1399
S1411
""".split())

# ---------------------------------------------------------------------------
# EC4  estudo secundario. Retidos em lista propria para o snowballing (fase 4).
# ---------------------------------------------------------------------------
marcar("EC4", """
S0061 S0167 S0189 S0214 S0238 S0268 S0273
S0325 S0333 S0356 S0415 S0474 S0476
S0539 S0540 S0549 S0574 S0576 S0579 S0584 S0585
S0664 S0749
S0887 S0893 S0897 S0974 S0975 S1005
S1019 S1026 S1029 S1032 S1035 S1046 S1060 S1073 S1077 S1088 S1109 S1110 S1111
S1113 S1114 S1129 S1130 S1133 S1134 S1138 S1162 S1168 S1169 S1200 S1205
S1240 S1277 S1287 S1293 S1333 S1340 S1347 S1352 S1368 S1398 S1406
""".split())

# ---------------------------------------------------------------------------
# EC1  fora do dominio. Inclui atribuicao de camera, esteganalise, marca d'agua
# de copyright, fake news textual, e falsos positivos da string ("splice" em
# fibra optica e em biologia molecular, "forensics" em isotopos).
# ---------------------------------------------------------------------------
marcar("EC1", """
S0067 S0181 S0239 S0243 S0306
S0344 S0366 S0382 S0411 S0432 S0469
S0491 S0507 S0513 S0520 S0525 S0533 S0544 S0560 S0562 S0563 S0575 S0577 S0580
S0581 S0586 S0587
S0916
S1050 S1055
S1284 S1389 S1392 S1401 S1403 S1412 S1413
""".split())

# ---------------------------------------------------------------------------
# EC7  idioma. Indonesio, chines, ucraniano.
# ---------------------------------------------------------------------------
marcar("EC7", "S0324 S0555 S1358 S1396".split())


def main():
    regs = list(csv.DictReader(io.open(CSV, encoding='utf-8')))
    cols = list(regs[0].keys())
    ids = {r['id'] for r in regs}
    orfaos = [i for i in EXCLUSOES if i not in ids]
    assert not orfaos, "identificadores inexistentes no corpus: %s" % orfaos

    for r in regs:
        ec = EXCLUSOES.get(r['id'])
        r['fase1_titulo_veredito'] = 'excluir' if ec else 'incluir'
        r['fase1_codigo_ec'] = ec or ''
        r['fase1_avaliador'] = 'IA-assistida'

    with io.open(CSV, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(regs)

    json.dump(EXCLUSOES, io.open(LOG, 'w', encoding='utf-8'), indent=1, sort_keys=True)

    c = collections.Counter(EXCLUSOES.values())
    print("=== Fase 1 concluida: triagem por titulo ===")
    print("  corpus                : %d" % len(regs))
    print("  excluidos             : %d  (%.1f%%)" % (len(EXCLUSOES), 100 * len(EXCLUSOES) / len(regs)))
    for k in sorted(c):
        print("    %s %4d" % (k, c[k]))
    print("  avancam para a fase 2 : %d" % (len(regs) - len(EXCLUSOES)))
    print("  registro auditavel    : %s" % LOG)


if __name__ == '__main__':
    main()
