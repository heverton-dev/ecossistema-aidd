---
name: impeccable-ui
description: Design System impecavel em Tailwind (paleta Slate/Indigo), modais acessiveis WCAG 2.1 e proibicao total de emojis em UI de producao.
---

# Impeccable UI — Design System Slate/Indigo

## Objetivo

Garantir consistencia visual e acessibilidade em toda interface gerada
pelo pipeline AIDD, sem depender de gosto subjetivo do subagente.

## Paleta

- **Neutros:** escala `slate` do Tailwind (`slate-50` a `slate-950`)
  para fundo, texto e bordas.
- **Acao/Destaque:** escala `indigo` (`indigo-500`/`indigo-600` para
  botoes primarios, `indigo-400` para foco/hover).
- Nunca usar cores fora dessas duas escalas sem justificativa explicita
  no PR (ex: `red`/`amber` reservados a erro/alerta).

## Modais e Componentes Acessiveis (WCAG 2.1)

- Todo modal precisa de: `role="dialog"`, `aria-modal="true"`,
  `aria-labelledby` apontando para o titulo.
- Foco preso dentro do modal (focus trap) e devolvido ao elemento que
  abriu o modal ao fechar.
- Fechar com `Esc` e clique fora sempre habilitados, salvo confirmacao
  destrutiva pendente.
- Contraste minimo AA (4.5:1 para texto normal, 3:1 para texto grande).

## Proibicao de Emojis

- **Zero emojis** em qualquer texto de UI de producao (botoes, labels,
  mensagens de erro, toasts, titulos).
- Emojis permitidos apenas em documentacao interna/exemplos quando
  explicitamente pedido pelo usuario.

## Gate de Saida

`exit 0` somente se: paleta restrita a slate/indigo (+ semanticas de
erro/alerta), modais com atributos ARIA corretos, e nenhum emoji em
string de UI.
