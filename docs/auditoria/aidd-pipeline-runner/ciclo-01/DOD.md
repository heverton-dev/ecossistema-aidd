# Definition of Done: aidd-pipeline-runner (Auditoria 15-D)

## Metas e Critérios Binários de Aceitação

1. **D1 (Contratos e Regras):**
   A ferramenta `aidd-pipeline-runner` deve validar manifestos contra `schemas/handoff-execucao.schema.json` e aplicar `gates/G_PIPELINE_HANDOFF.py`.

2. **D3 (Raio de Impacto e Isolamento):**
   Execuções paralelas devem ocorrer estritamente em worktrees efêmeras `.worktrees/<task_id>` em branches dedicados `task/<task_id>`.

3. **D14 (Rollback e Limpeza):**
   Qualquer falha na barreira de sincronização deve abortar o merge e remover 100% das worktrees efêmeras.
