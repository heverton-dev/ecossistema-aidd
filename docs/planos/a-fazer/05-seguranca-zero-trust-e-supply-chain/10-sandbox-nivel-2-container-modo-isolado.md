# Item — sandbox-nivel-2-container-modo-isolado

> **Escopo:** Adicionar suporte a Sandbox Nível 2 via container efêmero (--network none, read-only, memória restrita) para execução isolada em ambientes Linux/CI.
> **Status:** [RASCUNHO — Aguardando Aprovação Humana]

---

## Contexto já investigado

- Execuções em ambientes de CI precisam de isolamento total contra ataques de escape de processo [SEC-1].

## Definição de Pronto

1. Criar runner de container efêmero com Docker (`--network none`, `--cap-drop ALL`, `--read-only`).
2. Habilitar via flag `--isolate` no pipeline do generator.
3. Manter fallback seguro para o Sandbox Nível 1 quando o Docker não estiver disponível.

## Critério de saída

- Suporte a execução hermética em container no pipeline autônomo.
- Testes reais passando sem stubs falsos.
- Gates de integridade aprovados.

## Prompt de Execução (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Você vai implementar o Item: sandbox-nivel-2-container-modo-isolado.
Siga rigorosamente a Definição de Pronto acima:
1. Criar runner de container efêmero com Docker (`--network none`, `--cap-drop ALL`, `--read-only`).
2. Habilitar via flag `--isolate` no pipeline do generator.
3. Manter fallback seguro para o Sandbox Nível 1 quando o Docker não estiver disponível.
Garanta exit 0 nos testes e gates pertinentes.
```

## Prompt de Execução — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item: sandbox-nivel-2-container-modo-isolado.
Strictly follow the Definition of Done above:
1. Criar runner de container efêmero com Docker (`--network none`, `--cap-drop ALL`, `--read-only`).
2. Habilitar via flag `--isolate` no pipeline do generator.
3. Manter fallback seguro para o Sandbox Nível 1 quando o Docker não estiver disponível.
Ensure exit code 0 across relevant tests and gates.
```
