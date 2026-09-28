# Plano de Evolução (Fase 2) - aidd-forge

Este plano foi gerado pelo Arquiteto (Fase 2) do Pipeline Linear de Auditoria 4F, com o objetivo de readequar a ferramenta `aidd-forge` em conformidade com o Laudo 15-D e a Definição de Pronto (DoD).

## Estratégia de Execução
Todos os tickets abaixo requerem ciclo TDD estrito (Red-Green-Refactor) e isolamento em Git Worktree efêmera. Para cada requisito funcional, testes automatizados (exit 0 / exit 1) devem ser criados antes da implementação real.

### Ticket 1: Isolamento de Raio de Impacto e Worktree (Refere-se a D3 / DoD 2)
- **Falha 15-D:** `D3. Raio de Impacto e Isolamento`
- **Artefato de Handoff:** `.agents/skills/aidd-forge/scripts/isolamento.py`
- **Requisito TDD (Red):** Criar um teste que reprove (exit 1) se a ferramenta tentar modificar arquivos fora da pasta alvo permitida ou fora de uma Git Worktree efêmera isolada.
- **Implementação Técnica:**
  - Codificar rotina na infraestrutura da skill (`.agents/skills/aidd-forge/scripts/isolamento.py`) para validar limites de escrita e isolar execuções de bootstrap de governança em Git Worktree ou diretório alvo validado.
  - Bloquear acessos de I/O de escrita no repositório root a partir de invocações da skill sem alvo explícito ou sem worktree efêmera.
- **Verificação (Green):** Teste de ambiente passa (exit 0) após garantir o isolamento e sandboxing de execução.
- **Construtor Prompt (EN):**
  - Write failing test first: assert exit 1 when tool writes outside target directory or outside isolated worktree.
  - Implement .agents/skills/aidd-forge/scripts/isolamento.py to enforce strict path confinement.
  - Guard file system writes so target repo boundaries cannot be exceeded.
  - Run tests/test_forge_isolamento.py. Assert exit 0.

### Ticket 2: Componentes, Fractalidade e CLI Fallback (Refere-se a D4 / DoD 1)
- **Falha 15-D:** `D4. Componentes e Fractalidade`
- **Artefato de Handoff:** `.agents/skills/aidd-forge/scripts/cli.py`
- **Requisito TDD (Red):** Executar invocação CLI com parâmetros inválidos ou sem manifesto determinístico deve falhar (exit 1) por falta de fallback local.
- **Implementação Técnica:**
  - Estruturar a skill com scripts modulares locais em Python (`.agents/skills/aidd-forge/scripts/cli.py`) em vez de depender apenas de prompts de chat no `.agents`.
  - Integrar a interface CLI `ecossistema.py forge init [path]` e comandos da skill mapeando a entrada para acionar os scripts locais determinísticos da ferramenta.
- **Verificação (Green):** Execução do CLI retorna sucesso e processa os comandos e parâmetros adequadamente.
- **Construtor Prompt (EN):**
  - Write test first: verify CLI fails with exit 1 on missing parameters or unhandled input.
  - Implement .agents/skills/aidd-forge/scripts/cli.py to provide deterministic CLI entrypoint.
  - Connect ecossistema.py forge commands directly to local scripts instead of pure prompt interpretation.
  - Run tests/test_forge_cli.py. Assert exit 0.

### Ticket 3: Motor de Processamento e Bootstrap Determinístico (Refere-se a D8 / DoD 3)
- **Falha 15-D:** `D8. O que o Estágio Processa`
- **Artefato de Handoff:** `.agents/skills/aidd-forge/scripts/bootstrap.py`
- **Requisito TDD (Red):** Testar parser e validador do motor de injeção fornecendo payload malformado ou texto livre para confirmar crash esperado (exit 1).
- **Implementação Técnica:**
  - Substituir o processamento dependente de chat por motor determinístico interno em `.agents/skills/aidd-forge/scripts/bootstrap.py`.
  - Envelopar toda parametrização e renderização de templates em JSON Schema estrito, rejeitando entradas malformadas e validando integridade de governança via AST e checagens estáticas.
- **Verificação (Green):** O bootstrap determinístico executa e valida esquemas estruturados retornando exit 0.
- **Construtor Prompt (EN):**
  - Write test first: pass invalid bootstrap payload or unstructured input. Assert exit 1.
  - Implement .agents/skills/aidd-forge/scripts/bootstrap.py with strict schema validation.
  - Enforce deterministic template rendering and injection checks.
  - Run tests/test_forge_bootstrap.py. Assert exit 0.

### Ticket 4: Orquestração Multi-estágio e Topologia de Injeção (Refere-se a D10)
- **Falha 15-D:** `D10. Orquestração e Topologia`
- **Artefato de Handoff:** `.agents/skills/aidd-forge/scripts/orquestracao.py`
- **Requisito TDD (Red):** Injetar quebra ou desordem no estágio intermediário; o teste deve assinalar falha controlada (exit 1).
- **Implementação Técnica:**
  - Implementar pipeline encadeado de estágios em `.agents/skills/aidd-forge/scripts/orquestracao.py`: 1) Validação prévia de ambiente alvo, 2) Injeção de governança, 3) Verificação de integridade pós-injeção.
  - Persistir e validar transporte formal de estado e integridade de dados entre cada estágio.
- **Verificação (Green):** Fluxo multi-estágio executa sequencialmente com validação de estado e retorna exit 0.
- **Construtor Prompt (EN):**
  - Write test first: corrupt intermediate stage state. Assert pipeline aborts with exit 1.
  - Implement .agents/skills/aidd-forge/scripts/orquestracao.py defining sequential staged pipeline.
  - Enforce stage state transitions: pre-validation, injection, post-verification.
  - Run tests/test_forge_orquestracao.py. Assert exit 0.

### Ticket 5: Resiliência Operacional e Tratamento de Exceções (Refere-se a D11 / DoD 4)
- **Falha 15-D:** `D11. Tratamento de Exceções e Fallback`
- **Artefato de Handoff:** `.agents/skills/aidd-forge/scripts/resiliencia.py`
- **Requisito TDD (Red):** Simular falha de permissão de I/O em disco ou lock de git; o sistema deve propagar erro abrupto sem tratamento de fallback no estado atual.
- **Implementação Técnica:**
  - Implementar `.agents/skills/aidd-forge/scripts/resiliencia.py` com mecanismo de retry com backoff exponencial e tratamento estruturado de falhas operacionais.
  - Criar rotinas elegantes de captura e interrupção segura documentando a falha sem perder o estado de auditoria.
- **Verificação (Green):** Testes de estresse comprovam execução de retries e tratamento gracioso de falhas com exit codes apropriados.
- **Construtor Prompt (EN):**
  - Write test first: simulate IO permission error or lock failure. Current code must fail abruptly.
  - Implement .agents/skills/aidd-forge/scripts/resiliencia.py with exponential backoff and error handlers.
  - Handle transient git lock and permission exceptions gracefully.
  - Run tests/test_forge_resiliencia.py. Assert exit 0 and retry mechanisms verified.

### Ticket 6: Observabilidade e Telemetria Frugal (Refere-se a D12 / DoD 5)
- **Falha 15-D:** `D12. Observabilidade e Frugalidade`
- **Artefato de Handoff:** `.agents/skills/aidd-forge/scripts/observabilidade.py`
- **Requisito TDD (Red):** Testar a ausência de persistência de telemetria ou emissão de métricas pós-execução (falha esperada de conformidade com exit 1).
- **Implementação Técnica:**
  - Implementar `.agents/skills/aidd-forge/scripts/observabilidade.py` para instrumentar medição de tempos de execução, artefatos injetados e métricas de consumo frugal.
  - O log deverá ser padronizado e gravado em `secoes/` ou impresso no console durante a execução via CLI.
- **Verificação (Green):** Artefatos de log estruturado persistem com os metadados exigidos ao término da execução.
- **Construtor Prompt (EN):**
  - Write test first: assert failure when run does not emit structured execution metrics.
  - Implement .agents/skills/aidd-forge/scripts/observabilidade.py recording duration and injected artifacts.
  - Write structured JSON log to secoes/ or stdout.
  - Run tests/test_forge_observabilidade.py. Assert exit 0.

### Ticket 7: Quality Gates Determinísticos e Rótulo Honesto (Refere-se a D13 / DoD 6)
- **Falha 15-D:** `D13. Quality Gates (Portões)`
- **Artefato de Handoff:** `gates/G_aidd_forge.py`
- **Requisito TDD (Red):** Submeter diretório alvo onde faltem arquivos essenciais de governança ou onde haja stubs/afirmações ilusórias; `gates/G_aidd_forge.py` deve falhar (exit 1).
- **Implementação Técnica:**
  - Desenvolver o Quality Gate determinístico `gates/G_aidd_forge.py` provando que morde (Lei #8 e Lei #13) contra ausência de governança, templates corrompidos ou stubs.
  - Validar saída e conformidade estrutural completa da ferramenta `aidd-forge`.
- **Verificação (Green):** `gates/G_aidd_forge.py` passa (exit 0) sobre repositórios adequadamente blindados e barra com exit 1 violações reais.
- **Construtor Prompt (EN):**
  - Write test first: create incomplete forge bootstrap target. gates/G_aidd_forge.py must exit 1.
  - Implement gates/G_aidd_forge.py validating governance files and absence of stubs.
  - Enforce Lei 8 and Lei 13 with deterministic AST and file checks.
  - Run python gates/G_aidd_forge.py. Assert exit 0 on compliant target and exit 1 on incomplete target.

### Ticket 8: Critério de Rejeição, Limpeza e Rollback Automático (Refere-se a D14 / DoD 7)
- **Falha 15-D:** `D14. Critério de Rejeição (Rollback)`
- **Artefato de Handoff:** `.agents/skills/aidd-forge/scripts/rollback.py`
- **Requisito TDD (Red):** Injetar um erro no meio da injeção de arquivos; se sobrarem arquivos temporários ou corrompidos em disco, o teste deve reprovar (exit 1).
- **Implementação Técnica:**
  - Estabelecer rotina `finally` ou context manager em `.agents/skills/aidd-forge/scripts/rollback.py`.
  - Em caso de saída não-zero (`exit 1`) ou crash, o código DEVE excluir artefatos parciais e reverter modificações para o estado limpo anterior.
- **Verificação (Green):** O crash no meio do processo deixa zero rastro temporário ou corrupção no repositório.
- **Construtor Prompt (EN):**
  - Write test first: inject failure mid-bootstrap. Fail if orphaned files remain on disk.
  - Implement .agents/skills/aidd-forge/scripts/rollback.py using transactional cleanup handlers.
  - Revert written files and restore clean target directory state upon failure.
  - Run tests/test_forge_rollback.py. Assert exit 0 and zero residual files.

### Ticket 9: Output Consolidado e Handoff Estruturado (Refere-se a D15 / DoD 8)
- **Falha 15-D:** `D15. Output Consolidado e Handoff`
- **Artefato de Handoff:** `docs/teste-end-to-end/aidd-forge.md`
- **Requisito TDD (Red):** Testar pipeline com execução completa e checar ausência do `./handoff-forge.json`; deve falhar a barreira de saída (exit 1).
- **Implementação Técnica:**
  - Alterar o final da execução da skill para produzir e assinar estruturadamente o artefato `./handoff-forge.json`, relatando inventário com hashes SHA-256 dos componentes de governança injetados, habilitando consumo por `aidd-planner`.
  - Elaborar ou atualizar `docs/teste-end-to-end/aidd-forge.md` comprovando o fluxo (Ciclo de 5 passos do protocolo de testes).
  - Incluir no laudo a justificativa técnica obrigatória de que `aidd-forge` não terá Quarteto Sine Qua Non por ser ferramenta CLI de bootstrap sem servidor/UI persistente.
- **Verificação (Green):** `handoff-forge.json` emitido corretamente e documento de teste end-to-end validado.
- **Construtor Prompt (EN):**
  - Write test first: complete bootstrap without ./handoff-forge.json. Assert exit 1.
  - Emit structured ./handoff-forge.json with SHA-256 component hashes for aidd-planner handoff.
  - Create or update docs/teste-end-to-end/aidd-forge.md proving 5-step cycle.
  - Document Quarteto Sine Qua Non exemption for forge CLI tool in report.
  - Run tests/test_forge_handoff.py. Assert exit 0.
