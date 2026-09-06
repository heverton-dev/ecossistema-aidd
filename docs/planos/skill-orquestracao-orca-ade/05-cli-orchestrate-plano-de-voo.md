# Item 5 — CLI `ecossistema.py orchestrate` & Plano de Voo

> **Escopo:** integração da orquestração na CLI unificada `ecossistema.py orchestrate`, módulo compilador de plano de voo (`flight_plan.py`) com modos `--dry-run`, `--resume` e `--yes`.
> **Não faz parte deste item:** invocação real de agentes de LLM (Item 6). Em `--dry-run`, monta os comandos e exibe o plano de voo com custo zero.
> **Custo de LLM:** zero.

---

## Contexto já investigado

- Fonte: `docs/features/orquestracao-orca-ade/02-detalhamento-processo-comandos-e-agnosticidade.md` e `03-persistencia-resiliencia-e-crash-recovery.md`.
- O ponto de entrada unificado do ecossistema é [`ecossistema.py`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/ecossistema.py).
- Os subcomandos já existentes são: `forge`, `generate`, `master`, `enterprise`, `audit`, `status`, `components`.
- O novo comando `orchestrate` receberá o caminho para um diretório de plano estruturado (com `00-PROCESSO-E-DECISOES.md` + `NN-*.md`) e gerará o **Plano de Voo do ORCA ADE**.
- Em `--dry-run`, o sistema roda 100% determinístico sem gastar chamadas de LLM, exibindo a tabela consolidada de frentes, branches calculadas, perfis de harness associados e o comando exato que seria disparado.

---

## Definição de Pronto

5.1. `componentes/compartilhado/skills/orca-plan-orchestrator/scripts/flight_plan.py`:
- Função `gerar_plano_de_voo(plan_dir: Path, profiles_path: Path, harness_default: str = "mimo") -> dict`:
  - Utiliza `plan_parser.parse_plan` para extrair as frentes do diretório.
  - Carrega os perfis de `harness_profiles.json.example`.
  - Para cada frente, compila o comando final via `agent_spawner.compilar_comando`.
  - Retorna estrutura de dados contendo metadados do plano, lista de frentes com branch (`orca/<frente>`), worktree estimada, harness e comando compilado.
- Função `renderizar_plano_de_voo(flight_plan_data: dict) -> str`:
  - Retorna tabela formatada em ASCII / Markdown amigável para exibição no terminal.

5.2. Integração no `ecossistema.py`:
- Adição do subparser `orchestrate`:
  - Argumento posicional: `plano` (caminho para a pasta do plano, default: `.`).
  - Flag `--dry-run`: gera o plano de voo, imprime a tabela e finaliza com exit 0 sem executar agentes.
  - Flag `--resume`: lê o estado existente `.orca_state.json` via `state_engine.py` e foca apenas nas frentes não finalizadas.
  - Flag `--yes` / `-y`: confirmação não-interativa (necessária para execução futura em CI/CD).
  - Flag `--harness`: harness padrão a utilizar (default: `mimo`).

5.3. Suíte de testes (`tests/test_flight_plan.py` e teste de integração no `ecossistema.py`):
- Teste unitário de `gerar_plano_de_voo` contra as 4 fixtures reais do ecossistema.
- Teste de invocação subprocess de `python ecossistema.py orchestrate docs/planos/skill-gerador-planos-auditoria --dry-run` retornando exit 0 e exibindo o plano de voo.

---

## Critério de saída

- Execução real comprovada de `python ecossistema.py orchestrate docs/planos/skill-gerador-planos-auditoria --dry-run` com exit 0.
- Suíte pytest da skill e gates globais (`python ecossistema.py audit`) mantendo conformidade.
- `git status` da raiz contendo apenas os novos arquivos e a edição limpa de `ecossistema.py`.

---

## Prompt de Execução

> Copie o bloco abaixo integralmente para o agente executor. Autocontido — não pressupõe que ele viu esta conversa.

```
Você vai integrar o comando `orchestrate` e o gerador de Plano de Voo ao
ecossistema AIDD (raiz em C:\Users\trcnologia\Desktop\ecossistema-aidd).
Você NÃO vai executar nenhum agente de LLM real neste item — em modo --dry-run
tudo é 100% mecânico e determinístico.

CONTEXTO JÁ INVESTIGADO:
- Módulos já existentes em componentes/compartilhado/skills/orca-plan-orchestrator/scripts/:
  * plan_parser.py (parse_plan, Plan, Front)
  * state_engine.py (create_initial_state, load_state, save_state, etc.)
  * worktree_engine.py (criar_worktree, mergear_worktree, purgar_worktree)
  * gate_auditor.py (audit_front, resolve_commands)
  * agent_spawner.py (carregar_perfil, compilar_comando)
  * hooks.py (executar_pre_hook, executar_post_hook)
  * circuit_breaker.py (avaliar_saude, interromper_processo)
- Catálogo de perfis:
  componentes/compartilhado/skills/orca-plan-orchestrator/.orca/harness_profiles.json.example

DEFINIÇÃO DE PRONTO:
1. Criar componentes/compartilhado/skills/orca-plan-orchestrator/scripts/flight_plan.py:
   - gerar_plano_de_voo(plan_dir: str | Path, profiles_path: str | Path, harness: str = "mimo") -> dict:
     Lê o plano via plan_parser.parse_plan.
     Carrega o perfil via agent_spawner.carregar_perfil.
     Para cada Front no plano:
       Compila o comando com agent_spawner.compilar_comando(perfil, front.content).
       Define branch = f"orca/{front.name}"
       Define worktree = f"wt-{front.name}"
     Retorna dict com metadata do plano e frentes compiladas.
   - renderizar_plano_de_voo(data: dict) -> str:
     Formata uma tabela legível em texto puro / markdown mostrando:
     Frente | Branch | Harness | Comando Compilado (resumido se muito longo)

2. Integrar em ecossistema.py:
   - Adicionar subcomando 'orchestrate' no argparse:
     ecossistema.py orchestrate [plano] [--dry-run] [--resume] [--yes] [--harness {mimo,opencode,claude,agy}]
   - Se --dry-run:
     Gera e imprime o plano de voo e sai com returncode 0 sem tocar no git nem invocar subprocessos.

3. Criar testes unitários em:
   - componentes/compartilhado/skills/orca-plan-orchestrator/tests/test_flight_plan.py
   - Validar geração contra docs/planos/skill-gerador-planos-auditoria/ e outras fixtures.

Execute o teste de verdade agora e execute `python ecossistema.py orchestrate docs/planos/skill-gerador-planos-auditoria --dry-run` citando a saída real no relatório final.

CRITÉRIO DE SAÍDA:
- pytest componentes/compartilhado/skills/orca-plan-orchestrator/tests/ passando 100% com exit 0.
- Execução real de `python ecossistema.py orchestrate docs/planos/skill-gerador-planos-auditoria --dry-run` com exit 0.
- Nenhuma alteração fora de componentes/compartilhado/skills/orca-plan-orchestrator/ e ecossistema.py.
- git status da raiz limpo ao final, exceto os arquivos novos e a integração limpa de ecossistema.py.

REGRAS DE ESCOPO - NÃO FAÇA:
- Não dispare nenhum agente de LLM real neste item.
- Não crie branches ou worktrees no repositório real durante o modo --dry-run.
- Não faça git commit nem git push.

ENTREGÁVEL: caminho do flight_plan.py, caminho dos testes, saída real de execução do comando --dry-run e saída do pytest.
```

## Prompt de Execução — English version

> Copy the block below in full to the executor agent. Self-contained.

```
You are going to integrate the `orchestrate` command and the Flight Plan
generator into the ecossistema-aidd monorepo (root at
C:\Users\trcnologia\Desktop\ecossistema-aidd).
You will NOT execute any real LLM agent in this item — in --dry-run mode
everything is 100% mechanical and deterministic.

ALREADY-INVESTIGATED CONTEXT:
- Existing modules in componentes/compartilhado/skills/orca-plan-orchestrator/scripts/:
  * plan_parser.py (parse_plan, Plan, Front)
  * state_engine.py (create_initial_state, load_state, save_state, etc.)
  * worktree_engine.py (criar_worktree, mergear_worktree, purgar_worktree)
  * gate_auditor.py (audit_front, resolve_commands)
  * agent_spawner.py (carregar_perfil, compilar_comando)
  * hooks.py (executar_pre_hook, executar_post_hook)
  * circuit_breaker.py (avaliar_saude, interromper_processo)
- Harness profile catalog:
  componentes/compartilhado/skills/orca-plan-orchestrator/.orca/harness_profiles.json.example

DEFINITION OF DONE:
1. Create componentes/compartilhado/skills/orca-plan-orchestrator/scripts/flight_plan.py:
   - gerar_plano_de_voo(plan_dir: str | Path, profiles_path: str | Path, harness: str = "mimo") -> dict:
     Reads the plan via plan_parser.parse_plan.
     Loads the profile via agent_spawner.carregar_perfil.
     For each Front in the plan:
       Compiles the command with agent_spawner.compilar_comando(profile, front.content).
       Sets branch = f"orca/{front.name}"
       Sets worktree = f"wt-{front.name}"
     Returns dict with plan metadata and compiled fronts.
   - renderizar_plano_de_voo(data: dict) -> str:
     Formats a readable ASCII / markdown table showing:
     Front | Branch | Harness | Compiled Command (truncated if too long)

2. Integrate into ecossistema.py:
   - Add subparser 'orchestrate' in argparse:
     ecossistema.py orchestrate [plano] [--dry-run] [--resume] [--yes] [--harness {mimo,opencode,claude,agy}]
   - If --dry-run:
     Generates and prints the flight plan and exits with returncode 0 without touching git or spawning background agents.

3. Create unit tests in:
   - componentes/compartilhado/skills/orca-plan-orchestrator/tests/test_flight_plan.py
   - Validate flight plan generation against docs/planos/skill-gerador-planos-auditoria/ and other fixtures.

Run the tests for real now and run `python ecossistema.py orchestrate docs/planos/skill-gerador-planos-auditoria --dry-run` citing the real output in the final report.

EXIT CRITERIA:
- pytest componentes/compartilhado/skills/orca-plan-orchestrator/tests/ passing 100% with exit 0.
- Real verified execution of `python ecossistema.py orchestrate docs/planos/skill-gerador-planos-auditoria --dry-run` with exit 0.
- No modifications outside componentes/compartilhado/skills/orca-plan-orchestrator/ and ecossistema.py.
- git status clean at root at the end, except new files and the clean ecossistema.py integration.

SCOPE RULES - DO NOT:
- Do not launch any real LLM agent in this item.
- Do not create branches or worktrees in the real repository during --dry-run.
- Do not git commit or git push.

DELIVERABLE: path of flight_plan.py, path of tests, real execution output of the --dry-run command, and pytest output.
```


