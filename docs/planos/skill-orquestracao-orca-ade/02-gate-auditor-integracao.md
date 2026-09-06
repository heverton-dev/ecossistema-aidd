# Item 2 — `gate_auditor.py` Integrado ao `ecossistema.py audit`

> **Escopo:** módulo que roda os Quality Gates locais de uma worktree e retorna um veredito binário (exit 0/1) que o `state_engine` (Item 1) e o `worktree_engine` (Item 1) usam para decidir merge ou quarentena.
> **Não faz parte deste item:** criar gates novos — este item só integra/reaproveita o mecanismo de auditoria que `ecossistema.py audit` já tem.
> **Custo de LLM:** zero.

---

## Contexto já investigado

- `ecossistema.py audit` (raiz do monorepo) já roda, em sequência, os 6 Meta-Quality Gates: `G_ECOSSISTEMA_INTEGRIDADE.py`, `G_DRIFT_NUCLEO_COMPARTILHADO.py`, `G_HARNESS_COMPAT.py`, `G_SEGREDOS.py`, `G_CLI_HELP_CONSISTENCIA.py`, `G_COMPONENTE_AGNOSTICO.py` — confirmado por reprodução real na auditoria da Bateria 1 de `docs/planos/testes-completos-ecossistema/` (todos exit 0, isolados e em conjunto).
- Cada ferramenta (`aidd-forge`, `aidd-generator`, `aidd-master`, `aidd-enterprise`) também tem sua própria suíte `pytest` real, já rodada por `ecossistema.py status --testes` (1.384 testes confirmados passando na mesma auditoria).
- Manual (`MANUAL-UNIFICADO-ORQUESTRACAO-ORCA-ADE.md` §3, §9): o gate mecânico roda **localmente dentro da worktree** logo após o agente terminar, e é o único critério para decidir merge (aprovado 100% → merge; falhou → quarentena/retry/rollback). §9 lista `gate_auditor.py` como "Auditor binário de Quality Gates (exit 0 / exit 1)".

## Definição de Pronto

2.1. `componentes/compartilhado/skills/orca-plan-orchestrator/scripts/gate_auditor.py`: função que, dado um caminho de worktree e um identificador de "frente" (para saber que tipo de gate rodar — ex.: se a frente tocou `tools/aidd-master`, rodar a suíte de `aidd-master` + `ecossistema.py audit`; se for uma frente da raiz, só `ecossistema.py audit`), executa os comandos de verificação reais dentro daquela worktree via subprocess, captura exit code real de cada um (nunca mascarado por pipe), e retorna um veredito agregado: aprovado só se **todos** os comandos relevantes retornarem exit 0.

2.2. O auditor precisa suportar tanto o caso "gate de raiz" (`python ecossistema.py audit`) quanto "gate de ferramenta" (`pytest` dentro de `tools/<ferramenta>`), decidindo qual rodar com base em qual caminho a frente declara tocar (informação que vem do `plan_parser.py` do Item 1 — se o documento `NN-<nome>.md` da frente cita um caminho de `tools/*`, rodar a suíte daquela ferramenta também).

2.3. Teste real: criar uma worktree de teste (repositório git temporário, reaproveitando `worktree_engine.py` do Item 1) com 2 cenários — um onde o gate deveria passar (código/config válidos) e um onde deveria falhar de propósito (ex.: um teste quebrado de propósito, ou um Meta-Quality Gate que reprova por um motivo conhecido) — confirmando que o auditor distingue os dois casos corretamente com exit code real, nunca com um resultado presumido.

## Critério de saída

- `gate_auditor.py` rodando de verdade contra os 2 cenários de teste (passa/falha), exit code real citado para cada.
- Nenhum gate existente (`gates/*.py`) alterado — este item só consome os gates que já existem, não modifica sua lógica interna.
- Suíte de testes do módulo com exit 0 real.
- `git status` da raiz limpo ao final, exceto os arquivos novos deste item.

## Prompt de Execução

> Copie o bloco abaixo integralmente para o agente executor. Autocontido — não pressupõe que ele viu esta conversa.

```
Você vai construir um módulo Python que audita, de forma binária
(aprovado/reprovado, exit 0/1), o resultado de uma "frente" de trabalho
dentro de uma git worktree, reaproveitando os Quality Gates que já
existem no monorepo ecossistema-aidd (raiz em
C:\Users\trcnologia\Desktop\ecossistema-aidd). Você NÃO vai criar
nenhum gate novo - só integrar os que já existem.

CONTEXTO JÁ INVESTIGADO:
- python ecossistema.py audit (raiz do monorepo) roda em sequencia 6
  Meta-Quality Gates: gates/G_ECOSSISTEMA_INTEGRIDADE.py,
  G_DRIFT_NUCLEO_COMPARTILHADO.py, G_HARNESS_COMPAT.py, G_SEGREDOS.py,
  G_CLI_HELP_CONSISTENCIA.py, G_COMPONENTE_AGNOSTICO.py - todos exit 0
  no estado atual do repositorio (confirmado por auditoria real
  recente).
- Cada ferramenta (tools/aidd-forge, tools/aidd-generator,
  tools/aidd-master, tools/aidd-enterprise) tem sua propria suite
  pytest real, rodavel dentro da propria pasta da ferramenta.
- O modulo que voce vai criar (scripts/gate_auditor.py, dentro da pasta
  da skill) deve rodar dentro do CONTEXTO de uma worktree (um caminho
  de diretorio que sera passado como parametro), nao necessariamente na
  raiz do ecossistema-aidd principal - o objetivo final (fora de escopo
  deste item) e rodar isso dentro de git worktrees efemeras criadas
  pelo worktree_engine.py de um item anterior.

DEFINIÇÃO DE PRONTO:
1. Criar componentes/compartilhado/skills/orca-plan-orchestrator/scripts/gate_auditor.py
   com uma funcao que recebe (a) o caminho de uma worktree/diretorio de
   trabalho e (b) um identificador de frente (ou uma lista de caminhos
   que a frente declara tocar), e decide quais comandos de verificacao
   rodar: se a frente toca tools/<ferramenta>, rodar a suite pytest
   daquela ferramenta (via subprocess, dentro daquele diretorio); se a
   frente e de escopo raiz, rodar python ecossistema.py audit. Capturar
   o exit code REAL de cada comando (nunca mascarado por pipe) e
   retornar um veredito agregado: aprovado somente se TODOS os comandos
   relevantes retornarem exit 0.

2. A funcao deve suportar rodar mais de um comando de verificacao para
   a mesma frente (ex: uma frente que mexeu em tools/aidd-master E em
   arquivos de gates/ da raiz precisa passar nos dois).

3. Escrever um teste real com 2 cenarios, cada um dentro de uma
   worktree/diretorio de teste real (pode reaproveitar um repositorio
   git temporario simples, nao precisa necessariamente do
   worktree_engine.py completo se isso ainda nao existir no seu
   ambiente - documente essa dependencia no relatorio se for o caso):
   - Cenario A (deve passar): estrutura de arquivos valida, todos os
     comandos de verificacao relevantes retornam exit 0 de verdade.
   - Cenario B (deve falhar de proposito): crie um teste pytest
     propositalmente quebrado (assert False, por exemplo) dentro do
     diretorio de teste, e confirme que o gate_auditor detecta a falha
     e retorna reprovado com o exit code real capturado, nao um
     resultado presumido.

Execute os 2 cenarios de verdade agora e cite o exit code real de cada
comando individual, nao so o veredito agregado.

CRITÉRIO DE SAÍDA:
- gate_auditor.py rodando de verdade contra os 2 cenarios (passa/falha),
  exit code real citado para cada comando individual.
- Nenhum arquivo dentro de gates/ (raiz) alterado - a logica interna
  dos gates existentes nao muda.
- Suite de testes do modulo com exit 0 real.
- git status da raiz limpo ao final, exceto os arquivos novos deste
  item.

REGRAS DE ESCOPO - NÃO FAÇA:
- Não crie nenhum gate novo em gates/ (raiz) nem em tools/*/gates/ -
  este item so consome o que ja existe.
- Não altere a logica interna de nenhum gate existente.
- Não faça git commit nem git push.

ENTREGÁVEL: caminho do gate_auditor.py criado, saida real dos 2
cenarios de teste (exit code de cada comando individual + veredito
agregado), caminho da suite de testes do modulo.
```

## Prompt de Execução — English version

> Copy the block below in full to the executor agent. Self-contained.

```
You are going to build a Python module that audits, in a binary
pass/fail way (exit 0/1), the result of a work "front" inside a git
worktree, reusing the Quality Gates that already exist in the
ecossistema-aidd monorepo (root at
C:\Users\trcnologia\Desktop\ecossistema-aidd). You will NOT create any
new gate - only integrate the ones that already exist.

ALREADY-INVESTIGATED CONTEXT:
- python ecossistema.py audit (monorepo root) runs, in sequence, 6
  Meta-Quality Gates: gates/G_ECOSSISTEMA_INTEGRIDADE.py,
  G_DRIFT_NUCLEO_COMPARTILHADO.py, G_HARNESS_COMPAT.py, G_SEGREDOS.py,
  G_CLI_HELP_CONSISTENCIA.py, G_COMPONENTE_AGNOSTICO.py - all exit 0 in
  the current repository state (confirmed by a recent real audit).
- Each tool (tools/aidd-forge, tools/aidd-generator, tools/aidd-master,
  tools/aidd-enterprise) has its own real pytest suite, runnable inside
  its own tool folder.
- The module you will create (scripts/gate_auditor.py, inside the
  skill folder) must run within the CONTEXT of a worktree (a directory
  path that will be passed as a parameter), not necessarily inside the
  main ecossistema-aidd root - the end goal (out of scope for this
  item) is to run this inside ephemeral git worktrees created by a
  previous item's worktree_engine.py.

DEFINITION OF DONE:
1. Create componentes/compartilhado/skills/orca-plan-orchestrator/scripts/gate_auditor.py
   with a function that takes (a) a worktree/working-directory path and
   (b) a front identifier (or a list of paths the front declares it
   touches), and decides which verification commands to run: if the
   front touches tools/<tool>, run that tool's pytest suite (via
   subprocess, inside that directory); if the front is root-scoped, run
   python ecossistema.py audit. Capture the REAL exit code of each
   command (never masked by a pipe) and return an aggregated verdict:
   approved only if ALL relevant commands return exit 0.

2. The function must support running more than one verification
   command for the same front (e.g. a front that touched both
   tools/aidd-master AND root gates/ files must pass both).

3. Write a real test with 2 scenarios, each inside a real test
   worktree/directory (may reuse a simple temporary git repository, does
   not necessarily need the full worktree_engine.py if it does not
   exist yet in your environment - document this dependency in the
   report if so):
   - Scenario A (should pass): valid file structure, all relevant
     verification commands really return exit 0.
   - Scenario B (should fail on purpose): create a deliberately broken
     pytest test (assert False, for example) inside the test directory,
     and confirm gate_auditor detects the failure and returns a failed
     verdict with the real captured exit code, not an assumed result.

Run both scenarios for real now and cite the real exit code of each
individual command, not just the aggregated verdict.

EXIT CRITERIA:
- gate_auditor.py actually running against the 2 scenarios (pass/fail),
  real exit code cited for each individual command.
- No file inside gates/ (root) changed - existing gates' internal logic
  is untouched.
- Module's test suite with a real exit 0.
- Root git status clean at the end, except the new files of this item.

SCOPE RULES - DO NOT:
- Do not create any new gate under gates/ (root) or tools/*/gates/ -
  this item only consumes what already exists.
- Do not change any existing gate's internal logic.
- Do not git commit or git push.

DELIVERABLE: path of the created gate_auditor.py, real output of both
test scenarios (exit code of each individual command + aggregated
verdict), path of the module's test suite.
```
