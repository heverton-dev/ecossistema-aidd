---
name: melhoria
description: Recebe um pedido de melhoria em linguagem natural, investiga o codigo real de forma profunda e estruturada, e gera um relatorio com nota (0-10) em docs/melhorias/ — etapa anterior ao /plan.
---

# /melhoria — Analise Profunda Pre-Planejamento

Contrato executavel universal do slash command `/melhoria <descricao em linguagem natural>`.

## Posicao no Fluxo (leia antes de agir)

O ecossistema tem **um unico fluxo de trabalho de 3 etapas**, e cada etapa
termina com uma **parada obrigatoria** onde quem decide e o usuario:

| Etapa | Comando | Entra | Sai | Parada obrigatoria no fim |
|---|---|---|---|---|
| 1 | `/melhoria <pedido em linguagem natural>` | pedido do usuario, ou um plano existente pra reanalisar | relatorio em `docs/melhorias/` com Nota Atual e evidencia | "quer que eu gere o plano a partir disto?" |
| 2 | `/plan <nome>` | o relatorio da etapa 1 (ou o pedido direto) | pasta em `docs/planos/<nome>/` com todos os itens em rascunho | "aprova este plano?" |
| 3 | `/orchestrate <plano>` | plano aprovado | execucao real das frentes | escolha de ambiente + aprovacao do Plano de Voo |

**Nenhuma etapa dispara a seguinte sozinha** (Regra de Ouro #7 do `AGENTS.md`).
Cada comando tem **um dono unico**: `melhoria`, `plan` e `orchestrate`. As
skills-motor (`planos-auditoria-runner`, `orca-plan-orchestrator`) nao tem
slash command proprio e sao acionadas por elas.

> **Nome das iniciativas:** toda pasta de plano segue `PLAN-<NNNN>_<dd-mm-aaaa>-<nome-curto>` (ex.: `PLAN-0016_09-09-2026-qualidade-testes-mutacao`). O `NNNN` e um identificador global unico — use ele pra falar do plano sem ambiguidade, em vez de "plano 03", que existia em tres subpastas ao mesmo tempo. Quem gera o nome e o `plan init`; nunca monte a mao.

## Regra Imutavel: Universalidade e Agnosticismo

Esta skill (e todo o fluxo `/melhoria` → `/plan` → `/orchestrate`) **precisa funcionar
identica em qualquer harness** (Claude Code, Gemini CLI, Cursor, Qoder, OpenCode,
CodeBuddy, Antigravity, MimoCode, etc.), conforme a Regra de Ouro #6 (Supremacia
Agnostica) do `AGENTS.md`. Consequencias praticas, sem excecao:

1. **Fonte unica:** este arquivo vive em `componentes/compartilhado/skills/melhoria/`
   e e distribuido fisicamente para cada harness por
   `python scripts/gestor_componentes.py sync --tipo skill`. Nunca editar as copias
   dentro de `.claude/`, `.gemini/`, `.cursor/` etc. diretamente.
2. **Trabalho pesado em CLI compartilhada:** a geracao do relatorio (nome, pareamento
   `.html`+`.json`, nota) roda via `python ecossistema.py melhoria init ...` — o mesmo
   comando, o mesmo resultado, em qualquer harness. Nenhuma etapa desta skill pode
   depender de um recurso exclusivo de uma ferramenta de IA especifica.
3. **Ferramenta de busca profunda e best-effort, com fallback universal:** o uso do
   `code-review-graph` (ver Passo 2) e preferencial quando disponivel no harness em
   execucao, mas a skill nunca trava por falta dele — cai para Grep/Glob/Read, que
   existe em qualquer harness.

## Quando NAO usar esta skill

- Ja existe um relatorio de auditoria/evidencia pronto e o usuario so quer criar o
  plano a partir dele → use `/plan` diretamente.
- Gerar o esqueleto do plano em si → isso e `planos-auditoria-runner` (`/plan`).
- Decidir e executar a orquestracao do plano → isso e `orchestrate`.

## Protocolo Obrigatorio do Agente

Quando `/melhoria <descricao>` for acionado:

### Passo 1: Nao Iniciar Sozinha
So investiga sob pedido expresso do usuario, com a descricao em linguagem natural
do que ele quer melhorar. Nunca infira um pedido a partir de contexto ambiguo.

### Passo 2: Investigacao Profunda e Real (nunca leitura superficial)
Investigue o codigo de verdade, focado estritamente no pedido do usuario:
1. **Primeiro** use as ferramentas do `code-review-graph` (se disponiveis no harness
   atual) — `semantic_search_nodes_tool`, `get_architecture_overview_tool`,
   `get_impact_radius_tool`, `get_affected_flows_tool`, `query_graph_tool`,
   `get_review_context_tool` — para mapear onde aquilo vive, quem depende disso e o
   que pode quebrar.
2. **Se o graph nao cobrir algo, ou nao estiver disponivel**, complete com
   Grep/Glob/Read manuais. Nunca pare a investigacao so porque uma ferramenta
   especifica faltou.
3. Reproducao real sempre que fizer sentido (rodar um comando, um teste, um gate) —
   nunca aceitar leitura cruzada de codigo como prova de comportamento.
*Nota:* aprofunde ate o pedido do usuario estar coberto de forma concreta e
verificavel — nunca superficial, mas tambem nunca especulativo sobre partes fora
do escopo pedido.

### Passo 3: Nota Atual (0-10) com Evidencia Real
Ao final da investigacao, atribua uma nota de 0 a 10 para o estado atual daquilo que
foi pedido, **sempre acompanhada da evidencia concreta** que a sustenta (arquivos
checados, comando/teste rodado, achado especifico). Se a investigacao nao permitir
uma nota confiavel, o campo fica `NAO AUDITADO` — nunca um numero estimado.

### Passo 4: Reanalise de Plano Existente (so quando o pedido apontar pra um)
Se o pedido do usuario referenciar um plano ja criado (ex: um caminho dentro de
`docs/planos/...`), esta skill nao se limita a reler o documento do plano — ela
reinvestiga o **codigo real** (Passo 2) e so ENTAO compara com o que o plano previa:

1. Leia a Nota Atual anterior daquele plano/item com:
   ```bash
   python ecossistema.py plan ler-nota <caminho-do-plano> [--item <NN>]
   ```
   Retorna `NAO AUDITADO` automaticamente se o plano for de formato antigo (anterior
   a esta metrica) ou o item nao tiver essa nota registrada — nunca falha por isso.
2. Para cada item do plano dentro do escopo do pedido, leia o `Escopo` e a
   `Definicao de Pronto` daquele `NN-<item>.md`, e classifique com base na
   investigacao real do Passo 2 (nunca por suposicao):
   - `feito` — Definicao de Pronto cumprida no codigo atual, com prova.
   - `parcial` — parte cumprida, parte nao; explique exatamente o que falta.
   - `nao-feito` — nada do que o item previa foi encontrado no codigo atual.
3. Passe essa comparacao para o gerador via `--itens-avaliados`, uma entrada por
   item avaliado, formato `<item>::<feito|parcial|nao-feito>::<justificativa>`.

### Passo 5: Geracao Deterministica do Relatorio
Gere o relatorio com o CLI deterministico (nunca escrevendo HTML longo direto no chat):
```bash
python ecossistema.py melhoria init --pedido "<texto original do usuario>" \
  --nome "<3 palavras curtas do assunto>" \
  --nota-atual "<0-10 ou omitir>" --evidencia "<prova real ou omitir>" \
  --resumo "<2-3 frases>" \
  --achados "achado 1" "achado 2" --riscos "risco 1" \
  --recomendacao "<proximo passo sugerido>" \
  [--plano-existente "<caminho-do-plano>" [--item "<NN>"]] \
  [--itens-avaliados "01::parcial::justificativa" "02::feito::justificativa"]
```
As duas ultimas linhas so se aplicam quando o Passo 4 rodou (reanalise de plano
existente). O comando cria em `docs/melhorias/`:
- `<dd-mm-aaaa>_melhoria-<3-palavras>.html` — versao para leitura, seguindo as
  mesmas regras de nome e scrollbar de `docs/relatorios/DIRETRIZES-DESIGN-RELATORIOS.md`.
  Quando `--plano-existente` foi usado, o HTML traz a comparacao Nota Anterior →
  Nota Nova e a tabela item-a-item (previsto no plano vs. implementado hoje).
- `<dd-mm-aaaa>_melhoria-<3-palavras>.json` — dados brutos estruturados, para reuso
  (ex: pelo `/plan`, ao herdar a Nota Atual desta analise).

### Passo 6: Comunicacao Direta no Chat
Nunca cole o relatorio inteiro na conversa. Mostre apenas o caminho do arquivo e um
resumo executivo de 2-3 frases (incluindo a nota, e — se for reanalise — o resumo da
comparacao previsto-vs-implementado).

### Passo 7: Sugestao do Proximo Passo — Nunca Decisao Automatica
- Se **nao** foi uma reanalise de plano existente: pergunte se o usuario quer que o
  `/plan` seja iniciado a partir deste relatorio (a Nota Atual e a evidencia
  alimentam a Nota Atual do plano novo).
- Se **foi** uma reanalise de plano existente: pergunte se o usuario quer gravar a
  Nota Nova naquele mesmo plano, com:
  ```bash
  python ecossistema.py plan atualizar-nota <caminho-do-plano> [--item <NN>] \
    --nota-atual "<nota nova>" --evidencia "<caminho do relatorio gerado>"
  ```
**Em nenhum dos dois casos dispare `/plan` ou a atualizacao de nota sozinho** — o
`/plan` ja tem seu proprio gate de alinhamento de escopo (Passo 2 de
`planos-auditoria-runner`), e `atualizar-nota` grava permanentemente por cima de
uma nota existente; encadear isso sem essa parada removeria exatamente o ponto de
controle humano que o processo exige.
