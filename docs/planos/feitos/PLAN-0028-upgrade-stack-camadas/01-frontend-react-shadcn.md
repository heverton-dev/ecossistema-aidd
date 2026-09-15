# 01 — Frontend: React + shadcn/ui

## Nota Atual: 4/10 | Nota Alvo: 8/10 | Prioridade: CRÍTICA

## Evidência da Nota Atual
- Template `index.html`: Vanilla HTML + Tailwind CDN + JS inline
- Sem framework de build (Vite/Webpack)
- Sem componentização (tabs via onclick manual)
- Sem testes de UI
- Sem state management
- Sem reatividade

## O que será implementado
1. Scaffold React 19 + Vite + TypeScript no template `templates/v2/frontend/`
2. shadcn/ui como design system (copy-paste, não dependência npm)
3. Componentização dos 5 módulos: Triagem, PEP, Cirurgico, Farmacia, Faturamento
4. React Router para navegação entre módulos
5. TanStack Query para data fetching (chamadas à API FastAPI)
6. Tailwind v4 como estilização

## Arquivos afetados
- `tools/aidd-master/templates/v2/frontend/` (novo diretório)
- `tools/aidd-master/templates/v2/index.html` (manter como fallback)
- `tools/aidd-master/templates/v2/Dockerfile` (adicionar stage de build)

## Critério de aceitação
- [ ] `npm run build` gera bundle < 200KB gzipped
- [ ] Todos os 5 módulos funcionam via API FastAPI
- [ ] Testes de componente passam
- [ ] Acessibilidade WCAG 2.1 AA verificada

## Riscos
- Aumento da complexidade de build (mitigado: Vite é simples)
- Dependência npm (mitigado: shadcn/ui é copy-paste)

## Estimativa
- Esforço: Alto (~3-5 dias)
- Impacto: +4 pontos na nota (4→8)
