# Plano de Evolução (Fase 2) - aidd-plan

Este plano foi gerado pelo Arquiteto (Fase 2) do Pipeline Linear de Auditoria 4F, com o objetivo de readequar a ferramenta `aidd-plan` em conformidade com o Laudo 15-D e a Definição de Pronto (DoD).

## Estratégia de Execução
Todos os tickets abaixo requerem ciclo TDD estrito (Red-Green-Refactor). Para cada requisito funcional, testes automatizados (exit 0 / exit 1) devem ser criados antes da implementação real.

### Ticket 1: Contrato Programático e Regras do Ciclo de Vida (Refere-se a D1 / DoD 1)
- **Falha 15-D:** `D1. Contratos e Regras`
- **Artefato de Handoff:** `componentes/compartilhado/skills/aidd-plan/scripts/contrato.py`
- **Requisito TDD (Red):** Teste reprova com exit 1 quando transição de status inválida ou aprovação sem evidência é forçada.
- **Implementação Técnica:**
  - Criar asserções canônicas em `contrato.py`: validação de status de itens (DRAFT, APROVADO, EM EXECUCAO).
  - Validar que notas numéricas exigem caminho de evidência válido ou rótulo NAO AUDITADO.
- **Verificação (Green):** Teste `tests/test_plan_contrato.py` passa validando todas as invariantes contratuais.
- **Construtor Prompt (EN):**
  - Write test first in tests/test_plan_contrato.py. Assert exit 1 when status transition is invalid or grade lacks evidence.
  - Implement componentes/compartilhado/skills/aidd-plan/scripts/contrato.py with status lifecycle assertions and grade validation.
  - Enforce explicit evidence path requirement.
  - Run pytest tests/test_plan_contrato.py. Assert exit 0.

### Ticket 2: Isolamento de Raio de Impacto e Sandbox (Refere-se a D3 / DoD 2)
- **Falha 15-D:** `D3. Raio de Impacto e Isolamento`
- **Artefato de Handoff:** `componentes/compartilhado/skills/aidd-plan/scripts/isolamento.py`
- **Requisito TDD (Red):** Teste reprova com exit 1 quando tentativa de escrita ocorre fora de docs/planos/ ou de diretório temporário.
- **Implementação Técnica:**
  - Criar `PlanWorktreeManager` e `validar_caminho_escrita`.
  - Bloquear acessos de I/O de escrita no repositório fora de `docs/planos/`.
- **Verificação (Green):** Teste `tests/test_plan_isolamento.py` passa comprovando isolamento estrito de escrita.
- **Construtor Prompt (EN):**
  - Write test first in tests/test_plan_isolamento.py. Assert exit 1 when writing outside docs/planos/ or outside sandbox.
  - Implement componentes/compartilhado/skills/aidd-plan/scripts/isolamento.py with PlanWorktreeManager and validar_caminho_escrita.
  - Block write I/O on unauthorized directories. Allow only docs/planos/.
  - Run pytest tests/test_plan_isolamento.py. Assert exit 0.

### Ticket 3: Modularização e CLI Local (Refere-se a D4 / DoD 3)
- **Falha 15-D:** `D4. Componentes e Fractalidade`
- **Artefato de Handoff:** `componentes/compartilhado/skills/aidd-plan/scripts/cli.py`
- **Requisito TDD (Red):** Executar cli.py sem argumentos ou com subcomando inválido falha com exit 1.
- **Implementação Técnica:**
  - Implementar roteador de comandos em `componentes/compartilhado/skills/aidd-plan/scripts/cli.py` suportando `init`, `check-fences`, `aprovar`, `iniciar-execucao`, `ler-nota` e `atualizar-nota`.
  - Integrar com a biblioteca central desacoplando da raiz do repositório.
- **Verificação (Green):** Teste `tests/test_plan_cli.py` passa validando todos os subcomandos e saídas da CLI.
- **Construtor Prompt (EN):**
  - Write test first in tests/test_plan_cli.py. Assert exit 1 on missing arguments or invalid subcommands.
  - Implement componentes/compartilhado/skills/aidd-plan/scripts/cli.py with subcommands init, check-fences, aprovar, iniciar-execucao, ler-nota, atualizar-nota.
  - Wire CLI arguments to deterministic handlers.
  - Run pytest tests/test_plan_cli.py. Assert exit 0.

### Ticket 4: Tratamento de Exceções e Resolução de Conflitos (Refere-se a D11 / DoD 4)
- **Falha 15-D:** `D11. Tratamento de Exceções e Fallback`
- **Artefato de Handoff:** `componentes/compartilhado/skills/aidd-plan/scripts/fallback.py`
- **Requisito TDD (Red):** Colisão de pasta existente ou cerca de código aninhada sem tratamento falha com exit 1.
- **Implementação Técnica:**
  - Implementar detector de colisão de pastas com resolução de sufixo ou reuso seguro.
  - Implementar correção e normalização automática de cercas Markdown aninhadas (`~~~`).
- **Verificação (Green):** Teste `tests/test_plan_fallback.py` valida tratamento resiliente de erros.
- **Construtor Prompt (EN):**
  - Write test first in tests/test_plan_fallback.py. Assert safe handling of directory collisions and malformed markdown fences.
  - Implement componentes/compartilhado/skills/aidd-plan/scripts/fallback.py with folder collision resolution and fence repair.
  - Ensure graceful degradation without unhandled exceptions.
  - Run pytest tests/test_plan_fallback.py. Assert exit 0.

### Ticket 5: Observabilidade e Métricas de Plano (Refere-se a D12 / DoD 5)
- **Falha 15-D:** `D12. Observabilidade e Frugalidade`
- **Artefato de Handoff:** `componentes/compartilhado/skills/aidd-plan/scripts/observabilidade.py`
- **Requisito TDD (Red):** Teste reprova se telemetria de plano gerado não calcular itens, tokens estimados e notas.
- **Implementação Técnica:**
  - Implementar classe `RastreadorPlano` para inspecionar diretórios de plano em `docs/planos/`.
  - Computar contagem de itens, total de linhas, estimativa de tokens consumidos e status das notas.
- **Verificação (Green):** Teste `tests/test_plan_observabilidade.py` valida métricas e exportação de telemetria.
- **Construtor Prompt (EN):**
  - Write test first in tests/test_plan_observabilidade.py. Assert calculation of item count, total lines, estimated tokens, and grade distribution.
  - Implement componentes/compartilhado/skills/aidd-plan/scripts/observabilidade.py with RastreadorPlano class.
  - Export structured plan telemetry dictionary.
  - Run pytest tests/test_plan_observabilidade.py. Assert exit 0.

### Ticket 6: Quality Gate de Repositório para Planos (Refere-se a D13 / DoD 6)
- **Falha 15-D:** `D13. Quality Gates (Portões)`
- **Artefato de Handoff:** `gates/G_aidd_plan.py`
- **Requisito TDD (Red):** Gate reprova com exit 1 pasta de plano sem 00-PROCESSO-E-DECISOES.md, com cercas quebradas ou nota sem evidência.
- **Implementação Técnica:**
  - Implementar `gates/G_aidd_plan.py` que inspeciona pastas de planos sob `docs/planos/`.
  - Validar presença de arquivo de processo, integridade de cercas e regras de notas.
- **Verificação (Green):** Teste `gates/test_g_aidd_plan.py` passa comprovando retorno estrito exit 0 / exit 1.
- **Construtor Prompt (EN):**
  - Write test first in gates/test_g_aidd_plan.py. Assert exit 1 on missing process file, unclosed fences, or grades without evidence. Assert exit 0 on clean plan.
  - Implement gates/G_aidd_plan.py adhering to Binary Gate Law (pure exit 0 / exit 1).
  - Inspect plan folders and validate all mandatory rules.
  - Run pytest gates/test_g_aidd_plan.py. Assert exit 0.

### Ticket 7: Critério de Rejeição e Rollback Automático (Refere-se a D14 / DoD 7)
- **Falha 15-D:** `D14. Critério de Rejeição (Rollback)`
- **Artefato de Handoff:** `componentes/compartilhado/skills/aidd-plan/scripts/rollback.py`
- **Requisito TDD (Red):** Teste reprova se exceção durante criação de plano deixar pastas ou arquivos parciais órfãos.
- **Implementação Técnica:**
  - Implementar gerenciador de contexto `executar_com_rollback` em `scripts/rollback.py`.
  - Rastrear caminhos criados e remover automaticamente qualquer pasta ou arquivo parcial em caso de falha.
- **Verificação (Green):** Teste `tests/test_plan_rollback.py` valida descarte de resíduos em cenários de erro.
- **Construtor Prompt (EN):**
  - Write test first in tests/test_plan_rollback.py. Assert partial plan folders are deleted when an exception occurs.
  - Implement componentes/compartilhado/skills/aidd-plan/scripts/rollback.py with executar_com_rollback context manager.
  - Track created files and clean up upon exception.
  - Run pytest tests/test_plan_rollback.py. Assert exit 0.

### Ticket 8: Output Consolidado e Handoff Criptográfico (Refere-se a D15 / DoD 8)
- **Falha 15-D:** `D15. Output Consolidado e Handoff`
- **Artefato de Handoff:** `componentes/compartilhado/skills/aidd-plan/scripts/handoff.py`
- **Requisito TDD (Red):** Manifesto de plano sem assinatura HMAC-SHA256 ou com hash de conteúdo divergente falha na validação.
- **Implementação Técnica:**
  - Implementar `emitir_manifesto` e `verificar_manifesto` em `scripts/handoff.py`.
  - Calcular hash SHA-256 de todos os arquivos do plano e gerar assinatura HMAC-SHA256.
- **Verificação (Green):** Teste `tests/test_plan_assinatura.py` comprova integridade e detecção de adulteração.
- **Construtor Prompt (EN):**
  - Write test first in tests/test_plan_assinatura.py. Assert exit 1 on tampered plan files or invalid HMAC signature.
  - Implement componentes/compartilhado/skills/aidd-plan/scripts/handoff.py with emitir_manifesto and verificar_manifesto.
  - Compute SHA-256 hash across plan files and sign with HMAC-SHA256.
  - Run pytest tests/test_plan_assinatura.py. Assert exit 0.
