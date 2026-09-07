# Item 6 — Fase 4 - Investimento no diferencial real (pipeline do generator, protocolo delegado, materializador multi-harness)

> **Escopo:** Entra: só depois da Fase 3 provar que a base está sólida, decidir com o usuário onde investir esforço de verdade nos dois diferenciais sem equivalente de mercado (pipeline/protocolo delegado do generator; materializador multi-harness). Não entra: começar esse investimento antes da Fase 3 estar concluída — investir em diferencial sobre uma base não comprovada repete o erro original.
> **Status:** [RASCUNHO — Aguardando Aprovacao Humana — bloqueado até a Fase 3 (item 5) ter relatório publicado]
> **Modelo sugerido:** Claude Opus · Antigravity Gemini 3.8 · MiMo mimo-v2.5-pro (definição de roadmap de produto, não implementação mecânica)

---

## Contexto ja investigado

- Os únicos 2 itens do levantamento NIH marcados como "sem equivalente de mercado" (seção 5 de `docs/features/oportunidades-reaproveitamento-oss-nih.md`): sync de skill/comando/spec pra 7 harnesses com fonte física única (`componentes/`), e o protocolo delegado do generator (falar com o assistente ativo da sessão sem exigir API key externa).
- Fleet discovery (`fleet_discovery.py`) também citado como nicho demais pra ter lib pronta — candidato a receber atenção nesta fase também, não só os dois principais.

## Definicao de Pronto

1. Fase 3 (item 5) concluída com relatório publicado antes deste item começar.
2. Lista de melhorias concretas pro protocolo delegado e pro materializador multi-harness, priorizada com o usuário (ex.: reduzir timeout de polling do protocolo delegado, cobrir mais harnesses no materializador, robustecer fleet discovery pra novos binários).
3. Cada melhoria aprovada vira seu próprio item de execução com Definição de Pronto checável — este item só define a lista e a prioridade, não implementa.

## Criterio de saida

- Arquivos criados ou alterados no local correto.
- Testes reais passando sem stubs falsos.
- Gates de integridade aprovados.

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item 6: Fase 4 - Investimento no diferencial real (pipeline do generator, protocolo delegado, materializador multi-harness).
Siga rigorosamente a Definicao de Pronto acima.
Nao invente aprovacoes e mantenha as regras do monorepo.
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 6: Fase 4 - Investimento no diferencial real (pipeline do generator, protocolo delegado, materializador multi-harness).
Strictly follow the Definition of Done above.
Do not fabricate approvals and maintain monorepo governance rules.
```
