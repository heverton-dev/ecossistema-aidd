# Plano de Evolução (Fase 2) - aidd-enterprise

Este plano foi gerado pelo Arquiteto (Fase 2) do Pipeline Linear de Auditoria 4F, com o objetivo de readequar a ferramenta `aidd-enterprise` em conformidade com o Laudo 15-D (`LAUDO-15D-INICIAL.md`) e a Definição de Pronto (`DOD.md`).

## Estratégia de Execução
Todos os tickets abaixo requerem ciclo TDD estrito (Red-Green-Refactor). Para cada requisito funcional, testes automatizados (exit 0 / exit 1) devem ser criados antes da implementação real. Toda alteração estrutural deve ser executada com isolamento estrito em Git Worktree efêmera, garantindo as Leis Canônicas do ecossistema.

### Ticket 1: Isolamento de Raio de Impacto e Worktree (Refere-se a D3 / DoD 1)
- **Falha 15-D:** `D3. Raio de Impacto e Isolamento`
- **Artefato de Handoff:** `.agents/skills/aidd-enterprise/scripts/isolamento.py`
- **Requisito TDD (Red):** Teste deve reprovar com exit 1 se a rotina de injeção gravar ou modificar arquivos fora dos diretórios de componentes autorizados ou fora de uma Git Worktree efêmera isolada.
- **Implementação Técnica:**
  - Implementar `.agents/skills/aidd-enterprise/scripts/isolamento.py` com controle estrito de fronteira de diretórios e suporte a execução encapsulada em Git Worktree temporária.
  - Bloquear mutações no repositório root e restringir escrita aos diretórios de destino declarados no manifesto do componente.
- **Verificação (Green):** Teste unitário e de integração passa após garantir que tentativas de escrita fora do escopo são interceptadas e bloqueadas.
- **Construtor Prompt (EN):**
  - Write failing test first: fail with exit 1 when tool writes outside allowed component paths or outside ephemeral Git Worktree.
  - Implement .agents/skills/aidd-enterprise/scripts/isolamento.py to isolate filesystem operations.
  - Enforce boundary checks: reject writes targeting repo root or unlisted directories.
  - Run pytest tests/test_enterprise_isolamento.py. Assert exit 0.

### Ticket 2: Fractalidade, Scripts Locais e CLI Fallback (Refere-se a D4 / DoD 2)
- **Falha 15-D:** `D4. Componentes e Fractalidade`
- **Artefato de Handoff:** `.agents/skills/aidd-enterprise/scripts/cli.py`
- **Requisito TDD (Red):** Executar `python ecossistema.py enterprise inject --help` ou `python .agents/skills/aidd-enterprise/scripts/cli.py` sem implementação de CLI fallback local deve reprovar com exit 1.
- **Implementação Técnica:**
  - Criar `.agents/skills/aidd-enterprise/scripts/cli.py` com interface determinística para injeção e validação de componentes (`inject <type> <name>`, `audit <type> <name>`).
  - Modularizar a skill com scripts locais em Python em vez de depender exclusivamente de prompts conversacionais passivos.
  - Integrar com o roteador de comandos em `ecossistema.py`.
- **Verificação (Green):** CLI executa comandos de injeção e validação com argumentos formais retornando exit 0.
- **Construtor Prompt (EN):**
  - Write failing test first: calling cli fallback with missing implementation must exit 1.
  - Implement .agents/skills/aidd-enterprise/scripts/cli.py with subcommands inject and audit.
  - Support arguments type and name for component types: skill, rule, mcp, spec, config, hook, agent.
  - Wire command routing cleanly to Python modules instead of raw chat prompts.
  - Run pytest tests/test_enterprise_cli.py. Assert exit 0.

### Ticket 3: Processamento Criptográfico e Analítico Determinístico (Refere-se a D8 / DoD 3)
- **Falha 15-D:** `D8. O que o Estágio Processa`
- **Artefato de Handoff:** `.agents/skills/aidd-enterprise/scripts/injetor.py`
- **Requisito TDD (Red):** Testar processador com arquivo de manifesto JSON adulterado ou hash SHA-256 divergente; o teste deve falhar (exit 1).
- **Implementação Técnica:**
  - Desenvolver `.agents/skills/aidd-enterprise/scripts/injetor.py` contendo lógica determinística de cálculo e verificação de hash SHA-256 e validação contra schema JSON (`component_manifest.schema.json`).
  - Rejeitar payloads malformados ou divergências criptográficas sem intervenção subjetiva de LLM.
- **Verificação (Green):** Validador aceita componentes com hash íntegro e rejeita componentes corrompidos com exit 1.
- **Construtor Prompt (EN):**
  - Write failing test first: feed corrupted payload or mismatched SHA-256 hash. Assert exit 1.
  - Implement .agents/skills/aidd-enterprise/scripts/injetor.py.
  - Enforce strict JSON Schema validation against component_manifest.schema.json.
  - Compute and verify SHA-256 checksums deterministically before copying components.
  - Run pytest tests/test_enterprise_injetor.py. Assert exit 0.

### Ticket 4: Orquestração e Topologia Multi-Estágio (Refere-se a D10 / DoD 4)
- **Falha 15-D:** `D10. Orquestração e Topologia`
- **Artefato de Handoff:** `.agents/skills/aidd-enterprise/scripts/orquestrador.py`
- **Requisito TDD (Red):** Executar fluxo pulando etapa de pré-validação ou com estado intermediário corrompido; o teste deve reprovar (exit 1).
- **Implementação Técnica:**
  - Implementar `.agents/skills/aidd-enterprise/scripts/orquestrador.py` estruturando o fluxo em estágios encadeados: Pré-validação -> Snapshot -> Injeção -> Verificação Criptográfica -> Handoff.
  - Persistir o estado da transição em arquivo de estado formal para permitir auditoria de cada estágio.
- **Verificação (Green):** Execução segue topologia multi-estágio sequencial sem permitir queima de etapas.
- **Construtor Prompt (EN):**
  - Write failing test first: simulate skipped prevalidation or corrupted intermediate stage. Assert exit 1.
  - Implement .agents/skills/aidd-enterprise/scripts/orquestrador.py with strict phase pipeline.
  - Chain stages: prevalidation, snapshot, injection, verification, handoff.
  - Persist transition state to structured session file.
  - Run pytest tests/test_enterprise_orquestrador.py. Assert exit 0.

### Ticket 5: Resiliência Operacional e Tratamento de Exceções (Refere-se a D11 / DoD 5)
- **Falha 15-D:** `D11. Tratamento de Exceções e Fallback`
- **Artefato de Handoff:** `.agents/skills/aidd-enterprise/scripts/fallback.py`
- **Requisito TDD (Red):** Simular falha de disco (I/O error) ou bloqueio de permissão de arquivo durante a injeção; teste deve falhar se o sistema abortar sem tratamento gracioso.
- **Implementação Técnica:**
  - Desenvolver `.agents/skills/aidd-enterprise/scripts/fallback.py` fornecendo rotinas de tratamento de exceções, retries com backoff exponencial para operações recuperáveis e registro de diagnóstico em caso de erro terminal.
  - Proteger o estado do repositório evitando travamentos ou arquivos bloqueados.
- **Verificação (Green):** Testes de estresse com falhas simuladas registram o erro estruturado e encerram graciosamente.
- **Construtor Prompt (EN):**
  - Write failing test first: simulate disk IO error or permission lock during injection. Assert abrupt crash.
  - Implement .agents/skills/aidd-enterprise/scripts/fallback.py with graceful error handling.
  - Add retry mechanism with exponential backoff for transient filesystem errors.
  - Safely capture and format fatal errors into diagnostic report without corrupting workspace.
  - Run pytest tests/test_enterprise_fallback.py. Assert exit 0.

### Ticket 6: Observabilidade e Telemetria de Auditoria (Refere-se a D12 / DoD 6)
- **Falha 15-D:** `D12. Observabilidade e Frugalidade`
- **Artefato de Handoff:** `.agents/skills/aidd-enterprise/scripts/observabilidade.py`
- **Requisito TDD (Red):** Executar injeção e verificar ausência de log estruturado de telemetria e latência; o teste de conformidade deve reprovar (exit 1).
- **Implementação Técnica:**
  - Criar `.agents/skills/aidd-enterprise/scripts/observabilidade.py` para gravar telemetria da operação (duração, componentes injetados, contagem de bytes, hashes verificados e eventuais desvios).
  - Persistir relatórios de auditoria estruturados em `secoes/` ou console padronizado.
- **Verificação (Green):** Artefatos de telemetria persistem em `secoes/` com campos padronizados após a conclusão da tarefa.
- **Construtor Prompt (EN):**
  - Write failing test first: verify lack of structured telemetry log after injection. Assert exit 1.
  - Implement .agents/skills/aidd-enterprise/scripts/observabilidade.py.
  - Record execution metrics: start time, end time, duration, component counts, bytes transferred, verified hashes.
  - Persist audit telemetry log to secoes/ directory.
  - Run pytest tests/test_enterprise_observabilidade.py. Assert exit 0.

### Ticket 7: Quality Gate Próprio e Rótulo Honesto (Refere-se a D13 / DoD 7)
- **Falha 15-D:** `D13. Quality Gates (Portões)`
- **Artefato de Handoff:** `gates/G_aidd_enterprise.py`
- **Requisito TDD (Red):** Executar `python gates/G_aidd_enterprise.py` contra componente com hash divergente ou schema inválido; o gate deve obrigatoriamente reprovar com exit 1 (provando que morde).
- **Implementação Técnica:**
  - Desenvolver o Quality Gate determinístico `gates/G_aidd_enterprise.py`.
  - O portão deve verificar integridade dos contratos, aderência dos scripts locais de `.agents/skills/aidd-enterprise/`, conferência de hashes SHA-256 e conformidade com as Leis Canônicas (Lei #1, Lei #5, Lei #8, Lei #13).
  - Incluir teste sintético de quebra para garantir saída binária 1 sob adulteração.
- **Verificação (Green):** `gates/G_aidd_enterprise.py` retorna exit 0 para componentes válidos e exit 1 para violações.
- **Construtor Prompt (EN):**
  - Write failing test first: verify gate bites by feeding tampered component or broken schema. Assert exit 1.
  - Implement gates/G_aidd_enterprise.py as deterministic Quality Gate for aidd-enterprise.
  - Validate component contracts, SHA-256 checksums, and schema adherence.
  - Ensure binary exit code: 0 for compliant components, 1 for any violation.
  - Run pytest tests/test_gate_aidd_enterprise.py. Assert exit 0.

### Ticket 8: Critério de Rejeição, Limpeza e Rollback Automático (Refere-se a D14 / DoD 8)
- **Falha 15-D:** `D14. Critério de Rejeição (Rollback)`
- **Artefato de Handoff:** `.agents/skills/aidd-enterprise/scripts/rollback.py`
- **Requisito TDD (Red):** Injetar falha de validação no meio da injeção do componente; se arquivos parciais sobrarem no destino, o teste deve reprovar (exit 1).
- **Implementação Técnica:**
  - Criar `.agents/skills/aidd-enterprise/scripts/rollback.py` utilizando context managers transacionais ou blocos try/finally.
  - Em caso de falha ou rejeição pelo validador, restaurar snapshot pré-existente ou expurgar arquivos parciais criados durante a transação, mantendo o workspace limpo.
- **Verificação (Green):** Teste de injeção abortada demonstra reversão atômica sem resíduos em disco.
- **Construtor Prompt (EN):**
  - Write failing test first: inject failure mid-transaction. Assert exit 1 if orphan files persist.
  - Implement .agents/skills/aidd-enterprise/scripts/rollback.py with transactional context manager.
  - Create pre-injection snapshot. On error or exit 1, revert modified files and purge partial artifacts.
  - Verify workspace cleanliness after rollback.
  - Run pytest tests/test_enterprise_rollback.py. Assert exit 0.

### Ticket 9: Output Consolidado e Handoff Estruturado (Refere-se a D15 / DoD 9)
- **Falha 15-D:** `D15. Output Consolidado e Handoff`
- **Artefato de Handoff:** `docs/teste-end-to-end/aidd-enterprise.md`
- **Requisito TDD (Red):** Executar fluxo completo de injeção e verificar ausência do manifesto formal `handoff-enterprise.json`; o teste deve reprovar.
- **Implementação Técnica:**
  - Ao final do fluxo de injeção bem-sucedido, gerar o arquivo de handoff estruturado `./handoff-enterprise.json` com metadados, lista de componentes e hashes SHA-256.
  - Produzir o relatório de ciclo de 5 passos em `docs/teste-end-to-end/aidd-enterprise.md`.
  - Registrar justificativa técnica de dispensa do Quarteto Sine Qua Non (ferramenta CLI de infraestrutura interna sem rotas HTTP/servidor vivo).
- **Verificação (Green):** Handoff emitido e validado, permitindo o avanço determinístico de pipeline.
- **Construtor Prompt (EN):**
  - Write failing test first: run end-to-end flow and assert failure when handoff-enterprise.json is missing.
  - Emit structured handoff-enterprise.json at end of successful injection.
  - Document 5-step verification cycle in docs/teste-end-to-end/aidd-enterprise.md.
  - Include justification that aidd-enterprise is internal CLI tool without HTTP web UI or server routes.
  - Run pytest tests/test_enterprise_handoff.py. Assert exit 0.
