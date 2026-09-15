# Item 02: Fase 2 — Gerador de Gateway FastAPI

## Escopo
Implementar `scripts/phases/02_gateway.py` e `src/core/gateway_generator.py` que geram o Micro-Servico Gateway FastAPI.

## Definicao de Pronto
- [ ] `02_gateway.py` implementado com delegacao LLM via `utils_delegacao.py`
- [ ] `gateway_generator.py` monta o prompt estruturado com:
  - Lista de servicos do factory_analysis
  - Endpoints por servico (CRUD proxy)
  - Webhook receiver padronizado
  - Rate limiting middleware
  - Healthcheck endpoints (/healthz por servico)
- [ ] Template `templates/gateway/main.py.jinja2` renderizado com dados do nicho
- [ ] Output: `src/gateway/main.py`, `src/gateway/routes.py`, `src/gateway/models.py`
- [ ] Valida: `python -m py_compile` em cada .py gerado
- [ ] Valida: imports resolvem (fastapi, pydantic, httpx)
- [ ] Gate G_FACTORY_GATEWAY.py verifica estrutura e imports
- [ ] Testes: fixture clinicas gera gateway com 4 servicos

## Dependencias
- Item 01 (templates)
- PLAN-0027 item 02 (analisador)

## Evidencia
- v2 doc §4.3 Fase 2: "1 chamada LLM, ~3k tokens"
- `utils_delegacao.py` do generator ja tem `delegar_llm()` reutilizavel
- `fastapi==0.141.1` ja esta no requirements.txt do ecossistema
