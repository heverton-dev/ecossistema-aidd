# Definition of Done: aidd-livro-texto (Auditoria 15-D)

## Metas e Critérios Binários de Aceitação

1. **D1 (Contratos e Regras):**
   A ferramenta `aidd-livro-texto` deve cumprir as 6 Leis do Livro, exigindo rastreabilidade por capítulo e verificação estrutural determinística.

2. **D2 (Input e Gatilhos):**
   CLI `livro.py` deve suportar os comandos canônicos de ciclo de vida (`init`, `status`, `check`, `build`, `preview`, `update`).

3. **D13 (Quality Gate de Repositório):**
   O comando `python <skill>/scripts/livro.py check <folder>` deve atuar como Quality Gate retornando exit 0 somente em conformidade total.
