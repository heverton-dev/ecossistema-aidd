# Item 9 — Otimizacao de custo tokens

> **Escopo:** Entra: medir de verdade (não estimar) o consumo de token de uma rodada de `/master`, `/enterprise`, `/ops` e `python ecossistema.py audit`, identificar onde o assistente gasta token em tarefas que o próprio script já resolve, e cortar. Não entra: mexer no núcleo do aidd-generator — lá o gasto é estruturalmente necessário (fases 2-8 dependem de LLM real).
> **Status:** [APROVADO — Aguardando Execucao]
> **Nota Atual (0-10):** NAO AUDITADO — evidencia: (nota pendente de medicao real - nao preencher com estimativa)
> **Nota Alvo (0-10):** NAO AUDITADO
> **Nota Real (pos-implementacao):** [Pendente - preencher somente apos o fechamento real deste item/iniciativa, via o mesmo mecanismo que mediu a Nota Atual]

---

## Contexto ja investigado

- Números informados pelo usuário (não medidos por telemetria bruta nesta auditoria, tratar como estimativa a confirmar): aidd-forge 12k, aidd-generator 178k, aidd-master 69k, aidd-enterprise 52k, aidd-ops 30k, ecossistema-aidd (CLI/audit) 43k tokens por rodada.
- Confirmado no código-fonte: `add_module.py`/`compose_suite.py` (master/enterprise) são 100% template+parâmetro, zero chamada a LLM; `03_sizing.py` (ops) é "aritmética pura" por admissão do próprio código; os 8 gates da raiz são `subprocess`/AST/regex puro.
- Hipótese a validar (não fato ainda, ver relatório): o custo alto nessas 4 linhas provavelmente paga a conversa em volta do script (decidir nomes que poderiam vir de flag/schema, narrar saída de gate que já é texto pronto, redigir `AVALIACAO-AUTO-CRITICA.md`/`RELATORIO-AUDITORIA.json` via LLM quando são deriváveis por template a partir do JSON estruturado que os próprios gates produzem).

## Definicao de Pronto

1. Medir com telemetria real (não estimativa) o consumo de uma rodada de cada um dos 4 fluxos antes de qualquer mudança — linha de base registrada.
2. Listar, com exemplo concreto de arquivo/prompt, quais passos de cada fluxo hoje pedem geração de texto por LLM que poderia ser template puro.
3. Implementar a troca para pelo menos 2 desses passos e remedir o consumo da mesma rodada — reportar redução real (número antes/depois), não estimada, sem perda de informação no relatório/telemetria gerada.

## Criterio de saida

- Arquivos criados ou alterados no local correto.
- Testes reais passando sem stubs falsos.
- Gates de integridade aprovados.

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item 9: Otimizacao de custo tokens.
Siga rigorosamente a Definicao de Pronto acima.
Nao invente aprovacoes e mantenha as regras do monorepo.
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 9: Otimizacao de custo tokens.
Strictly follow the Definition of Done above.
Do not fabricate approvals and maintain monorepo governance rules.
```
