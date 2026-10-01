# Instruções de extração — fase 3 da revisão sistemática

Documento normativo para a extração de dados do texto completo. Derivado das seções 7 (avaliação de qualidade) e 8 (extração, Tabela 3b) do `revisao_sistematica/protocolo_rsl.md`. Em caso de dúvida, o protocolo tem precedência.

## Contexto

TCC (CESAR School) sobre detecção de fraudes em documentos. O estudo primário propõe combinar customização no domínio da frequência (ramo de transformada discreta do cosseno) com customização no domínio da borda (módulos de atenção em borda) sobre um mesmo backbone, e reivindica originalidade nessa combinação.

A revisão testa essa reivindicação. A camada de profundidade reúne estudos que combinam frequência com borda ou ruído — os candidatos a precedente. O campo **`avalia_interacao` é o que decide a afirmação de originalidade** e precisa ser preenchido com rigor extremo.

## Onde estão as coisas

- Texto extraído: `revisao_sistematica/dados/texto/<id>.txt` (use este, é mais barato que abrir o PDF)
- PDF original: `revisao_sistematica/pdfs/<id>.pdf` (consulte quando o texto estiver confuso, tabelas quebradas, ou precisar conferir uma figura)
- Saída: **um arquivo JSON por estudo** em `revisao_sistematica/dados/extracao/<id>.json`

## Regra de ouro

**Campo não reportado pelo estudo recebe a string `nao_informado`. Nunca inferir, nunca deduzir do que parece provável, nunca preencher com o que "deveria" estar lá.** Um `nao_informado` honesto vale mais que um valor plausível inventado — a revisão reporta exatamente a proporção de estudos que omitem cada informação, e um preenchimento otimista destrói esse número.

## Campos

| Campo | Vocabulário / formato |
|---|---|
| `id` | identificador do estudo, ex: `S0020` |
| `autores` | sobrenomes dos autores, separados por `; ` |
| `ano` | ano de publicação |
| `veiculo` | nome do periódico ou da conferência |
| `tipo_publicacao` | `periodico` ou `conferencia` |
| `tipo_veiculo` | nome curto da editora/organização (IEEE, ACM, Elsevier, Springer, MDPI, CVF...) |
| `dominio_aplicacao` | `documento`, `face`, `imagem_natural`, `misto`, `sensoriamento_remoto`, `medico` |
| `tipo_adulteracao` | o que o estudo detecta: `splicing`, `copy_move`, `inpainting`, `deepfake`, `recompressao`, `seam_carving`, `generico`, `multiplo` (liste com `+` se mais de um, ex: `splicing+copy_move`) |
| `backbone_base` | rede base, ex: `ResNet50`, `EfficientNet-B4`, `Xception`, `ViT`, `U-Net`, `proprio` (se arquitetura do zero) |
| `estrategia_customizacao` | descrição curta e concreta da customização, 1 frase |
| `ponto_intervencao` | **vocabulário fechado**: `entrada_bruta`, `camadas_iniciais`, `corpo`, `camadas_finais`, `cabeca`, `transversal` |
| `dominio_representacao` | domínios explorados, separados por `+`: `espacial`, `frequencia`, `borda`, `ruido`, `textura`, `metadados`, `temporal` |
| `operador_fusao` | **vocabulário fechado**: `concatenacao`, `soma`, `atencao`, `gate_aprendivel`, `canais_entrada`, `ausente` |
| `fusao_condicional` | `sim` quando a fusão é modulada pelo conteúdo (gate, atenção, pesos dependentes da entrada); `nao` quando é fixa pela arquitetura (concatenação ou soma com pesos estáticos) |
| `combina_multiplas` | `sim` se o estudo combina duas ou mais customizações de domínios distintos sobre o mesmo backbone; senão `nao` |
| `quais_combinadas` | quais domínios, ex: `frequencia+borda`; `nao_aplica` se `combina_multiplas` for `nao` |
| `avalia_interacao` | **ver regra crítica abaixo** — `sim`, `nao` ou `parcial` |
| `datasets` | conjuntos de avaliação, separados por `; ` (ex: `CASIA v2; Columbia; NIST16; FF++`) |
| `metricas` | métricas reportadas, separadas por `; ` (ex: `AUC; F1; IoU; acuracia`) |
| `protocolo_validacao` | divisão treino/teste, folds, sementes, seleção de limiar — o que o estudo declarar; `nao_informado` se omitido |
| `resultado_principal` | melhor resultado no conjunto principal, com métrica e número |
| `ganho_sobre_baseline` | ganho declarado sobre baseline, com número; `nao_informado` se o estudo não compara |
| `cross_dataset` | `sim` se avalia treinando num conjunto e testando em outro; senão `nao` |
| `queda_cross_dataset` | queda reportada nessa avaliação, com número; `nao_aplica` se `cross_dataset` for `nao` |
| `custo_params` | número de parâmetros; `nao_informado` se omitido |
| `custo_flops` | operações de ponto flutuante; `nao_informado` se omitido |
| `custo_latencia` | latência/tempo de inferência; `nao_informado` se omitido |
| `hardware_reportado` | GPU/CPU declarada; `nao_informado` se omitido |
| `ablacao` | `sim` se há estudo de ablação; `nao` caso contrário |
| `escopo_ablacao` | o que a ablação varia, 1 frase; `nao_aplica` se não houver |
| `limitacoes_declaradas` | limitações que os próprios autores declaram; `nao_informado` se não declaram |

## Regra crítica: `avalia_interacao`

Este campo responde à pergunta de pesquisa RQ1.3 e é o núcleo da revisão. Leia com atenção:

- **`sim`** — **apenas** quando há **ablação cruzada**: o estudo mede o componente A sozinho, o componente B sozinho, **e** A+B juntos, permitindo isolar o efeito da interação. Os três números precisam existir no texto ou na tabela de ablação.
- **`parcial`** — o estudo tem ablação removendo componentes do modelo completo (mede A+B, A+B menos A, A+B menos B) mas não reporta os componentes isolados sobre o baseline puro. É informativo mas não isola a interação.
- **`nao`** — sem ablação, ou ablação que só varia hiperparâmetro/backbone, ou os componentes aparecem em experimentos separados sem serem cruzados.

**Reportar A e B em experimentos separados NÃO conta como `sim`.** Na dúvida entre `sim` e `parcial`, escolha `parcial` e explique na evidência.

## Avaliação de qualidade (QA1 a QA6)

Pontuação: `1` = sim, `0.5` = parcialmente, `0` = não.

| ID | Critério |
|---|---|
| `qa1` | O estudo examina customização arquitetural para detecção forense de adulteração? |
| `qa2` | Os objetivos estão claramente definidos? |
| `qa3` | O contexto (conjunto de dados, tipo de adulteração, domínio) está adequadamente descrito? |
| `qa4` | A customização é descrita em nível reprodutível, incluindo posição na rede, operações e hiperparâmetros? |
| `qa5` | Os achados são validados com baseline de comparação, estudo de ablação, teste estatístico ou avaliação entre conjuntos de dados? |
| `qa6` | O estudo contribui com evidência aplicável à comparação entre estratégias de customização? |

A avaliação de qualidade **não exclui estudos** — ela caracteriza rigor e alimenta a análise de sensibilidade. Pontue com honestidade: um corpus onde todos tiram 6 não informa nada.

## Evidência obrigatória

Para os **quatro campos de julgamento** — `ponto_intervencao`, `operador_fusao`, `avalia_interacao` e `qa4` — registre em `evidencia` uma citação **literal e curta** do texto (1 a 3 frases) que sustenta a decisão, com indicação da seção ou tabela. É o que torna a extração verificável pelo autor sem reler o artigo inteiro.

## Formato de saída

Um arquivo por estudo: `revisao_sistematica/dados/extracao/<id>.json`

```json
{
  "id": "S0020",
  "autores": "Gao; Sun; Cheng",
  "ano": "2022",
  "veiculo": "IEEE Access",
  "tipo_publicacao": "periodico",
  "tipo_veiculo": "IEEE",
  "dominio_aplicacao": "imagem_natural",
  "tipo_adulteracao": "splicing+copy_move",
  "backbone_base": "ResNet50",
  "estrategia_customizacao": "ramo de frequência baseado em DCT acoplado ao backbone espacial",
  "ponto_intervencao": "camadas_iniciais",
  "dominio_representacao": "espacial+frequencia",
  "operador_fusao": "atencao",
  "fusao_condicional": "sim",
  "combina_multiplas": "sim",
  "quais_combinadas": "frequencia+borda",
  "avalia_interacao": "parcial",
  "datasets": "CASIA v2; NIST16; Columbia",
  "metricas": "AUC; F1",
  "protocolo_validacao": "divisão 80/20, sem folds, limiar fixo em 0,5",
  "resultado_principal": "F1 0,812 em CASIA v2",
  "ganho_sobre_baseline": "+0,043 F1 sobre ResNet50 puro",
  "cross_dataset": "sim",
  "queda_cross_dataset": "AUC cai de 0,91 para 0,68 em Columbia",
  "custo_params": "42,3 M",
  "custo_flops": "nao_informado",
  "custo_latencia": "nao_informado",
  "hardware_reportado": "NVIDIA RTX 3090",
  "ablacao": "sim",
  "escopo_ablacao": "remove o ramo de frequência e o módulo de borda do modelo completo, um de cada vez",
  "limitacoes_declaradas": "desempenho degrada sob recompressão JPEG forte",
  "qa1": 1, "qa2": 1, "qa3": 1, "qa4": 0.5, "qa5": 1, "qa6": 1,
  "evidencia": {
    "ponto_intervencao": "\"The DCT branch is inserted after the first residual stage...\" (Seção 3.2)",
    "operador_fusao": "\"...features are fused through a channel attention module\" (Seção 3.3, Fig. 4)",
    "avalia_interacao": "Tabela 5 remove cada módulo do modelo completo, mas não reporta o módulo de borda isolado sobre o baseline puro — por isso parcial",
    "qa4": "\"kernel size 3, stride 1, 64 channels\" (Seção 3.2); não informa taxa de aprendizado nem otimizador"
  },
  "extracao_origem": "ia_pendente_verificacao",
  "observacao_extrator": "texto do PDF vem com tabelas quebradas; números da Tabela 5 conferidos no PDF original"
}
```

Use exatamente esses nomes de campo. `qa1` a `qa6` são números (`1`, `0.5` ou `0`), não strings. Mantenha `extracao_origem` com o valor `ia_pendente_verificacao` — a revisão do autor é que valida.

## Integridade

Não preencha nenhum campo que você não tenha efetivamente localizado no texto. Se o texto extraído estiver ilegível ou truncado a ponto de impedir a leitura, registre `"falha_leitura": "<motivo>"` no JSON e preencha apenas o que conseguir — é melhor um registro honestamente incompleto que um completo e inventado.
