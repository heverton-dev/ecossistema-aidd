# Definition of Done: aidd-session (Auditoria 15-D)

## Metas e Critérios Binários de Aceitação

1. **D1 (Contratos e Regras):**
   A ferramenta `aidd-session` deve persistir dados de sessão em `secoes/historico_sessoes.json` e atualizar `secoes/INDICE-SESSOES.md` de forma determinística.

2. **D2 (Input e Gatilhos):**
   Comandos `python ecossistema.py sessao registrar|buscar|listar` devem validar parâmetros e responder com determinismo.

3. **D3 (Raio de Impacto e Isolamento):**
   A gravação de arquivos deve ocorrer via arquivo temporário `.tmp` seguido de substituição atômica, confinando alterações a `secoes/`.

4. **D11 (Tratamento de Exceções):**
   Atualizações para o mesmo ID de sessão devem ser idempotentes, atualizando o registro existente sem criar duplicatas.

5. **D13 (Quality Gate de Repositório):**
   O gate `gates/G_aidd_session.py` deve validar a consistência e integridade do histórico, retornando exit 0 para histórico íntegro e exit 1 para dados corrompidos.
