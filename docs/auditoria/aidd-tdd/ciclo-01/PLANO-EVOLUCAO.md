# Plano de Evolução (Fase 2) - aidd-tdd

Este plano foi gerado pelo Arquiteto (Fase 2) do Pipeline Linear de Auditoria 4F, com o objetivo de readequar a ferramenta `aidd-tdd` em conformidade com o Laudo 15-D (`LAUDO-15D-INICIAL.md`, nota 3/10) e a Definição de Pronto (`DOD.md`).

## Estratégia de Execução
Todos os tickets abaixo requerem ciclo TDD estrito (Red-Green-Refactor). Para cada requisito funcional, testes automatizados (exit 0 / exit 1) devem ser criados antes da implementação real. Toda alteração no `SKILL.md` é feita na fonte `componentes/compartilhado/skills/aidd-tdd/SKILL.md` e propagada pelo mecanismo oficial; `python gates/G_HARNESS_COMPAT.py` deve continuar com exit 0.

### Ticket 1: CLI Determinística e Contrato de Entrada (Refere-se a D2 / DoD 1)
- **Falha 15-D:** `D2. Input e Gatilhos`
- **Artefato de Handoff:** `.agents/skills/aidd-tdd/scripts/cli.py`
- **Requisito TDD (Red):** `python ecossistema.py tdd iniciar --alvo "x"` retorna exit 1 ("comando desconhecido"); o teste deve exigir exit 0 e a criação da sessão de TDD em disco.
- **Implementação Técnica:**
  - Criar `.agents/skills/aidd-tdd/scripts/cli.py` com subcomandos `iniciar --alvo <arquivo> --seam <nome>`, `red`, `green`, `refactor`, `status`.
  - Registrar o comando `tdd` no CLI principal `ecossistema.py` apontando para o script.
  - Gravar estado da sessão em `docs/tdd/<data>_<slug>/sessao.json`.
- **Verificação (Green):** Execução do CLI `ecossistema.py tdd iniciar` retorna exit 0 e gera `sessao.json` válido.
- **Construtor Prompt (EN):**
  - Create .agents/skills/aidd-tdd/scripts/cli.py with commands: iniciar, red, green, refactor, status.
  - Write session state to docs/tdd/<date>_<slug>/sessao.json.
  - Register tdd command in ecossistema.py delegating to scripts/cli.py.
  - Test: python ecossistema.py tdd iniciar --alvo "tests/test_x.py" --seam "seam_1". Assert exit 0 and sessao.json created.

### Ticket 2: Isolamento da Execução em Git Worktree Efêmera (Refere-se a D3 / DoD 2)
- **Falha 15-D:** `D3. Raio de Impacto e Isolamento`
- **Artefato de Handoff:** `.agents/skills/aidd-tdd/scripts/isolamento.py`
- **Requisito TDD (Red):** Teste reprova com exit 1 se modificações forem aplicadas na working tree principal sem worktree ativa.
- **Implementação Técnica:**
  - Implementar gerenciador `TddWorktreeManager` em `.agents/skills/aidd-tdd/scripts/isolamento.py` criando `../worktrees_tdd-<slug>/`.
  - Impedir escritas fora da worktree efêmera, com exceção de `docs/tdd/`.
  - Reutilizar abstrações comprovadas de isolamento git do ecossistema.
- **Verificação (Green):** Criação e destruição de worktrees efêmeras sem poluição do working tree raiz.
- **Construtor Prompt (EN):**
  - Create .agents/skills/aidd-tdd/scripts/isolamento.py with TddWorktreeManager.
  - Create ephemeral worktree ../worktrees_tdd-<slug>/ on start, remove on finalize or rollback.
  - Block file writes outside ephemeral worktree except docs/tdd/.
  - Test: create and teardown worktree. Assert exit 0 and git status clean in main tree.

### Ticket 3: Validador de Costuras Públicas e Anti-Stubs (Refere-se a D4 / DoD 3)
- **Falha 15-D:** `D4. Componentes e Fractalidade`
- **Artefato de Handoff:** `.agents/skills/aidd-tdd/scripts/validador_seams.py`
- **Requisito TDD (Red):** Teste falha com exit 1 se código contiver stubs vazios (`pass`, `NotImplementedError`, `assert True`) ou testar membros privados.
- **Implementação Técnica:**
  - Analisar via AST os arquivos de teste gerados verificando ausência de stubs vazios e chamadas a métodos privados `_helper()`.
  - Validar se a costura testada pertence à lista acordada no `sessao.json`.
- **Verificação (Green):** Validador aprova código com asserções reais (exit 0) e rejeita stubs vazios com exit 1.
- **Construtor Prompt (EN):**
  - Create .agents/skills/aidd-tdd/scripts/validador_seams.py using Python ast module.
  - Inspect test files to detect empty stubs, trivial assertions (assert True), and private calls.
  - Verify that tested entry point belongs to agreed seams list in sessao.json.
  - Test: run validator on file with pass or trivial assert. Assert exit 1. On real assert, exit 0.

### Ticket 4: Motor de Execução Red-Green Multi-Runner (Refere-se a D8 / DoD 3)
- **Falha 15-D:** `D8. O que o Estágio Processa`
- **Artefato de Handoff:** `.agents/skills/aidd-tdd/scripts/motor_tdd.py`
- **Requisito TDD (Red):** Teste reprova com exit 1 quando o estado Red é satisfeito com erro de sintaxe em vez de erro de asserção funcional.
- **Implementação Técnica:**
  - Implementar motor para orquestrar execução de runners suportados (`pytest`, `vitest`, `cargo test`, `go test`).
  - Diferenciar explicitamente falha de asserção (`AssertionError` / failure funcional) de erros de sintaxe ou compilação.
  - Transicionar estado `sessao.json` de Red para Green somente após exit code 0 na suíte.
- **Verificação (Green):** Red com SyntaxError é rejeitado (exit 1); Red com AssertionError é aceito (exit 0); Green com todos os testes passando avança o estado.
- **Construtor Prompt (EN):**
  - Create .agents/skills/aidd-tdd/scripts/motor_tdd.py supporting pytest, vitest, cargo, go.
  - Parse runner output to verify Red fails with AssertionError, not SyntaxError or compile error.
  - Advance session state in sessao.json from RED to GREEN only on runner exit code 0.
  - Test: run test with syntax error. Assert rejected. Run test with assertion failure. Assert accepted as RED.

### Ticket 5: Fallback e Resiliência Operacional (Refere-se a D11 / DoD 4)
- **Falha 15-D:** `D11. Tratamento de Exceções e Fallback`
- **Artefato de Handoff:** `.agents/skills/aidd-tdd/scripts/fallback.py`
- **Requisito TDD (Red):** Teste trava em timeout ou falha sem diagnóstico quando runner não está instalado no PATH do sistema.
- **Implementação Técnica:**
  - Implementar detecção prévia de runners no ambiente com timeout rígido (max 60s).
  - Adicionar proteção de circuit-breaker contra loops infinitos de Red-Green (máximo 5 tentativas consecutivas).
  - Emitir instruções claras de dependência ausente caso runner inexista.
- **Verificação (Green):** Detecção de runner inexistente devolve mensagem estruturada e exit 1 sem crash.
- **Construtor Prompt (EN):**
  - Create .agents/skills/aidd-tdd/scripts/fallback.py.
  - Implement runner pre-check in system PATH with execution timeout of 60 seconds.
  - Add circuit breaker limiting consecutive Red-Green attempts to 5 max before aborting.
  - Test: simulate missing runner executable. Assert structured failure and exit 1.

### Ticket 6: Observabilidade e Telemetria de Ciclos (Refere-se a D12 / DoD 5)
- **Falha 15-D:** `D12. Observabilidade e Frugalidade`
- **Artefato de Handoff:** `.agents/skills/aidd-tdd/scripts/observabilidade.py`
- **Requisito TDD (Red):** Execuções do ciclo não registram duração, contagem de asserções nem métricas de token em disco.
- **Implementação Técnica:**
  - Criar `RastreadorTdd` que registra timestamps, duração de fases (Red, Green, Refactor) e quantidade de asserções em `docs/tdd/<slug>/metricas.json`.
  - Integrar com log padrão de sessões em `secoes/`.
- **Verificação (Green):** `metricas.json` é gravado com esquema válido contendo tempos de cada ciclo e métricas consolidadas.
- **Construtor Prompt (EN):**
  - Create .agents/skills/aidd-tdd/scripts/observabilidade.py with RastreadorTdd.
  - Record phase durations (Red, Green, Refactor), assertion counts, and timestamps in metricas.json.
  - Integrate with secoes/ audit trail.
  - Test: run sample Red-Green cycle. Assert metricas.json exists and contains valid metrics.

### Ticket 7: Quality Gate Próprio e Rótulo Honesto (Refere-se a D13 / DoD 6)
- **Falha 15-D:** `D13. Quality Gates (Portões)`
- **Artefato de Handoff:** `gates/G_aidd_tdd.py`
- **Requisito TDD (Red):** Não existe `gates/G_aidd_tdd.py` nem teste que prove que ele morde sob violação de stubs ou falso-positivo (Lei #13).
- **Implementação Técnica:**
  - Criar `gates/G_aidd_tdd.py` validando integridade de `sessao.json`, ausência de stubs, testes com asserções reais e cobertura do seam.
  - Criar `gates/test_g_aidd_tdd.py` provando que o gate reprova (exit 1) diante de stubs vazios e aprova (exit 0) sob ciclo concluído.
  - Registrar no portão canônico de auditoria `ecossistema.py audit`.
- **Verificação (Green):** `python gates/G_aidd_tdd.py` executa e `test_g_aidd_tdd.py` passa comprovando exit 1 em mutação e exit 0 em caso íntegro.
- **Construtor Prompt (EN):**
  - Create gates/G_aidd_tdd.py validating session state, absence of stubs, real assertions, and agreed seam adherence.
  - Create gates/test_g_aidd_tdd.py proving gate bites (exit 1 on stub, exit 0 on clean pass per Law 13).
  - Register G_aidd_tdd in ecossistema.py audit.
  - Test: run test_g_aidd_tdd.py. Assert exit 0.

### Ticket 8: Limpeza, Rollback e Handoff Assinado (Refere-se a D14 / DoD 7 e DoD 8)
- **Falha 15-D:** `D14. Critério de Rejeição (Rollback)`
- **Artefato de Handoff:** `.agents/skills/aidd-tdd/scripts/handoff.py`
- **Requisito TDD (Red):** Não existe rollback automático em caso de falha de refatoração nem emissão de manifesto assinado HMAC-SHA256 de entrega.
- **Implementação Técnica:**
  - Criar `.agents/skills/aidd-tdd/scripts/rollback.py` revertendo arquivos alterados para o último estado Green conhecido caso a refatoração falhe.
  - Criar `.agents/skills/aidd-tdd/scripts/handoff.py` gerando `docs/tdd/<slug>/handoff-tdd.json` com assinatura HMAC-SHA256, lista de testes verdes, commits e status final.
- **Verificação (Green):** Quebra na refatoração reverte arquivos automaticamente; conclusão bem-sucedida gera `handoff-tdd.json` assinado e íntegro.
- **Construtor Prompt (EN):**
  - Create .agents/skills/aidd-tdd/scripts/rollback.py to revert to last Green state on refactor regression.
  - Create .agents/skills/aidd-tdd/scripts/handoff.py producing signed docs/tdd/<slug>/handoff-tdd.json with HMAC-SHA256.
  - Test: introduce regression during refactor, assert automatic rollback to last Green.
  - Test: successful completion generates verified handoff-tdd.json with exit 0.
