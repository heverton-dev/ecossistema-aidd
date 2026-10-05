# Definition of Done: aidd-enterprise-runner (Auditoria 15-D)

## Metas e Critérios Binários de Aceitação

1. **D1 & D13 (Contratos e Quality Gate):**
   A ferramenta `aidd-enterprise-runner` deve ser validada pelo quality gate canônico `gates/G_aidd_enterprise.py`, garantindo correspondência exata do hash SHA-256 e schema JSON Draft 2020-12.

2. **D3 (Isolamento e Atomicidade):**
   A injeção de componentes deve ser atômica, abortando e realizando rollback diante de qualquer divergência binária.

3. **D15 (Handoff Formal):**
   O manifesto gerado para a camada de infraestrutura deve cumprir estritamente o schema `componentes/compartilhado/specs/handoff-enterprise-to-ops.schema.json`.
