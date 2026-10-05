# Definition of Done: aidd-forge-runner (Auditoria 15-D)

## Metas e Critérios Binários de Aceitação

1. **D1 (Contratos e Regras):**
   A ferramenta `aidd-forge-runner` deve implementar bootstrap com zero stubs (Lei #5), rótulo honesto (Lei #8) e quality gates com caminho de falha explícito (Lei #13).

2. **D13 (Quality Gate Canônico):**
   O alvo configurado pelo forge deve ser aprovado com `exit 0` pelo script `gates/G_aidd_forge.py`.

3. **D15 (Handoff Estruturado):**
   O manifesto `handoff-forge.json` gerado deve estar em estrita conformidade com o schema `componentes/compartilhado/specs/handoff-forge-to-planner.schema.json`.
