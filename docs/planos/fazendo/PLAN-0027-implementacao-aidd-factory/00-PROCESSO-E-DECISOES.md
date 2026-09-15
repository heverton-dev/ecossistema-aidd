# PLAN-0027: Implementacao do AIDD-Factory

## Origem
- **Melhoria:** `docs/melhorias/14-09-2026_melhoria-aidd-factory-implementacao.json`
- **Nota Atual:** 1/10
- **Nota Alvo:** 7/10 (fase MVP funcional)
- **Documento de referencia:** `docs/features/v2_arquitetura-aidd-ops-factory.md`

## Escopo
Criar a 7a ferramenta do ecossistema-aidd: **aidd-factory** — gerador de codigo de aplicacao e integracao para stacks multi-serviço.

## Decisoes
1. **Foco MVP:** Apenas Fases 1, 4, 7, 8, 9 do pipeline factory (deterministicas). Fases 2, 3, 5, 6, 10 (LLM) ficam para iteracao posterior.
2. **Reusar infra existente:** Result pattern de `componentes/compartilhado/`, schemas de `componentes/compartilhado/specs/`, templates infra de `aidd-ops/templates/infra/`.
3. **Nao tocar no aidd-ops:** Mantido intocado. Factory e ferramenta separada.
4. **Contrato de entrada:** `PLANO-INFRAESTRUTURA.json` (schema ja existente).
5. **Contrato de saida:** `FACTORY_OUTPUT.json` com lista de artefatos gerados.

## Restricoes
- Zero stubs (lei #5 do AGENTS.md)
- Determinismo primeiro (lei #1)
- Testes reais (lei #8)
- Gate de validacao antes de cada fase

---

## Registro de Progresso

| Item | Status | Nota |
|------|--------|------|
| 01-scaffold-factory | ⏳ | - |
| 02-analisador-deterministico | ⏳ | - |
| 03-compose-unificado | ⏳ | - |
| 04-init-db-dinamico | ⏳ | - |
| 05-env-geracao | ⏳ | - |
| 06-integracao-aidd-ops | ⏳ | - |
| 07-gates-validacao | ⏳ | - |
| 08-testes-e2e | ⏳ | - |
