---
title: "Ecossistema AIDD"
subtitle: "Tratado completo: do macro ao micro"
author:
  - Ecossistema AIDD — Governança Canônica
date: "21 de setembro de 2026"
lang: pt-BR
toc: true
toc-depth: 2
abstract: |
  Este livro descreve o **Ecossistema AIDD** em três níveis de profundidade e sob três
  eixos fixos de análise.

  Os três níveis são o **macro** (o ecossistema como organismo único: leis, governança,
  CLI unificada, portões de qualidade e distribuição multi-harness), o **meso** (os três
  fluxos canônicos de criação — `aidd-pure`, `aidd-open` e `aidd-freedom` [motor `aidd-bridge`] — e o fluxo de
  evolução `/melhoria → /plan → /orchestrate`) e o **micro** (cada uma das oito
  ferramentas homologadas, uma a uma).

  Os três eixos, aplicados em todos os níveis, são: **Engenharia Agêntica Aplicada**
  (como foi pensada, construída, configurada e como está aplicada), **Arquitetura**
  (como está, de fato, hoje) e **Economia de Tokens Aplicada** (como foi pensada,
  construída, configurada e como está aplicada).

  Cada ferramenta é descrita em três camadas sucessivas — funcionamento **individual**,
  funcionamento **dentro do fluxo** e funcionamento **dentro do ecossistema** — e, em
  cada camada, sempre pelos mesmos sete itens: passo a passo de execução, portões de
  qualidade, habilidades, determinismo, ferramentas acessadas, hooks e regras, e o
  contrato de entrega (o quê, como e para quem).

  A obra é descritiva, não promocional: descreve o estado real do repositório na data
  de geração, inclui o que está incompleto ou pendente de decisão humana e cita o
  arquivo-fonte de cada afirmação.
---

# Como ler este livro

## A quem este livro se destina

Este livro tem três leitores simultâneos, e a diagramação foi pensada para servir aos
três sem obrigar nenhum deles a ler o livro inteiro.

O **arquiteto ou engenheiro** que precisa entender a topologia, os contratos formais
entre etapas e o modelo de qualidade encontra na Parte I e na Parte IV o material
denso: leis invioláveis, catálogo de portões, esquemas JSON de handoff, regras de
isolamento arquitetural.

O **operador** que precisa rodar o ecossistema — gerar um sistema, evoluir um módulo,
subir uma infraestrutura — encontra na Parte II o passo a passo dos fluxos e, na
Parte III, a ficha técnica de cada ferramenta com a CLI exata, entradas, saídas e o
que falha quando algo falha.

O **avaliador** (auditor, gestor técnico, revisor externo) que precisa julgar se o que
está escrito corresponde ao que existe encontra, ao final de cada capítulo, a seção
*Rastreabilidade*, que aponta os arquivos do repositório que sustentam cada afirmação.

## A estrutura em três níveis e três eixos

O livro é uma matriz. O eixo vertical é o nível de aproximação; o eixo horizontal é a
pergunta que se faz em cada nível.

| Nível de aproximação                       | Engenharia agêntica aplicada                                             | Arquitetura                                                          | Economia de tokens aplicada                                          |
| :----------------------------------------- | :----------------------------------------------------------------------- | :------------------------------------------------------------------- | :------------------------------------------------------------------- |
| **Macro** — o ecossistema (Parte I)        | Capítulo 2: leis, papéis, autonomia limitada, desenvolvedor no controle   | Capítulo 3: monorepo, CLI unificada, núcleo compartilhado, harnesses  | Capítulo 4: tríade Caveman, determinismo como economia, orçamentos   |
| **Meso** — os fluxos (Parte II)            | Capítulo 6 e 10: quem decide o quê em cada etapa da esteira               | Capítulos 7–9: topologia de cada fluxo e contratos de handoff        | Capítulo 6: onde o token é gasto e onde é proibido gastar            |
| **Micro** — as ferramentas (Parte III)     | Seções "como foi pensada" e "individual" de cada capítulo                 | Seções "como está estruturada" de cada capítulo                      | Seções "economia de tokens" de cada capítulo                         |

## As convenções visuais

Alguns elementos se repetem ao longo do livro e têm sempre o mesmo significado.

```{=typst}
#painel("Painel de contexto")[
  Caixas como esta trazem contexto, decisão histórica ou advertência. Quando o painel
  descreve algo que está *incompleto ou pendente*, o texto diz isso explicitamente —
  este livro não maquia estado.
]
```

Blocos de código em fundo claro são sempre **comandos reais** da CLI ou trechos
literais de arquivos do repositório. Tabelas de duas colunas com a primeira coluna em
cinza são **fichas técnicas** — o cartão de identidade de uma ferramenta ou etapa.
Diagramas em caixas escuras representam **etapas determinísticas**; caixas claras com
borda representam **etapas que consomem modelo de linguagem**. Essa distinção é a mais
importante do livro inteiro e reaparece em todos os diagramas.

```{=typst}
#esteira(
  no("ETAPA DETERMINÍSTICA", sub: "Python puro, zero token"),
  no-claro("ETAPA COM LLM", sub: "custo real em tokens"),
  no("PORTÃO DE QUALIDADE", sub: "exit 0 ou bloqueia", cor: rgb("#334155")),
)
```

## O que este livro não é

Não é um manual de instalação — esse papel é do `README.md` e do
`docs/manuais/`. Não é a lei do ecossistema — essa é o `AGENTS.md`, e em caso de
divergência entre este livro e o `AGENTS.md`, **o `AGENTS.md` vence**. Não é um
documento de marketing: onde há dívida técnica, gate vermelho ou decisão adiada, o
texto registra o fato, a data e o motivo, porque a Lei Inviolável #8 do ecossistema —
Honestidade de Rótulo — se aplica também à documentação sobre ele.
