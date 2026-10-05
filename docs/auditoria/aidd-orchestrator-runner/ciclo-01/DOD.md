# Definition of Done: aidd-orchestrator-runner (Auditoria 15-D)

## Metas e Critérios Binários de Aceitação

1. **D1 (Contratos e Regras):**
   A ferramenta `aidd-orchestrator-runner` deve exigir aprovação explícita do usuário antes da execução do Plano de Voo e respeitar a Golden Rule #7.

2. **D2 (Input e Gatilhos):**
   Subcomando `python ecossistema.py orchestrate` deve suportar os ambientes `orca`, `subagent` e `gitworktree` com compilação determinística.

3. **D13 (Quality Gate de Repositório):**
   A execução de frentes deve exigir aprovação de testes e auditoria `python ecossistema.py audit` com exit 0 antes de merge.
