# Definition of Done: aidd-componentes (Auditoria 15-D)

## Metas e Critérios Binários de Aceitação

1. **D1 (Contratos e Regras):**
   A ferramenta `aidd-componentes` deve sincronizar artefatos de `componentes/` para harnesses em conformidade com `gates/manifesto_harnesses.json`.

2. **D2 (Input e Gatilhos):**
   Comandos `python ecossistema.py components sync --tipo <tipo>` e `python ecossistema.py components verify --tipo <tipo>` devem executar com determinismo absoluto.

3. **D3 (Raio de Impacto e Isolamento):**
   Arquivos sob `componentes/` devem permanecer soberanos e isolados; sincronização deve manipular apenas pastas geradas nos harnesses.

4. **D13 (Quality Gate de Repositório):**
   Os gates `gates/G_COMPONENTE_AGNOSTICO.py` e `gates/G_SKILL_ROT.py` devem aprovar o estado do repositório com exit 0 comprovando ausência de drifts ou órfãos.
