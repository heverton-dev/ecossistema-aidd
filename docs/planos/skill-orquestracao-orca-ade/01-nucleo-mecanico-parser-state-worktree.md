# Item 1 — Núcleo Mecânico (`plan_parser.py` + `state_engine.py` + `worktree_engine.py`)

> **Escopo:** os 3 módulos 100% determinísticos que não dependem de nenhum agente de LLM — leitura/parse de pastas de plano, persistência de estado, ciclo de vida de `git worktree`.
> **Não faz parte deste item:** disparo de agentes reais (Item 3), hooks/circuit breaker (Item 4), CLI/Plano de Voo (Item 5).
> **Custo de LLM:** zero.

---

## Contexto já investigado

- Fonte: `docs/features/orquestracao-orca-ade/MANUAL-UNIFICADO-ORQUESTRACAO-ORCA-ADE.md` §2 (contrato de entrada), §3 (ciclo de vida efêmero), §4 (resiliência/crash recovery) + detalhamento em `02-detalhamento-processo-comandos-e-agnosticidade.md`, `03-persistencia-resiliencia-e-crash-recovery.md`, `06-ciclo-de-vida-ephemeral-worktrees.md` (mesma pasta).
- Contrato de entrada do plano (§2 do manual): `<diretório>/00-PROCESSO-E-DECISOES.md` (contexto mestre) + `NN-<nome>.md` (uma "frente" por arquivo). Este monorepo já tem 4 pastas reais nesse formato exato para usar como fixture de teste: `docs/planos/evolucao-notas-auditoria/`, `docs/planos/refinamento-notas-auditoria/`, `docs/planos/testes-completos-ecossistema/`, `docs/planos/skill-gerador-planos-auditoria/`.
- Dupla camada de estado (§4 do manual): `memory.md` (humano/LLM-readable, tabela de progresso) + `.orca_state.json` (máquina de estados: `PENDING`, `RUNNING`, `GATE_PASSED`, `MERGED`, `FAILED`, `PAUSED_QUOTA`).
- Ciclo de vida da worktree (§3 do manual): `git worktree add ../wt-<frente> -b orca/<frente>` → operação isolada → gate mecânico local → `git merge --no-ff` (se aprovado) → `git worktree remove --force` + `git branch -D` (purga). Falha → quarentena/retry/rollback sem tocar na branch principal.

## Definição de Pronto

1.1. `componentes/compartilhado/skills/orca-plan-orchestrator/scripts/plan_parser.py`: função que recebe um caminho de pasta de plano (relativo, absoluto, ou `.`) e retorna uma estrutura de dados (ex.: lista de "frentes" com nome, arquivo, conteúdo) a partir de `00-PROCESSO-E-DECISOES.md` + `NN-<nome>.md`. Deve rodar sem erro contra as 4 pastas fixture reais listadas acima, cada uma com número de itens diferente (1, 5, 5, 6) — prova que o parser não assume uma contagem fixa de frentes.

1.2. `componentes/compartilhado/skills/orca-plan-orchestrator/scripts/state_engine.py`: gravação atômica de `.orca_state.json` (escrita em arquivo temporário + rename, nunca escrita direta que pode corromper em queda de energia) com os 6 estados do manual, e renderização de `memory.md` a partir do estado (tabela com frente/branch/commit SHA/status/timestamp). Deve incluir uma função de retomada que, dado um `.orca_state.json` existente, classifica cada frente em: já `MERGED` (ignorar), `GATE_PASSED` (mergear e limpar), `RUNNING` (retomar do ponto de interrupção, decisão de "como retomar" documentada mas pode ficar como stub explícito de decisão futura — não é este item que implementa o agent_spawner), outro estado (tratar conforme a máquina de estados).

1.3. `componentes/compartilhado/skills/orca-plan-orchestrator/scripts/worktree_engine.py`: funções `criar_worktree(nome_frente)`, `mergear_worktree(nome_frente)`, `purgar_worktree(nome_frente)` que executam de verdade `git worktree add/merge --no-ff/remove --force` + `git branch -D` via subprocess real (nunca simulado), sempre contra um **repositório git temporário isolado criado pelo próprio teste** (nunca o `ecossistema-aidd` real). Inclui tratamento do caminho de falha (gate reprovado → não mergear, deixar em quarentena).

1.4. Suíte de testes real (pytest) para os 3 módulos, incluindo pelo menos: parse das 4 pastas fixture reais (1.1); crash-recovery simulado (gravar um `.orca_state.json` com uma frente em `RUNNING`, matar o processo simulando queda, rodar de novo e confirmar que o estado é lido corretamente); ciclo de vida completo de worktree em repositório temporário (criar → merge → purgar, e também o caminho de falha sem merge).

## Critério de saída

- Suíte de testes dos 3 módulos rodando com exit 0 real, citada com a contagem exata de testes passando.
- Parse das 4 pastas fixture reais confirmado (não hipotético — rodar e mostrar a saída).
- Nenhuma escrita fora de: `componentes/compartilhado/skills/orca-plan-orchestrator/scripts/`, os arquivos de teste correspondentes, e diretórios temporários isolados.
- `git status` da raiz do ecossistema-aidd limpo ao final, exceto os arquivos novos deste item.

## Prompt de Execução

> Copie o bloco abaixo integralmente para o agente executor. Autocontido — não pressupõe que ele viu esta conversa.

```
Você vai construir o núcleo mecânico (3 módulos Python, zero uso de LLM
em runtime) de um motor de orquestração multi-agente, no monorepo
ecossistema-aidd (raiz em C:\Users\trcnologia\Desktop\ecossistema-aidd).
Valide tudo com testes reais (pytest, exit code real) - nunca escreva
código que "deveria funcionar" sem uma suíte de teste real provando.

CONTEXTO JÁ INVESTIGADO (leia antes de escrever código):
- docs/features/orquestracao-orca-ade/MANUAL-UNIFICADO-ORQUESTRACAO-ORCA-ADE.md
  secoes 2 (contrato de entrada), 3 (ciclo de vida de worktree), 4
  (resiliencia/crash recovery).
- docs/features/orquestracao-orca-ade/02-detalhamento-processo-comandos-e-agnosticidade.md
- docs/features/orquestracao-orca-ade/03-persistencia-resiliencia-e-crash-recovery.md
- docs/features/orquestracao-orca-ade/06-ciclo-de-vida-ephemeral-worktrees.md
- 4 pastas reais deste monorepo servem de fixture de teste do parser
  (cada uma no formato 00-PROCESSO-E-DECISOES.md + NN-nome.md, com
  contagens diferentes de frentes - 1, 5, 5 e 6 arquivos numerados):
  docs/planos/evolucao-notas-auditoria/
  docs/planos/refinamento-notas-auditoria/
  docs/planos/testes-completos-ecossistema/
  docs/planos/skill-gerador-planos-auditoria/

DEFINIÇÃO DE PRONTO:
1. Criar componentes/compartilhado/skills/orca-plan-orchestrator/scripts/plan_parser.py
   com uma função que recebe um caminho de pasta de plano (relativo,
   absoluto ou ".") e retorna uma estrutura de dados com a lista de
   frentes (nome, caminho do arquivo, conteúdo) extraída de
   00-PROCESSO-E-DECISOES.md + NN-<nome>.md. Rode contra as 4 pastas
   fixture reais listadas acima e confirme que cada uma é parseada sem
   erro, com a contagem de frentes batendo com a realidade de cada
   pasta (conte manualmente os arquivos NN-*.md de cada uma antes,
   para comparar).

2. Criar componentes/compartilhado/skills/orca-plan-orchestrator/scripts/state_engine.py
   com:
   - gravação atômica de um arquivo .orca_state.json (escrever em
     arquivo temporário e fazer rename atômico, nunca escrita direta
     que possa corromper o arquivo se o processo morrer no meio);
   - os 6 estados do manual: PENDING, RUNNING, GATE_PASSED, MERGED,
     FAILED, PAUSED_QUOTA;
   - uma função que renderiza memory.md (Markdown, tabela humana) a
     partir do estado atual;
   - uma função de classificação de retomada: dado um .orca_state.json
     existente, para cada frente, decidir a ação (MERGED -> ignorar;
     GATE_PASSED -> pronta pra merge; RUNNING -> marcar como candidata
     a retomada, mas a lógica de COMO retomar o processo do agente real
     não é escopo deste item - deixe isso como uma função separada e
     claramente nomeada, ex. retomar_frente_em_execucao(), com um
     comentário de uma linha dizendo que a implementação real vem no
     Item 3/6 de um plano futuro - não implemente lógica de agente
     aqui).

3. Criar componentes/compartilhado/skills/orca-plan-orchestrator/scripts/worktree_engine.py
   com 3 funções que executam comandos git REAIS via subprocess (nunca
   simulados): criar_worktree(nome_frente) (git worktree add + -b),
   mergear_worktree(nome_frente) (git merge --no-ff), purgar_worktree(nome_frente)
   (git worktree remove --force + git branch -D). Todas devem operar
   sobre um repositório git temporário criado pelo teste (nunca o
   ecossistema-aidd real) - use um diretório temporário com git init
   real, alguns commits reais, para o teste ter uma base real de onde
   criar branches/worktrees.

4. Escrever uma suíte de testes pytest real cobrindo, no mínimo:
   - parse das 4 pastas fixture reais (item 1);
   - simulação de crash-recovery: grave um .orca_state.json com uma
     frente em RUNNING, releia com a função de state_engine e confirme
     que o estado é corretamente identificado e classificado para
     retomada;
   - ciclo de vida completo de worktree em repositório git temporário:
     criar -> merge -> purgar, e também o caminho de falha (gate
     reprovado -> nunca mergear, worktree fica intacta em quarentena).

Execute a suíte de testes de verdade agora. Rode também, manualmente,
o parser contra as 4 pastas fixture reais fora da suíte de testes, e
cite a saída real no relatório final.

CRITÉRIO DE SAÍDA:
- Suíte de testes com exit 0 real, contagem exata de testes passando
  citada no relatório.
- As 4 pastas fixture parseadas com sucesso, contagem de frentes
  batendo com a realidade de cada pasta (mostrar a comparação).
- Nenhuma escrita fora de
  componentes/compartilhado/skills/orca-plan-orchestrator/scripts/,
  os arquivos de teste correspondentes, e diretórios temporários
  isolados.
- git status da raiz do ecossistema-aidd limpo ao final, exceto os
  arquivos novos deste item.

REGRAS DE ESCOPO - NÃO FAÇA:
- Não implemente disparo de agente real (isso é um item futuro
  separado) - a função de retomada de RUNNING pode ficar como
  interface/stub claramente nomeado e documentado, nunca como um
  disparo real de subprocess de CLI de agente.
- Não crie nem destrua worktrees dentro do repositório ecossistema-aidd
  real - sempre em repositório git temporário isolado criado pelo
  próprio teste.
- Não faça git commit nem git push no repositório real.

ENTREGÁVEL: caminho dos 3 módulos criados, caminho da suíte de testes,
saída real do pytest (exit code + contagem de testes), e a comparação
real de contagem de frentes das 4 pastas fixture.
```

## Prompt de Execução — English version

> Copy the block below in full to the executor agent. Self-contained.

```
You are going to build the mechanical core (3 Python modules, zero LLM
use at runtime) of a multi-agent orchestration engine, in the
ecossistema-aidd monorepo (root at
C:\Users\trcnologia\Desktop\ecossistema-aidd). Validate everything with
real tests (pytest, real exit code) - never write code that "should
work" without a real test suite proving it.

ALREADY-INVESTIGATED CONTEXT (read before writing code):
- docs/features/orquestracao-orca-ade/MANUAL-UNIFICADO-ORQUESTRACAO-ORCA-ADE.md
  sections 2 (input contract), 3 (worktree lifecycle), 4
  (resilience/crash recovery).
- docs/features/orquestracao-orca-ade/02-detalhamento-processo-comandos-e-agnosticidade.md
- docs/features/orquestracao-orca-ade/03-persistencia-resiliencia-e-crash-recovery.md
- docs/features/orquestracao-orca-ade/06-ciclo-de-vida-ephemeral-worktrees.md
- 4 real folders in this monorepo serve as parser test fixtures (each
  in the 00-PROCESSO-E-DECISOES.md + NN-name.md format, with different
  front counts - 1, 5, 5 and 6 numbered files):
  docs/planos/evolucao-notas-auditoria/
  docs/planos/refinamento-notas-auditoria/
  docs/planos/testes-completos-ecossistema/
  docs/planos/skill-gerador-planos-auditoria/

DEFINITION OF DONE:
1. Create componentes/compartilhado/skills/orca-plan-orchestrator/scripts/plan_parser.py
   with a function that takes a plan folder path (relative, absolute,
   or ".") and returns a data structure with the list of fronts (name,
   file path, content) extracted from 00-PROCESSO-E-DECISOES.md +
   NN-<name>.md. Run it against the 4 real fixture folders above and
   confirm each parses without error, with the front count matching
   reality for each folder (manually count the NN-*.md files of each
   one first, to compare).

2. Create componentes/compartilhado/skills/orca-plan-orchestrator/scripts/state_engine.py
   with:
   - atomic writes of an .orca_state.json file (write to a temp file
     and atomic rename, never a direct write that could corrupt the
     file if the process dies mid-write);
   - the 6 states from the manual: PENDING, RUNNING, GATE_PASSED,
     MERGED, FAILED, PAUSED_QUOTA;
   - a function that renders memory.md (Markdown, human table) from
     the current state;
   - a resume-classification function: given an existing
     .orca_state.json, for each front, decide the action (MERGED ->
     ignore; GATE_PASSED -> ready to merge; RUNNING -> mark as a resume
     candidate, but the logic of HOW to resume the real agent process
     is out of scope for this item - leave this as a separate, clearly
     named function, e.g. resume_running_front(), with a one-line
     comment saying the real implementation comes in a future
     Item 3/6 - do not implement agent logic here).

3. Create componentes/compartilhado/skills/orca-plan-orchestrator/scripts/worktree_engine.py
   with 3 functions that run REAL git commands via subprocess (never
   simulated): criar_worktree(front_name) (git worktree add + -b),
   mergear_worktree(front_name) (git merge --no-ff), purgar_worktree(front_name)
   (git worktree remove --force + git branch -D). All must operate on
   a temporary git repository created by the test (never the real
   ecossistema-aidd) - use a temp directory with a real git init and a
   few real commits, so the test has a real base to branch/worktree
   from.

4. Write a real pytest suite covering, at minimum:
   - parsing the 4 real fixture folders (item 1);
   - crash-recovery simulation: write an .orca_state.json with one
     front in RUNNING, re-read it with the state_engine function and
     confirm the state is correctly identified and classified for
     resume;
   - full worktree lifecycle in a temporary git repository: create ->
     merge -> purge, and also the failure path (gate failed -> never
     merge, worktree stays intact in quarantine).

Run the test suite for real now. Also manually run the parser against
the 4 real fixture folders outside the test suite, and cite the real
output in the final report.

EXIT CRITERIA:
- Test suite with a real exit 0, exact passing test count cited in the
  report.
- The 4 fixture folders parsed successfully, front count matching
  reality for each folder (show the comparison).
- No writes outside
  componentes/compartilhado/skills/orca-plan-orchestrator/scripts/,
  the corresponding test files, and isolated temporary directories.
- ecossistema-aidd root git status clean at the end, except the new
  files of this item.

SCOPE RULES - DO NOT:
- Do not implement real agent dispatch (that is a future separate
  item) - the RUNNING resume function may remain a clearly named
  interface/stub, never a real agent-CLI subprocess dispatch.
- Do not create or destroy worktrees inside the real ecossistema-aidd
  repository - always in an isolated temporary git repository created
  by the test itself.
- Do not git commit or git push in the real repository.

DELIVERABLE: path of the 3 created modules, path of the test suite,
real pytest output (exit code + test count), and the real front-count
comparison for the 4 fixture folders.
```
