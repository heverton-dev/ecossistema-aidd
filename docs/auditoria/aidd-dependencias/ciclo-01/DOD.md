# Definition of Done: aidd-dependencias (Auditoria 15-D)

## Metas e Critérios Binários de Aceitação

1. **D1 (Contratos e Regras):**
   A ferramenta `aidd-dependencias` deve manter o inventário formal em `gates/dependencias_externas.json` sem segredos ou credenciais embutidas.

2. **D2 (Input e Gatilhos):**
   Comandos `python ecossistema.py dependencia verify` e `python ecossistema.py dependencia bootstrap` devem operar com determinismo.

3. **D13 (Quality Gate de Repositório):**
   O gate `gates/G_dependencias_externas.py` deve retornar `exit 0` atestando integridade das dependências registradas e ausência de drifts não mapeados.
