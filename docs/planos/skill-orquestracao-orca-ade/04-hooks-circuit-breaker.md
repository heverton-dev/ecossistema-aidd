# Item 4 — Hooks Pre/Post & Circuit Breaker / Timeout

> **Escopo:** os módulos de ciclo de vida reativo orientados a eventos (`hooks.py`) e proteção anti-loop/timeout/heartbeat (`circuit_breaker.py`), ambos 100% determinísticos e testáveis sem gastar nenhuma chamada de LLM.
> **Não faz parte deste item:** disparo de agentes reais de LLM (Item 6), interface de linha de comando CLI unificada (Item 5).
> **Custo de LLM:** zero.

---

## Contexto já investigado

- Fonte: `docs/features/orquestracao-orca-ade/10-arquitetura-hooks-reativos-pre-e-pos-execucao.md` e `docs/features/orquestracao-orca-ade/12-circuit-breaker-e-timeouts-de-seguranca.md`.
- **Hooks Reativos (§2 e §3 do doc 10):** em vez de busy-wait/polling contínuo, a execução adota pre-hook e post-hook.
  - **Pre-hook:** executado antes do agente, valida a integridade da worktree, atualiza atomicamente o estado para `RUNNING` via `state_engine.py` e registra o timestamp de início.
  - **Post-hook:** disparado imediatamente no término do processo do agente, captura o exit code, executa o `gate_auditor.py`, atualiza o estado para `GATE_PASSED` ou `FAILED` via `state_engine.py` e gera o evento de sinalização (ex.: `.orca/events/<frente>.done`).
- **Circuit Breaker (§2 e §3 do doc 12):** protege contra travamento (stale process), loops infinitos ou prompts que exigem stdin.
  - `max_execution_time_seconds` (teto total da frente).
  - `idle_heartbeat_seconds` (tempo sem novo output/modificação no log da frente).
  - Ação em timeout: matar processo (`taskkill` no Windows / `kill -9` no Unix), marcar `FAILED` no estado com motivo de timeout, reter worktree em quarentena sem bloquear as demais frentes.

---

## Definição de Pronto

4.1. `componentes/compartilhado/skills/orca-plan-orchestrator/scripts/hooks.py`:
- Função `executar_pre_hook(front_name: str, worktree_path: Path, state_path: Path) -> dict`:
  - Valida que a pasta da worktree existe.
  - Atualiza o `.orca_state.json` para `RUNNING` via `state_engine.py`.
  - Atualiza o `memory.md` correspondente.
  - Retorna metadados de execução (timestamp inicial, paths validados).
- Função `executar_post_hook(front_name: str, worktree_path: Path, state_path: Path, agent_exit_code: int, touched_paths: list[str]) -> dict`:
  - Se `agent_exit_code != 0`, marca a frente como `FAILED` no `.orca_state.json`.
  - Se `agent_exit_code == 0`, executa `audit_front` de `gate_auditor.py`. Se aprovado, marca `GATE_PASSED`; se reprovado, marca `FAILED`.
  - Atualiza o `memory.md` correspondente.
  - Emite sinalizador de conclusão (cria arquivo `<worktree_path>/.orca/events/<front_name>.done`).
  - Retorna resultado estruturado (status final, veredito do gate, caminho do sinalizador).

4.2. `componentes/compartilhado/skills/orca-plan-orchestrator/scripts/circuit_breaker.py`:
- Enum `HealthStatus`: `OK`, `TIMEOUT_TOTAL`, `TIMEOUT_IDLE`.
- Classe `CircuitBreakerConfig`: dataclass com `max_execution_time_seconds: float = 1800.0`, `idle_heartbeat_seconds: float = 300.0`.
- Função `avaliar_saude(start_time: float, last_activity_time: float, current_time: float, config: CircuitBreakerConfig) -> HealthStatus`:
  - Retorna `HealthStatus.TIMEOUT_TOTAL` se `(current_time - start_time) > config.max_execution_time_seconds`.
  - Retorna `HealthStatus.TIMEOUT_IDLE` se `(current_time - last_activity_time) > config.idle_heartbeat_seconds`.
  - Retorna `HealthStatus.OK` caso contrário.
- Função `interromper_processo(pid: int) -> bool`:
  - Encerra de forma segura o processo pelo PID (compatível com Windows via `taskkill /F /T /PID` e POSIX via `signal.SIGKILL` / `os.kill`).
  - Trata exceções caso o processo já tenha finalizado.

4.3. Suíte de testes (`tests/test_hooks.py` e `tests/test_circuit_breaker.py`):
- Teste de Pre-hook e Post-hook com ciclo feliz (`GATE_PASSED` + criação de `.done`).
- Teste de Post-hook com falha do agente (`agent_exit_code != 0` -> `FAILED`).
- Teste de Post-hook com falha de gate (`audit_front` reprovado -> `FAILED`).
- Teste de `CircuitBreaker` avaliando condições normais, timeout absoluto e timeout por inatividade (heartbeat).
- Teste de `interromper_processo` em subprocesso dormente (ex.: `python -c "import time; time.sleep(10)"`).

---

## Critério de saída

- Suíte de testes dos 2 novos módulos rodando com exit 0 real.
- Nenhum módulo de LLM real invocado.
- Zero alterações fora de `componentes/compartilhado/skills/orca-plan-orchestrator/`.
- `git status` da raiz limpo ao final, exceto os arquivos novos.

---

## Prompt de Execução

> Copie o bloco abaixo integralmente para o agente executor. Autocontido — não pressupõe que ele viu esta conversa.

```
Você vai construir os módulos de Hooks Reativos e Circuit Breaker para o motor
de orquestração multi-agente ORCA ADE, no monorepo ecossistema-aidd
(raiz em C:\Users\trcnologia\Desktop\ecossistema-aidd).
Você NÃO vai executar nenhum agente de LLM real neste item — todo o código
é 100% mecânico, determinístico e testável via pytest.

CONTEXTO JÁ INVESTIGADO:
- docs/features/orquestracao-orca-ade/10-arquitetura-hooks-reativos-pre-e-pos-execucao.md
- docs/features/orquestracao-orca-ade/12-circuit-breaker-e-timeouts-de-seguranca.md
- Módulos já existentes em componentes/compartilhado/skills/orca-plan-orchestrator/scripts/:
  * state_engine.py (create_initial_state, load_state, save_state, update_front_state, render_memory_md, FrontState)
  * gate_auditor.py (audit_front, AuditVerdict)
  * worktree_engine.py (criar_worktree, mergear_worktree, purgar_worktree)
  * plan_parser.py (parse_plan)

DEFINIÇÃO DE PRONTO:
1. Criar componentes/compartilhado/skills/orca-plan-orchestrator/scripts/hooks.py:
   - executar_pre_hook(front_name: str, worktree_path: Path, state_path: Path) -> dict:
     Valida que worktree_path existe (se não existir, levanta FileNotFoundError).
     Carrega state de state_path, atualiza a frente para FrontState.RUNNING via update_front_state, salva atomicamente.
     Atualiza memory.md no diretório pai de state_path (ou ao lado do state_path).
     Retorna dict com {"status": "RUNNING", "timestamp": time.time(), "front": front_name}.
   - executar_post_hook(front_name: str, worktree_path: Path, state_path: Path, agent_exit_code: int, touched_paths: list[str]) -> dict:
     Se agent_exit_code != 0: novo_estado = FrontState.FAILED
     Se agent_exit_code == 0: roda audit_front(worktree_path, front_name, touched_paths). Se verdict.approved: GATE_PASSED, senão: FAILED.
     Atualiza estado via update_front_state e salva atomicamente via save_state.
     Renderiza e grava memory.md atualizado.
     Gera arquivo de sinalização: event_file = worktree_path / ".orca" / "events" / f"{front_name}.done" (cria diretório .orca/events se não existir).
     event_file.write_text(novo_estado.value, encoding="utf-8")
     Retorna dict com {"front": front_name, "state": novo_estado.value, "event_file": str(event_file)}.

2. Criar componentes/compartilhado/skills/orca-plan-orchestrator/scripts/circuit_breaker.py:
   - HealthStatus(str, Enum): OK = "OK", TIMEOUT_TOTAL = "TIMEOUT_TOTAL", TIMEOUT_IDLE = "TIMEOUT_IDLE"
   - CircuitBreakerConfig(dataclass): max_execution_time_seconds: float = 1800.0, idle_heartbeat_seconds: float = 300.0
   - avaliar_saude(start_time: float, last_activity_time: float, current_time: float, config: CircuitBreakerConfig) -> HealthStatus:
     Se (current_time - start_time) > config.max_execution_time_seconds: return HealthStatus.TIMEOUT_TOTAL
     Se (current_time - last_activity_time) > config.idle_heartbeat_seconds: return HealthStatus.TIMEOUT_IDLE
     return HealthStatus.OK
   - interromper_processo(pid: int) -> bool:
     Finaliza o processo de forma segura no SO.
     No Windows: roda subprocess taskkill /F /T /PID <pid>
     No Linux/Unix: roda os.kill(pid, signal.SIGKILL)
     Tratar exceções (ex.: ProcessLookupError ou erro se processo já encerrou) e retornar True se finalizado com sucesso.

3. Criar testes unitários em:
   - componentes/compartilhado/skills/orca-plan-orchestrator/tests/test_hooks.py
   - componentes/compartilhado/skills/orca-plan-orchestrator/tests/test_circuit_breaker.py
   Todos rodando em diretórios temporários (tmp_path).

Execute o teste de verdade agora e cite a saída real do pytest no relatório final.

CRITÉRIO DE SAÍDA:
- pytest componentes/compartilhado/skills/orca-plan-orchestrator/tests/ passando 100% com exit 0.
- Nenhuma alteração fora de componentes/compartilhado/skills/orca-plan-orchestrator/.
- git status da raiz limpo ao final, exceto os arquivos novos deste item.

REGRAS DE ESCOPO - NÃO FAÇA:
- Não dispare nenhum processo de agente de LLM real neste item.
- Não crie worktrees ou arquivos fora de diretórios temporários de teste.
- Não faça git commit nem git push.

ENTREGÁVEL: caminho dos 2 módulos criados (hooks.py, circuit_breaker.py), caminho dos testes e saída real do pytest com contagem de testes.
```

## Prompt de Execução — English version

> Copy the block below in full to the executor agent. Self-contained.

```
You are going to build the Reactive Hooks and Circuit Breaker modules for the
ORCA ADE multi-agent orchestration engine, in the ecossistema-aidd monorepo
(root at C:\Users\trcnologia\Desktop\ecossistema-aidd).
You will NOT execute any real LLM agent in this item — all code is 100%
mechanical, deterministic, and testable via pytest.

ALREADY-INVESTIGATED CONTEXT:
- docs/features/orquestracao-orca-ade/10-arquitetura-hooks-reativos-pre-e-pos-execucao.md
- docs/features/orquestracao-orca-ade/12-circuit-breaker-e-timeouts-de-seguranca.md
- Existing modules in componentes/compartilhado/skills/orca-plan-orchestrator/scripts/:
  * state_engine.py (create_initial_state, load_state, save_state, update_front_state, render_memory_md, FrontState)
  * gate_auditor.py (audit_front, AuditVerdict)
  * worktree_engine.py (criar_worktree, mergear_worktree, purgar_worktree)
  * plan_parser.py (parse_plan)

DEFINITION OF DONE:
1. Create componentes/compartilhado/skills/orca-plan-orchestrator/scripts/hooks.py:
   - executar_pre_hook(front_name: str, worktree_path: Path, state_path: Path) -> dict:
     Validates that worktree_path exists (if missing, raises FileNotFoundError).
     Loads state from state_path, updates front to FrontState.RUNNING via update_front_state, saves atomically.
     Updates memory.md in the state_path parent directory (or next to state_path).
     Returns dict with {"status": "RUNNING", "timestamp": time.time(), "front": front_name}.
   - executar_post_hook(front_name: str, worktree_path: Path, state_path: Path, agent_exit_code: int, touched_paths: list[str]) -> dict:
     If agent_exit_code != 0: new_state = FrontState.FAILED
     If agent_exit_code == 0: runs audit_front(worktree_path, front_name, touched_paths). If verdict.approved: GATE_PASSED, else: FAILED.
     Updates state via update_front_state and saves atomically via save_state.
     Renders and writes updated memory.md.
     Emits completion event signal: event_file = worktree_path / ".orca" / "events" / f"{front_name}.done" (creates .orca/events if missing).
     event_file.write_text(new_state.value, encoding="utf-8")
     Returns dict with {"front": front_name, "state": new_state.value, "event_file": str(event_file)}.

2. Create componentes/compartilhado/skills/orca-plan-orchestrator/scripts/circuit_breaker.py:
   - HealthStatus(str, Enum): OK = "OK", TIMEOUT_TOTAL = "TIMEOUT_TOTAL", TIMEOUT_IDLE = "TIMEOUT_IDLE"
   - CircuitBreakerConfig(dataclass): max_execution_time_seconds: float = 1800.0, idle_heartbeat_seconds: float = 300.0
   - avaliar_saude(start_time: float, last_activity_time: float, current_time: float, config: CircuitBreakerConfig) -> HealthStatus:
     If (current_time - start_time) > config.max_execution_time_seconds: return HealthStatus.TIMEOUT_TOTAL
     If (current_time - last_activity_time) > config.idle_heartbeat_seconds: return HealthStatus.TIMEOUT_IDLE
     return HealthStatus.OK
   - interromper_processo(pid: int) -> bool:
     Terminates the process cleanly in the OS.
     On Windows: runs subprocess taskkill /F /T /PID <pid>
     On Linux/Unix: runs os.kill(pid, signal.SIGKILL)
     Catches exceptions (e.g. ProcessLookupError or already dead process) and returns True on clean termination.

3. Create unit tests in:
   - componentes/compartilhado/skills/orca-plan-orchestrator/tests/test_hooks.py
   - componentes/compartilhado/skills/orca-plan-orchestrator/tests/test_circuit_breaker.py
   All running in isolated temporary directories (tmp_path).

Run the tests for real now and cite the real pytest output in the final report.

EXIT CRITERIA:
- pytest componentes/compartilhado/skills/orca-plan-orchestrator/tests/ passing 100% with exit 0.
- No modifications outside componentes/compartilhado/skills/orca-plan-orchestrator/.
- git status clean at root at the end, except the new files of this item.

SCOPE RULES - DO NOT:
- Do not launch any real LLM agent subprocess in this item.
- Do not create worktrees or files outside temporary test directories.
- Do not git commit or git push.

DELIVERABLE: path of the 2 created modules (hooks.py, circuit_breaker.py), path of the tests, and real pytest output with test count.
```


