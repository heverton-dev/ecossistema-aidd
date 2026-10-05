# Definition of Done: aidd-mcp (Auditoria 15-D)

## Metas e Critérios Binários de Aceitação

1. **D1 (Contratos e Regras):**
   A ferramenta `aidd-mcp` deve utilizar bibliotecas padronizadas FastMCP/mcp e confinar a autoria a `componentes/<escopo>/mcps/<nome>/server.py`.

2. **D3 (Raio de Impacto e Isolamento):**
   Proibição estrita de credenciais embutidas no código; variáveis devem ser lidas via ambiente documentado.

3. **D13 (Quality Gate de Repositório):**
   Validação por `py_compile`, `components verify --tipo mcp` e `gates/G_SEGREDOS.py` deve retornar exit 0.
