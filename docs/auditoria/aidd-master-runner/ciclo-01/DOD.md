# Definition of Done: aidd-master-runner (Auditoria 15-D)

## Metas e Critérios Binários de Aceitação

1. **D1 (Contratos e Regras):**
   A ferramenta `aidd-master-runner` deve impor isolamento estrito de fatias verticais VSA, garantindo rotas, modelos e serviços desacoplados.

2. **D13 (Quality Gate e Fronteiras):**
   Suíte de testes de fronteira e integrador master (`tools/aidd-master/tests/test_fronteira_master.py`) deve executar com `exit 0`.

3. **D15 (Handoff Formal):**
   Manifesto de integração deve cumprir integralmente o schema `componentes/compartilhado/specs/handoff-master-to-enterprise.schema.json`.
