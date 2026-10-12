# Plano de Evolução Técnica: e2e-pure (Ciclo 02)

> **Alvo:** Resolução Cirúrgica das Falhas E2E do Fluxo 01 (AIDD-PURE)
> **Referência:** `RELATORIO-E2E-FLUXO-01.md`
> **Data:** 2026-10-12
> **Status:** Aprovado para Execução

---

## Bloco 1: Correção do Motor Pure e Clean Architecture

### Ticket 1: Correção do DDL Inicial no Fallback Determinístico do SQLite (Refere-se a D11)
- **Falha 15-D:** D11. Tratamento de Exceções
- **Artefato de Handoff:** `modulos/02-triade-motores/fluxo-01-pure/core/aidd-pure/scripts/phases/08_implementador.py`
- **Gate do Ticket:** `pytest modulos/02-triade-motores/fluxo-01-pure/core/aidd-pure/tests/unit/test_phase8_verifier.py`
- **Construtor Prompt (EN):**
  - Locate RepositorioSQLite template inside 08_implementador.py
  - Ensure in-memory connections persist connection handle instead of closing immediately
  - Run initial table creation DDL on initialization
  - Verify unit tests and integration tests pass without missing table operational error

### Ticket 2: Reorganização de Pastas de Persistência per Clean Architecture (Refere-se a D2)
- **Falha 15-D:** D2. Modularidade e Acoplamento
- **Artefato de Handoff:** `modulos/02-triade-motores/fluxo-01-pure/core/aidd-pure/scripts/phases/08_implementador.py`
- **Gate do Ticket:** `python modulos/03-plataforma-e-entrega/gates/G_ARQUITETURA_DELIVERABLE.py`
- **Construtor Prompt (EN):**
  - Update default destination for SQLite persistence scripts to infrastructure subfolder
  - Adjust import statements in generated unit tests and integration tests
  - Confirm G_ARQUITETURA_DELIVERABLE passes without SQL-fora-infra violations for generated persistence

### Ticket 3: Isolação de SQL no Servidor Modular do Master (Refere-se a D2)
- **Falha 15-D:** D2. Modularidade e Acoplamento
- **Artefato de Handoff:** `modulos/03-plataforma-e-entrega/fatiamento-master/aidd-master/templates/cookiecutter-scaffold/suite/{{cookiecutter.suite_slug}}/server.py.j2`
- **Gate do Ticket:** `python modulos/03-plataforma-e-entrega/gates/G_ARQUITETURA_DELIVERABLE.py`
- **Construtor Prompt (EN):**
  - Add helper methods to WebhookDispatcher for webhook operations and schema initialization
  - Replace raw invoke and executescript calls in server template with dispatcher calls
  - Ensure server template contains zero direct SQL calls outside infrastructure

## Bloco 2: Contratos Enterprise e Governança Forge

### Ticket 4: Emissão Explícita do Contrato C5 Handoff Enterprise to Ops (Refere-se a D1)
- **Falha 15-D:** D1. Contratos Formais
- **Artefato de Handoff:** `modulos/03-plataforma-e-entrega/blindagem-enterprise/aidd-enterprise/application_enterprise/commands/verificar_drift.py`
- **Gate do Ticket:** `pytest tests/test_orquestrador_contratos_reais.py`
- **Construtor Prompt (EN):**
  - Generate HANDOFF_ENTERPRISE_OPS.json upon successful drift verification
  - Validate output contract against handoff-enterprise-to-ops schema
  - Ensure synchronizer passes C5 gate to ops stage

### Ticket 5: Atualização dos Templates de Governança do Forge e Criador (Refere-se a D8)
- **Falha 15-D:** D8. Higiene de Repositório
- **Artefato de Handoff:** `modulos/02-triade-motores/fluxo-01-pure/core/aidd-pure/scripts/phases/05_criador.py`
- **Gate do Ticket:** `python modulos/01-governanca-e-qualidade/gates/G_SAIDA_BINARIA.py`
- **Construtor Prompt (EN):**
  - Update gitignore generator in Phase 5 to include node_modules entry
  - Update AGENTS template in Phase 5 to include execution directives in English
  - Verify forge audit compliance achieves high score on generated project
