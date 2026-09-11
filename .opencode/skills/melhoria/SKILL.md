---
name: melhoria
description: Recebe um pedido de melhoria em linguagem natural, investiga o codigo real de forma profunda e estruturada, e gera um relatorio com nota (0-10) em docs/melhorias/ — etapa anterior ao /plan.
---

# /melhoria — Analise Profunda Pre-Planejamento

Contrato executavel universal do slash command `/melhoria <descricao em linguagem natural>`.

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

### Passo 4: Geracao Deterministica do Relatorio
Gere o relatorio com o CLI deterministico (nunca escrevendo HTML longo direto no chat):
```bash
python ecossistema.py melhoria init --pedido "<texto original do usuario>" \
  --nome "<3 palavras curtas do assunto>" \
  --nota-atual "<0-10 ou omitir>" --evidencia "<prova real ou omitir>" \
  --resumo "<2-3 frases>" \
  --achados "achado 1" "achado 2" --riscos "risco 1" \
  --recomendacao "<proximo passo sugerido>"
```
O comando cria em `docs/melhorias/`:
- `<dd-mm-aaaa>_melhoria-<3-palavras>.html` — versao para leitura, seguindo as
  mesmas regras de nome e scrollbar de `docs/relatorios/DIRETRIZES-DESIGN-RELATORIOS.md`.
- `<dd-mm-aaaa>_melhoria-<3-palavras>.json` — dados brutos estruturados, para reuso
  (ex: pelo `/plan`, ao herdar a Nota Atual desta analise).

### Passo 5: Comunicacao Direta no Chat
Nunca cole o relatorio inteiro na conversa. Mostre apenas o caminho do arquivo e um
resumo executivo de 2-3 frases (incluindo a nota).

### Passo 6: Sugestao do Proximo Passo — Nunca Decisao Automatica
Termine perguntando explicitamente se o usuario quer que o `/plan` seja iniciado a
partir deste relatorio (a Nota Atual e a evidencia do relatorio alimentam a Nota
Atual do plano). **Nunca dispare o `/plan` sozinho** — o `/plan` ja tem seu proprio
gate de alinhamento de escopo (Passo 2 de `planos-auditoria-runner`), e encadear os
dois sem essa parada removeria exatamente o ponto de controle humano que o processo
exige.
