# Definition of Done — aidd-skills ciclo-02

1. As 43 skills têm `## Negative Guardrails`, `## Failure Modes & Fallback` e `## Stopping Checklist` (`python gates/G_SKILL_FORMATO.py --secoes-estritas` exit 0).
2. Cada seção cita arquivos, comandos ou gates reais da própria skill; nenhum item idêntico entre skills.
3. Frontmatter e o resto do corpo de cada skill sem mudança; corpo abaixo de 450 linhas.
4. Cópias por harness sincronizadas (`G_HARNESS_COMPAT` exit 0) e `G_SKILL_ROT` exit 0.
5. Um `LOTE-NN.md` por lote, com o que foi acrescentado em cada skill.
6. `gate_final` (`python ecossistema.py audit`) exit 0 antes do merge.
