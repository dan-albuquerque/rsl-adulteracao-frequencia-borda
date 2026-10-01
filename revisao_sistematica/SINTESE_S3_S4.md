# Síntese S1 a S4

Sob a string da seção 4.3 do protocolo, o vocabulário de detecção de domínio da seção 3.1 e a promoção pelo par exato frequência+borda.

**Base:** 17 estudos lidos por completo (camada de profundidade), 1.423 caracterizados por metadado (camada de mapeamento).

---

## S3. Matriz de combinação de domínios (RQ1.3)

A pergunta que esta matriz responde: entre os estudos que combinam customizações de domínios distintos, quantos **medem a interação** entre elas, em vez de apenas somá-las?

| Par de domínios | Estudos | `sim` | `parcial` | `nao` |
|---|---|---|---|---|
| borda + frequência | 7 | 3 | 3 | 1 |
| borda + frequência + ruído | 3 | 0 | 3 | 0 |
| borda + espacial + frequência | 1 | 0 | 1 | 0 |
| borda + espacial | 2 | 0 | 2 | 0 |
| espacial + frequência | 1 | 0 | 1 | 0 |
| ruído + textura | 1 | 1 | 0 | 0 |
| sem par de domínios a cruzar | 2 | 0 | 0 | 2 |

**Regra de `sim`** (protocolo, seção 8): a ablação cruza a **presença ou ausência** de dois domínios de representação distintos, cada um isolado como operador próprio, sobre um baseline. Variar só a multiplicidade de componentes já presentes, ou cruzar um domínio com algo que não é domínio (um módulo de fusão multimodal), não basta. O campo `par_cruzado` registra o que cada ablação realmente cruza.

### O achado central

**11 estudos combinam frequência e borda, inclusive nas combinações triplas. Três medem a interação com ablação cruzada genuína sobre esse par.**

| Estudo | Ano | Veículo | Interação | Domínio | Observação |
|---|---|---|---|---|---|
| **S0059** | 2022 | IEEE Trans. on Knowledge and Data Eng. | **sim** | imagem natural | fatorial completo RGB × frequência × borda, nos quatro datasets |
| **S0280** | 2025 | Journal of Electronic Imaging | **sim** | imagem natural | Tabela 7, um único dataset (NIST16) |
| **S0272** | 2023 | Electronics | **sim** | imagem natural | borda só no treino; frequência vem com atenção espacial; um único dataset |
| S0467 | 2025 | ICCV | parcial | imagem natural | fatorial cruza multiplicidade, não presença; borda só na Tabela 4 |
| S0876 | 2024 | PLoS ONE | parcial | face | borda embutida no ramo espacial, nunca isolada |
| S0020 | 2022 | IEEE Access | parcial | imagem natural | |
| S0231 | 2025 | Sensors | parcial | imagem natural | |
| S0404 | 2026 | IEEE Trans. on Geoscience and Remote Sensing | parcial | sensoriamento remoto | |
| S1095 | 2026 | Information | parcial | face | |
| S1118 | 2026 | Journal on Communications | parcial | imagem natural | |
| S0334 | 2025 | Signal, Image and Video Processing | não | imagem natural | declara ablação no material suplementar, não obtido |

**Notas de classificação.** S0043 (Electronics, 2024) chama de "componente de alta frequência" a saída de um filtro Sobel, sem transformada espectral, e por isso é classificado como espacial+borda. S0795 é o único `sim` fora do par frequência+borda (ruído + textura, face).

**Consequência para a reivindicação de originalidade do estudo primário.** A combinação frequência+borda **tem precedente validado**, três vezes, todas em imagem natural e em tarefa de localização. A lacuna L3, na forma "ninguém combinou esses domínios medindo a interação", **não se sustenta**. Outros oito estudos combinam os dois domínios sem isolar a interação, um deles em ICCV 2025 (S0467), e devem ser citados como trabalho relacionado, não como precedente de ablação.

**O que permanece em aberto.** Nenhum dos três precedentes é do **domínio documental** e nenhum reporta custo em CPU. Diferenças que valem citação: S0272 usa a borda apenas como supervisão de treino, e S0280 e S0272 avaliam a ablação em um único dataset. Um contraste de resultado com o estudo primário: no S0059 a frequência sozinha já supera o baseline, enquanto no estudo primário o DCT sozinho fica abaixo dele e só rende junto com a borda.

**Recomendação de redação.** Citar S0059, S0280 e S0272 como precedentes de ablação cruzada, S0467 e S0876 como combinações sem interação isolada, e delimitar a contribuição ao domínio documental com relato de custo em CPU. S0467 está em ICCV: omiti-lo seria insustentável.

---

## S4. Quadro de evidência (RQ1.4)

Sobre os 17 estudos da camada de profundidade. Script: `scripts/rsl_v2_s4_sensibilidade.py`. Um campo de custo só conta como reportado quando traz valor.

| Prática | n | % |
|---|---|---|
| Realizam ablação | 17 | **100%** |
| Avaliam entre conjuntos de dados distintos | 11 | 65% |
| Reportam custo em parâmetros | 8 | 47% |
| Reportam latência | 5 | 29% |

**Qualidade (QA1 a QA6):** média 5,82 de 6, mediana 6,00.

**`avalia_interacao`:** 4 `sim`, 10 `parcial`, 3 `nao`.

**Concordância entre as duas extrações independentes:** Kappa de Cohen 0,65 sobre os 19 estudos extraídos (15 de 19 concordâncias) e 0,70 sobre os 17 retidos (14 de 17). As divergências foram sobre a aplicação da regra, não sobre os dados.

**Por que a base é pequena e de qualidade alta.** O vocabulário fechado de detecção de domínio (protocolo, seção 3.1) só promove estudos que nomeiam de fato os dois domínios, deixando de fora casamentos léxicos espúrios, que são sistematicamente de menor aderência ao tema.

**Para a redação do artigo.** Com **47% reportando parâmetros**, reportar custo computacional não é, por si, diferencial. O que os dados sustentam é mais específico: dos 5 que reportam latência, nenhum a mede em CPU (quatro declaram GPU, um não especifica o dispositivo). **Latência em CPU**, condição real de auditoria documental, não aparece em nenhum dos 17.

---

## Análise de sensibilidade

As conclusões se sustentam quando se restringe a base por qualidade ou por tipo de veículo?

**Critério de qualidade.** 13 dos 17 estudos têm nota máxima (6), então a mediana coincide com o máximo e um corte "acima da mediana" seria vazio. Os cortes usados são **nota máxima (QA = 6)** e **QA ≥ 5,5**, cada um calculado com a nota das duas extrações independentes (desvio 19 do protocolo).

| Subconjunto | n | Freq.+borda | Precedentes `sim` nesse par | Entre datasets | Parâmetros | Latência |
|---|---|---|---|---|---|---|
| Todos | 17 | 11 | 3 (S0059, S0272, S0280) | 65% | 47% | 29% |
| Só periódicos | 15 | 10 | 3 (S0059, S0272, S0280) | 67% | 47% | 27% |
| QA ≥ 5,5 nas duas extrações | 15 | 10 | 3 (S0059, S0272, S0280) | 67% | 47% | 27% |
| QA = 6, primeira extração | 13 | 9 | 1 (S0059) | 69% | 54% | 31% |
| QA = 6, segunda extração | 5 | 4 | 1 (S0059) | 60% | 40% | 20% |

**O que se sustenta em todos os cortes:**
- **A lacuna L3, na forma "ninguém combinou esses domínios medindo a interação", não se sustenta.** O S0059 tem nota máxima nas duas extrações, é periódico (IEEE TKDE) e tem o fatorial completo nos quatro datasets. Sobrevive a qualquer restrição.
- **Nenhum estudo é do domínio documental**, em nenhum subconjunto.
- **Custo:** parâmetros entre 40% e 54%, latência entre 20% e 31%, e nenhum declara CPU. O argumento de latência em CPU vale em qualquer corte.
- **Só periódicos não muda nada no achado central:** os três precedentes são de periódico. O único estudo de anais com frequência+borda é o S0467 (ICCV), que é `parcial`.

**O que depende do corte:** o **número** de precedentes cai de 3 para 1 quando se exige nota máxima. S0272 e S0280 perdem meio ponto só em QA4 (reprodutibilidade: hiperparâmetros incompletos), não em QA5 (validação). Um corte por QA4 não diz nada sobre a validade da ablação deles. Por isso a redação recomendada é "ao menos um precedente com qualidade máxima, e três no total", e não depender do número três.

**Achado lateral sobre o instrumento de qualidade.** A segunda extração foi sistematicamente mais rigorosa em QA4: deu 0,5 a 10 dos 13 estudos que a primeira pontuou com 6. A escala QA, como definida, tem efeito teto e discrimina pouco. Isso vale uma frase na seção de limitações do relatório.

---

## S1. Estratégias de customização (RQ1.1)

Taxonomia de cinco categorias, construída indutivamente sobre as descrições de arquitetura.

| Código | Categoria |
|---|---|
| A | Multi-ramo paralelo: dois ou mais ramos dedicados, fundidos em algum ponto |
| B | Módulo único ou transformação de entrada sobre um backbone só |
| C | Clássico, sem rede neural treinada |
| D | Não-arquitetural: treino, dados, marca d'água, evasão |
| E | Ensemble entre modelos independentes |

**Sobre a camada de mapeamento (1.423 estudos), com 391 classificados por leitura de título e resumo:**

| Categoria | n |
|---|---|
| A, multi-ramo paralelo | 139 |
| B, módulo ou transformação de entrada | 106 |
| Não classificável mesmo lendo | 74 |
| D, não-arquitetural | 43 |
| C, clássico sem rede | 25 |
| E, ensemble entre modelos | 4 |

**S1 é amostra, não censo.** 391 de 1.423 corresponde a 27% da camada de mapeamento. Os demais têm apenas o domínio de representação detectado por regra mecânica. Declarado como desvio 14 na Tabela 6.

---

## S2. Domínios de representação (RQ1.2)

Frequência de cada domínio sobre a camada de mapeamento (1.423 estudos). Domínio de cada estudo: regra mecânica do vocabulário final (seção 3.1 do protocolo) em todo o corpus, unida aos domínios atribuídos por leitura nos 391 estudos lidos. Script: `scripts/rsl_v2_mapeamento_s2.py`.

| Domínio | n |
|---|---|
| frequência | 583 |
| ruído | 161 |
| espacial | 105 |
| borda | 54 |
| temporal | 46 |
| textura | 17 |
| nenhum domínio detectado | 672 |

**Ressalva de vocabulário.** Frequência, borda e ruído são quase censo: a regra mecânica os procura em todos os registros. Espacial, textura, temporal e metadados só aparecem nos estudos efetivamente lidos, porque a regra mecânica nunca os procurou. Estão **subcontados no corpus inteiro, não ausentes**.

**Termos excluídos do vocabulário.** `residual` (conexão do ResNet) não conta como ruído e `gradient` (gradiente descendente) não conta como borda: são termos onipresentes em artigos de aprendizado profundo e inflariam as duas contagens.
