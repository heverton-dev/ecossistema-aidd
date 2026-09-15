# Item 07: Gates de Validacao

## Escopo
Implementar os quality gates especificos do factory.

## Definicao de Pronto
- [ ] `gates/G_FACTORY_MVP.py` — valida estrutura do diretorio factory
- [ ] `gates/G_FACTORY_ANALYSIS.py` — valida factory_analysis.json contra schema
- [ ] `gates/G_FACTORY_COMPOSE.py` — valida compose unificado (sem colisao portas, healthchecks, redes)
- [ ] `gates/G_FACTORY_INIT_DB.py` — valida sintaxe bash do init script
- [ ] `gates/G_FACTORY_ENV.py` — valida completude dos .env
- [ ] `gates/G_FACTORY_INTEGRATION.py` — valida cadeia completa (input -> analysis -> output)
- [ ] Todos os gates rodam via `python ecossistema.py audit` (pre-commit hooks)
- [ ] Zero stubs verificados por AST

## Dependencias
- Itens 01-06 (todos os anteriores)

## Evidencia
- Padrao de gates: `tools/aidd-ops/gates/G_OPS_MVP.py`, `G_OPS_SSH.py`
- `gates/G_INFRA_COMPOSE.py` ja existe no ecossistema
- `gates/G_HADOLINT.py` valida Dockerfiles
