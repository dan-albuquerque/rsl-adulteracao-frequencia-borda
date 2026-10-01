# Instruções de extração — camada de mapeamento (Tabela 3a)

Documento normativo para a extração reduzida da camada de mapeamento. Derivado da seção 8 (Tabela 3a) do `revisao_sistematica/protocolo_rsl.md` e da taxonomia S1 construída sobre a camada de profundidade (`scripts/rsl_sintese_s1_taxonomia.py`). Em caso de dúvida, o protocolo tem precedência.

## Contexto

Revisão sistemática de um TCC sobre detecção de adulteração em imagens (documentos, faces, imagem natural) por **customização de arquitetura de rede neural**. A camada de mapeamento reúne os estudos que **não** foram promovidos à leitura de texto completo. Eles respondem às perguntas amplas: que estratégias de customização existem (RQ1.1) e que domínios de representação e operadores de fusão são usados (RQ1.2).

Você recebe **título e resumo** de cada estudo (às vezes só título). Não há texto completo. Não invente o que não está escrito.

## Regra de ouro

**Campo que o título e o resumo não permitem determinar recebe `nao_informado`.** Nunca inferir do que "costuma ser" na área. Um `nao_informado` honesto vale mais que um valor plausível: a revisão reporta a proporção de estudos que não declaram cada informação, e preenchimento otimista destrói esse número. Isto vale em dobro para registros **sem resumo**: título raramente revela ponto de intervenção ou operador de fusão.

## Campos (vocabulário fechado, use exatamente estas strings)

| Campo | Valores permitidos |
|---|---|
| `id` | copie do registro |
| `dominio_aplicacao` | `documento`, `face`, `imagem_natural`, `misto`, `sensoriamento_remoto`, `medico`, `nao_informado` |
| `estrategia` | `A`, `B`, `C`, `D`, `E`, `nao_informado` (ver taxonomia abaixo) |
| `ponto_intervencao` | `entrada_bruta`, `camadas_iniciais`, `corpo`, `camadas_finais`, `cabeca`, `transversal`, `nao_informado` |
| `dominios` | um ou mais de `espacial`, `frequencia`, `borda`, `ruido`, `textura`, `metadados`, `temporal`, unidos por `+` em ordem alfabética (ex: `espacial+frequencia`); ou `nao_informado` |
| `operador_fusao` | `concatenacao`, `soma`, `atencao`, `gate_aprendivel`, `canais_entrada`, `ausente`, `nao_informado` |
| `fonte` | `resumo` se o registro tem resumo; `titulo` se o resumo está vazio |
| `alerta` | string vazia `""` na maioria dos casos. Preencha com uma frase curta só quando o estudo **claramente não propõe customização de rede neural para detectar adulteração** (ver "Alertas" abaixo) |

### `dominio_aplicacao`
- `documento`: documentos, recibos, notas fiscais, texto em imagem, identidade, certificados
- `face`: deepfake facial, troca de rosto, manipulação de expressão
- `imagem_natural`: splicing, copy-move, inpainting, imagem gerada por IA em geral, cenas naturais
- `misto`: o estudo avalia explicitamente em mais de um desses domínios
- `sensoriamento_remoto`, `medico`: quando declarado

### `estrategia` — taxonomia S1 (aplique na ordem; a primeira que valer decide)

| Código | Categoria | Quando usar |
|---|---|---|
| `D` | Não-arquitetural | A contribuição **não é uma arquitetura de detecção**: estratégia de treino, aumento de dados, função de perda sozinha, geração de dataset, marca d'água ativa, ataque ou evasão contra detectores |
| `E` | Ensemble entre modelos | Combina **dois ou mais backbones inteiros e independentes** (prontos ou treinados separadamente) por votação, média ou fusão tardia de escores |
| `C` | Clássico, sem rede | Sem rede neural treinada: SVM, KNN, árvore, estatística, SIFT, casamento de blocos, atributos manuais |
| `A` | Multi-ramo paralelo | **Dois ou mais ramos/encoders/fluxos** com peso próprio, cada um dedicado a um domínio (ex.: ramo RGB + ramo de frequência; "two-stream", "dual-branch", "multi-stream"), fundidos em algum ponto |
| `B` | Módulo único / transformação de entrada | **Um backbone só**, com um ou poucos módulos inseridos nele (bloco de atenção, camada de borda, conv restrita, módulo de frequência plugável), **ou** a entrada é transformada/aumentada (canais extras, DCT como entrada, filtro SRM na entrada) antes de um backbone único |
| `nao_informado` | — | O título/resumo não permite distinguir. Comum em registros só com título |

Diferença A × B: se o resumo fala em "two-stream", "dual-branch", "parallel branches", "two encoders" → `A`. Se fala em "we insert/propose a module", "plug-and-play", "we add a layer", "we feed DCT coefficients to" um único backbone → `B`. Se não dá para saber → `nao_informado`.

### `ponto_intervencao`
- `entrada_bruta`: a customização age sobre a imagem antes do backbone (pré-processamento aprendido ou fixo, canais extras, transformada na entrada)
- `camadas_iniciais` / `corpo` / `camadas_finais`: módulo inserido numa posição declarada do backbone
- `cabeca`: só a cabeça de classificação/segmentação é customizada, ou a fusão ocorre só no final
- `transversal`: a customização atravessa a rede (ramos paralelos ao longo da profundidade, módulos em múltiplos estágios)
- **Em geral, resumo não diz isso com precisão. Use `nao_informado` sem culpa.**

### `dominios`
Domínios de representação **explicitamente explorados** pelo método: `frequencia` (DCT, FFT, wavelet, espectro, alta frequência), `borda` (edge, boundary, contorno, gradiente, Sobel), `ruido` (noise, SRM, residual, PRNU, Bayar/constrained conv, noiseprint), `textura` (texture, LBP, Gabor), `espacial` (o ramo RGB/pixel, quando o estudo o nomeia como um domínio em contraste com outro), `metadados` (EXIF, JPEG header), `temporal` (vídeo, quadros). Só marque o que o texto declara.

### `operador_fusao`
Só preencha se o resumo **declara** como os domínios/ramos são combinados. `ausente` se o estudo tem um único domínio/ramo sem fusão. Senão `nao_informado`.

## Alertas

A triagem anterior já removeu a maioria dos estudos fora de escopo, mas 613 resumos desta camada nunca foram lidos individualmente. Se você perceber que o estudo:
- não usa rede neural nenhuma (método clássico) → `estrategia: "C"` e `alerta: "sem rede neural"`
- não propõe detector (ataque, evasão, geração de dataset, só treino) → `estrategia: "D"` e `alerta: "<motivo curto>"`
- não é sobre adulteração/falsificação/geração sintética de imagem → `alerta: "fora de escopo: <motivo>"`

Não deixe de classificar os demais campos por causa do alerta. **Nunca** marque alerta só com base no título quando o título é ambíguo.

## Formato de saída

Escreva **um único arquivo JSON** (um array) no caminho indicado na sua tarefa, com **exatamente um objeto por estudo do lote, na mesma ordem**, sem pular nenhum:

```json
[
  {"id": "S0012", "dominio_aplicacao": "imagem_natural", "estrategia": "A", "ponto_intervencao": "transversal", "dominios": "espacial+ruido", "operador_fusao": "atencao", "fonte": "resumo", "alerta": ""},
  {"id": "N0044", "dominio_aplicacao": "face", "estrategia": "nao_informado", "ponto_intervencao": "nao_informado", "dominios": "frequencia", "operador_fusao": "nao_informado", "fonte": "titulo", "alerta": ""}
]
```

Nenhum outro campo, nenhum comentário dentro do JSON.
