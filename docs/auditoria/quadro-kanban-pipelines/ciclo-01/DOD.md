# Definição de Pronto (Definition of Done - DoD) — quadro-kanban-pipelines (Ciclo 01: Fase 0)

> Critérios estáticos de conformidade arquitetural baseados no plano `08-10-2026_melhoria-quadro-kanban-pipelines.md` e na Fase 0 (Contrato vivo e inventário).

## Critérios Obrigatórios de Aceite

1. **DoD 1: Contrato Único de Pipelines (D1/D8)**
   - Criação de `modulos/04-nucleo-compartilhado/contracts/PIPELINES.json` declarando os 12 pipelines e as etapas de cada um (id, nome, etapas com id e título curto em português, comando de entrada e origem de estado).
   - Teste unitário de forma em `tests/test_pipelines_contrato.py` validando schema e integridade.

2. **DoD 2: Consumo no Catálogo de Peças e Mapas (D3/D8)**
   - `scripts/catalogo_pecas.py` (`coletar_pipelines`) consome `PIPELINES.json`.
   - Catálogo `docs/auditoria/mapa-pecas/catalogo-pecas.json` e mapa visual de pipelines refletem exatamente o contrato vivo.

3. **DoD 3: Cobertura Completa de Pipelines (D8)**
   - Todas as etapas dos 12 pipelines declaradas, incluindo `aidd-ops` e `aidd-pipeline` (anteriormente zeradas).

4. **DoD 4: Detector do Contrato Vivo (D13 - Prova que Morde)**
   - Teste determinístico provando que a existência de pipeline no código não declarado em `PIPELINES.json` invalida o catálogo e reprova com exit 1 no `G_mapa_pecas`.

5. **DoD 5: Integridade e Bateria Verde (D13)**
   - `python ecossistema.py audit` com EXIT 0 sem quebras de governança ou regressões.
