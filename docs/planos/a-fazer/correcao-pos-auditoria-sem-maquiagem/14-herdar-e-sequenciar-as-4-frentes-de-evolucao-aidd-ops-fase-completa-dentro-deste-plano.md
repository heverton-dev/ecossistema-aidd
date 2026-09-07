# Item 14 — Herdar e sequenciar as 4 frentes de evolucao-aidd-ops-fase-completa dentro deste plano

> **Escopo:** Entra: revisar as 4 frentes já rascunhadas em `docs/planos/evolucao-aidd-ops-fase-completa/` e decidir a ordem de execução relativa aos itens 8 e 9 deste plano (que corrigem bugs ativos no mesmo diretório `tools/aidd-ops`). Não entra: reescrever o conteúdo técnico dessas 4 frentes — elas mantêm seu próprio processo de aprovação.
> **Status:** [RASCUNHO — Aguardando Aprovacao Humana]
> **Modelo sugerido:** Claude Sonnet · Antigravity Gemini 3.7 · MiMo mimo-v2.5-pro (planejamento/sequenciamento, não implementação)

---

## Contexto ja investigado

- `docs/planos/evolucao-aidd-ops-fase-completa/00-PROCESSO-E-DECISOES.md` e os 4 arquivos de item (`01-intake-interativo-web-sem-friccao.md`, `02-cofre-local-e-coleta-segura-de-credenciais.md`, `03-appshell-white-label-e-studios-openapi-webhook-mcp.md`, `04-isolamento-estrito-em-vps-compartilhada-e-uninstall-atomico.md`) já existem, com seu próprio processo de aprovação — este item não os substitui.
- Os itens 8 e 9 deste plano corrigem bugs ativos no mesmo diretório (`tools/aidd-ops`) que as 4 frentes vão tocar — risco real de conflito de merge/retrabalho se a ordem for errada (ex.: consertar sincronização de CLI antes de adicionar intake web novo, não depois).

## Definicao de Pronto

1. Ordem de execução definida e registrada (proposta de partida: itens 8 e 9 primeiro — bugs ativos reproduzíveis hoje —, depois as 4 frentes na ordem já rascunhada 01→04, salvo justificativa em contrário).
2. Nenhuma das 4 frentes é marcada como iniciada ou aprovada sem veredito humano explícito nos seus próprios arquivos — esta iniciativa só referencia e sequencia, não aprova escopo alheio.
3. `docs/planos/evolucao-aidd-ops-fase-completa/00-PROCESSO-E-DECISOES.md` ganha uma nota de rastreabilidade linkando para este plano maior.

## Criterio de saida

- Arquivos criados ou alterados no local correto.
- Testes reais passando sem stubs falsos.
- Gates de integridade aprovados.

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item 14: Herdar e sequenciar as 4 frentes de evolucao-aidd-ops-fase-completa dentro deste plano.
Siga rigorosamente a Definicao de Pronto acima.
Nao invente aprovacoes e mantenha as regras do monorepo.
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 14: Herdar e sequenciar as 4 frentes de evolucao-aidd-ops-fase-completa dentro deste plano.
Strictly follow the Definition of Done above.
Do not fabricate approvals and maintain monorepo governance rules.
```
