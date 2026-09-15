# Item 08: Testes das Fases LLM

## Escopo
Implementar testes para as fases 2, 3, 7 do factory (gateway, frontend, webhooks).

## Definicao de Pronto
- [ ] `tests/test_gateway_generator.py` — gera gateway para fixture clinicas
- [ ] `tests/test_frontend_generator.py` — gera frontend para fixture clinicas
- [ ] `tests/test_webhooks.py` — gera webhooks para fixture clinicas
- [ ] `tests/test_swagger_generator.py` — gera swagger para fixture clinicas
- [ ] `tests/test_validacao_cross.py` — validacao completa E2E
- [ ] Cada teste: input -> analysis -> fase -> output -> validacao
- [ ] Coverage minimo: 80% em phases/
- [ ] Todos os testes passam com `pytest tests/ -v`

## Dependencias
- Itens 01-07 (todos os anteriores)

## Evidencia
- Padrao de testes: `test_pipeline_factory.py` (13 testes existentes)
- Fixture clinicas ja definida e funcionando
- `tests/test_contrato_infraestrutura.py` ja testa cross-tool contract
