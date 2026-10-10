# Plano de Evolucao (Fase 2) - quadro-kanban-pipelines

Plano do ciclo-01 para implementar o contrato vivo e inventario de pipelines do ecossistema.
Origem: `docs/melhorias/08-10-2026_melhoria-quadro-kanban-pipelines.md`. Criterios: `DOD.md` deste ciclo.

## Estrategia de Execucao
- Todo ticket segue TDD estrito: teste que reprova (exit 1) antes da implementacao.
- Zero Stubs / Zero Mocks (Lei #5): dados reais de pipelines e etapas do repositorio.
- A main so recebe codigo que passou na bateria de gates completa (`python ecossistema.py audit`).
- Cada ticket entrega um arquivo novo (o orquestrador pula o ticket se o arquivo de entrega ja existir).

### Ticket 1: Contrato unico de pipelines e teste de schema (Refere-se a D1 / DoD 1)
- **Falha 15-D:** `D1. Aderencia Arquitetural e Contratos`
- **Artefato de Handoff:** `modulos/04-nucleo-compartilhado/contracts/PIPELINES.json`
- **Requisito TDD (Red):** Teste `tests/test_pipelines_contrato.py` valida que `PIPELINES.json` existe, contem os 12 pipelines obrigatorios e que cada pipeline possui id, nome, comando, etapas validas e origem de estado. Reprova antes da criacao do contrato.
- **Implementacao Tecnica:**
  - Criar `modulos/04-nucleo-compartilhado/contracts/PIPELINES.json` com os 12 pipelines.
  - Declarar as etapas formais de `aidd-ops` e `aidd-pipeline`.
  - Criar `tests/test_pipelines_contrato.py` com assercoes deterministas sobre a estrutura.
- **Verificacao (Green):** `pytest tests/test_pipelines_contrato.py` passa com exit 0.
- **Construtor Prompt (EN):**
  - Write tests/test_pipelines_contrato.py asserting modulos/04-nucleo-compartilhado/contracts/PIPELINES.json exists and contains 12 pipelines.
  - Run pytest tests/test_pipelines_contrato.py and verify exit 1 before contract creation.
  - Create modulos/04-nucleo-compartilhado/contracts/PIPELINES.json declaring all 12 pipelines with their respective stages and state source.
  - Declare explicit stages for aidd-ops and aidd-pipeline.
  - Re-run pytest tests/test_pipelines_contrato.py and assert exit 0.

### Ticket 2: Consumo do contrato vivo no catalogo de pecas (Refere-se a D8 / DoD 2)
- **Falha 15-D:** `D8. Determinismo e AST`
- **Artefato de Handoff:** `tests/test_catalogo_pipelines_contrato.py`
- **Requisito TDD (Red):** Teste em `tests/test_catalogo_pipelines_contrato.py` verifica se a funcao coletar_pipelines em `scripts/catalogo_pecas.py` consome os dados diretamente de `PIPELINES.json`.
- **Implementacao Tecnica:**
  - Atualizar `scripts/catalogo_pecas.py` na funcao `coletar_pipelines` para carregar `modulos/04-nucleo-compartilhado/contracts/PIPELINES.json`.
  - Regenerar catalogo de pecas em `docs/auditoria/mapa-pecas/catalogo-pecas.json`.
- **Verificacao (Green):** `pytest tests/test_catalogo_pipelines_contrato.py` passa e catalogo contem as etapas exatas do contrato.
- **Construtor Prompt (EN):**
  - Write tests/test_catalogo_pipelines_contrato.py asserting coletar_pipelines in scripts/catalogo_pecas.py reads stages from PIPELINES.json contract.
  - Run pytest tests/test_catalogo_pipelines_contrato.py and assert failure if logic does not read contract.
  - Modify scripts/catalogo_pecas.py to load stages from modulos/04-nucleo-compartilhado/contracts/PIPELINES.json.
  - Re-run pytest tests/test_catalogo_pipelines_contrato.py and assert exit 0.

### Ticket 3: Detector do contrato vivo e teste de mordida (Refere-se a D13 / DoD 4)
- **Falha 15-D:** `D13. Quality Gates (Portoes)`
- **Artefato de Handoff:** `tests/test_pipelines_detector_vivo.py`
- **Requisito TDD (Red):** Teste que simula a presenca de um novo pipeline no codigo que nao esteja registrado em `PIPELINES.json`. Deve provar que a verificacao do catalogo reprova com erro e que o gate morde.
- **Implementacao Tecnica:**
  - Implementar verificador em `scripts/catalogo_pecas.py` para comparar comandos com `PIPELINES.json`.
  - Criar `tests/test_pipelines_detector_vivo.py` injetando pipeline sintetico e validando reprovacao explicita.
- **Verificacao (Green):** `pytest tests/test_pipelines_detector_vivo.py` passa com exit 0.
- **Construtor Prompt (EN):**
  - Write tests/test_pipelines_detector_vivo.py injecting an unregistered mock pipeline command into check routines.
  - Assert the check routine flags contract divergence and rejects validation.
  - Implement dynamic comparison logic in scripts/catalogo_pecas.py to compare detected pipelines with PIPELINES.json contract.
  - Re-run pytest tests/test_pipelines_detector_vivo.py and assert exit 0.

### Ticket 4: Regeneracao e validacao com gates do ecossistema (Refere-se a D13 / DoD 5)
- **Falha 15-D:** `D13. Quality Gates (Portoes)`
- **Artefato de Handoff:** `docs/auditoria/quadro-kanban-pipelines/ciclo-01/EVIDENCIA-FASE-0.md`
- **Requisito TDD (Red):** Execucao dos gates do catalogo e mapas visuais deve confirmar total alinhamento e consistencia sem divergencias.
- **Implementacao Tecnica:**
  - Regenerar derivados oficiais via `python ecossistema.py derivados regenerar`.
  - Rodar `python gates/G_mapa_pecas.py` e registrar a saida em `EVIDENCIA-FASE-0.md`.
- **Verificacao (Green):** `python gates/G_mapa_pecas.py` retorna exit 0 e documenta conformidade da Fase 0.
- **Construtor Prompt (EN):**
  - Regenerate ecosystem visual maps and pieces catalog using existing regeneration scripts.
  - Run python gates/G_mapa_pecas.py and capture returncode.
  - Write docs/auditoria/quadro-kanban-pipelines/ciclo-01/EVIDENCIA-FASE-0.md with full execution logs and exit codes.
  - Assert returncode equals 0.
