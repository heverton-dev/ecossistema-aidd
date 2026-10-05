# Definition of Done: code-review-graph (Integração e Auditoria 15-D)

## Metas e Critérios Binários de Aceitação

1. **D1 (Contratos e Regras):**
   A dependência `code-review-graph` e suas 4 skills (`debug-issue`, `review-changes`, `refactor-safely`, `explore-codebase`) devem estar declaradas em `gates/dependencias_externas.json` com comando de instalação e hash SHA-256 verificado.

2. **D2 (Input e Gatilhos):**
   Comandos `python ecossistema.py dependencia verify` e `python ecossistema.py dependencia bootstrap` devem validar e instalar a dependência com determinismo estrito.

3. **D3 (Raio de Impacto e Isolamento):**
   Diretório `.code-review-graph/` e arquivos residuais de banco devem estar explicitamente ignorados ou contidos fora do rastreamento de código-fonte soberano.

4. **D12 (Frugalidade e Orçamento de Tokens):**
   Skills associadas devem impor o padrão de tokens `get_minimal_context` com chamadas restritas a ≤800 tokens por consulta.

5. **D13 (Quality Gate de Repositório):**
   O gate `gates/G_dependencias_externas.py` deve retornar `exit 0` comprovando que o pacote e suas skills estão íntegros e sincronizados.
