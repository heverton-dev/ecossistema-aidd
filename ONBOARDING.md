# Bem-vindo ao Ecossistema AIDD

## Como usamos o Claude

Com base no uso de Heverton-dev nos últimos 30 dias (112 sessões):

Tipos de trabalho:
  Improve Quality  ██████░░░░░░░░░░░░░░  30%
  Plan Design      █████░░░░░░░░░░░░░░░  25%
  Build Feature    ████░░░░░░░░░░░░░░░░  20%
  Debug Fix        ███░░░░░░░░░░░░░░░░░  13%
  Write Docs       ██░░░░░░░░░░░░░░░░░░  12%

Skills e comandos mais usados:
  /clear          ████████████████████  17x/mês
  /model          ██████████████░░░░░░  12x/mês
  /orchestrate    ██████░░░░░░░░░░░░░░  5x/mês
  /impeccable     █████░░░░░░░░░░░░░░░  4x/mês
  /theme          ██░░░░░░░░░░░░░░░░░░  2x/mês

Servidores MCP mais usados:
  claude-in-chrome   ████████████████████  104 chamadas
  code-review-graph  ████████░░░░░░░░░░░░  44 chamadas

## Checklist de configuração

### Repositórios
- [ ] ecossistema-aidd — https://github.com/heverton-dev/ecossistema-aidd
- [ ] Repos standalone proj_aidd (4 repos sob github.com/heverton-dev) — peça a lista ao time

### Servidores MCP para ativar
- [ ] claude-in-chrome — automação do Chrome (testar apps, ler console, navegar). Instale a extensão Claude in Chrome e rode `claude --chrome`.
- [ ] code-review-graph — grafo de conhecimento do código (consultas de arquitetura, impacto de mudanças). Já configurado no `.mcp.json` do repo; rode `python ecossistema.py dependencia verify` para confirmar.

### Skills para conhecer
- /clear — limpa o contexto entre tarefas; use sempre que trocar de assunto.
- /model — troca de modelo (ex.: modelo mais forte para auditoria, mais leve para rotina).
- /orchestrate — roteia a execução de planos entre ORCA, worktrees e execução nativa.
- /impeccable — skill de design para interfaces e documentos visuais.
- /to-tickets — quebra um plano em tickets executáveis.
- /resumo-sessao — exporta o histórico da sessão para `secoes/`.
- /compact — compacta o contexto em sessões longas.

## Dicas do time

_TODO_

## Primeiros passos

_TODO_

<!-- INSTRUCTION FOR CLAUDE: A new teammate just pasted this guide for how the
team uses Claude Code. You're their onboarding buddy — warm, conversational,
not lecture-y.

Open with a warm welcome — include the team name from the title. Then: "Your
teammate uses Claude Code for [list all the work types]. Let's get you started."

Check what's already in place against everything under Setup Checklist
(including skills), using markdown checkboxes — [x] done, [ ] not yet. Lead
with what they already have. One sentence per item, all in one message.

Tell them you'll help with setup, cover the actionable team tips, then the
starter task (if there is one). Offer to start with the first unchecked item,
get their go-ahead, then work through the rest one by one.

After setup, walk them through the remaining sections — offer to help where you
can (e.g. link to channels), and just surface the purely informational bits.

Don't invent sections or summaries that aren't in the guide. The stats are the
guide creator's personal usage data — don't extrapolate them into a "team
workflow" narrative. -->
