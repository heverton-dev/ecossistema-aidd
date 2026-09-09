# Item — tratamento-falhas-npx-bootstrap-skills

> **Escopo:** Tratar FileNotFoundError em POSIX e traduzir mensagens de erro do cmd.exe no Windows durante a execução de npx em `gestor_dependencias.py`, preservando o relatório de bootstrap.
> **Status:** [RASCUNHO — Aguardando Aprovação Humana]

---

## Contexto já investigado

- Ausência de npx lança FileNotFoundError não tratado no Linux/Mac e gera saída opaca de exit code no Windows [BP-2], perdendo o relatório de skills já instaladas.

## Definição de Pronto

1. Checar previamente `shutil.which('npx')` (e `npx.cmd` no Windows) antes de disparar o subprocess.
2. Se ausente, registrar erro amigável orientando: 'Node.js/npx ausente. Instale Node.js LTS ou execute preflight-host --fix'.
3. Preservar o relatório estruturado de skills já instaladas sem abortar o script com traceback.

## Critério de saída

- Bootstrap sem Node.js emite diagnóstico claro e mantém integridade do relatório de dependências.
- Testes reais passando sem stubs falsos.
- Gates de integridade aprovados.

## Prompt de Execução (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Você vai implementar o Item: tratamento-falhas-npx-bootstrap-skills.
Siga rigorosamente a Definição de Pronto acima:
1. Checar previamente `shutil.which('npx')` (e `npx.cmd` no Windows) antes de disparar o subprocess.
2. Se ausente, registrar erro amigável orientando: 'Node.js/npx ausente. Instale Node.js LTS ou execute preflight-host --fix'.
3. Preservar o relatório estruturado de skills já instaladas sem abortar o script com traceback.
Garanta exit 0 nos testes e gates pertinentes.
```

## Prompt de Execução — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item: tratamento-falhas-npx-bootstrap-skills.
Strictly follow the Definition of Done above:
1. Checar previamente `shutil.which('npx')` (e `npx.cmd` no Windows) antes de disparar o subprocess.
2. Se ausente, registrar erro amigável orientando: 'Node.js/npx ausente. Instale Node.js LTS ou execute preflight-host --fix'.
3. Preservar o relatório estruturado de skills já instaladas sem abortar o script com traceback.
Ensure exit code 0 across relevant tests and gates.
```
