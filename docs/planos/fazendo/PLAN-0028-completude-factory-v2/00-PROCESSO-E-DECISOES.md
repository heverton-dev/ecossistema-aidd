# PLAN-0028: Completude do AIDD-Factory conforme v2

## Origem
- **Documento:** `docs/features/v2_arquitetura-aidd-ops-factory.md`
- **Melhoria:** `docs/melhorias/14-09-2026_melhoria-aidd-factory-implementacao.json`
- **Nota Atual:** 4/10 (apos PLAN-0027)
- **Nota Alvo:** 10/10 (todas as 9 fases implementadas)
- **Plan anterior:** PLAN-0027 (MVP — fases 1,4,5,6)

## Escopo
Completar as 5 fases restantes do aidd-factory conforme o documento v2:
- Fase 2: Gateway FastAPI (LLM + Templates)
- Fase 3: Frontend Next.js whitelabel (LLM + Templates)
- Fase 7: Webhooks/Integracoes (LLM + Templates)
- Fase 8: Documentacao Swagger/OpenAPI (Deterministica)
- Fase 9: Validacao Cross-Service (Deterministica)
- Integracao full: intake -> factory -> deploy encadeado

## Decisoes
1. **Fases 2, 3, 7 usam LLM** — precisam de delegacao via `utils_delegacao.py` do generator
2. **Templates Jinja2** para gateway (main.py, routes.py, models.py) e frontend (layout, page, tenant.config)
3. **Fase 8 reutiliza** `RouteRegistry` de `aidd-master/enterprise`
4. **Fase 9 e a soma** de todos os gates anteriores
5. **Intake web** ganha botao "Gerar Stack Completa"

---

## Registro de Progresso

| Item | Status | Nota |
|------|--------|------|
| 01-templates-jinja2 | ⏳ | - |
| 02-fase2-gateway | ⏳ | - |
| 03-fase3-frontend | ⏳ | - |
| 04-fase7-webhooks | ⏳ | - |
| 05-fase8-swagger | ⏳ | - |
| 06-fase9-validacao | ⏳ | - |
| 07-integracao-full | ⏳ | - |
| 08-testes-fases-llm | ⏳ | - |
