# Item — journal-recuperacao-pos-crash-multi-arquivo

> **Escopo:** Implementar journal de recuperação pós-crash para operações de injeção multi-arquivo, permitindo concluir ou descartar publicações parciais no boot.
> **Status:** [RASCUNHO — Aguardando Aprovação Humana]

---

## Contexto já investigado

- Falha no meio de publicação multi-arquivo deixa staging órfão sem journal de intenção [FS-2], gerando descompasso.

## Definição de Pronto

1. Gravar `_journal.json` no staging listando a sequência ordenada de substituições atômicas pendentes.
2. Criar rotina de recuperação no boot do materializador que inspeciona staging e conclui ou descarta journals órfãos.
3. Registrar log estruturado de recuperação pós-crash.

## Critério de saída

- Teste simulando kill durante publicação multi-arquivo é recuperado com integridade total no próximo boot.
- Testes reais passando sem stubs falsos.
- Gates de integridade aprovados.

## Prompt de Execução (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Você vai implementar o Item: journal-recuperacao-pos-crash-multi-arquivo.
Siga rigorosamente a Definição de Pronto acima:
1. Gravar `_journal.json` no staging listando a sequência ordenada de substituições atômicas pendentes.
2. Criar rotina de recuperação no boot do materializador que inspeciona staging e conclui ou descarta journals órfãos.
3. Registrar log estruturado de recuperação pós-crash.
Garanta exit 0 nos testes e gates pertinentes.
```

## Prompt de Execução — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item: journal-recuperacao-pos-crash-multi-arquivo.
Strictly follow the Definition of Done above:
1. Gravar `_journal.json` no staging listando a sequência ordenada de substituições atômicas pendentes.
2. Criar rotina de recuperação no boot do materializador que inspeciona staging e conclui ou descarta journals órfãos.
3. Registrar log estruturado de recuperação pós-crash.
Ensure exit code 0 across relevant tests and gates.
```
