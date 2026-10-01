# Plano de Evolução (Fase 2) - agilidade-gates

Plano do ciclo-01 para deixar o processo de mudança do ecossistema rápido sem perder a segurança.
Origem: `docs/melhorias/30-09-2026_melhoria-agilidade-gates-commit.html`. Critérios: `DOD.md` deste ciclo.

## Estratégia de Execução
- Todo ticket segue TDD estrito: o teste que reprova (exit 1) vem antes da implementação.
- Princípio de segurança: a main só recebe código que passou na bateria completa (`gate_final` + `--aprovar`). O modo rápido vale só para commits intermediários.
- Cada ticket entrega um arquivo **novo** (o orquestrador pula o ticket se o arquivo de entrega já existir).
- Ordem por ganho: medir (T1) -> gates rápidos (T2-T4) -> derivados (T5-T6) -> fila/aviso (T7) -> push (T8).

### Ticket 1: Medição real do tempo de cada gate (Refere-se a D12 / DoD 1)
- **Falha 15-D:** `D12. Observabilidade e Frugalidade`
- **Artefato de Handoff:** `scripts/medir_gates.py`
- **Requisito TDD (Red):** Teste que chama `medir_gates.py` com um gate falso que dorme 1s e sai 1; deve reprovar enquanto o script não existir e, depois, gravar `segundos>=1` e `exit_code=1`.
- **Implementação Técnica:**
  - Ler os hooks de `.pre-commit-config.yaml` (id + entry), rodar cada um com `subprocess`, medir com `time.perf_counter`.
  - Gravar JSON em `secoes/medicoes/gates-<data>-<modo>.json` com `id`, `segundos`, `exit_code`, `modo`.
  - Flags `--modo rapido|completo`, `--so <id>` e `--saida <arquivo>`.
- **Verificação (Green):** `tests/test_medir_gates.py` passa; uma execução real grava o JSON "antes" no ciclo.
- **Construtor Prompt (EN):**
  - Write tests/test_medir_gates.py first. Fake gate sleeps 1s, exits 1. Assert JSON has segundos>=1 and exit_code=1. Run. Assert exit 1 before implementation.
  - Implement scripts/medir_gates.py. Parse hook id and entry from .pre-commit-config.yaml. Run each entry via subprocess. Time with time.perf_counter.
  - Write JSON to secoes/medicoes/gates-DATE-MODE.json with keys id, segundos, exit_code, modo.
  - Support flags --modo rapido or completo, --so HOOK_ID, --saida PATH.
  - Run tests/test_medir_gates.py. Assert exit 0.

### Ticket 2: G_TESTES_REAIS testa só a ferramenta tocada (Refere-se a D3 / DoD 2)
- **Falha 15-D:** `D3. Raio de Impacto e Isolamento`
- **Artefato de Handoff:** `gates/_escopo_commit.py`
- **Requisito TDD (Red):** Teste com stage fictício `tools/aidd-forge/x.py` espera só `aidd-forge`; com `gates/G_TESTES_REAIS.py` no stage espera todas; com `AIDD_GATES_MODO=completo` espera todas. Reprova antes da implementação.
- **Implementação Técnica:**
  - Novo módulo `gates/_escopo_commit.py`: `modo()` (lê `AIDD_GATES_MODO`, padrão `rapido`), `arquivos_staged()` (`git diff --cached --name-only`), `ferramentas_afetadas(arquivos, todas)`.
  - Regra: `tools/<nome>/...` com `<nome>` na lista -> só ele; qualquer outro caminho em `tools/`, o próprio gate ou `gates/allowlist_skipped_testes.json` -> todas.
  - `G_TESTES_REAIS.py` usa o módulo quando `AIDD_TESTES_REAIS_FERRAMENTAS` não foi definido (a variável manual continua valendo).
- **Verificação (Green):** `tests/test_escopo_commit.py` passa; `gates/test_g_testes_reais.py` continua passando.
- **Construtor Prompt (EN):**
  - Write tests/test_escopo_commit.py first. Staged tools/aidd-forge/x.py returns only aidd-forge. Staged gates/G_TESTES_REAIS.py returns all tools. AIDD_GATES_MODO=completo returns all tools. Run. Assert exit 1.
  - Implement gates/_escopo_commit.py with modo(), arquivos_staged(), ferramentas_afetadas(arquivos, todas). Default mode is rapido.
  - Unknown path under tools/, gates/G_TESTES_REAIS.py or gates/allowlist_skipped_testes.json returns all tools.
  - Wire gates/G_TESTES_REAIS.py to use it only when AIDD_TESTES_REAIS_FERRAMENTAS is unset.
  - Run tests/test_escopo_commit.py and gates/test_g_testes_reais.py. Assert exit 0.

### Ticket 3: G_SEGREDOS varre só os arquivos do commit (Refere-se a D3 / DoD 3)
- **Falha 15-D:** `D3. Raio de Impacto e Isolamento`
- **Artefato de Handoff:** `gates/test_g_segredos_escopo.py`
- **Requisito TDD (Red):** Em repo git temporário: segredo novo plantado num arquivo do stage deve reprovar (exit 1) no modo rápido; arquivo fora do stage não é lido no modo rápido; modo completo varre tudo.
- **Implementação Técnica:**
  - `G_SEGREDOS.py`: em modo rápido, a lista de arquivos vem de `_escopo_commit.arquivos_staged()` (só os que existem); em modo completo, `git ls-files` como hoje.
  - Mantém comparação contra `.secrets.baseline` e o tratamento de barras do Windows já existente.
  - Stage vazio no modo rápido -> exit 0 sem varrer.
- **Verificação (Green):** `gates/test_g_segredos_escopo.py` passa; o teste do gate atual continua passando.
- **Construtor Prompt (EN):**
  - Write gates/test_g_segredos_escopo.py first. Build temp git repo. Plant new secret in staged file. Assert exit 1 in rapido mode. Assert unstaged file not scanned in rapido mode. Assert completo mode scans all tracked files. Run. Assert exit 1 before change.
  - Change gates/G_SEGREDOS.py. Rapido mode scans only existing files from _escopo_commit.arquivos_staged(). Completo mode keeps git ls-files.
  - Keep baseline compare and Windows backslash handling. Empty stage in rapido mode exits 0.
  - Run gates/test_g_segredos_escopo.py and existing G_SEGREDOS tests. Assert exit 0.

### Ticket 4: gate_final é sempre bateria completa (Refere-se a D13 / DoD 4)
- **Falha 15-D:** `D13. Quality Gates (Portões)`
- **Artefato de Handoff:** `tests/test_gate_final_modo_completo.py`
- **Requisito TDD (Red):** Teste que roda `rodar_gate` do orquestrador com `AIDD_GATES_MODO=rapido` no ambiente e um gate falso que imprime o modo; deve ver `completo`. Reprova antes da mudança.
- **Implementação Técnica:**
  - `scripts/orquestrador_4f.py`: o `gate_final` roda com `AIDD_GATES_MODO=completo` forçado no ambiente do subprocesso, ignorando o valor herdado.
  - `python ecossistema.py audit` também força `completo`.
  - O `gate_fase` de cada ticket continua no modo herdado.
- **Verificação (Green):** teste passa; saída do gate_final mostra `modo=completo`.
- **Construtor Prompt (EN):**
  - Write tests/test_gate_final_modo_completo.py first. Set AIDD_GATES_MODO=rapido in env. Run orchestrator gate_final path with fake gate printing mode. Assert output is completo. Run. Assert exit 1.
  - Change scripts/orquestrador_4f.py. Force AIDD_GATES_MODO=completo in gate_final subprocess env. Ignore inherited value.
  - Force completo in python ecossistema.py audit too. Keep gate_fase on inherited mode.
  - Run tests/test_gate_final_modo_completo.py. Assert exit 0.

### Ticket 5: Arquivos derivados num comando só (Refere-se a D15 / DoD 5)
- **Falha 15-D:** `D15. Output Consolidado e Handoff`
- **Artefato de Handoff:** `scripts/regenerar_derivados.py`
- **Requisito TDD (Red):** Teste que roda o comando duas vezes e exige zero diff na segunda; exige hash do `handoff-melhoria.json` calculado sobre o blob em LF (arquivo gravado com CRLF no Windows não pode mudar o hash). Reprova antes da implementação.
- **Implementação Técnica:**
  - Lista única `DERIVADOS` (caminho -> função que regenera): `handoff-melhoria.json`, `.secrets.baseline`, `PLANO-EXECUCAO-ESTRUTURADO.json`, livro, `ACHADOS.json`. Reusar os geradores que já existem; não duplicar lógica.
  - Gravar sempre com `newline="\n"`.
  - Registrar `python ecossistema.py derivados regenerar [--so <caminho>]`.
- **Verificação (Green):** `tests/test_regenerar_derivados.py` passa; segunda execução real não gera diff.
- **Construtor Prompt (EN):**
  - Write tests/test_regenerar_derivados.py first. Run command twice. Assert zero diff on second run. Assert handoff-melhoria.json hash uses LF blob, CRLF file gives same hash. Run. Assert exit 1.
  - Implement scripts/regenerar_derivados.py with one DERIVADOS map, path to regenerate function. Cover handoff-melhoria.json, .secrets.baseline, PLANO-EXECUCAO-ESTRUTURADO.json, book, ACHADOS.json. Reuse existing generators. No duplicated logic.
  - Always write with newline="\n".
  - Register python ecossistema.py derivados regenerar with optional --so PATH.
  - Run tests/test_regenerar_derivados.py. Assert exit 0.

### Ticket 6: `--aprovar` resolve conflito só em derivado (Refere-se a D14 / DoD 6)
- **Falha 15-D:** `D14. Limpeza e Rollback`
- **Artefato de Handoff:** `tests/test_aprovar_conflito_derivados.py`
- **Requisito TDD (Red):** Repo git temporário com duas branches em conflito: (a) só em `handoff-melhoria.json` -> merge conclui; (b) em um `.py` comum -> merge aborta e `git status` fica limpo. Reprova antes da mudança.
- **Implementação Técnica:**
  - No `--aprovar` do `orquestrador_4f.py`: se o merge falhar, listar conflitos (`git diff --name-only --diff-filter=U`).
  - Todos em `DERIVADOS` -> `git checkout --theirs`, rodar `regenerar_derivados`, `git add`, concluir merge.
  - Algum fora -> `git merge --abort` e mensagem com a lista.
- **Verificação (Green):** teste passa nos dois casos.
- **Construtor Prompt (EN):**
  - Write tests/test_aprovar_conflito_derivados.py first. Temp git repo, two branches. Conflict only in handoff-melhoria.json must finish merge. Conflict in plain .py must abort merge with clean git status. Run. Assert exit 1.
  - Change --aprovar path in scripts/orquestrador_4f.py. On merge failure list conflicts via git diff --name-only --diff-filter=U.
  - All conflicts in DERIVADOS: checkout theirs, run regenerar_derivados, git add, finish merge.
  - Any other conflict: git merge --abort, print conflict list, exit 1.
  - Run tests/test_aprovar_conflito_derivados.py. Assert exit 0.

### Ticket 7: Um ciclo pesado por vez + aviso ao terminar (Refere-se a D11 / DoD 7)
- **Falha 15-D:** `D11. Tratamento de Exceções e Fallback`
- **Artefato de Handoff:** `scripts/fila_ciclos.py`
- **Requisito TDD (Red):** Teste: segundo processo que pede a trava espera até o primeiro liberar; trava com PID morto é liberada; ao liberar, grava resultado e chama o aviso. Reprova antes da implementação.
- **Implementação Técnica:**
  - `scripts/fila_ciclos.py`: trava em arquivo (`.aidd/fila-ciclos.lock` com PID, ciclo e início), espera com mensagem periódica, libera trava de PID morto.
  - `orquestrador_4f.py` pega a trava antes da primeira fase e solta no fim (inclusive em erro, via `finally`).
  - Aviso no fim: notificação local do sistema (Windows toast / `notify-send` / `osascript`), com fallback para imprimir no console; grava `secoes/medicoes/ultimo-ciclo.json`.
  - `AGENTS.md`: regra "tarefa longa roda em segundo plano; o agente volta sozinho ao terminar; proibido pedir 'me chame em N minutos'".
- **Verificação (Green):** `tests/test_fila_ciclos.py` passa.
- **Construtor Prompt (EN):**
  - Write tests/test_fila_ciclos.py first. Second process waits until first releases lock. Lock with dead PID is released. Release writes result and calls notifier. Run. Assert exit 1.
  - Implement scripts/fila_ciclos.py. File lock .aidd/fila-ciclos.lock with pid, cycle, start time. Wait with periodic message. Free lock of dead PID.
  - Wire scripts/orquestrador_4f.py: acquire lock before first phase, release in finally.
  - Notify at end via OS toast, notify-send or osascript. Fallback to console print. Write secoes/medicoes/ultimo-ciclo.json.
  - Add rule to AGENTS.md: long task runs in background, agent resumes on completion, never ask user to call back later.
  - Run tests/test_fila_ciclos.py. Assert exit 0.

### Ticket 8: Push com código exige bateria completa verde (Refere-se a D13 / DoD 8)
- **Falha 15-D:** `D13. Quality Gates (Portões)`
- **Artefato de Handoff:** `.githooks/pre-push`
- **Requisito TDD (Red):** Teste em repo temporário: push de mudança em `.py` sem registro de bateria completa verde para o SHA -> exit 1; push só de `secoes/`/`docs/`/`*.md` -> exit 0; push de `.py` com registro verde do mesmo SHA -> exit 0.
- **Implementação Técnica:**
  - `.githooks/pre-push` (sh) chama `python scripts/medir_gates.py --verificar-push`, que lê o intervalo enviado no stdin do hook.
  - Registro verde: `secoes/medicoes/completo-<sha>.json` gravado pelo modo completo com exit 0 em todos os gates.
  - Sem registro -> roda a bateria completa ali mesmo e grava o registro se passar.
- **Verificação (Green):** `tests/test_pre_push.py` passa nos três casos.
- **Construtor Prompt (EN):**
  - Write tests/test_pre_push.py first. Temp repo. Push .py change without green full record for SHA returns exit 1. Push only secoes/, docs/ or .md returns exit 0. Push .py with green record for same SHA returns exit 0. Run. Assert exit 1.
  - Create .githooks/pre-push as sh script calling python scripts/medir_gates.py --verificar-push with hook stdin.
  - Green record is secoes/medicoes/completo-SHA.json written by completo mode when all gates exit 0.
  - No record: run full battery now, write record on pass.
  - Run tests/test_pre_push.py. Assert exit 0.
