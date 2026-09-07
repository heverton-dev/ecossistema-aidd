# Item 13 — Reduzir custo de token nas ferramentas de nucleo deterministico (master/enterprise/ops/CLI)

> **Escopo:** Entra: medir de verdade (não estimar) o consumo de token de uma rodada de `/master`, `/enterprise`, `/ops` e `python ecossistema.py audit`, identificar onde o assistente gasta token em tarefas que o próprio script já resolve, e cortar. Não entra: mexer no núcleo do aidd-generator — lá o gasto é estruturalmente necessário (fases 2-8 dependem de LLM real).
> **Status:** [RASCUNHO — Aguardando Aprovacao Humana]
> **Modelo sugerido:** Claude Opus · Antigravity Gemini 3.8 · MiMo mimo-v2.5-pro (requer profiling real e redesenho de fluxo, não é troca mecânica)
> **Dependência com o plano estratégico:** a Fase 3 (reauditoria) de `direcionamento-estrategico-anti-nih/` já remede o consumo de token de tudo depois da troca de motor — este item **não duplica** essa remedição formal antes/depois. Este item cobre só a linha de base inicial e a implementação de pelo menos 2 trocas (passo 3 da Definição de Pronto); a comparação final "antes/depois" definitiva fica a cargo da Fase 3.
> **Ferramenta candidata (item 30 do levantamento NIH, achada em 2026-09-07):** **Langfuse** — mede consumo de LLM de verdade em vez de estimativa/autodeclaração. Checar primeiro `github.com/Heverton-web/token-economy-core` (projeto próprio do usuário no mesmo tema) antes de adotar, para não duplicar esforço já existente.

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
Voce vai implementar o Item 13: Reduzir custo de token nas ferramentas de nucleo deterministico (master/enterprise/ops/CLI).
Siga rigorosamente a Definicao de Pronto acima.
Nao invente aprovacoes e mantenha as regras do monorepo.
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 13: Reduzir custo de token nas ferramentas de nucleo deterministico (master/enterprise/ops/CLI).
Strictly follow the Definition of Done above.
Do not fabricate approvals and maintain monorepo governance rules.
```
