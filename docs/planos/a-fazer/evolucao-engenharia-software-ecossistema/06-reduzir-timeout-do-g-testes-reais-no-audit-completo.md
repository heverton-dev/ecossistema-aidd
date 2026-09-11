# Item 6 — Reduzir timeout do G_TESTES_REAIS no audit completo

> **Escopo:** Resolver o estouro de timeout (>300s) que ocorre especificamente no passo `aidd-ops` durante `python ecossistema.py audit` completo — sabendo que `aidd-ops` sozinho roda em ~30s (168 testes). Ajustar o timeout/paralelismo/escopo desse passo dentro do audit agregado, sem reduzir a cobertura real de testes.
> **Status:** [APROVADO — Aguardando Execucao]
> **Nota Atual (0-10):** 5.0 — evidencia: python ecossistema.py audit estoura timeout >300s no passo aidd-ops; aidd-ops passa isolado (168 testes em ~30s)
> **Nota Alvo (0-10):** 9.0
> **Nota Real (pos-implementacao):** [Pendente - preencher somente apos o fechamento real deste item/iniciativa, via o mesmo mecanismo que mediu a Nota Atual]

---

## Contexto ja investigado

- `python ecossistema.py audit` estoura timeout >300s no passo aidd-ops.
- Rodando aidd-ops isolado: 168 testes passam em ~30s — o timeout nao e sobre lentidao real dos testes, e sim de alguma configuracao/interacao do passo agregado.

## Definicao de Pronto

1. Causa raiz do estouro de timeout no passo aidd-ops dentro do audit agregado identificada (ex.: contencao de recursos, configuracao de timeout desalinhada, execucao serial desnecessaria).
2. Correcao aplicada (ajuste de timeout, paralelismo, ou isolamento do passo) sem reduzir a cobertura real de testes.
3. `python ecossistema.py audit` completo roda ate o fim sem estourar timeout no passo aidd-ops.

## Criterio de saida

- `python ecossistema.py audit` completo rodado de verdade, do inicio ao fim, sem timeout no passo aidd-ops.
- Os mesmos ~168 testes de aidd-ops continuam sendo executados (nao removidos/pulados pra "resolver" o timeout).

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item 6: Reduzir timeout do G_TESTES_REAIS no audit completo.
Siga rigorosamente a Definicao de Pronto acima.
Nao invente aprovacoes e mantenha as regras do monorepo.
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 6: Reduzir timeout do G_TESTES_REAIS no audit completo.
Strictly follow the Definition of Done above.
Do not fabricate approvals and maintain monorepo governance rules.
```
