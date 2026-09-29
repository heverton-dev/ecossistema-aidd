# Template de Auditoria de Ferramenta (Lens 15-D)

> **Laudo REVISADO (Fase 4 — Inspetor/Retorno).** Este laudo consolida a auditoria final da ferramenta `aidd-forge` no **Ciclo 02**, após a conclusão com êxito da Fase 3 (Construtor / TICKET-01 e TICKET-02). A análise cobre a totalidade do código-fonte em `.agents/skills/aidd-forge/` (composto por `SKILL.md` e os 7 módulos determinísticos em `scripts/`), o pacote local em `tools/aidd-forge/aidd_forge/`, o quality gate `gates/G_aidd_forge.py` e a suíte de testes de fechamento.

Este documento descreve a estrutura canônica para auditar qualquer ferramenta (Skill/Tool) do ecossistema, dissecando sua arquitetura através do framework Lens 15-D (The Agentic Anatomical Matrix).

## 1. Identificação da Ferramenta

- **Nome da Ferramenta:** `aidd-forge` (skill determinística + pacote local `tools/aidd-forge/aidd_forge`)
- **Descrição Breve:** Injeta o kit completo de governança AIDD em um repositório alvo — orquestração efêmera de subagentes com *context purge*, quality gates determinísticos, git hooks, regras de economia extrema de tokens (Caveman Ultra) e fatiamento de fases com microambientes isolados. Opera como um invólucro de 7 módulos Python determinísticos que confinam o *blast radius*, validam payload, renderizam templates, persistem estado, aplicam resiliência, telemetria, rollback transacional e emitem handoff assinado por SHA-256 ao `aidd-planner`.
- **Comando de Gatilho:** `python ecossistema.py forge init [path]` ou slash command `/forge [path]` (declarados em `.agents/skills/aidd-forge/SKILL.md`). Subcomandos declarativos reais em `scripts/cli.py`: `init`, `inject`, `audit`, `conform`, `handoff {emit,verify}`.

## 2. A Matriz Anatômica (Lens 15-D)

### Fase 1: Governança e Blindagem

- **D1. Contratos e Regras:**
  - **Status:** IMPLEMENTADO (Nota: 10/10).
  - **Detalhes Técnicos:** O frontmatter YAML de `SKILL.md` declara os metadados canônicos (`name: aidd-forge`, `description`). Os contratos executáveis residem em `scripts/bootstrap.py`: `_CAMPOS_OBRIGATORIOS = ("tool", "ciclo", "alvo", "kits")`, `_CAMPOS_OPCIONAIS = ("force",)` e allow-list fechada `_TODOS_CAMPOS`. A função `validar_payload()` rejeita chaves estranhas com `PayloadValidationError`. Cada módulo de script declara explicitamente o critério DoD/Lens ao qual atende (`cli.py` -> D4/DoD 1; `isolamento.py` -> D3/DoD 2; `bootstrap.py` -> D8/DoD 3; `resiliencia.py` -> D11/DoD 4; `observabilidade.py` -> D12/DoD 5; `rollback.py` -> D14/DoD 7; `G_aidd_forge.py` -> D13/DoD 6). Nenhuma dependência de LLM é utilizada em tarefas mecânicas (conformidade estrita com a Lei #1). No ciclo-02, foi garantida a estrita conformidade com a Lei #11 (abolição de menções residuais a Next.js nos templates do forge) e com a Lei #5 (eliminação de stub em `aidd_forge/cli.py::cli`).

- **D2. Input e Gatilhos:**
  - **Status:** IMPLEMENTADO (Nota: 10/10).
  - **Detalhes Técnicos:** Duplo nível de entrada estritamente validada:
    1. *Baixo Nível:* `carregar_payload()` (bootstrap.py) consome arquivo JSON posicional com validação de tipos (`Mapping`), verificação de campos mandatórios e rejeição imediata de path traversal (`..`).
    2. *Alto Nível:* `_montar_parser()` (cli.py) processa argv via `argparse` com subparser obrigatório (`required=True`): `init [path] [--force]`, `inject <tipo> <nome> --descricao <str> [--conteudo|--conteudo-file] [--path] [--force]`, `audit [path] [--format json|md|html] [--output]`, `conform [path] [--dry-run] [--item N]` e `handoff <emit|verify> [--path] [--componente]`.
    3. *Pré-condição de Estado:* Exige presença da raiz do ecossistema (`encontrar_raiz_repositorio()`) e existência física do pacote local `tools/aidd-forge/aidd_forge/cli.py` (`raiz_pacote_local()`); caso ausente, levanta `RuntimeError` resultando em `exit 1`.
    4. *Critério de Aceite:* Declarado no `SKILL.md`: *"Done when: the command exits 0 and the target contains the injected gates and hooks"*.

- **D3. Raio de Impacto e Isolamento:**
  - **Status:** IMPLEMENTADO (Nota: 10/10).
  - **Detalhes Técnicos:** Implementado em `scripts/isolamento.py`. O confinamento é assegurado por `validar_caminho_escrita()`, que resolve caminhos canônicos absolutos e autoriza escrita exclusivamente quando o caminho pertence à raiz do repositório (`repo_root`) ou a uma worktree efêmera (`worktree_dir`). Qualquer tentativa de fuga — inclusive via traversal `..` ou symlinks — levanta `SandboxViolationError` (subclasse de `PermissionError`). `escrever_com_isolamento()` é a única primitiva autorizada de I/O em disco para a skill, sendo consumida compulsoriamente por `bootstrap.py:152`, `orquestracao.py:108` e `rollback.py:63`. A suíte `tests/test_forge_isolamento.py` comprova com 5/5 testes que violações de sandbox são bloqueadas deterministamente. Não há interação com banco de dados externo ou processos não confinados.

- **D4. Componentes e Fractalidade:**
  - **Status:** IMPLEMENTADO (Nota: 10/10).
  - **Detalhes Técnicos:** Malha fractal composta por 7 módulos em `scripts/` articulados pelo roteador central `scripts/cli.py`: `bootstrap.py`, `cli.py`, `isolamento.py`, `observabilidade.py`, `orquestracao.py`, `resiliencia.py`, `rollback.py` e o quality gate `gates/G_aidd_forge.py`. A lista oficial é exposta em `COMPONENTES_PADRAO` (cli.py:62-71). O carregamento inter-módulos utiliza importação dinâmica controlada com cache em `sys.modules` com namespaces isolados por módulo (`aidd_forge_isolamento_bootstrap`, `_orquestracao`, `_rollback`). A integração com o pacote de suporte ocorre via `executar_script_local()` (cli.py:43). A fonte única soberana reside em `componentes/compartilhado/skills/aidd-forge/`, replicada de forma agnóstica para todos os harnesses (`.agents/`, `.claude/`, `.cursor/`, `.gemini/`, `.mimocode/`, `.opencode/`). Zero dependência de servidores MCP de terceiros; autossuficiência determinística total (Lei #6).

### Fase 2: O Chão de Fábrica (Workflow Agêntico)

- **D5. Visão e Escopo:**
  - **Status:** IMPLEMENTADO (Nota: 10/10).
  - **Detalhes Técnicos:** A missão central é transformar qualquer repositório arbitrário em uma base de software estritamente blindada e governada pelos protocolos AIDD. A camada de skill fornece a barreira de proteção de entrada (sandbox, schema, transação, resiliência), enquanto `tools/aidd-forge/aidd_forge/` provê os motores de injeção (`injector.py`, `git_hooks.py`, `token_optimizer.py`, `phase_fencer.py`, `harness_sync.py`, etc.). No ciclo-02, o escopo foi aperfeiçoado para garantir adesão completa ao Padrão-Ouro de Stack Tecnológica TanStack (Lei #11) e erradicação de stubs (Lei #5).

*(Para cada estágio da execução, detalhe D6 a D9)*

- **[Estágio 1 - CLI Router] D6. O que o Estágio Faz:** Roteia e valida a invocação sem executar trabalho colateral desnecessário: detecta o subcomando, monta o parser declarativo via `_montar_parser()` e invoca `parse_args()` com estratégia de *fail-fast*.
- **[Estágio 1 - CLI Router] D7. O que o Estágio Recebe:** `argv: List[str]` cru de `sys.argv[1:]` ou fornecido via injeção em testes, caminho alvo opcional (default `"."`), flags de execução (`--force`, `--dry-run`).
- **[Estágio 1 - CLI Router] D8. O que o Estágio Processa:** Parser mecânico via `argparse` padrão Python. Tratamento do `SystemExit` para manter a garantia binária: código `0` para `--help` e código `1` para erros de sintaxe ou subcomandos inválidos (nunca código `2`). Zero uso de LLM.
- **[Estágio 1 - CLI Router] D9. O que o Estágio Entrega:** Exit code binário determinístico (`0` ou `1`) e, no subcomando `handoff`, o caminho `Path` para `handoff-forge.json`.

- **[Estágio 2 - Validador de Payload] D6. O que o Estágio Faz:** Lê o arquivo de entrada JSON e valida seu conteúdo contra o schema normativo de bootstrap.
- **[Estágio 2 - Validador de Payload] D7. O que o Estágio Recebe:** Caminho do arquivo JSON posicional (`bootstrap.py <arquivo_payload.json>`).
- **[Estágio 2 - Validador de Payload] D8. O que o Estágio Processa:** `carregar_payload()` e `validar_payload()` em `bootstrap.py`: parse `json.loads()`, verificação de tipo de dicionário, conferência das 4 chaves obrigatórias (`tool`, `ciclo`, `alvo`, `kits`), rejeição de campos não declarados, sanitização contra path traversal (`..`) e 3 expressões regulares compiladas (`_RE_TOOL`, `_RE_CICLO`, `_RE_KIT`). Converte qualquer inconsistência em `PayloadValidationError` e `exit 1`.
- **[Estágio 2 - Validador de Payload] D9. O que o Estágio Entrega:** Dicionário estruturado, tipado e normalizado pronto para consumo pelo motor de renderização.

- **[Estágio 3 - Renderizador de Templates] D6. O que o Estágio Faz:** Renderiza deterministicamente o manifesto de bootstrap através de interpolação contextual com trava contra resíduos.
- **[Estágio 3 - Renderizador de Templates] D7. O que o Estágio Recebe:** Dicionário normalizado pelo Estágio 2 e o contexto derivado (`tool`, `ciclo`, `kits` concatenados por vírgula, `force` booleano).
- **[Estágio 3 - Renderizador de Templates] D8. O que o Estágio Processa:** `renderizar_template()` em `bootstrap.py`: substituição por regex de cada marcador `{{chave}}`. Se uma chave não existir no contexto ou se após a substituição restar qualquer `{{` ou `}}`, aborta levantando `PayloadValidationError("renderizacao deixou placeholder malformado residual")`. Gera a assinatura de domínio `forge/{{tool}}/{{ciclo}}`.
- **[Estágio 3 - Renderizador de Templates] D9. O que o Estágio Entrega:** String canônica do manifesto JSON serializado com `sort_keys=True`, `ensure_ascii=False` e quebra de linha terminal padrão.

- **[Estágio 4 - Escrita Confinada] D6. O que o Estágio Faz:** Grava o manifesto de bootstrap fisicamente em disco sob estrita contenção de sandbox.
- **[Estágio 4 - Escrita Confinada] D7. O que o Estágio Recebe:** String JSON renderizada pelo Estágio 3 e o caminho destino validado.
- **[Estágio 4 - Escrita Confinada] D8. O que o Estágio Processa:** Invocação de `isolamento.escrever_com_isolamento()`, acionando `validar_caminho_escrita(repo_root=destino, alvo_relativo="FORGE-BOOTSTRAP.json")`, garantindo que o arquivo não escape da raiz alvo antes de executar `mkdir(parents=True)` e `write_text(encoding="utf-8")`.
- **[Estágio 4 - Escrita Confinada] D9. O que o Estágio Entrega:** Arquivo físico `FORGE-BOOTSTRAP.json` gravado no disco, log informativo `[aidd-forge] bootstrap gravado: <path>` e `exit 0`.

- **[Estágio 5 - Orquestração e Verificação Sequencial] D6. O que o Estágio Faz:** Orquestra a execução sequencial dos três subestágios (`pre_validacao`, `injecao`, `pos_verificacao`) com persistência de estado a cada transição.
- **[Estágio 5 - Orquestração e Verificação Sequencial] D7. O que o Estágio Recebe:** Caminho da pasta alvo, handlers de estágio injetáveis (padrão via `_handlers_padrao()`) e arquivo `ORQUESTRACAO-ESTADO.json` prévio quando houver retomada.
- **[Estágio 5 - Orquestração e Verificação Sequencial] D8. O que o Estágio Processa:** `executar_pipeline()` e `validar_estado()` em `scripts/orquestracao.py`: máquina de estados finita (`versao == 1`, campos fechados, prefixo ordenado de estágios, estados válidos `em_execucao`, `concluido`, `abortado`). Persistência atômica via `salvar_estado()` (`.tmp` + `os.replace`). Idempotência: caso `status == "concluido"`, não reexecuta. Em caso de falha, marca atomicamente `status = "abortado"` antes do retorno `1` (fail-closed).
- **[Estágio 5 - Orquestração e Verificação Sequencial] D9. O que o Estágio Entrega:** `ORQUESTRACAO-ESTADO.json` atômico com `status = "concluido"`, marcador físico `ORQUESTRACAO-MARCADOR.txt` e código de saída `0`.

- **[Estágio 6 - Telemetria e Handoff] D6. O que o Estágio Faz:** Coleta métricas operacionais frugais e emite o manifesto final de handoff assinado por SHA-256 para o próximo ator do pipeline.
- **[Estágio 6 - Telemetria e Handoff] D7. O que o Estágio Recebe:** Contexto de medição (`operacao`), caminho `secoes/`, relógio monotônico e lista oficial `COMPONENTES_PADRAO`.
- **[Estágio 6 - Telemetria e Handoff] D8. O que o Estágio Processa:** `observabilidade.execucao()` calcula a duração precisa, valida as 4 chaves canônicas da métrica (`operacao`, `duracao_s`, `artefatos`, `status`) e registra em append-only em `secoes/FORGE-TELEMETRIA.jsonl` (ou stdout em fallback). `cli.montar_handoff()` calcula hash SHA-256 e tamanho de cada componente em disco, gravando `handoff-forge.json`.
- **[Estágio 6 - Telemetria e Handoff] D9. O que o Estágio Entrega:** Linha JSON estruturada de telemetria e o arquivo de handoff `handoff-forge.json` devidamente assinado, apontando explicitamente `consumidor: "aidd-planner"`.

- **D10. Orquestração e Topologia:**
  - **Status:** IMPLEMENTADO (Nota: 10/10).
  - **Detalhes Técnicos:** Implementado em `scripts/orquestracao.py`. O transporte de dados é estruturado através de estado persistido em disco (`ORQUESTRACAO-ESTADO.json`), banindo variáveis voláteis em memória de agente (Lei #3). Características topológicas:
    1. *Execução Determinística:* Sequenciamento rígido `("pre_validacao", "injecao", "pos_verificacao")`.
    2. *Retomabilidade (Resume-Safe):* Executa `ESTAGIOS[len(estado["concluidos"]):]`, dispensando etapas já consolidadas.
    3. *Atomicidade e Transacionalidade:* Gravações via arquivo temporário com rename atômico (`os.replace`).
    4. *Fail-Closed:* Captura exceções, persiste `status = "abortado"` e retorna `1`, impedindo que estados fiquem inconsistentes.
    5. *Comunicação Interna:* Acoplamento procedural direto sem rede, sem subprocessos ocultos e sem IPC complexo.

### Fase 3: Resiliência e Economia (Engenharia Operacional)

- **D11. Tratamento de Exceções e Fallback:**
  - **Status:** IMPLEMENTADO (Nota: 10/10).
  - **Detalhes Técnicos:** Implementado em `scripts/resiliencia.py`. Trata exceções operacionais através de três mecanismos determinísticos:
    1. *Classificação Transiente:* `eh_transiente()` categoriza `PermissionError`, errnos transientes (`EACCES`, `EPERM`, `EBUSY`, `ETIMEDOUT`, `EAGAIN`), código Win32 `_EBUSY_WINDOWS = 32` (assegurando interoperabilidade Windows/POSIX per Lei #6) e strings conhecidas de travamento (`index.lock`, `resource temporarily unavailable`).
    2. *Retry com Backoff Exponencial:* `com_retry()` executa loop controlado com backoff exponencial (`base * fator ** (tentativa - 1)`). Erros permanentes propagam imediatamente sem atrasos artificiais. Ao esgotar tentativas, levanta `ResilienciaEsgotadaError` preservando a exceção original (`raise ... from exc`).
    3. *Persistência de Falhas:* Registra incidentes em `secoes/FORGE-FALHAS.jsonl` via `registrar_falha()` e `persistir_falha()`. Todas as interfaces CLI e scripts interceptam erros e imprimem mensagens sanitizadas em `stderr` com padrão `[aidd-forge] ...`, retornando `exit 1` limpo.

- **D12. Observabilidade e Frugalidade:**
  - **Status:** IMPLEMENTADO (Nota: 10/10).
  - **Detalhes Técnicos:** Implementado em `scripts/observabilidade.py`. O módulo estabelece obrigatoriedade formal de métricas:
    1. *Context Manager Frugal:* `Execucao` rastreia o tempo via relógio monotônico (`time.monotonic`), acumula artefatos gerados e exige invocação de `emitir()` no `__exit__`, disparando `MetricaAusenteError` caso a execução finalize sem registro.
    2. *Schema de Métrica:* Validação estrita por `validar_metrica()`, exigindo exatamente 4 chaves: `operacao`, `duracao_s` (float >= 0, rejeitando booleanos), `artefatos` (lista de strings) e `status` (`"sucesso"` ou `"falha"`).
    3. *Frugalidade de I/O e Tokens:* Persistência em `secoes/FORGE-TELEMETRIA.jsonl` com fallback para stdout em uma única linha. A execução mecânica dos 7 módulos consome **zero tokens** de modelo, pois não faz chamadas a provedores de LLM. Respostas concisas e estruturadas em conformidade com a Rule 10 e Lei #4.

### Fase 4: O Inspetor e a Expedição (Validação)

- **D13. Quality Gates (Portões):**
  - **Status:** IMPLEMENTADO (Nota: 10/10).
  - **Detalhes Técnicos:** O quality gate oficial `gates/G_aidd_forge.py` (declarado em `COMPONENTES_PADRAO` e calibrado para atender D13/DoD 6) valida 4 eixos estruturais:
    1. *Governança:* `verificar_governanca()` valida presença e preenchimento de `AGENTS.md` e bloqueia rótulos ilusórios por regex (`100% testad`, `zero bugs?`, `certifica[çc][ãa]o` - Lei #8).
    2. *Gates com Caminho de Falha:* `verificar_gates_alvo()` inspeciona a pasta `gates/`, faz parse via AST e assegura que todo gate possua caminho explícito de reprovação (`return 1`, `sys.exit(1)`, `SystemExit(1)` - Lei #13, provando que morde).
    3. *Git Hook:* `verificar_hook()` confere a presença do pre-commit não vazio (suportando tanto repositórios `.git` quanto pastas desacopladas).
    4. *Zero Stubs:* `verificar_stubs()` varre todos os arquivos `.py` via AST garantindo ausência de nós `pass`, `...` ou `raise NotImplementedError` (Lei #5).
    5. *Prova de Mordida Bidirecional:* A suíte `gates/test_g_aidd_forge.py` (7/7 testes aprovados) e os testes de fechamento do ciclo-02 comprovam que o portão retorna `EXIT 0` em alvos íntegros e `EXIT 1` perante qualquer desvio. No TICKET-01, os templates foram alinhados à Lei #11 e o stub residual em `aidd_forge/cli.py::cli` foi erradicado, mantendo a suite própria (`tools/aidd-forge/tests`) com 297 testes aprovados.

- **D14. Critério de Rejeição (Rollback):**
  - **Status:** IMPLEMENTADO (Nota: 10/10).
  - **Detalhes Técnicos:** Implementado em `scripts/rollback.py`. Fornece rollback atômico e transacional guiado por journal:
    1. *Transação Controlada:* `TransacaoForge` registra arquivos e pastas criados no journal `.FORGE-ROLLBACK-JOURNAL.json` persistido atomicamente (`_persistir_jornal` via `.tmp` + `os.replace`).
    2. *Revalidação Contínua:* `escriturar()` valida caminhos através de `isolamento.validar_caminho_escrita()` antes de qualquer operação de gravação.
    3. *Reversão Automática:* Qualquer exceção levantada dentro do bloco de contexto dispara `desfazer()`, que remove arquivos criados e limpa diretórios vazios em ordem inversa de criação, preservando a exceção original.
    4. *Recuperação Pós-Crash:* Função `recuperar()` lê o journal pré-existente e executa limpeza fail-safe garantindo que nenhum resíduo permaneça no repositório. A suíte `tests/test_forge_rollback.py` atesta 100% de eficácia em cenários normais e de crash.

- **D15. Output Consolidado e Handoff:**
  - **Status:** IMPLEMENTADO (Nota: 10/10).
  - **Detalhes Técnicos:** Implementado em `scripts/cli.py` através das rotinas `montar_handoff()`, `emitir_handoff()` e `verificar_handoff()`:
    1. *Manifesto Estruturado:* Emite `handoff-forge.json` com campos `{versao: "1.0", ferramenta: "aidd-forge", consumidor: "aidd-planner", gerado_em: <ISO-8601>, componentes: [...]}`.
    2. *Assinatura SHA-256:* Cada um dos 8 componentes (`scripts/*.py` e `gates/G_aidd_forge.py`) possui seu hash criptográfico SHA-256 e tamanho em bytes registrados.
    3. *Verificação Estrita de Integridade:* `verificar_handoff()` recalcula os hashes de disco e compara com o manifesto; qualquer alteração (mesmo de 1 byte) resulta em `exit 1` imediato (`hash divergente no handoff`).
    4. *Fechamento Ciclo-02 (TICKET-02):* O manifesto foi re-emitido e sincronizado com os hashes finais pós-ajustes de conformidade (`python ecossistema.py forge handoff verify` -> `exit 0`), e a suíte `tests/test_forge_fechamento_ciclo02.py` atesta a sincronia completa e o cumprimento dos 8 critérios do `DOD.md`.

---

## 3. Matriz de Avaliação da Execução

- [x] A ferramenta isolou seu raio de impacto corretamente? Sim. `scripts/isolamento.py` assegura contenção estrita a `repo_root` e `worktree_dir` com bloqueio contra path traversal (`..`) e validação prévia de caminhos, validado por 5 testes unitários dedicados.
- [x] O workflow seguiu as fases sem alucinações de LLM em tarefas mecânicas? Sim. Os 7 módulos Python utilizam puramente lógica mecânica e determinística (AST, expressões regulares, JSON e hashlib), sem uso de LLM para tarefas operacionais (Lei #1).
- [x] O output final passou em todos os Quality Gates e emitiu o Handoff? Sim. O quality gate `gates/G_aidd_forge.py` e o gate `G_auditoria_15D.py` foram plenamente validados com `EXIT 0`, e o manifesto assinado `handoff-forge.json` foi verificado com 100% de integridade SHA-256 direcionado ao `aidd-planner`.
