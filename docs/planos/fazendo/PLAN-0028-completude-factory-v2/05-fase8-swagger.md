# Item 05: Fase 8 — Gerador de Documentacao Swagger/OpenAPI

## Escopo
Implementar `scripts/phases/08_docs.py` e `src/core/swagger_generator.py` que geram documentacao OpenAPI 3.1.

## Definicao de Pronto
- [ ] `08_docs.py` implementado com 100% determinismo (zero LLM)
- [ ] `swagger_generator.py` extrai rotas do gateway FastAPI gerado
- [ ] Reutiliza `RouteRegistry` de `componentes/compartilhado/src-core/openapi.py`
- [ ] Gera `openapi.json` (spec completa)
- [ ] Gera `README.md` com instrucoes de deploy
- [ ] Valida: openapi.json e JSON valido com campo "openapi": "3.1.0"
- [ ] Gate G_FACTORY_DOCS.py valida spec
- [ ] Testes: fixture clinicas gera spec com endpoints de 4 servicos

## Dependencias
- Item 02 (gateway — precisa do codigo gerado para extrair rotas)
- PLAN-0027 item 02 (analisador)

## Evidencia
- v2 doc §4.3 Fase 8: "100% deterministico"
- `RouteRegistry.generate_openapi_json()` ja existe em aidd-master/enterprise
- `swagger_dark.css` ja existe em `componentes/compartilhado/`
