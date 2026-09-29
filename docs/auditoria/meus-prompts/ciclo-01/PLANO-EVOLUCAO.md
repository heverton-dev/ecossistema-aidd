# Plano de Evolução (Fase 2) - meus-prompts

Este plano foi gerado pela Fase 2 do Pipeline de Ingestão AIDD, com o objetivo de incorporar utilitários funcionais do repositório `meus-prompts` ao ecossistema canônico.

### Ticket 1: Port Document Utility Skills (Refere-se a D2 / DoD 1)
- **Falha 15-D:** `D2. Input e Gatilhos`
- **Artefato de Handoff:** `docs/auditoria/meus-prompts/ciclo-01/HANDOFF-TICKET-01.json`
- **Requisito TDD (Red):** Test fails if document utility skills are missing from ecosystem components.
- **Implementação Técnica:**
  - Extrair as skills funcionais de documentos (docx, pptx, xlsx, pdf) de `.tmp/ingest/meus-prompts/Anthropic/claude-code/skills/`.
  - Converter para o formato canônico AIDD em `componentes/compartilhado/skills/`.
- **Verificação (Green):** Portão G_SKILL_FORMATO passa com sucesso.
- **Construtor Prompt (EN):**
  - Extract document utility skills from temporary sandbox.
  - Convert to canonical AIDD format in components shared skills directory.
  - Verify skill format conformance with quality gates.
  - Ensure zero proprietary lock-in.

### Ticket 2: Port Dataviz Script Tools (Refere-se a D8 / DoD 2)
- **Falha 15-D:** `D8. O que o Estágio Processa`
- **Artefato de Handoff:** `docs/auditoria/meus-prompts/ciclo-01/HANDOFF-TICKET-02.json`
- **Requisito TDD (Red):** Test fails if dataviz palette validation script is missing or fails execution.
- **Implementação Técnica:**
  - Migrar `validate_palette.py` de `.tmp/ingest/meus-prompts/` para `componentes/compartilhado/skills/aidd-dataviz/scripts/`.
  - Adicionar testes determinísticos para validação de paletas.
- **Verificação (Green):** Testes passam com exit 0.
- **Construtor Prompt (EN):**
  - Migrate dataviz palette validation script to shared skills directory.
  - Add deterministic unit tests for palette validation.
  - Run pytest to assert exit code zero.
  - Deliver handoff summary.
