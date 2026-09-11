# Item — mcp-defensivo-cap-limite-e-env-denylist

> **Escopo:** Implementar teto máximo no parâmetro limite das queries MCP e deny-list de variáveis de ambiente no launcher de servidores MCP.
> **Status:** [RASCUNHO — Aguardando Aprovação Humana]
> **Auditoria por reproducao real (11-09-2026):** NAO-FEITO. Nao ha deny-list de segredos no launcher de MCP nem teto de 500 registros em sistema_executar_consulta.

---

## Contexto já investigado

- mcp_server.py aceita limite arbitrário sem teto [SEC-15], gerando risco de DoS de memória. Subprocessos herdam secrets no launcher.

## Definição de Pronto

1. Limitar o parâmetro `limite` a no máximo 500 registros em `sistema_executar_consulta`.
2. Adicionar deny-list de segredos (`JWT_SECRET_KEY`, `SSH_KEY_PATH`, `*_API_KEY`) no launcher de servidores MCP.
3. Bloquear chamadas `executescript` em conexões com RLS ativo.

## Critério de saída

- Servidores MCP blindados contra DoS e vazamento de segredos.
- Testes reais passando sem stubs falsos.
- Gates de integridade aprovados.

## Prompt de Execução (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Você vai implementar o Item: mcp-defensivo-cap-limite-e-env-denylist.
Siga rigorosamente a Definição de Pronto acima:
1. Limitar o parâmetro `limite` a no máximo 500 registros em `sistema_executar_consulta`.
2. Adicionar deny-list de segredos (`JWT_SECRET_KEY`, `SSH_KEY_PATH`, `*_API_KEY`) no launcher de servidores MCP.
3. Bloquear chamadas `executescript` em conexões com RLS ativo.
Garanta exit 0 nos testes e gates pertinentes.
```

## Prompt de Execução — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item: mcp-defensivo-cap-limite-e-env-denylist.
Strictly follow the Definition of Done above:
1. Limitar o parâmetro `limite` a no máximo 500 registros em `sistema_executar_consulta`.
2. Adicionar deny-list de segredos (`JWT_SECRET_KEY`, `SSH_KEY_PATH`, `*_API_KEY`) no launcher de servidores MCP.
3. Bloquear chamadas `executescript` em conexões com RLS ativo.
Ensure exit code 0 across relevant tests and gates.
```
