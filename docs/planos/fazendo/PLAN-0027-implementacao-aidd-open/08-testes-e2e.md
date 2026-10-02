# Item 08: Testes E2E

## Escopo
Implementar testes end-to-end que validam o pipeline completo do factory.

## Definicao de Pronto
- [ ] `tests/test_pipeline_factory.py` — teste E2E do pipeline completo
- [ ] Fixture: PLANO-INFRAESTRUTURA.json para nicho clinicas
- [ ] Fixture: PLANO-INFRAESTRUTURA.json para nicho delivery
- [ ] Fixture: PLANO-INFRAESTRUTURA.json para nicho b2b_industrial
- [ ] Cada teste: input -> factory_analysis -> compose -> init_db -> env -> FACTORY_OUTPUT
- [ ] Valida compose com `docker compose config` (dry-run)
- [ ] Valida init_db com shellcheck (sintaxe)
- [ ] Valida .env com completude de variaveis
- [ ] Todos os testes passam com `pytest tests/ -v`
- [ ] Coverage minimo: 80% em phases/

## Dependencias
- Itens 01-07 (todos os anteriores)

## Evidencia
- Padrao de testes: `tools/aidd-ops/tests/test_pipeline_ops.py` (373 linhas, gold fixtures)
- `test_contrato_infraestrutura.py` ja testa cross-tool contract
- `test_infra_roteamento.py` valida NIH #16 (port collision)
