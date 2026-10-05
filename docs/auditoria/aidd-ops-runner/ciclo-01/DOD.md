# Definition of Done: aidd-ops-runner (Auditoria 15-D)

## Metas e Critérios Binários de Aceitação

1. **D1 (Contratos e Regras):**
   A ferramenta `aidd-ops-runner` deve produzir manifests IaC consistentes e reproduzíveis acompanhados de `PLANO-INFRAESTRUTURA.json`.

2. **D11 (Resiliência a Entradas Ambíguas):**
   O motor deve rejeitar ou tratar deterministicamente comandos ambíguos ou nichos não catalogados sem alucinar arquitetura.

3. **D13 (Quality Gate Canônico):**
   A execução da suíte de testes de pipeline de infraestrutura `tools/aidd-ops/tests/test_pipeline_ops.py` deve retornar `exit 0`.
