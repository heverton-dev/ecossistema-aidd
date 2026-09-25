# Relatório Técnico — Análise comparativa `mattpocock/skills` × Ecossistema AIDD (ciclo-01)

> **Data:** 24/09/2026 · **Upstream:** `https://github.com/mattpocock/skills` commit `c55ee46` (licença MIT)
> **Antecedente:** PLAN-0030 (16/09/2026) integrou 7 skills (`aidd-grill`, `aidd-grill-docs`, `aidd-spec`, `aidd-tickets`, `aidd-tdd`, `aidd-diagnose`, `aidd-handoff`) e o relatório `docs/reports/analise-integracao-skills-matt-pocock.md`.
> **Método:** clone do upstream + comparação linha a linha de cada `SKILL.md` com a nossa versão em `componentes/compartilhado/skills/` e com as cópias globais em `~/.agents/skills/`.
> **Nota de fase:** este ciclo não tem Laudo 15-D (Fase 1), porque o alvo é um conjunto de skills-texto e não uma ferramenta com código. Esta análise faz o papel da Fase 1.

## 1. Regressões da adaptação de setembro (consertar)

| Skill | Nossa versão | Original | Gravidade |
|---|---|---|---|
| `aidd-diagnose` | "Formular **exatamente UMA** hipótese" | 3 a 5 hipóteses em ordem, antes de testar qualquer uma (uma só faz o agente se agarrar à primeira ideia). Também perdemos: comando vermelho já executado como pré-requisito, minimizar a reprodução, logs `[DEBUG-xxxx]`, "sem ponto certo para testar = achado de arquitetura" | Alta |
| `aidd-tickets` | Ticket 1 = testes, 2 = código, 3 = refatoração | Isso é fatiar em camadas, o anti-padrão que o original proíbe. O certo é cada ticket entregar um comportamento completo, com "Bloqueado por"; refatoração ampla = adicionar → migrar em lotes → remover | Alta |
| `aidd-grill` | Uma pergunta por vez | Rodadas com todas as perguntas desbloqueadas, cada uma com resposta recomendada; fatos são do agente, decisões são do usuário | Média |
| `aidd-tdd` | Refatorar dentro do ciclo | Refatorar vai para a revisão; pontos de teste combinados antes; proibir teste tautológico, acoplado e em camadas | Média |

O que a nossa versão tem de **melhor** e deve ficar: modo não-interativo do `aidd-grill`, "Validation Command" exato por ticket, Zero Stubs, lista de runners poliglota.

## 2. Integrar (novo)

| Upstream | Nome AIDD | Por quê | Ganho |
|---|---|---|---|
| `writing-for-agents` | `aidd-escrita-agentes` | AGENTS.md (152 linhas) + referência (208) e várias regras que o agente ignora | Menos regras que não mudam nada; ponteiros mais fortes |
| `retro` | `aidd-retro` | Várias memórias "GRAVE" de agente pulando gate | Cada erro mecânico vira gate determinístico em `gates/` |
| `domain-modeling` (CONTEXT.md + ADR) | `CONTEXT.md` + `docs/adr/` | Não existem no repo; "ciclo", "fase", "plano", "sessão" mudam de sentido | Nomes consistentes e menos tokens |
| `pr` | `aidd-entrega` | Caso do checkbox marcado sem código (Sessão 16) | Sem evidência antes/depois, não fecha |
| `wizard` | `aidd-wizard` | Segredos/VPS/Cloudflare feitos à mão; `VPS-CONEXAO.md` saiu do versionamento | Procedimento repetível sem segredo no chat |
| `wait-what` | `aidd-reexplica` | Regra de linguagem simples do usuário | Custo zero |
| `wayfinder` (só 2 seções) | modelo do `aidd-planos` | Planos misturam "ainda não sei" com "fora de escopo" | Escopo explícito |

## 3. Não integrar

| Upstream | Motivo |
|---|---|
| `setup-matt-pocock-skills`, `triage`, `wayfinder` (inteiro) | Dependem de issue tracker com etiquetas e bloqueio nativo; nosso controle é `docs/planos` + ciclos + INDEX |
| `claude-handoff` | Abre agente em segundo plano sem supervisão, mesmo cenário do incidente ORCA; `aidd-handoff` é mais seguro |
| `implement`, `implement-spec` | Já temos `implementacao`/`executing-plans` com gates; o paralelismo por fronteira fica para depois do Ticket 2 |
| `git-guardrails-claude-code`, `setup-pre-commit` | Nossos gates e pre-commit são mais rígidos |
| `setup-ts-deep-modules`, `migrate-to-shoehorn`, `scaffold-exercises` | Só TypeScript / cursos do autor |
| `teach`, `to-questionnaire`, `loop-me`, `writing-beats/fragments/shape` | Produtividade pessoal e escrita, fora do foco |
| `research`, `prototype`, `resolving-merge-conflicts`, `codebase-design`, `improve-codebase-architecture` | Já cobertos (`aidd-pesquisador`, graphify/code-review-graph, `refactor-safely`) ou já instalados globalmente |

## 4. Achado lateral: cópias globais duplicadas

As 33 skills do upstream presentes em `~/.agents/skills/` estão **todas** diferentes da versão atual do upstream (ex.: `diagnosing-bugs` com 272 linhas de diferença). Várias disputam o gatilho com as nossas (`grilling` × `aidd-grill`, `tdd` × `aidd-tdd`, `diagnosing-bugs` × `aidd-diagnose`, `code-review` × `review-changes`). Remoção fica com o usuário (fora do repo); o Ticket 11 só gera o relatório.
