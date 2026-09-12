# Item — registry-writers-com-lock-e-rename-atomico

> **Escopo:** Implementar lock de arquivo cooperativo e atomic rename na atualização de registries (CAPABILITIES.json e mcp.json) para evitar lost updates em injeções simultâneas.
> **Status:** [EM EXECUCAO]
> **Auditoria por reproducao real (11-09-2026):** NAO-FEITO. Nenhuma biblioteca de lock cooperativo em uso: grep -rln fcntl/msvcrt/filelock/fasteners nao retorna nada.

---

## Contexto já investigado

- Gravação de CAPABILITIES e mcp.json é read-modify-write sem lock [FS-5]. Injeções paralelas de componentes causam perda de registros.

## Definição de Pronto

1. Utilizar lockfile cooperativo (ex: fcntl/msvcrt via fastener ou context manager atômico) para leitura e escrita dos registries.
2. Gravar o novo JSON em arquivo temporário e aplicar via `os.replace`.
3. Garantir limpeza de lockfiles residuais em caso de falha.

## Critério de saída

- Teste com 2 injeções concorrentes preserva as entradas de ambos os componentes nos manifestos.
- Testes reais passando sem stubs falsos.
- Gates de integridade aprovados.

## Prompt de Execução (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Você vai implementar o Item: registry-writers-com-lock-e-rename-atomico.
Siga rigorosamente a Definição de Pronto acima:
1. Utilizar lockfile cooperativo (ex: fcntl/msvcrt via fastener ou context manager atômico) para leitura e escrita dos registries.
2. Gravar o novo JSON em arquivo temporário e aplicar via `os.replace`.
3. Garantir limpeza de lockfiles residuais em caso de falha.
Garanta exit 0 nos testes e gates pertinentes.
```

## Prompt de Execução — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item: registry-writers-com-lock-e-rename-atomico.
Strictly follow the Definition of Done above:
1. Utilizar lockfile cooperativo (ex: fcntl/msvcrt via fastener ou context manager atômico) para leitura e escrita dos registries.
2. Gravar o novo JSON em arquivo temporário e aplicar via `os.replace`.
3. Garantir limpeza de lockfiles residuais em caso de falha.
Ensure exit code 0 across relevant tests and gates.
```
