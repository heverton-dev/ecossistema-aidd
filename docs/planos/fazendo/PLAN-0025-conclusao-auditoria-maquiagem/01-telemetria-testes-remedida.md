# Item 1 — Telemetria de testes remedida

> **Escopo:** Entra: garantir que o bloco "testes" de `PLANO-EXECUCAO-ESTRUTURADO.json` seja sempre regenerado por script antes de ser lido/citado, nunca editado à mão. Não entra: mudar o formato do JSON ou os números de outros blocos (fases, ferramentas).
> **Status:** [APROVADO — Aguardando Execucao]
> **Nota Atual (0-10):** NAO AUDITADO — evidencia: (nota pendente de medicao real - nao preencher com estimativa)
> **Nota Alvo (0-10):** NAO AUDITADO
> **Nota Real (pos-implementacao):** [Pendente - preencher somente apos o fechamento real deste item/iniciativa, via o mesmo mecanismo que mediu a Nota Atual]

---

## Contexto ja investigado

- `PLANO-EXECUCAO-ESTRUTURADO.json:82-127` (medido em 2026-09-06T22:50:15Z) afirma aidd-master 216 passed/0 failed, aidd-enterprise 205/0, aidd-ops 0/0/0/0.
- Medição ao vivo em 2026-09-07 (auditoria): aidd-master 212 passed/2 failed/4 skipped; aidd-enterprise 201/2/4; aidd-ops 48 passed/8 failed. Três das cinco linhas estavam erradas.
- O próprio arquivo (bloco "fase 6") já documenta a lição aprendida em 2026-09-04: "esse bloco 'testes' passou a ser gerado por script (`python ecossistema.py status --testes`) em vez de digitado a mão" — mas nada re-executa esse script automaticamente; o arquivo ficou parado desde 09-06 enquanto o código mudou.

## Definicao de Pronto

1. Existe um comando (`python ecossistema.py status --testes --write`) que sobrescreve o bloco "testes" do JSON com números medidos na hora da chamada.
2. Esse comando roda automaticamente antes de qualquer commit que toque `tools/**` — via hook do gate criado no item 1, ou via `.githooks/` já existente no repo — de forma que um JSON desatualizado bloqueie o commit ou seja corrigido nele.
3. Rodar o comando agora e confirmar que os 5 números batem exatamente com `pytest -q` ao vivo em cada ferramenta no momento da execução.

## Criterio de saida

- Arquivos criados ou alterados no local correto.
- Testes reais passando sem stubs falsos.
- Gates de integridade aprovados.

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item 1: Telemetria de testes remedida.
Siga rigorosamente a Definicao de Pronto acima.
Nao invente aprovacoes e mantenha as regras do monorepo.
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 1: Telemetria de testes remedida.
Strictly follow the Definition of Done above.
Do not fabricate approvals and maintain monorepo governance rules.
```
