# Instruções de triagem por título — candidatos do snowballing (fase 4)

Aplica aos candidatos do snowballing **os mesmos critérios da fase 1** já usados no corpus primário (protocolo, seção 5, e `scripts/rsl_fase1_vereditos.py`). Nenhum critério novo.

## Princípio

**Só se exclui o CLARAMENTE fora de escopo. Na dúvida, inclui** (Kitchenham e Charters, 2007, seção 6.2.2). Um falso positivo aqui é corrigido na fase 2; um falso negativo é perdido para sempre. Por isso, erre sempre para o lado da inclusão.

## Escopo da revisão

Redes neurais para **detecção** de adulteração, falsificação ou geração sintética em **imagens**: splicing, copy-move, inpainting, detecção de deepfake facial (inclusive em vídeo analisado quadro a quadro, decisão D3), detecção de imagem gerada por GAN ou difusão, localização de manipulação, fraude documental, antispoofing facial, esteganálise, forense de câmera e de compressão.

## Códigos de exclusão aplicáveis nesta fase

| Código | Quando usar | Exemplos típicos no snowballing |
|---|---|---|
| **EC1** | Não aborda detecção de adulteração, falsificação ou geração sintética em imagens | Arquiteturas genéricas (ResNet, Swin Transformer, ConvNeXt, ViT, EfficientNet), métodos de **geração** de imagem (GAN, difusão, StyleGAN) sem detecção, classificação, detecção de objetos, segmentação semântica, super-resolução, conjuntos de dados genéricos (ImageNet, COCO), otimizadores, aprendizado autossupervisionado genérico, bibliotecas (Albumentations), reconhecimento facial sem antispoofing, compressão de imagem sem forense, medicina sem forense |
| **EC3** | Exclusivamente áudio, fala, música ou texto, sem componente de imagem | Deepfake de voz, detecção de texto gerado por modelo de linguagem, fake news textual |
| **EC4** | Estudo secundário: survey, review, overview, bibliometria, revisão sistemática, tutorial de área | "A survey of...", "...: a review", "A comprehensive review", "Systematic literature review" |
| **EC7** | Título indica publicação fora de inglês ou português | Título em chinês, russo etc. (raro, o título costuma vir traduzido) |

**Cuidado com EC4:** "state-of-the-art" num título de artigo primário ("...achieves state-of-the-art...") **não** é estudo secundário. Só marque EC4 quando o título anuncia claramente que o trabalho é revisão da literatura. `tipo = review` no OpenAlex é indício forte, mas confirme pelo título.

**Não aplicar nesta fase:** EC2 (sem customização arquitetural) exige ler o resumo e é fase 2. EC5, EC6 e EC8 já foram tratados por filtro de tipo e deduplicação.

## Casos limítrofes: INCLUIR

- Detecção de deepfake em vídeo (D3 mantém no escopo)
- Esteganálise, forense de câmera, detecção de dupla compressão JPEG
- Antispoofing ou ataque de apresentação facial
- Robustez adversarial **de detectores forenses**
- Detecção multimodal de desinformação **com componente de imagem**
- Qualquer título ambíguo

## Saída

Grave um JSON com **apenas as exclusões**, mapeando id para código:

```json
{"N0002": "EC1", "N0014": "EC4", "N0103": "EC3"}
```

Tudo que não estiver no JSON avança para a fase 2.
