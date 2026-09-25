# Relatório do Construtor (Fase 3) — skills-pocock ciclo-01

> Branch `audit/evolucao-skills-pocock-ciclo-01`. Tabela por ticket preenchida no Ticket 12; execução real do gate de prova no Ticket 13 (manual).

## Ticket 11 — execução real contra as skills globais

Comando: `python scripts/relatorio_skills_duplicadas.py > saida.txt 2>&1; echo $?` → exit 0 (25/09/2026).

| Skill global | Par AIDD | Sugestão |
|---|---|---|
| `~/.agents/skills/code-review` | `review-changes` | remover |
| `~/.agents/skills/diagnosing-bugs` | `aidd-diagnose` | remover |
| `~/.agents/skills/grill-me` | `aidd-grill` | remover |
| `~/.agents/skills/grill-with-docs` | `aidd-grill-docs` | remover |
| `~/.agents/skills/grilling` | `aidd-grill` | remover |
| `~/.agents/skills/handoff` | `aidd-handoff` | remover |
| `~/.agents/skills/tdd` | `aidd-tdd` | remover |
| `~/.agents/skills/to-spec` | `aidd-spec` | remover |
| `~/.agents/skills/to-tickets` | `aidd-tickets` | remover |

Remoção só à mão pelo usuário; este script nunca apaga nada.
