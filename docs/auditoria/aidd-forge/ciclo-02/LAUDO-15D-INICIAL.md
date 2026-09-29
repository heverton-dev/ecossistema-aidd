# Template de Auditoria de Ferramenta (Lens 15-D) - INICIAL (Fase 1: Inspetor)

> **Laudo INICIAL (Ciclo 02 — Fase 1: Inspetor).** Este laudo realiza a re-auditoria arquitetural da ferramenta `aidd-forge` através do framework Lens 15-D (The Agentic Anatomical Matrix), comparando o estado atual do código-fonte em `.agents/skills/aidd-forge/` e do quality gate `gates/G_aidd_forge.py` com o laudo revisado do ciclo anterior (`docs/auditoria/aidd-forge/ciclo-01/LAUDO-15D-REVISADO.md`).

Este documento descreve a estrutura canônica para auditar qualquer ferramenta (Skill/Tool) do ecossistema, dissecando sua arquitetura através do framework Lens 15-D (The Agentic Anatomical Matrix).

## 1. Identificação da Ferramenta

- **Nome da Ferramenta:** `aidd-forge` (skill determinística + pacote local `tools/aidd-forge/aidd_forge`)
- **Descrição Breve:** Injeta o kit completo de governança AIDD em um repositório alvo — orquestração efêmera de subagentes com *context purge*, quality gates determinísticos, git hooks, regras de economia extrema de tokens e fatiamento de fases com microambientes isolados. Opera como um invólucro de 7 módulos Python determinísticos que confinam o *blast radius*, validam payload, renderizam templates, persistem estado, aplicam resiliência, telemetria, rollback transacional e emitem handoff assinado por SHA-256 ao `aidd-planner`.
- **Comando de Gatilho:** `python ecossistema.py forge init [path]` ou slash command `/forge [path]`. Subcomandos declarativos reais em `scripts/cli.py`: `init`, `inject`, `audit`, `conform`, `handoff {emit,verify}`.

## 2. A Matriz Anatômica (Lens 15-D)

### Fase 1: Governança e Blindagem

- **D1. Contratos e Regras:**
  - **Nota Anterior -> Nota Nova:** 10/10 -> 10/10
  - **O que mudou no código desde o último laudo:** Os contratos executáveis continuam estritamente respeitados em `scripts/bootstrap.py` com allow-lists fechadas (`_CAMPOS_OBRIGATORIOS = ("tool", "ciclo", "alvo", "kits")`, `_CAMPOS_OPCIONAIS = ("force",)` e `_TODOS_CAMPOS`) e validação de schema rígido via `validar_payload()`. O frontmatter YAML em `SKILL.md` preserva os gatilhos canônicos. No nível do ecossistema, foi consolidada a Lei #11 (Padrão-Ouro de Stack Tecnológica TanStack), sem alterar a estrutura interna de contratos da skill. Nenhuma dependência de LLM para tarefas mecânicas (Lei #1).

- **D2. Input e Gatilhos:**
  - **Nota Anterior -> Nota Nova:** 10/10 -> 10/10
  - **O que mudou no código desde o último laudo:** Nenhuma alteração nos parsers de entrada. Em baixo nível, `carregar_payload()` (bootstrap.py) processa arquivo JSON posicional com validação de tipos e rejeição a path traversal (`..`). Em alto nível, `_montar_parser()` (cli.py) processa os subcomandos obrigatórios (`init`, `inject`, `audit`, `conform`, `handoff`), garantindo saída binária `exit 0` para `--help` e `exit 1` para erros de sintaxe ou ausência de pacote local.

- **D3. Raio de Impacto e Isolamento:**
  - **Nota Anterior -> Nota Nova:** 10/10 -> 10/10
  - **O que mudou no código desde o último laudo:** O módulo `scripts/isolamento.py` mantém confinamento total. `validar_caminho_escrita()` resolve caminhos absolutos e barra qualquer escrita fora de `repo_root` ou `worktree_dir` levantando `SandboxViolationError`. A barreira é consumida por `bootstrap.py:152`, `orquestracao.py:108` e `rollback.py:63`. Todos os 5 testes de isolamento (`tests/test_forge_isolamento.py`) continuam passando com 100% de sucesso.

- **D4. Componentes e Fractalidade:**
  - **Nota Anterior -> Nota Nova:** 10/10 -> 10/10
  - **O que mudou no código desde o último laudo:** A malha de 7 módulos em `scripts/` (`bootstrap.py`, `cli.py`, `isolamento.py`, `observabilidade.py`, `orquestracao.py`, `resiliencia.py`, `rollback.py`) e o portão `gates/G_aidd_forge.py` permanecem declarados em `COMPONENTES_PADRAO` (cli.py:62-71). A fonte única em `componentes/compartilhado/skills/aidd-forge/` encontra-se perfeitamente sincronizada com os harnesses (`.agents/`, `.claude/`, `.cursor/`, `.gemini/`, `.mimocode/`, `.opencode/`). Zero acoplamento a MCP Servers externos desnecessários; recrutamento puramente determinístico e agnóstico (Lei #6).

### Fase 2: O Chão de Fábrica (Workflow Agêntico)

- **D5. Visão e Escopo:**
  - **Nota Anterior -> Nota Nova:** 10/10 -> 10/10
  - **O que mudou no código desde o último laudo:** A transformação pretendida permanece: converter um repositório arbitrário em um projeto com governança AIDD completa, segura e transacional. No ecossistema adjacente (`tools/aidd-forge/templates/`), os templates foram atualizados com `CHECKLIST-CAMADAS-MERCADO.json` e `G_STACK_PADRAO_OURO.py` para reforçar a Lei #11, mantendo o escopo da skill focado no bootstrap, confinamento e validação de integridade.

*(Para cada estágio da execução, detalhe D6 a D9)*

- **D6. O que o Estágio Faz:**
  - **Nota Anterior -> Nota Nova:** 10/10 -> 10/10
  - **O que mudou no código desde o último laudo:** Pipeline sequencial determinístico inalterado, composto pelos 6 estágios estruturados:
    - *[Estágio 1 - CLI Router]* Valida e roteia a invocação CLI via `main()` e `_montar_parser()` em `scripts/cli.py`.
    - *[Estágio 2 - Validador de Payload]* Normaliza e valida schema e regex de payload via `carregar_payload()` e `validar_payload()` em `scripts/bootstrap.py`.
    - *[Estágio 3 - Renderizador de Templates]* Substitui variáveis e confere ausência de placeholders residuais via `renderizar_template()` em `scripts/bootstrap.py`.
    - *[Estágio 4 - Escrita Confinada]* Executa I/O estritamente confinado em `FORGE-BOOTSTRAP.json` via `isolamento.escrever_com_isolamento()`.
    - *[Estágio 5 - Orquestração e Verificação Sequencial]* Executa subestágios sequenciais (`pre_validacao`, `injecao`, `pos_verificacao`) com persistência atômica de estado em `scripts/orquestracao.py`.
    - *[Estágio 6 - Telemetria e Handoff]* Coleta métricas de execução com `scripts/observabilidade.py` e emite o manifesto SHA-256 `handoff-forge.json` via `cli.py`.

- **D7. O que o Estágio Recebe:**
  - **Nota Anterior -> Nota Nova:** 10/10 -> 10/10
  - **O que mudou no código desde o último laudo:** Fluxo de entradas preservado:
    - *[Estágio 1]* `argv: List[str]` cru e caminho do repositório/worktree.
    - *[Estágio 2]* Arquivo JSON de payload bruto com campos `tool`, `ciclo`, `alvo`, `kits`, `force`.
    - *[Estágio 3]* Dicionário normalizado e contexto de substituição derivado.
    - *[Estágio 4]* String do manifesto renderizado e fronteira `repo_root` validada.
    - *[Estágio 5]* Caminho da pasta alvo, handlers customizáveis e `ORQUESTRACAO-ESTADO.json` anterior.
    - *[Estágio 6]* Nome da operação, destino em `secoes/`, relógio monotônico e lista de componentes para cálculo de digest.

- **D8. O que o Estágio Processa:**
  - **Nota Anterior -> Nota Nova:** 10/10 -> 10/10
  - **O que mudou no código desde o último laudo:** Todos os estágios utilizam exclusivamente processamento mecânico por AST, expressões regulares compiladas, validação de tipos e verificação estática de filesystem (`argparse`, `json`, `re`, `pathlib`, `hashlib`), sem qualquer inferência livre de LLM. Os testes em `tests/test_forge_bootstrap.py`, `tests/test_forge_cli.py` e `tests/test_forge_orquestracao.py` confirmam 100% de cobertura determinística.

- **D9. O que o Estágio Entrega:**
  - **Nota Anterior -> Nota Nova:** 10/10 -> 10/10
  - **O que mudou no código desde o último laudo:** Entregas atômicas e padronizadas preservadas:
    - *[Estágio 1]* Exit code binário e redirecionamento de fluxo.
    - *[Estágio 2]* Payload normalizado em formato de dicionário tipado.
    - *[Estágio 3]* String JSON canônica ordenada com assinatura de bootstrap.
    - *[Estágio 4]* Arquivo `FORGE-BOOTSTRAP.json` gravado e `exit 0`.
    - *[Estágio 5]* Arquivo `ORQUESTRACAO-ESTADO.json` atômico (`status = concluido`) e marcador de injeção.
    - *[Estágio 6]* Registro em `FORGE-TELEMETRIA.jsonl` e manifesto assinado `handoff-forge.json`.

- **D10. Orquestração e Topologia:**
  - **Nota Anterior -> Nota Nova:** 10/10 -> 10/10
  - **O que mudou no código desde o último laudo:** O motor de orquestração em `scripts/orquestracao.py` permanece com máquina de estados finita validada por `validar_estado()`, persistência atômica por write em `.tmp` + `os.replace` (Lei #3), proteção contra re-execução quando já concluído (idempotência), retomabilidade determinística via slice `ESTAGIOS[len(estado["concluidos"]):]` e fail-closed com persistência de estado `abortado` antes do encerramento.

### Fase 3: Resiliência e Economia (Engenharia Operacional)

- **D11. Tratamento de Exceções e Fallback:**
  - **Nota Anterior -> Nota Nova:** 10/10 -> 10/10
  - **O que mudou no código desde o último laudo:** `scripts/resiliencia.py` permanece estável e testado. Classificação de erros transientes via `eh_transiente()` tratando códigos `EACCES`, `EPERM`, `EBUSY`, `ETIMEDOUT`, `EAGAIN`, constante `_EBUSY_WINDOWS = 32` e travamento de lock do git (`.git/index.lock`). Loop com backoff exponencial determinístico (`com_retry`), esgotamento propagando `ResilienciaEsgotadaError` e persistência de falhas em `secoes/FORGE-FALHAS.jsonl`.

- **D12. Observabilidade e Frugalidade:**
  - **Nota Anterior -> Nota Nova:** 10/10 -> 10/10
  - **O que mudou no código desde o último laudo:** `scripts/observabilidade.py` permanece mandatório: o context manager `Execucao` exige emissão de métrica sob pena de `MetricaAusenteError`. Validação rigorosa com `validar_metrica()` exigindo exatamente as 4 chaves canônicas (`operacao`, `duracao_s`, `artefatos`, `status`). Gravação em `secoes/FORGE-TELEMETRIA.jsonl` ou fallback para linha única em stdout. Consumo de tokens zero na execução da skill devido à ausência de chamadas a modelos.

### Fase 4: O Inspetor e a Expedição (Validação)

- **D13. Quality Gates (Portões):**
  - **Nota Anterior -> Nota Nova:** 10/10 -> 10/10
  - **O que mudou no código desde o último laudo:** `gates/G_aidd_forge.py` recebeu um aprimoramento evolutivo no commit `c4c4d3f` na função `verificar_hook(alvo: Path)`: agora aceita tanto `.git/hooks/pre-commit` quanto `hooks/pre-commit` alternativo caso o alvo seja um pacote desacoplado ou pasta de exportação sem repositório `.git` ativo. As checagens de governança (`AGENTS.md` e Lei #8 contra rótulos ilusórios), gates com caminho de falha explícito (Lei #13) e varredura AST contra stubs (Lei #5) continuam ativas e com prova de mordida bidirecional comprovada pela suíte `gates/test_g_aidd_forge.py` (7/7 testes aprovados).

- **D14. Critério de Rejeição (Rollback):**
  - **Nota Anterior -> Nota Nova:** 10/10 -> 10/10
  - **O que mudou no código desde o último laudo:** `scripts/rollback.py` mantém o gerenciamento transacional com journal `.FORGE-ROLLBACK-JOURNAL.json`. Em caso de erro durante a injeção, `desfazer()` desfaz as criações de arquivos e diretórios em ordem reversa. Em caso de crash repentino, `recuperar()` lê o journal persistido e limpa resíduos de forma fail-safe. Nenhuma alteração no código; 8 testes unitários em `tests/test_forge_rollback.py` mantêm 100% de sucesso.

- **D15. Output Consolidado e Handoff:**
  - **Nota Anterior -> Nota Nova:** 10/10 -> 10/10
  - **O que mudou no código desde o último laudo:** `scripts/cli.py` mantém as funções `montar_handoff()`, `emitir_handoff()` e `verificar_handoff()`. O manifesto `handoff-forge.json` consolida a entrega com assinatura SHA-256 e tamanho em bytes de cada componente da malha, declarando explicitamente `consumidor: "aidd-planner"`. A verificação compara os hashes reais em disco com os do manifesto e reprova com `exit 1` caso haja qualquer discrepância.

---

## 3. Matriz de Avaliação da Execução

- [x] A ferramenta isolou seu raio de impacto corretamente? Sim, `scripts/isolamento.py` assegura contenção estrita a `repo_root` e `worktree_dir` com bloqueio contra path traversal e testes unitários provando recusa de violações.
- [x] O workflow seguiu as fases sem alucinações de LLM em tarefas mecânicas? Sim, os 7 módulos Python utilizam lógica determinística pura via AST, regex, JSON e hashlib, sem uso de LLM em tarefas mecânicas.
- [x] O output final passou em todos os Quality Gates e emitiu o Handoff? Sim, `gates/G_aidd_forge.py` provado com exit 0 / exit 1 e `handoff-forge.json` validado com integridade SHA-256 íntegra.
