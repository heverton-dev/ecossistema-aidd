# Plano de evolução — aidd-skills ciclo-02

## Origem

Ciclo-01 (03/10/2026): a convenção passou a exigir `Negative Guardrails`, `Failure Modes & Fallback` e `Stopping Checklist` em toda skill própria, e o `G_SKILL_FORMATO` passou a apontar quem não tem (Ticket 3). Medição no repositório real: 43 de 44 skills sem as 3 seções. Só a `aidd-skills` está adequada.

## Objetivo

Cada skill ganha as 3 seções escritas para o seu domínio, citando arquivos, comandos e gates reais e os erros que os agentes já cometeram neste ecossistema. Texto genérico não é aceito. No fim, `--secoes-estritas` passa a valer para o repositório inteiro.

## Lotes

| Lote | Tema | Skills | Lista |
|---|---|---|---|
| 1 | Construção | 7 | aidd-forge, aidd-planner, aidd-pure, aidd-open, aidd-freedom, aidd-master, aidd-enterprise |
| 2 | Entrega e orquestração | 7 | aidd-ops, aidd-orchestrate, aidd-pipeline, aidd-dispatch, aidd-handoff, aidd-orca, aidd-9router |
| 3 | Auditoria e qualidade | 7 | aidd-audit-4f, aidd-diagnose, aidd-improvement, aidd-evolution, aidd-retro, aidd-tdd, aidd-spec |
| 4 | Planejamento e conhecimento | 8 | aidd-plan, aidd-tickets, aidd-grill, aidd-grill-docs, aidd-reexplain, aidd-anatomy, aidd-ingest, aidd-wizard |
| 5 | Documentos | 7 | aidd-docx, aidd-pdf, aidd-pptx, aidd-xlsx, aidd-textbook, aidd-dataviz, aidd-agent-writing |
| 6 | Infraestrutura do ecossistema | 7 | aidd-components, aidd-dependencies, aidd-mcp, aidd-session, aidd-delivery, aidd-frontend-forms, aidd-visual-maps |

## Execução

Pipeline 4F (`scripts/orquestrador_4f.py --manifest docs/auditoria/aidd-skills/ciclo-02/MANIFESTO-4F.json`), uma fase por lote, agente claude (passa pelo portão do graph, Lei #14). Gate de cada lote: `G_SKILL_FORMATO --secoes-estritas --apenas <lote>`, `G_SKILL_FORMATO`, `G_SKILL_ROT` e `G_HARNESS_COMPAT`; o último lote cobra `--secoes-estritas` no repositório inteiro.

## Depois do ciclo

Tornar `--secoes-estritas` o padrão do `G_SKILL_FORMATO` (o gate passa a reprovar skill nova sem as seções).
