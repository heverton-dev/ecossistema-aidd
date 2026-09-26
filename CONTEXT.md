# CONTEXT.md — Linguagem do Ecossistema AIDD

> Glossário de domínio para agentes e pessoas. Um termo = um sentido. Onde o repositório usa o mesmo nome para coisas diferentes, o termo fica em **Ambiguidades sinalizadas** até o usuário decidir; o agente nunca escolhe sozinho.
> Rascunho do Ticket 7 do ciclo `docs/auditoria/skills-pocock/ciclo-01/` (adaptado de `domain-modeling` de mattpocock/skills, licença MIT).
> Decisões de termo viram ADR em `docs/adr/` (formato em `docs/adr/README.md`).

## Linguagem

- **gate** — script determinístico em `gates/` (`G_*.py`) que sai com exit 0 (aprova) ou exit 1 (barra). Roda no pre-commit (`.pre-commit-config.yaml`) ou sob demanda (`python ecossistema.py audit`). Todo gate precisa de teste que prove que ele reprova (Lei #13). Também chamado de "portão" / "quality gate".
- **harness** — programa que roda o agente (Claude Code, Gemini CLI, Cursor, Codex, OpenCode, Mimo...). Cada harness tem sua pasta de cópia (`.claude/`, `.gemini/`, `.cursor/`...). A fonte única é `componentes/compartilhado/`; as cópias saem de `python ecossistema.py components sync`.
- **4F** — pipeline linear de auditoria em 4 fases: Inspetor (laudo) → Arquiteto (plano de evolução) → Construtor (tickets) → Inspetor de Retorno. Definido em `docs/protocolos/PIPELINE-AUDITORIA-4F.md`.
- **15-D** — lente de auditoria com 15 dimensões (D1 a D15) aplicada pelo Inspetor da 4F. Cada ticket de plano de evolução cita a dimensão que corrige ("Falha 15-D").
- **worktree** — cópia de trabalho isolada criada por `git worktree`, numa branch própria, fora da pasta principal. Construtor e agentes paralelos trabalham só nela; o merge em `main` depende de aprovação do usuário.
- **DoD** — Definição de Pronto: lista de critérios de aceite de um ciclo (`DOD.md`).
- **laudo** — relatório do Inspetor com a nota por dimensão 15-D (ex.: `RELATORIO-TECNICO.md`).

## Relações

- Uma **ferramenta** auditada tem vários **ciclos** (`docs/auditoria/<ferramenta>/ciclo-NN/`); cada ciclo percorre as 4 **fases** da 4F.
- Na fase Arquiteto nasce o `PLANO-EVOLUCAO.md` do ciclo; ele contém **tickets**; cada ticket cita uma dimensão 15-D e um item do DoD.
- Cada ticket é executado numa **worktree** e só fecha com os **gates** em exit 0.
- As iniciativas de `docs/planos/` (`PLAN-NNNN`) são outra trilha, separada da 4F: planos de auditoria nunca vão para `docs/planos/`.
- Skills e hooks nascem em `componentes/compartilhado/` e chegam a cada **harness** pelo sync.

## Ambiguidades sinalizadas

### ciclo
- **Status:** aberta
- Sentido A: rodada de auditoria 4F de uma ferramenta (`docs/auditoria/aidd-diagnose/ciclo-01/`).
- Sentido B: o "ciclo de 5 passos" de teste de ferramenta da Lei #9 (`docs/protocolos/PROTOCOLO-TESTES-FERRAMENTAS.md`).
- Sentido C: o ciclo Red → Green do TDD (`aidd-tdd`).
- Pergunta ao usuário: "ciclo" fica só com o sentido A? Os outros passam a se chamar como?

### fase
- **Status:** aberta
- Sentido A: uma das 4 etapas da 4F (Inspetor, Arquiteto, Construtor, Retorno).
- Sentido B: etapa de um plano em `docs/planos/` (ex.: "Fase 4 anti-nih", "Fase 8").
- Sentido C: etapa interna de uma ferramenta ou skill (as 8 fases do `aidd-generator`, as fases do `aidd-diagnose`).
- Pergunta ao usuário: qual sentido é o padrão e como nomear os outros?

### plano
- **Status:** aberta
- Sentido A: iniciativa em `docs/planos/` (`PLAN-NNNN-...`, índice em `docs/planos/INDEX.md`).
- Sentido B: `PLANO-EVOLUCAO.md` de um ciclo 4F em `docs/auditoria/`.
- Sentido C: o PRÉ-PLANO do `aidd-planner` e o JSON de `python ecossistema.py run-plan`.
- Pergunta ao usuário: manter "plano" para os três ou dar nome próprio a cada um?

### sessão
- **Status:** aberta
- Sentido A: conversa com um agente, registrada em `secoes/` (`aidd-sessao`, `aidd-handoff`).
- Sentido B: etapa numerada de um plano ("Sessão 1 — Teste Real Isolado", `docs/planos/feitos/PLAN-0008-validacao-humana-testes/`).
- Pergunta ao usuário: "sessão" fica só com o sentido A?

### ticket
- **Status:** aberta
- Sentido A: item "### Ticket N" do `PLANO-EVOLUCAO.md` de um ciclo 4F.
- Sentido B: item `[TICKET-XX]` gerado pela skill `aidd-tickets` e lido por `scripts/compilador_tickets_plano.py`.
- Pergunta ao usuário: são o mesmo conceito (e devem ter o mesmo formato) ou dois nomes?

### glossário duplicado
- **Status:** aberta
- `docs/glossario/glossario.md` traduz termos para o usuário leigo (Quarteto `/docs`); este `CONTEXT.md` fixa o sentido para agentes. Há sobreposição (harness, gate, worktree).
- Pergunta ao usuário: manter os dois (públicos diferentes) ou fundir num só como fonte única?
