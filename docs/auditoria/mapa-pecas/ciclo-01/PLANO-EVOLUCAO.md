# Plano de Evolução (Fase 2) - mapa-pecas

Este plano foi gerado pelo Arquiteto (Fase 2) do Pipeline Linear de Auditoria 4F, com o objetivo de readequar o subsistema `mapa-pecas` e sanear os 34 achados críticos mapeados através do framework Lens 15-D.

## Estratégia de Execução
Todos os tickets abaixo requerem ciclo TDD estrito (Red-Green-Refactor). Para cada requisito funcional, testes automatizados (exit 0 / exit 1) devem comprovar a resolução dos achados catalogados em `docs/auditoria/mapa-pecas/ciclo-01/ACHADOS.json`.

### Ticket 1: Integridade de Portões e Leis Fundamentais (Refere-se a D1 / DoD 6)
- **Falha 15-D:** `D1. Contratos e Regras`
- **Artefato de Handoff:** `docs/auditoria/mapa-pecas/ciclo-01/ENTREGA-TICKET-01.json`
- **Requisito TDD (Red):** Executar verificação determinística que falha (exit 1) quando houver comentários inline no AGENTS.md impedindo leitura pelo meta-guarda ou gates com corrida de concorrência.
- **Implementação Técnica:**
  - Corrigir declarações no AGENTS.md para que G_LEI_DECLARA_PORTAO identifique todos os portões de forma consistente.
  - Ajustar G_CONTRACT_ROT para evitar falsos positivos quando contratos não puderem ser inspecionados.
  - Corrigir condição de corrida concorrente nos testes de G_PORTAO_PROVA_QUE_MORDE.
  - Sincronizar versões divergentes de guardas homônimos.
- **Verificação (Green):** Executar auditoria de leis e portões com sucesso (exit 0).
- **Construtor Prompt (EN):**
  - Inspect AGENTS.md law declarations and G_LEI_DECLARA_PORTAO logic.
  - Fix inline comments after proved markers to make all declarations visible.
  - Fix G_CONTRACT_ROT to strictly fail instead of passing when contract check fails.
  - Fix concurrency race condition in tests for G_PORTAO_PROVA_QUE_MORDE.
  - Sync divergent guard codes between root gates and tool subdirectories.
  - Run pytest on affected gate tests. Assert exit 0.
  - Write handoff json to docs/auditoria/mapa-pecas/ciclo-01/ENTREGA-TICKET-01.json.

### Ticket 2: Correção de Encaixes de Pipeline e CLI (Refere-se a D10 / DoD 1)
- **Falha 15-D:** `D10. Orquestração e Topologia`
- **Artefato de Handoff:** `docs/auditoria/mapa-pecas/ciclo-01/ENTREGA-TICKET-02.json`
- **Requisito TDD (Red):** Testes de integração de encaixes devem reprovar (exit 1) para comandos `bridge scan` e `factory curate` com parâmetros incompatíveis.
- **Implementação Técnica:**
  - Ajustar orquestrador síncrono para despachar parâmetros corretos para bridge scan e factory curate.
  - Conectar etapas 6 (ops) e 7 (auditoria) a ferramentas reais do ecossistema.
  - Garantir que a etapa 7 execute portões de qualidade reais antes de atribuir conformidade.
  - Fornecer PLANO-INFRAESTRUTURA.json exigido pela etapa 3 do Fluxo 02.
  - Assegurar que flag --dry-run não realize operações de escrita em disco.
- **Verificação (Green):** Catálogo de peças registra zero incompatibilidades de encaixe nas chamadas.
- **Construtor Prompt (EN):**
  - Fix orchestrator recipe calls for bridge scan and factory curate to match accepted tool CLI args.
  - Wire step 06 ops and step 07 audit to invoke real tools and gates.
  - Prevent step 07 from recording 100 percent compliance without executing quality gates.
  - Supply required PLANO-INFRAESTRUTURA.json in step 03 of Flow 02 before factory run.
  - Ensure dry run flag never writes README-USUARIO.md to disk.
  - Replace internal imports in step 02 planner and step 03 engine with public tool interfaces.
  - Run tests on pipeline orchestration. Assert exit 0.
  - Write handoff json to docs/auditoria/mapa-pecas/ciclo-01/ENTREGA-TICKET-02.json.

### Ticket 3: Resiliência de Hooks, Handoff e Testes Quebrados (Refere-se a D11 / DoD 4)
- **Falha 15-D:** `D11. Tratamento de Exceções e Fallback`
- **Artefato de Handoff:** `docs/auditoria/mapa-pecas/ciclo-01/ENTREGA-TICKET-03.json`
- **Requisito TDD (Red):** Testes unitários falhando em aidd-orca e aidd-improvement devem ser isolados e consertados para atingir exit 0.
- **Implementação Técnica:**
  - Corrigir os 6 testes quebrando em tools/aidd-orca.
  - Corrigir os 2 testes quebrando em tools/aidd-improvement.
  - Corrigir verificação de assinatura e hash em G_HANDOFF_MELHORIA.py.
  - Garantir que hook .githooks/pre-commit forneça mensagem de erro legível ao desenvolvedor em caso de falha.
  - Corrigir template de AGENTS.md no aidd-forge e remover geração legada de .agent/.
  - Sanitizar caminhos absolutos locais gerados por detect-secrets em .secrets.baseline.
- **Verificação (Green):** Bateria de testes de tools/aidd-orca e tools/aidd-improvement executa com 100% de aprovação.
- **Construtor Prompt (EN):**
  - Fix 6 failing tests in tools/aidd-orca.
  - Fix 2 failing tests in tools/aidd-improvement.
  - Fix G_HANDOFF_MELHORIA validation against versioned handoff manifest.
  - Enhance pre commit hook to output clear error message on failure.
  - Update aidd-forge templates and remove legacy agent directory creation.
  - Sanitize absolute machine paths in secrets baseline.
  - Run pytest on fixed suites. Assert exit 0.
  - Write handoff json to docs/auditoria/mapa-pecas/ciclo-01/ENTREGA-TICKET-03.json.

### Ticket 4: Higienização de Skills, Comandos e Fontes Únicas (Refere-se a D4 / DoD 1)
- **Falha 15-D:** `D4. Componentes e Fractalidade`
- **Artefato de Handoff:** `docs/auditoria/mapa-pecas/ciclo-01/ENTREGA-TICKET-04.json`
- **Requisito TDD (Red):** Script de verificação de skills deve falhar (exit 1) quando existirem referências de comandos inválidos ou sync reverso de harnesses.
- **Implementação Técnica:**
  - Garantir que o sync de componentes seja estritamente unidirecional (fonte componentes/ para os harnesses), eliminando sync reverso.
  - Resolver skills duplicadas e unificar convenção de nomenclatura.
  - Corrigir comandos slash /aidd-livro-texto e /planner para mapear para skills válidas existentes.
  - Remover pasta legada .gemini/skills.
  - Limpar MCPs internos não utilizados por nenhum agente.
- **Verificação (Green):** python ecossistema.py components verify e verificação de skills executam com exit 0.
- **Construtor Prompt (EN):**
  - Ensure component sync is strictly one way from source to harnesses.
  - Clean duplicated skills and harmonize naming conventions in single source.
  - Fix slash command mappings for book generation and planner skills.
  - Remove legacy .gemini/skills directory.
  - Clean or mark unused internal MCP definitions.
  - Run component verification. Assert exit 0.
  - Write handoff json to docs/auditoria/mapa-pecas/ciclo-01/ENTREGA-TICKET-04.json.

### Ticket 5: Deduplicação de Artefatos, Moldes e Scripts Órfãos (Refere-se a D12 / DoD 5)
- **Falha 15-D:** `D12. Observabilidade e Frugalidade`
- **Artefato de Handoff:** `docs/auditoria/mapa-pecas/ciclo-01/ENTREGA-TICKET-05.json`
- **Requisito TDD (Red):** Teste de verificação de integridade de código acusa duplicação redundante entre ferramentas.
- **Implementação Técnica:**
  - Consolidar arquivos utilitários idênticos compartilhados entre ferramentas sob componentes ou módulos comuns.
  - Padronizar moldes de artefatos de entrega e eliminar cópias divergentes.
  - Remover ou conectar scripts utilitários órfãos em scripts/.
  - Unificar verbos repetidos na CLI para evitar ambiguidade de subcomandos.
- **Verificação (Green):** Catálogo mede redução substancial de arquivos redundantes e zero scripts órfãos.
- **Construtor Prompt (EN):**
  - Review 100 identical files across tools and consolidate shared logic where possible.
  - Unify delivery templates across tools into canonical shared molds.
  - Link or clean orphan scripts in scripts directory.
  - Harmonize CLI command verbs across tools.
  - Run repository sanity checks. Assert exit 0.
  - Write handoff json to docs/auditoria/mapa-pecas/ciclo-01/ENTREGA-TICKET-05.json.

### Ticket 6: Quality Gate e Rótulo Honesto do Mapa de Peças (Refere-se a D14 / DoD 6)
- **Falha 15-D:** `D14. Critério de Rejeição (Rollback)`
- **Artefato de Handoff:** `gates/G_mapa_pecas.py`
- **Requisito TDD (Red):** Executar teste do portão G_mapa_pecas.py com catálogo inconsistente ou documento ausente; o portão deve reprovar com exit 1 (provando que morde).
- **Implementação Técnica:**
  - Criar `gates/G_mapa_pecas.py` que audita a integridade do catálogo de peças e mapas visuais.
  - Criar teste automatizado `tests/test_g_mapa_pecas.py` validando o portão tanto no caso válido (exit 0) quanto sob violação sintética (exit 1) atendendo à Lei #13.
  - Completar a documentação canônica dos ciclos mapa-pecas/ciclo-01 e skills-pocock/ciclo-01.
- **Verificação (Green):** `python gates/G_mapa_pecas.py` retorna exit 0 e o teste unitário passa com exit 0.
- **Construtor Prompt (EN):**
  - Implement quality gate gates/G_mapa_pecas.py verifying parts catalog and visual maps integrity.
  - Implement tests/test_g_mapa_pecas.py proving gate bites with exit 1 on corrupted catalog and passes with exit 0.
  - Ensure canonical audit cycle documents exist for mapa-pecas and skills-pocock.
  - Run pytest on tests/test_g_mapa_pecas.py. Assert exit 0.
  - Deliver gates/G_mapa_pecas.py.
