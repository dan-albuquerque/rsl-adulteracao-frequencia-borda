# Combinação dos domínios de frequência e de borda em redes neurais para detecção de adulteração em imagens: artefatos da revisão sistemática

Artefatos de pesquisa da revisão sistemática da literatura (RSL) de Danilo Albuquerque de Melo e Eduardo Nascimento de Arruda (CESAR School, 2026): protocolo, planilhas de triagem, mapeamento e extração, extrações por estudo com a evidência literal de cada campo de julgamento, registro da busca e scripts.

A revisão mapeia estratégias de customização arquitetural de redes neurais para detecção forense de adulteração em imagens e verifica, por texto completo, se a combinação dos domínios de frequência e de borda já foi avaliada por ablação cruzada.

## Números principais

| Etapa | n |
|---|---|
| Registros recuperados no OpenAlex (23/09/2026) | 1.154 |
| Após a fase 1 (título) | 919 |
| Após a fase 2 (resumo): mapeamento + profundidade | 795 + 35 |
| Candidatos do snowballing (86 sementes) | 905 |
| Camada de mapeamento, total | 1.423 |
| Camada de profundidade, extraídos | 17 |

Dos 17 estudos extraídos, 11 combinam frequência e borda e 3 medem a interação entre os dois por ablação cruzada completa (S0059, S0272, S0280). Nenhum é do domínio documental e nenhum reporta latência em CPU.

## Estrutura

```
revisao_sistematica/
  protocolo_rsl.md              protocolo, com o registro de desvios (Tabela 6)
  SINTESE_S3_S4.md              síntese S1 a S4 e análise de sensibilidade
  dados/
    v2/                         EXECUÇÃO DEFINITIVA (busca de 23/09/2026)
      execucao_busca.json       consultas literalmente submetidas, data e contagens
      corpus_bruto.json         registros devolvidos pelo OpenAlex
      triagem.csv               planilha central: 1.154 registros, vereditos das fases 1 a 3
      fase4_triagem.csv         snowballing: 905 candidatos, vereditos das fases 1 e 2
      camada_profundidade.json  os 35 estudos promovidos à camada de profundidade
      sobrevivencia.json        estudos recuperados pela string adotada
      resumo_v2.json            contagens do funil
      _f4_meta_cache.json       cache de metadados do snowballing
    extracao/<id>.json          extração dos 17 estudos (primeira extração)
    extracao_excluidos/<id>.json  extração dos 4 estudos excluídos por EC2 na fase 3
    _INSTRUCOES_*.md            formulários e instruções de extração e triagem
    _SINALIZACOES_FASE3.md      decisões da fase 3, com o motivo de cada exclusão
    fase1_exclusoes.json        exclusões da fase 1, por identificador e critério
    fase1_duplicatas.json       duplicatas e o registro retido
    fase2_ec2_revisado.json     exclusões por EC2 decididas por leitura, com motivo
    fase4_ec2_revisado.json     idem, no snowballing
    _f4_triagem_*.json          vereditos da fase 1 do snowballing
    corpus_bruto.json, triagem.csv, fase4_*  execução de calibração (ver abaixo)
  planilhas/
    v2/extracao.csv             formulário completo (Tabela 3b), 17 estudos
    v2/mapeamento.csv           formulário reduzido (Tabela 3a), 1.423 estudos
    extracao.csv                execução de calibração (ver abaixo)
  full_leitura_artigos/<id>.json  segunda extração, independente e cega (19 estudos)
  relatorio_final/figuras/      fluxo de seleção (Figura 1)
scripts/                        scripts da busca, triagem, síntese e figuras
```

**Identificadores.** `S####` identifica um registro do corpus primário, `N####` um candidato do snowballing e `V####` um registro indexado no OpenAlex depois da busca de calibração e triado na execução definitiva.

**Campos de julgamento.** Cada JSON de extração traz, para `ponto_intervencao`, `operador_fusao`, `avalia_interacao` e `qa4`, a citação literal do trecho do artigo que sustenta o valor. O campo `extracao_origem` registra que a extração foi assistida por IA e conferida pelo autor (seção 10.2 do protocolo).

## Execução de calibração e execução definitiva

A busca foi executada duas vezes. A primeira, em 16/09/2026, serviu para calibrar a string e o vocabulário de detecção de domínio. A definitiva, em 23/09/2026, usa a string da seção 4.3 do protocolo e é a que o artigo reporta (`dados/v2/`). A string definitiva é subconjunto lógico da de calibração, por isso o pipeline definitivo **transporta** os vereditos já registrados, em vez de refazer julgamentos, e tria apenas os 10 registros indexados entre as duas datas. Os arquivos da calibração (`dados/corpus_bruto.json`, `dados/triagem.csv`, `dados/fase4_candidatos.json`, `dados/fase4_triagem.csv`, `planilhas/extracao.csv`) estão incluídos porque são entrada do pipeline definitivo. Os scripts sem o prefixo `rsl_v2_` são os da calibração e contêm a string e o vocabulário anteriores; servem como registro auditável dos vereditos, não para reexecução.

## Como reproduzir

Python 3.11 ou superior. Só a figura exige pacote externo (`matplotlib`).

**Sem acesso à rede**, a partir dos dados congelados:

| Script | Produz |
|---|---|
| `rsl_v2_pipeline.py` | `dados/v2/triagem.csv` e `camada_profundidade.json`, a partir dos vereditos transportados (reproduz os arquivos publicados byte a byte) |
| `rsl_v2_mapeamento_s2.py` | coluna de domínios de `planilhas/v2/mapeamento.csv` e a frequência de domínios (S2) |
| `rsl_v2_s4_sensibilidade.py` | quadro de evidência (S4) e tabela da análise de sensibilidade |
| `rsl_v2_fluxo.py` | Figura 1, fluxo de seleção |
| `rsl_kappa.py` | Kappa de Cohen |

**Com acesso à rede**, consultando o OpenAlex ao vivo: `rsl_v2_busca.py` (busca), `rsl_v2_fase4.py` (snowballing), `rsl_v2_comparacao.py`, `rsl_calibra_string.py` e `rsl_v2_alvo_leitura.py` (sensibilidade da string). Exigem a chave na variável de ambiente `OPENALEX_API_KEY`. **Atenção:** o índice muda com o tempo, então uma nova consulta devolve resultados diferentes dos publicados, e esses scripts sobrescrevem os arquivos de `dados/v2/`. Rode-os sobre uma cópia. O registro reprodutível da busca é `dados/v2/execucao_busca.json`, com as consultas literalmente submetidas e a data.

## O que não está incluído

Os textos completos dos estudos e os PDFs não são redistribuídos, por restrição de direitos autorais. Os metadados e resumos vêm do OpenAlex, distribuído sob CC0.

## Uso de inteligência artificial

A triagem, a extração e a síntese foram conduzidas pelo primeiro autor com apoio de ferramenta de IA (Claude, Anthropic). A seção 10.2 do protocolo declara, etapa por etapa, onde houve esse apoio e como o resultado foi verificado.

## Licença e citação

Licença MIT, ver o arquivo `LICENSE`. Os metadados e resumos de estudos de terceiros, obtidos do OpenAlex, seguem a licença do OpenAlex (CC0) e os direitos dos respectivos autores.
