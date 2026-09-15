# Item 03: Fase 3 — Gerador de Frontend Next.js Whitelabel

## Escopo
Implementar `scripts/phases/03_frontend.py` e `src/core/frontend_generator.py` que geram o scaffold do frontend whitelabel.

## Definicao de Pronto
- [ ] `03_frontend.py` implementado com delegacao LLM
- [ ] `frontend_generator.py` monta prompt com:
  - Nicho e servicos do factory_analysis
  - Modulos por servico (CRM, Atendimento, Agendamento)
  - tenant.config.json para personalizacao de marca
- [ ] Templates renderizados: layout.tsx, page.tsx, next.config.js, tenant.config.json
- [ ] Output: `frontend/` com estrutura Next.js + Tailwind + shadcn/ui
- [ ] BFF routes que consomem o gateway
- [ ] Valida: `npm run build` (ou pelo menos sintaxe TypeScript)
- [ ] Gate G_FACTORY_FRONTEND.py verifica estrutura
- [ ] Testes: fixture clinicas gera frontend com 3 modulos

## Dependencias
- Item 01 (templates)
- PLAN-0027 item 02 (analisador)

## Evidencia
- v2 doc §4.3 Fase 3: "1 chamada LLM, ~4k tokens"
- `componentes/compartilhado/src-core/nextjs_exporter.py` existe (reutilizavel para BFF)
- shadcn/ui ja e padrao no ecossistema
