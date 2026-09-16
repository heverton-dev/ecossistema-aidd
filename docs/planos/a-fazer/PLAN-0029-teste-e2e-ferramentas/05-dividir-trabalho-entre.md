# Item 5 — Dividir trabalho entre agentes

> **Escopo:** Item CONDICIONAL. So entra em jogo se o item 3 mostrar que uma unica sessao/agente nao da conta do volume de pedidos do protocolo delegado, ou se o usuario explicitamente quiser testar o `orchestrate` neste ciclo. Nao entra: disparar qualquer ambiente (`orca`/`subagent`/`gitworktree`) sem decisao humana explicita — a propria CLI exige isso.
> **Status:** [APROVADO — Aguardando Execucao]
> **Nota Atual (0-10):** NAO AUDITADO — evidencia: (nota pendente de medicao real - nao preencher com estimativa)
> **Nota Alvo (0-10):** 9
> **Nota Real (pos-implementacao):** [Pendente - preencher somente apos o fechamento real deste item/iniciativa, via o mesmo mecanismo que mediu a Nota Atual]

---

## Contexto ja investigado

- `python ecossistema.py orchestrate <plano> [--dry-run] [--resume] [--ambiente {orca,subagent,gitworktree}] [--harness {mimo,opencode,claude,agy}] ...` gera um "Flight Plan" a partir de um plano ORCA — o CLI NUNCA executa a orquestracao sozinho, so compila o JSON no formato certo; quem dispara de fato e sempre o assistente da sessao, com revisao humana.
- A Lei 7 do `AGENTS.md` do monorepo e explicita: "Developer in Control: Strictly sequential, interactive executions. Zero invisible headless background subagents." Ou seja, este item so pode rodar com confirmacao humana em cada disparo, nunca em background sem supervisao.
- Ambiente `gitworktree` executa orquestracao multi-agente nativa de verdade (git worktrees + harness), sem depender do app ORCA — e o mais provavel de ser usado neste teste, se necessario.

## Definicao de Pronto

1. So iniciar este item apos o item 3 terminar (com sucesso ou com um bloqueio real documentado) e apos o usuario confirmar explicitamente que quer testar `orchestrate` neste ciclo.
2. `python ecossistema.py orchestrate <caminho-do-plano> --dry-run` roda primeiro e mostra o Flight Plan gerado sem disparar nada.
3. Só depois de revisao humana do dry-run, disparar de verdade com `--ambiente gitworktree` (ou o ambiente que o usuario escolher), sempre com confirmacao explicita antes de cada disparo real.

## Criterio de saida

- Nenhum disparo de orquestracao aconteceu sem uma mensagem explicita de "pode disparar" do usuario.
- O `--dry-run` foi executado e o Flight Plan foi lido de verdade antes de qualquer execucao real.

## Comandos estruturados (ordem real de execucao — sempre pausando para confirmacao humana)

```bash
cd ecossistema-aidd
python ecossistema.py orchestrate docs/planos/PLAN-0029-teste-e2e-ferramentas --dry-run
# PARAR AQUI e mostrar o Flight Plan gerado ao usuario.
# Só depois de "pode disparar" explicito:
python ecossistema.py orchestrate docs/planos/PLAN-0029-teste-e2e-ferramentas --ambiente gitworktree --yes
```

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item 5: Dividir trabalho entre agentes - MAS SO SE o item 3 realmente
precisar disso, ou se o usuario pedir explicitamente para testar o orchestrate.
Rode primeiro com --dry-run e PARE - mostre o Flight Plan gerado ao usuario antes de qualquer coisa.
So dispare de verdade apos uma mensagem explicita de aprovacao do usuario para ESSE disparo especifico
(aprovar o plano geral nao conta como autorizacao de execucao).
Nunca dispare orchestrate sozinho, em background, sem supervisao - a Lei 7 do AGENTS.md exige
execucao sequencial e interativa, nunca headless invisivel.
Siga rigorosamente a Definicao de Pronto acima.
Nao invente aprovacoes e mantenha as regras do monorepo.
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 5: Dividir trabalho entre agentes (split work across agents) -
BUT ONLY IF item 3 actually needs it, or the user explicitly asks to test orchestrate.
Run with --dry-run first and STOP - show the generated Flight Plan to the user before anything else.
Only trigger a real run after an explicit approval message from the user for THAT specific run
(approving the overall plan document does not count as authorization to execute).
Never trigger orchestrate on your own, in the background, unsupervised - AGENTS.md Law 7 requires
strictly sequential, interactive execution, never invisible headless subagents.
Strictly follow the Definition of Done above.
Do not fabricate approvals and maintain monorepo governance rules.
```
