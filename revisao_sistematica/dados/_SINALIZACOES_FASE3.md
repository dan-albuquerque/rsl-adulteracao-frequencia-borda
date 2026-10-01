# Sinalizações da fase 3 — decisões que são do autor

Casos levantados durante a extração do texto completo que **não** podem ser resolvidos pelo extrator, porque implicam reclassificar ou excluir estudo já admitido pelas fases 1 e 2. Veículo e DOI conferidos por mim na `triagem.csv`, não no texto.

## A. Candidatos a exclusão por EC5 + IC4 (preprints, decisão D2)

D2 exclui preprints. Estes têm identificador de objeto digital (DOI) do Zenodo e nenhum veículo formal, ou seja, são autodepósitos:

| id | Ano | Veículo registrado | DOI | Agravante |
|---|---|---|---|---|
| S1137 | 2026 | Zenodo (CERN) | 10.5281/zenodo.18252663 | **Resultados fictícios.** A própria seção 8 rotula a Tabela II como "illustrative... placeholders until empirical experiments are run". Não pode entrar em nenhuma síntese quantitativa |
| S1251 | 2026 | Zenodo (CERN) | 10.5281/zenodo.22643882 | Autor único, aparenta relatório de conclusão de curso. Combina espacial + áudio, fora do par de domínios da RQ1.3 |

**Falsos alarmes já descartados por mim:** S0588 (arXiv no texto, mas DOI 10.1109/cvpr46437.2021.01605, CVPR 2021) e S0683 (DOI 10.1109/tcsvt.2023.3325427, IEEE TCSVT 2023). Ambos publicados, ficam.

> **S1137 e S1251 — RESOLVIDO em 2026-09-21, decisão do autor: excluir.** `fase3_fulltext_veredito` marcado `excluir` com `EC5` em `dados/triagem.csv`. JSONs movidos para `dados/extracao_excluidos/`. Junto com S0430 (seção I) e S0434 (seção I), `planilhas/extracao.csv` caiu de 91 para **87** estudos.

## B. Candidatos a exclusão por EC2 (não propõe customização arquitetural)

| id | Veículo | Motivo |
|---|---|---|
| S0293 | IEEE Transactions on Cybernetics, 2021 | Método estatístico clássico sobre transformada discreta do cosseno em blocos, para estimar fator de reamostragem. **Sem rede neural nenhuma**; só cita redes de outros autores no trabalho relacionado. Falso negativo da regra léxica de EC2, do tipo já previsto no CLAUDE.md ("EC2 não pode ser automatizado") |
| S0683 | IEEE TCSVT, 2023 | DeepNotch é pipeline de **evasão** contra detectores de deepfake, não customização de detector. O extrator pontuou QA1 = 0. Publicação legítima, escopo errado |

> **S0293 — RESOLVIDO em 2026-09-21, decisão do autor: excluir.** `fase3_fulltext_veredito` marcado `excluir` com `EC2` em `dados/triagem.csv`. JSON movido para `dados/extracao_excluidos/S0293.json`.
>
> **S0683 — RESOLVIDO em 2026-09-21, decisão do autor: excluir, fora de escopo.** `fase3_fulltext_veredito` marcado `excluir` com `EC1` em `dados/triagem.csv`. Mesmo padrão do S1301: DeepNotch ataca detectores (ruído adversarial PGD contra um substituto ResNet50 + rede de filtragem KPN estilo U-Net) para reduzir a acurácia deles (queda média de 36,79%, até 97% no melhor caso) — não propõe nem avalia um detector, então não aborda a tarefa que a revisão cobre. JSON movido para `dados/extracao_excluidos/S0683.json`.

## C. Qualidade editorial baixa, mas dentro dos critérios

Ficam no corpus; o baixo escore de avaliação de qualidade (QA) é o instrumento correto e alimenta a análise de sensibilidade.

| id | Veículo | QA | Nota |
|---|---|---|---|
| S0521 | Int. J. of Science Engineering and Technology, 2026 | 3,0 | Hiperparâmetros publicados como `[fill value]` não preenchidos |
| S0427 | IJTLS, 2026 | 4,0 | Ablação citada no resumo, sem tabela no corpo |
| S1066 | IJACSA, 2026 | 4,5 | Autores declaram na seção VI-A: "An ablation study was not conducted" |

## D. Reclassificação possível, não exclusão

| id | Questão |
|---|---|
| S1028 | ACM 2025, publicado. Os dois ramos (LGrad e FreqNet) são **backbones inteiros distintos**, não duas customizações sobre o mesmo backbone. O critério de promoção à camada de profundidade fala em mesmo backbone. `avalia_interacao` saiu `sim`, mas o `sim` é sobre fusão de modelos, não sobre interação de customizações |
| S0122 | IEEE Access 2020. Ablação cruzada genuína, mas o par de domínios é espacial + ruído, não frequência + borda |

> **Arquivo órfão `pdfs/multimedia-02-00011.pdf` — RESOLVIDO em 2026-09-21, decisão do autor: descartar.** Movido para `dados/_descartados/multimedia-02-00011.pdf`, fora da pasta `pdfs/` (não é mais varrido por `rsl_pendencias.py` nem por nenhum outro script). Não tinha id no corpus, então não afeta nenhum funil ou contagem.

## E. Problemas de arquivo

| id | Situação |
|---|---|
| S1149 | PDF corrompido de forma irrecuperável. **Precisa ser rebaixado** de https://dl.acm.org/doi/10.1145/3785353.3815096 |
| S0941 | Periódico chinês 计算机工程 (Computer Engineering). A fonte do PDF não tem mapa ToUnicode, então tanto pdftotext quanto PyMuPDF devolvem códigos de glifo, não texto. Extração por leitura só é possível rasterizando as páginas, como foi feito no S0393 |
| S0795 | Journal of Image and Graphics, 2023. Texto veio parcialmente corrompido no corpo em chinês, mas resumo, tabelas e referências em inglês ficaram íntegros. Extração considerada confiável pelo extrator |

---

## F. Mais candidatos a EC2 (lotes 4 e 6)

| id | Motivo |
|---|---|
| S1256 | Sistema declaradamente "training-free": Canny, transformada rápida de Fourier e coeficientes cepstrais de frequência mel, todos clássicos. **Zero rede neural.** Mesmo caso do S0293 |
| S0191 | Usa backbones prontos sem customização, testando domínios de entrada (pixel, frequência, autocorrelação) separadamente e sem fusão. Contribuição é de protocolo experimental, não de arquitetura |

> **S1256 — RESOLVIDO em 2026-09-21, decisão do autor: excluir.** `fase3_fulltext_veredito` marcado `excluir` com `EC2`. JSON movido para `dados/extracao_excluidos/S1256.json`. Estava contado na matriz S3 no par frequência+borda (`avalia_interacao = nao`, não afetava nenhum `sim`); removido do denominador desse par.
>
> **S0191 — RESOLVIDO em 2026-09-21, decisão do autor: excluir.** `fase3_fulltext_veredito` marcado `excluir` com `EC2` (o critério exige customização arquitetural; aqui são redes prontas — InceptionV3, ResNet50, EfficientNetB2 — treinadas separadamente sobre RGB, Fourier ou autocorrelação, sem fusão nem qualquer modificação de arquitetura). JSON movido para `dados/extracao_excluidos/S0191.json`.

## G. Ensemble entre modelos ≠ fusão dentro do backbone

Categoria que a taxonomia S1 precisa separar, senão a síntese S3 conta como precedente algo que não é:

| id | Situação |
|---|---|
| S1374 | DeepFakeBuster: ensemble de 6 backbones independentes com portão de confiança aprendido. **Excluído em 2026-09-30**, ver abaixo |
| S1028 | Dois backbones inteiros distintos (LGrad e FreqNet), fundidos a posteriori. Permanece no corpus, fora da matriz S3 |

Nos dois casos existe ablação com componentes isolados, então `avalia_interacao` saiu alto na extração original, mas o que é isolado são **modelos**, não customizações sobre um backbone compartilhado.

**S1374 excluído por EC2 em 2026-09-30.** A validação independente (leitura às cegas, sem acesso à extração original) descreveu a mesma arquitetura, mas foi além: as modificações internas de cada um dos seis detectores ("EdgeAnalysis", "Noise", "Custom", "Custom Attention") não são descritas em nenhum lugar do texto, e o QA4 (customização descrita em nível reprodutível) caiu de 1 para 0. Não há grafo computacional customizado em nenhum dos seis modelos, verificável no texto: a contribuição inteira está na regra de fusão das saídas de modelos prontos, que é exatamente o caso que a nota do EC2 (protocolo, seção 5.2) descreve como exclusão. JSON movido para `dados/extracao_excluidos/S1374.json`. Efeito: `planilhas/v2/extracao.csv` cai de 19 para **18** estudos.

**S0913 excluído por EC2 em 2026-09-30, decisão do autor.** WaveDIF (CVPR Workshops 2025) não usa rede neural em nenhuma etapa: DFT 2D, filtro passa-baixas gaussiano, wavelet de Haar, quatro energias de sub-banda e regressão logística. A extração já o marcava como candidato retroativo a EC2 (QA1 = 0). É o caso "método clássico sem rede neural" da nota do EC2 (protocolo, seção 5.2). Não afetava a matriz S3 (`avalia_interacao = nao`, sem par de domínios). JSON movido para `dados/extracao_excluidos/S0913.json`. Efeito: `planilhas/v2/extracao.csv` cai de 18 para **17** estudos; fase 3 passa a 18 exclusões (EC6 14, EC2 4).

**S1028 permanece.** É estrutura de ensemble equivalente, mas não foi submetido à segunda leitura nesta rodada; segue no corpus como estudo válido para RQ1.1/RQ1.2, fora da matriz S3.

## H. Ablação não verificável no texto extraído

`avalia_interacao` é o campo que decide a RQ1.3, então nestes casos ele está provisório:

| id | Problema |
|---|---|
| S0334 | A ablação cruzada existe, mas está no **material suplementar**, que não veio no PDF. Marcado `nao` por não poder ser confirmada |
| ~~S0578~~ | Tabelas III e IV quebradas na extração. Ponto ficou moot: o estudo foi excluído por EC2 na seção K (é KNN, sem rede neural) |
| S0799 | Tabela 2 severamente quebrada. Texto confirma direcionalmente, valor de SRM isolado não conferido |
| S0678 | Inconsistência interna do próprio artigo na numeração dos itens (c) e (d) da ablação |
| S0200 | Tabela I com operações de ponto flutuante e latência quebrada |

---

## I. Lote 5

**Mais um candidato a preprint (EC5 + IC4, decisão D2):** S0430, 2026, veículo registrado como Zenodo (CERN), identificador `10.5281/zenodo.20157196`. Junta-se a S1137 e S1251 na seção A.

**Falsos alarmes de preprint já descartados por mim:** S0677 é IEEE Transactions on Image Processing 2024 (`10.1109/tip.2024.3441821`) e S1063 é a conferência FLAIRS (`10.32473/flairs.39.1.141438`). Ambos publicados, ficam.

**Escopo:** S0434 (identificador `10.1145/3785353.3815070`, 2026) é forense temporal, estima a idade de uma imagem. Não é detecção de fraude nem de adulteração. O extrator rebaixou QA1 por isso. Candidato a EC1 ou EC3, decisão do autor.

> **RESOLVIDO em 2026-09-21, decisão do autor: excluir.** `fase3_fulltext_veredito` marcado `excluir` com `EC1` em `dados/triagem.csv`. O JSON de extração foi movido para `dados/extracao_excluidos/S0434.json` (fora da consolidação, preservado para auditoria).

> **S0430 — RESOLVIDO em 2026-09-21, decisão do autor: excluir.** Mesmo tratamento: preprint Zenodo, `fase3_fulltext_veredito` marcado `excluir` com `EC5`, JSON movido para `dados/extracao_excluidos/S0430.json`.

**Distinção fina que o extrator pegou bem:** em S0447 existe ablação cruzada de verdade (Tabela II), mas a única customização de domínio é frequência. O segundo componente é fusão entre modalidades, não uma segunda customização de domínio. Por isso a ablação **não conta** para a RQ1.3. Esse é o tipo de erro que inflaria a contagem de precedentes.

## K. Achados de integridade na construção da taxonomia S1 (2026-09-21)

Levantados lendo `estrategia_customizacao` dos 87 estudos para `scripts/rsl_sintese_s1_taxonomia.py`, não faziam parte das sinalizações originais da leitura em lote.

| id | Problema | Decisão do autor |
|---|---|---|
| **S0578** | `qa1` estava marcado `1` (equivocado). O método é **KNN sobre vetor de 79 dimensões de atributos manuais** (DFT do histograma + filtro passa-alta multiescala), classificado explicitamente por "KNN", sem rede neural nenhuma. Mesmo padrão de falso positivo já descrito no CLAUDE.md ("EC2 não pode ser automatizado"), agora encontrado numa extração feita por leitura completa, não por regra léxica. | **RESOLVIDO, excluir (EC2)** |
| **S1301** | `qa1` já estava corretamente em `0`. É pipeline de **purificação adversarial que ataca detectores** (substitui deconvolução por upsampling+blur, suprime alta frequência, alinha distribuição latente via DINO-v2) — mesmo padrão do S0683 (DeepNotch, ainda pendente, seção B), que também não aborda detecção. | **RESOLVIDO, excluir (EC1)** |

> **Ambos RESOLVIDOS em 2026-09-21, decisão do autor: excluir.** `fase3_fulltext_veredito` marcado `excluir` em `dados/triagem.csv` (S0578 com `EC2`, S1301 com `EC1`, por não abordar detecção). JSONs movidos para `dados/extracao_excluidos/`.

**Por que S0578 importava mais que uma correção de rotina**: ele estava contado como um dos 6 estudos com `avalia_interacao = sim` no par frequência+borda em `SINTESE_S3_S4.md` — a lista recomendada para citar no artigo como precedente direto da combinação de domínios do estudo primário. Com a exclusão, **o par ficou definitivamente em 5** precedentes genuinamente neurais (S0467, S0280, S0876, S0272, S0059); S0578 não é citável como "arquitetura precedente" porque não é arquitetura. Ainda vale mencionar como curiosidade à parte: um método clássico supera baselines de aprendizado profundo na mesma tarefa — mas é um argumento diferente do que "5 arquiteturas neurais já combinaram os dois domínios".

**S1301 não afetava a matriz S3** (`avalia_interacao = nao`); removido do denominador do par espacial+frequência (34 → 33).

## J. Achado positivo a destacar na síntese

**S0734** é o caso mais forte encontrado até aqui: ablação cruzada genuína e completa, com o módulo de ruído isolado, o módulo de frequência isolado e os dois juntos, sobre um mesmo backbone de dois ramos, medida dentro e entre conjuntos de dados. É precedente direto para a RQ1.3 e precisa ser lido pelo autor com prioridade máxima, porque é o estudo com maior potencial de contestar a reivindicação de originalidade do trabalho principal.

Outros casos limpos de ablação cruzada, por ordem de proximidade ao par frequência + borda: S0622, S1152, S0747, S0727, S0795, S1011, S0523, S0588, S0122.
