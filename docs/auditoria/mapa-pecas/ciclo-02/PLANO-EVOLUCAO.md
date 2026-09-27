# Plano de Evolução (Fase 2) - mapa-pecas (Ciclo 02)

Este plano foi gerado pelo Arquiteto (Fase 2) do Pipeline Linear de Auditoria 4F para o subsistema `mapa-pecas` (Ciclo 02), com o objetivo de sanear os 12 achados catalogados em `docs/auditoria/mapa-pecas/ciclo-01/ACHADOS.json` através do framework Lens 15-D.

## Estratégia de Execução
Todos os tickets abaixo seguem ciclo TDD estrito e conferência determinística. Cada ticket aborda um agrupamento funcional dos achados de catálogo com evidência verificável e handoff estruturado.

### Ticket 1: Harmonização de Leis, Guardas e Pre-Commit (Refere-se a D1 / DoD 6)
- **Falha 15-D:** `D1. Contratos e Regras`
- **Artefato de Handoff:** `docs/auditoria/mapa-pecas/ciclo-02/ENTREGA-TICKET-01.json`
- **Requisito TDD (Red):** Testes determinísticos devem reprovar se guardas declarados em leis não estiverem registrados no pre-commit, se guardas da raiz não tiverem amarração legal em AGENTS.md ou se houver guardas homônimos divergentes.
- **Implementação Técnica:**
  - Adicionar os 8 guardas declarados em leis ao `.pre-commit-config.yaml` (`G_DISPATCH_PIPELINE_VSA`, `G_GESTOR_SESSOES`, `G_mapa_pecas`, `G_TEMPLATE_FORGE_ROT`, `G_amelhoria`, `G_aidd_diagnose`, `G_HANDOFF_MELHORIA`, `G_DOCS_ROT`).
  - Amarrar os 22 guardas da raiz às suas respectivas Leis no `AGENTS.md`.
  - Sincronizar as versões divergentes dos 11 guardas homônimos entre ferramentas e a raiz.
  - Atualizar o baseline de segredos e hashes se necessário.
- **Verificação (Green):** Executar auditoria de leis e portões com 100% de conformidade (exit 0).
- **Construtor Prompt (EN):**
  - Read AGENTS.md and .pre-commit-config.yaml to inspect all declared gates.
  - Add missing law declared gates to .pre-commit-config.yaml hooks.
  - Link root gates to their corresponding laws in AGENTS.md section 2.
  - Synchronize duplicate gate files across tool templates with root gates.
  - Fix any failing gate assertions in G_amelhoria and G_HANDOFF_MELHORIA.
  - Run pytest on gate test suites. Assert exit 0.
  - Write handoff json to docs/auditoria/mapa-pecas/ciclo-02/ENTREGA-TICKET-01.json.

### Ticket 2: Desacoplamento de Encaixes e Remoção de Atalhos Internos (Refere-se a D10 / DoD 1)
- **Falha 15-D:** `D10. Orquestração e Topologia`
- **Artefato de Handoff:** `docs/auditoria/mapa-pecas/ciclo-02/ENTREGA-TICKET-02.json`
- **Requisito TDD (Red):** Catálogo de peças deve apontar zero atalhos internos em etapas da receita e zero scripts órfãos sem chamador.
- **Implementação Técnica:**
  - Refatorar `etapa_02_planner` em `scripts/orquestrador_sincrono.py` para usar CLI/interface pública do `aidd-planner`.
  - Refatorar `etapa_03_engine` em `scripts/orquestrador_sincrono.py` para despachar fatias VSA via comando canônico `ecossistema.py dispatch`.
  - Conectar os 3 scripts sem chamador (`gerador_relatorio_evolucao_planos`, `gerador_templates_gates`, `gerar_chave_manifesto`) como comandos ou utilitários registrados.
- **Verificação (Green):** Execução do catálogo de peças registra `etapas_com_atalho_interno` e `scripts_sem_chamador` resolvidos.
- **Construtor Prompt (EN):**
  - Refactor etapa_02_planner in scripts/orquestrador_sincrono.py to remove internal tool imports.
  - Refactor etapa_03_engine in scripts/orquestrador_sincrono.py to use canonical dispatch CLI command.
  - Wire orphan scripts in scripts directory to CLI dispatcher or documented entry points.
  - Run orchestrator unit tests. Assert exit 0.
  - Write handoff json to docs/auditoria/mapa-pecas/ciclo-02/ENTREGA-TICKET-02.json.

### Ticket 3: Saneamento de Donas de Tarefas, MCPs e Verbos de CLI (Refere-se a D4 / DoD 1)
- **Falha 15-D:** `D4. Componentes e Fractalidade`
- **Artefato de Handoff:** `docs/auditoria/mapa-pecas/ciclo-02/ENTREGA-TICKET-03.json`
- **Requisito TDD (Red):** Verificação de integridade de ferramentas deve acusar tarefas redundantes e sobreposição desnecessária de verbos de CLI.
- **Implementação Técnica:**
  - Definir dona única para as tarefas compartilhadas e unificar responsabilidades.
  - Registrar formalmente o propósito dos 3 MCPs das ferramentas (`mcp-verificador-cve`, `cloudflare-mcp`, `docker-mcp`).
  - Clarificar na documentação e interfaces a separação dos verbos de CLI.
- **Verificação (Green):** Auditoria de componentes e ferramentas executa com exit 0.
- **Construtor Prompt (EN):**
  - Harmonize task ownership across tool descriptions and component definitions.
  - Register purpose of internal MCP servers in manifest and dependency documentation.
  - Document distinct tool CLI command verbs to prevent duplicate CLI collision.
  - Run verification of components and tools. Assert exit 0.
  - Write handoff json to docs/auditoria/mapa-pecas/ciclo-02/ENTREGA-TICKET-03.json.

### Ticket 4: Deduplicação de Arquivos e Moldes de Entrega (Refere-se a D12 / DoD 5)
- **Falha 15-D:** `D12. Observabilidade e Frugalidade`
- **Artefato de Handoff:** `docs/auditoria/mapa-pecas/ciclo-02/ENTREGA-TICKET-04.json`
- **Requisito TDD (Red):** Teste de frugabilidade deve detectar duplicações desnecessárias entre scaffolds de `aidd-master` e `aidd-enterprise`.
- **Implementação Técnica:**
  - Consolidar templates e moldes idênticos sob fonte canônica única.
  - Eliminar redundâncias nos 7 moldes de entrega homônimos.
- **Verificação (Green):** Redução mensurável no catálogo de arquivos idênticos duplicados.
- **Construtor Prompt (EN):**
  - Inspect duplicate files between aidd-master and aidd-enterprise scaffolding.
  - Consolidate common templates into shared mold locations.
  - Update mold catalog references to designate single source of truth.
  - Run repository integrity tests. Assert exit 0.
  - Write handoff json to docs/auditoria/mapa-pecas/ciclo-02/ENTREGA-TICKET-04.json.

### Ticket 5: Alinhamento 15-D e Fechamento de Ciclo (Refere-se a D14 / DoD 8)
- **Falha 15-D:** `D14. Critério de Rejeição (Rollback)`
- **Artefato de Handoff:** `docs/auditoria/mapa-pecas/ciclo-02/ENTREGA-TICKET-05.json`
- **Requisito TDD (Red):** Portão G_mapa_pecas e laudo 15-D devem validar todas as 15 dimensões e catálogo 100% atualizado.
- **Implementação Técnica:**
  - Garantir abertura e rastreabilidade formal do próximo ciclo de `aidd-melhoria` para as 7 dimensões apontadas.
  - Regerar catálogo factual de peças e todos os 13 mapas visuais em `docs/mapas-visuais/`.
  - Executar quality gate `G_mapa_pecas.py` e bateria completa de testes.
- **Verificação (Green):** `python gates/G_mapa_pecas.py` e `python scripts/mapa_visual.py <tipo> --check` retornam exit 0.
- **Construtor Prompt (EN):**
  - Verify that aidd-melhoria ciclo-02 scaffold is open for remaining dimensions.
  - Recompute parts catalog with scripts/catalogo_pecas.py.
  - Recompile all 13 visual maps and book parts.
  - Run gates/G_mapa_pecas.py and test suites. Assert exit 0.
  - Write handoff json to docs/auditoria/mapa-pecas/ciclo-02/ENTREGA-TICKET-05.json.
