# Item 5 — Corrigir drift de documentacao do G_HONESTIDADE_ROTULO (AGENTS.md + termos_proibidos_marketing.json)

> **Escopo:** Atualizar AGENTS.md (secao 4) e gates/termos_proibidos_marketing.json pra refletir que o G_HONESTIDADE_ROTULO ja passa (52 arquivos, 0 termos proibidos, "blindagem militar" ja removido de G_SEGURANCA.py) — hoje a documentacao ainda cita uma violacao pendente que nao existe mais.
> **Status:** [APROVADO — Aguardando Execucao]
> **Nota Atual (0-10):** 6.0 — evidencia: G_HONESTIDADE_ROTULO passa (52 arquivos, 0 termos) mas AGENTS.md secao 4 e gates/termos_proibidos_marketing.json ainda citam violacao pendente em G_SEGURANCA.py
> **Nota Alvo (0-10):** 10.0
> **Nota Real (pos-implementacao):** [Pendente - preencher somente apos o fechamento real deste item/iniciativa, via o mesmo mecanismo que mediu a Nota Atual]

---

## Contexto ja investigado

- G_HONESTIDADE_ROTULO rodado de verdade: aprovado, 52 arquivos, 0 termos proibidos.
- AGENTS.md secao 4 e gates/termos_proibidos_marketing.json ainda citam a violacao antiga (ja corrigida em G_SEGURANCA.py) como pendente.

## Definicao de Pronto

1. AGENTS.md secao 4 atualizada pra refletir o estado real (gate aprovado, sem violacao pendente).
2. gates/termos_proibidos_marketing.json revisado/atualizado pra nao citar mais a violacao ja corrigida como pendente.
3. `python gates/G_HONESTIDADE_ROTULO.py` (ou equivalente) rodado de novo confirma aprovado.

## Criterio de saida

- Documentacao e gate concordam entre si (nenhuma mencao a violacao que nao existe mais).
- Gate rodado de verdade, aprovado.

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item 5: Corrigir drift de documentacao do G_HONESTIDADE_ROTULO (AGENTS.md + termos_proibidos_marketing.json).
Siga rigorosamente a Definicao de Pronto acima.
Nao invente aprovacoes e mantenha as regras do monorepo.
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 5: Corrigir drift de documentacao do G_HONESTIDADE_ROTULO (AGENTS.md + termos_proibidos_marketing.json).
Strictly follow the Definition of Done above.
Do not fabricate approvals and maintain monorepo governance rules.
```
