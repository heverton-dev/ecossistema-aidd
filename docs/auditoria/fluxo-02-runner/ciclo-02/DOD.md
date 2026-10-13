# Definition of Done: fluxo-02-runner (Auditoria 15-D)

## Metas e Critérios Binários de Aceitação

1. **D1 (Contratos e Regras):**
   A ferramenta `fluxo-02-runner` deve validar estritamente a sequência de contratos formais de handoff C1 a C5, abortando com `exit 1` na ausência de qualquer um deles.

2. **D2 & D10 (Orquestração e CLI):**
   Suporte a `python ecossistema.py run-fluxo --fluxo 2` com execução determinística de 7 etapas e suporte a `--dry-run`.

3. **D13 (Quality Gate e Auditoria):**
   A etapa final deve executar `forge audit` sobre o projeto gerado exigindo `exit 0`.
