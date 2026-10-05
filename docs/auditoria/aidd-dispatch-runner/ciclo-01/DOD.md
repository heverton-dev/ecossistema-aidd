# Definition of Done: aidd-dispatch-runner (Auditoria 15-D)

## Metas e Critérios Binários de Aceitação

1. **D1 (Contratos e Regras):**
   A ferramenta `aidd-dispatch-runner` deve validar manifestos com `gates/G_DISPATCH_PIPELINE_VSA.py` e impor ordem DAG sem ciclos.

2. **D3 (Raio de Impacto e Isolamento):**
   Fatias devem ser despachadas em `.worktrees/<slice_id>` em branches dedicados `slice/<slice_id>`.

3. **D13 (Quality Gate de Repositório):**
   O gate `gates/G_DISPATCH_PIPELINE_VSA.py` deve retornar exit 0 para grafos ordenados e válidos.
