# Item 3 — Registrar duplicacao de codigo real da skill orca-plan-orchestrator nas 7 pastas de harness (sem acao corretiva)

> **Escopo:** Entra: só documentar o achado, com evidência real, neste arquivo e no `00-PROCESSO-E-DECISOES.md`. Não entra: nenhuma mudança de código — este item não tem correção porque o achado não é um bug, é o mecanismo de materialização multi-harness já usado por toda skill deste projeto (mesmo padrão do item 6.2/6.5 da iniciativa `docs/planos/feitos/.../02-direcionamento-estrategico-anti-nih/`).

> **Status:** [REGISTRO — não requer aprovação para execução porque não há execução; fica marcado ✅ ao ser revisado]

---

## Contexto já investigado

- Achado via `code-review-graph` (`list_communities`) em 2026-09-08: 7 comunidades de código idênticas (204 nós cada, mesma coesão 0.3678) correspondem à skill `orca-plan-orchestrator` copiada em `.agents/`, `.claude/`, `.cursor/`, `.gemini/`, `.mimocode/`, `.opencode/` e `skills/` (bare).
- Diferença em relação a outras skills: a maioria das skills deste projeto é só documentação (`SKILL.md` + `references/*.md`); esta tem lógica de programação real — `scripts/circuit_breaker.py`, `scripts/agent_spawner.py`, `scripts/flight_plan.py`, `scripts/state_engine.py`, `scripts/gate_auditor.py`.
- Isso significa que um bug nessa lógica precisa ser corrigido na fonte única (`componentes/compartilhado/skills/orca-plan-orchestrator/` ou onde a fonte canônica viver) e depois sincronizado — o mecanismo de sincronização (`python ecossistema.py components sync`) já existe e já é usado; não há gap de ferramenta aqui, só um lembrete de que mudar essa skill tem efeito em 7 lugares.
- Não é o mesmo tipo de achado dos itens 1 e 2 (que são sobre organização/monitoramento de código) — este item existe só para a auditoria não "esconder" esse achado, coerente com a regra de honestidade deste monorepo.

## Definição de Pronto

1. Achado documentado aqui com os arquivos e o motivo exatos (feito acima).
2. Registrado no `00-PROCESSO-E-DECISOES.md` como concluído (é um registro, não uma implementação).
3. Nenhuma DpP de correção — não aplicável a este item.

## Critério de saída

- Este documento revisado e aceito como registro fiel do achado.
- Nenhum código alterado como parte deste item.

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item 3: Registrar duplicacao de codigo real da skill orca-plan-orchestrator nas 7 pastas de harness (sem acao corretiva).
Siga rigorosamente a Definicao de Pronto acima.
Nao invente aprovacoes e mantenha as regras do monorepo.
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 3: Registrar duplicacao de codigo real da skill orca-plan-orchestrator nas 7 pastas de harness (sem acao corretiva).
Strictly follow the Definition of Done above.
Do not fabricate approvals and maintain monorepo governance rules.
```
