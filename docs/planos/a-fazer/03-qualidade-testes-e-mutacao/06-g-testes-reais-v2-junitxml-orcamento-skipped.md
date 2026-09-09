# Item — g-testes-reais-v2-junitxml-orcamento-skipped

> **Escopo:** Aprimorar o gate G_TESTES_REAIS para consumir métricas estruturadas via JUnitXML em vez de regex em stdout, e impor orçamento estrito para skipped tests.
> **Status:** [RASCUNHO — Aguardando Aprovação Humana]

---

## Contexto já investigado

- G_TESTES_REAIS.py analisa stdout com regex e não falha se houver testes ignorados [GE-1/2].

## Definição de Pronto

1. Executar pytest gerando relatório temporário --junitxml.
2. Fazer parsing XML estruturado.
3. Travar com exit 1 em skipped não autorizado.

## Critério de saída

- Gate extrai métricas 100% de XML estruturado e valida allowlist de skips.
- Testes reais passando sem stubs falsos.
- Gates de integridade aprovados.

## Prompt de Execução (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Você vai implementar o Item: g-testes-reais-v2-junitxml-orcamento-skipped.
Siga rigorosamente a Definição de Pronto acima:
1. Executar pytest gerando relatório temporário --junitxml.
2. Fazer parsing XML estruturado.
3. Travar com exit 1 em skipped não autorizado.
Garanta exit 0 nos testes e gates pertinentes.
```

## Prompt de Execução — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item: g-testes-reais-v2-junitxml-orcamento-skipped.
Strictly follow the Definition of Done above:
1. Executar pytest gerando relatório temporário --junitxml.
2. Fazer parsing XML estruturado.
3. Travar com exit 1 em skipped não autorizado.
Ensure exit code 0 across relevant tests and gates.
```
