---
name: ascii2img
description: >-
  Turn ASCII draw (mocks/{n}.txt) into UI images as mocks/{n}-a.png, {n}-b.png.
  Default OpenRouter gpt-image-2 at 1K. Use when the user mentions ascii2img.
disable-model-invocation: true
---

# ASCII → Img


Utiliza suas ferramentas de geração de imagem para transformar uma planta ASCII em uma **imagem de tela de app** — não um poster, não um moodboard. O PNG precisa parecer um produto real, com capricho de design fora da caixa, incomum, de alto nível e impactante o bastante para redes e aulas.

Não gere HTML. O agente lê o ASCII, monta o pedido **na cabeça** e chama a CLI — o prompt **não vira arquivo**.

O molde visual (HTML, screenshot, design system, `{n}-ref.png`) **não é desta skill** — chega por outra. Não procure, não anexe, não copie molde para `mocks/`.

## Background

O usuário cria **conteúdo para redes sociais e cursos** (Reels, ads, aulas, demos). Esta skill continua o trabalho da planta ASCII: **visualizar a tela** que depois aparece nesse conteúdo.

O ASCII é a planta (regiões, funções, momento da UI). A imagem é a tela pronta: tipografia, superfícies, hierarquia, estados, paleta. O roteiro fica com o usuário.

Não é mock enterprise genérico nem screenshot “cara de IA” (cards vazios, gradiente clichê, widgets literais copiados do ASCII).

## Os dois pilares (idealmente os 2)

1. **Impacto visual** — cores, profundidade, efeitos, 3D se couber, backgrounds com presença, tipografia forte, superfícies com identidade.
2. **Funcionalidade fora da caixa** — a UI precisa **funcionar**: áreas com propósito, textos reais. O pulo do gato do app já visível na tela.

**Capricho é sempre prioridade.**

## Fluxo

### 1. Ler o ASCII (e o app)

Leia `mocks/{n}.txt` (ou o ASCII no chat + o número). Se faltar path ou número, peça.

O arquivo costuma trazer: `from:`, o **parágrafo do app**, a planta boxed, o que torna a tela marcante e o que veio da referência.

Antes de promptar o modelo:

- Entenda **o que é o app** (problema, para quem, pulo do gato). Se o parágrafo estiver magro, complete no prompt: explique o produto em 2–4 frases para o modelo não inventar um SaaS genérico.
- Entenda **que momento da UI** é esse (scan pronto, chat + viewport, onboarding…).
- Traduza o ASCII em **regiões e funções** (chat, canvas, agente, CTA…), não em caixinhas ASCII literais nem em widgets copiados traço a traço.

A tela gerada tem que parecer **um app usável**, não uma ilustração da planta.

### 2. Paleta e clima

Pense nas cores **antes** de chamar o modelo — ou peça explicitamente que o modelo pense nelas.

Escolha (ou peça) uma paleta **adequada e harmônica ao objetivo do app e da tela**: temperatura, contraste, acento, fundo. Se o briefing no `.txt` já fechou paleta, respeite. Se não fechou, defina no prompt (3–5 cores + papel de cada uma: fundo, superfície, texto, acento, alerta).

Não deixe o modelo no “paleta livre” sem direção: sem isso ele cai em teal/gradiente genérico.

### 3. Pedido ao modelo

Default: `openrouter-img` — `gpt2`, `1K`, `16:9`. Nano Banana só se o usuário pedir.

`--filename` = `mocks/{n}-a.png` (ou a próxima letra livre). Nunca o padrão com timestamp da skill de imagem.

Primeira geração: **sem** `--input-image`. `--input-image` só na volta image→image de um PNG **já gerado aqui** (`{n}-a.png` → `{n}-a-i2.png`).

O prompt é o trabalho desta skill e vai **somente** em `--prompt` da CLI. Inclua, nesta ordem de ideia:

1. O que é o **app** (se necessário, explique).
2. Que **tela** é essa e o que o usuário consegue fazer nela.
3. **Regiões** tiradas do ASCII (função, não traço).
4. **Paleta** e materiais (fundo, vidro, neon, papel, 3D…).
5. Instrução de **capricho**: UI premium, incomum, impactante; textos reais; hierarquia clara; nada de mock vazio.

Quantidade: o agente decide (default **1** → próximo `n-<letra>.png` livre daquele n).

### 4. Disco — o que esta skill grava

Só PNGs, sem subpasta. Não criar `{n}.txt` nem `{n}-ref.png`.

```
mocks/
  1.txt          ← já existe (plan-screen). NÃO criar, NÃO editar
  1-a.png        ← esta skill
  1-b.png
  1-b-i2.png     ← image→image do PNG anterior
```

**Proibido gravar o prompt (ou qualquer rascunho) em disco.** Nada de `__p1a.txt`, `_p1b.txt`, `prompt.txt`, `*-prompt.md`, dump do `--prompt`. Isso não é artefato do fluxo — o pedido vive só na chamada da CLI.

Liste os paths dos PNGs. Não edite o `.txt`.
