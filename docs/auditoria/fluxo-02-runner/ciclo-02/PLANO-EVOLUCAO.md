# Plano de Evolução (Fase 2) - fluxo-02-runner (Ciclo 02)

Plano de evolução para a ferramenta `fluxo-02-runner` aplicando as correções cirúrgicas do laudo E2E do Fluxo 02.

## Estratégia de Execução
Aplicação sequencial dos micro-tickets garantindo contratos determinísticos reais, eliminação de stubs e injeção completa de serviços.

### Ticket 1: Implement C5 Contract Handoff in aidd-enterprise and SHA-256 Validator Alias
- **Falha 15-D:** `D1. Contratos e Regras`
- **Artefato de Handoff:** `docs/auditoria/fluxo-02-runner/ciclo-02/ENTREGA-TICKET-01.json`
- **Gate do Ticket:** `python -m pytest -q -p no:cacheprovider tests/test_orquestrador_contratos_reais.py`
- **Construtor Prompt (EN):**
  - Update application_enterprise verificar_drift.py to write HANDOFF_ENTERPRISE_OPS.json when drift check succeeds.
  - Ensure HANDOFF_ENTERPRISE_OPS.json conforms to handoff-enterprise-to-ops.schema.json.
  - Export verificar_integridade_payload as alias to validar_integridade_contrato in contratos/validador_sha256.py.
  - Run pytest on tests/test_orquestrador_contratos_reais.py and assert exit 0.
  - Write handoff json to docs/auditoria/fluxo-02-runner/ciclo-02/ENTREGA-TICKET-01.json.

### Ticket 2: Align Real Contract Execution in Orchestrator Tests
- **Falha 15-D:** `D13. Rótulo Honesto e Quality Gates`
- **Artefato de Handoff:** `docs/auditoria/fluxo-02-runner/ciclo-02/ENTREGA-TICKET-02.json`
- **Gate do Ticket:** `python -m pytest -q -p no:cacheprovider tests/test_orquestrador_contratos_reais.py`
- **Construtor Prompt (EN):**
  - Update tests/test_orquestrador_contratos_reais.py to test real contract persistence without fake C5 generation.
  - Verify that C5 validation passes through both jsonschema and validar_handoff.
  - Run pytest on tests/test_orquestrador_contratos_reais.py and assert exit 0.
  - Write handoff json to docs/auditoria/fluxo-02-runner/ciclo-02/ENTREGA-TICKET-02.json.

### Ticket 3: Integrate Curated Open Source Services into Ops Compose Rendering
- **Falha 15-D:** `D4. Componentes e Fractalidade`
- **Artefato de Handoff:** `docs/auditoria/fluxo-02-runner/ciclo-02/ENTREGA-TICKET-03.json`
- **Gate do Ticket:** `python -m pytest -q -p no:cacheprovider modulos/03-plataforma-e-entrega/operacoes-ops/aidd-ops/tests`
- **Construtor Prompt (EN):**
  - Update infra_perfil.py in aidd-ops to parse external open-source tools from PLANNER.json or C2 entrada.
  - Inject external tool services into docker-compose.yml structure when specified.
  - Run pytest on modulos/03-plataforma-e-entrega/operacoes-ops/aidd-ops/tests and assert exit 0.
  - Write handoff json to docs/auditoria/fluxo-02-runner/ciclo-02/ENTREGA-TICKET-03.json.

### Ticket 4: Fortify Frontend Templates in aidd-master and aidd-enterprise
- **Falha 15-D:** `D11. Padrão-Ouro de Stack e UI`
- **Artefato de Handoff:** `docs/auditoria/fluxo-02-runner/ciclo-02/ENTREGA-TICKET-04.json`
- **Gate do Ticket:** `python modulos/04-nucleo-compartilhado/gates/G_DRIFT_NUCLEO_COMPARTILHADO.py`
- **Construtor Prompt (EN):**
  - Add missing src/lib/utils.ts and src/lib/api.ts to templates/v2/frontend in both aidd-master and aidd-enterprise.
  - Fix react-router-dom useNavigate import in App.tsx.
  - Add @types/node to devDependencies in package.json.
  - Verify zero drift between aidd-master and aidd-enterprise templates/v2.
  - Write handoff json to docs/auditoria/fluxo-02-runner/ciclo-02/ENTREGA-TICKET-04.json.

