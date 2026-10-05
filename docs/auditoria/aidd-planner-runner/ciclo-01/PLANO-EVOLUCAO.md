# Plano de Evolução (Fase 2) - aidd-planner-runner

Este plano foi gerado pelo Arquiteto (Fase 2) do Pipeline Linear de Auditoria 4F, com o objetivo de readequar a ferramenta `aidd-planner-runner` em conformidade com o Laudo 15-D e a Definição de Pronto (DoD).

## Estratégia de Execução
Todos os tickets abaixo requerem ciclo TDD estrito (Red-Green-Refactor). Para cada requisito funcional, testes automatizados (exit 0 / exit 1) devem ser criados antes da implementação real.

### Ticket 1: Isolamento de Raio de Impacto e Sandbox (Refere-se a D3 / DoD 1)
- **Falha 15-D:** `D3. Raio de Impacto e Isolamento`
- **Artefato de Handoff:** `componentes/compartilhado/skills/aidd-planner/scripts/isolamento.py`
- **Requisito TDD (Red):** Teste reprova com exit 1 quando tentativa de escrita de blueprint ocorre fora do escopo ou sem sandbox.
- **Implementação Técnica:**
  - Criar `PlannerWorktreeManager` e `validar_caminho_escrita`.
  - Confinar criação de blueprints a diretórios permitidos ou Git Worktree efêmera.
- **Verificação (Green):** Teste `tests/test_planner_runner_isolamento.py` passa comprovando isolamento de escrita.
- **Construtor Prompt (EN):**
  - Write test first in tests/test_planner_runner_isolamento.py. Assert exit 1 when writing blueprint outside authorized sandbox.
  - Implement componentes/compartilhado/skills/aidd-planner/scripts/isolamento.py with PlannerWorktreeManager and validar_caminho_escrita.
  - Block write I/O outside target directory.
  - Run pytest tests/test_planner_runner_isolamento.py. Assert exit 0.

### Ticket 2: Tratamento de Exceções e Resolução de Conflitos (Refere-se a D11 / DoD 2)
- **Falha 15-D:** `D11. Tratamento de Exceções e Fallback`
- **Artefato de Handoff:** `componentes/compartilhado/skills/aidd-planner/scripts/fallback.py`
- **Requisito TDD (Red):** Colisão de pasta de projeto existente falha sem resolução determinística de sufixo.
- **Implementação Técnica:**
  - Implementar detector e resolvedor de colisão de pastas de projeto (`-2`).
  - Prevenir sobrescrita acidental de blueprints já existentes.
- **Verificação (Green):** Teste `tests/test_planner_runner_fallback.py` valida resolução segura de conflitos.
- **Construtor Prompt (EN):**
  - Write test first in tests/test_planner_runner_fallback.py. Assert safe resolution of project directory collisions.
  - Implement componentes/compartilhado/skills/aidd-planner/scripts/fallback.py with directory collision resolver.
  - Run pytest tests/test_planner_runner_fallback.py. Assert exit 0.

### Ticket 3: Observabilidade e Métricas de Blueprint (Refere-se a D12 / DoD 3)
- **Falha 15-D:** `D12. Observabilidade e Frugalidade`
- **Artefato de Handoff:** `componentes/compartilhado/skills/aidd-planner/scripts/observabilidade.py`
- **Requisito TDD (Red):** Teste reprova se rastreador não calcular bounded contexts, entidades, rotas e estimativa de tokens.
- **Implementação Técnica:**
  - Implementar classe `RastreadorPlanner` que inspeciona `PLANNER.json`.
  - Extrair contagem de bounded contexts, entidades de domínio, rotas e estimativa de tokens.
- **Verificação (Green):** Teste `tests/test_planner_runner_observabilidade.py` valida métricas estruturadas.
- **Construtor Prompt (EN):**
  - Write test first in tests/test_planner_runner_observabilidade.py. Assert extraction of bounded contexts, entities, routes, and estimated tokens from PLANNER.json.
  - Implement componentes/compartilhado/skills/aidd-planner/scripts/observabilidade.py with RastreadorPlanner.
  - Run pytest tests/test_planner_runner_observabilidade.py. Assert exit 0.

### Ticket 4: Quality Gate de Repositório para o Planner (Refere-se a D13 / DoD 4)
- **Falha 15-D:** `D13. Quality Gates (Portões)`
- **Artefato de Handoff:** `gates/G_aidd_planner_runner.py`
- **Requisito TDD (Red):** Gate reprova com exit 1 diretório sem PLANNER.json ou com arquivos corrompidos.
- **Implementação Técnica:**
  - Implementar `gates/G_aidd_planner_runner.py` que inspeciona pasta do projeto sob a Lei #13.
  - Validar presença de PLANNER.json e conformidade dos arquivos mínimos.
- **Verificação (Green):** Teste `gates/test_g_aidd_planner_runner.py` passa comprovando retorno estrito exit 0 / exit 1.
- **Construtor Prompt (EN):**
  - Write test first in gates/test_g_aidd_planner_runner.py. Assert exit 1 on missing PLANNER.json and exit 0 on clean valid project.
  - Implement gates/G_aidd_planner_runner.py adhering to Binary Gate Law.
  - Run pytest gates/test_g_aidd_planner_runner.py. Assert exit 0.

### Ticket 5: Critério de Rejeição e Rollback Automático (Refere-se a D14 / DoD 5)
- **Falha 15-D:** `D14. Critério de Rejeição (Rollback)`
- **Artefato de Handoff:** `componentes/compartilhado/skills/aidd-planner/scripts/rollback.py`
- **Requisito TDD (Red):** Teste reprova se falha durante inicialização de blueprint deixar arquivos parciais no disco.
- **Implementação Técnica:**
  - Implementar gerenciador de contexto `executar_com_rollback` em `scripts/rollback.py`.
  - Reverter qualquer arquivo criado em caso de erro de inicialização.
- **Verificação (Green):** Teste `tests/test_planner_runner_rollback.py` valida descarte de arquivos órfãos.
- **Construtor Prompt (EN):**
  - Write test first in tests/test_planner_runner_rollback.py. Assert partial project files are deleted when an exception occurs.
  - Implement componentes/compartilhado/skills/aidd-planner/scripts/rollback.py with executar_com_rollback context manager.
  - Run pytest tests/test_planner_runner_rollback.py. Assert exit 0.

### Ticket 6: Output Consolidado e Handoff Criptográfico (Refere-se a D15 / DoD 6)
- **Falha 15-D:** `D15. Output Consolidado e Handoff`
- **Artefato de Handoff:** `componentes/compartilhado/skills/aidd-planner/scripts/handoff.py`
- **Requisito TDD (Red):** Manifesto de blueprint sem assinatura HMAC-SHA256 ou com hash divergente falha na validação.
- **Implementação Técnica:**
  - Implementar `emitir_manifesto` e `verificar_manifesto` em `scripts/handoff.py`.
  - Calcular hash SHA-256 de PLANNER.json e contratos associados, gerando assinatura HMAC-SHA256.
- **Verificação (Green):** Teste `tests/test_planner_runner_assinatura.py` comprova integridade e detecção de adulteração.
- **Construtor Prompt (EN):**
  - Write test first in tests/test_planner_runner_assinatura.py. Assert exit 1 on tampered blueprint files or invalid HMAC signature.
  - Implement componentes/compartilhado/skills/aidd-planner/scripts/handoff.py with emitir_manifesto and verificar_manifesto.
  - Compute SHA-256 across blueprint files and sign with HMAC-SHA256.
  - Run pytest tests/test_planner_runner_assinatura.py. Assert exit 0.
