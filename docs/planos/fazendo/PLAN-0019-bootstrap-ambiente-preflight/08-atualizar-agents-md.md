# Item — atualizar-agents-md-bootstrap-preflight-sessao

> **Escopo:** Atualizar a Seção 0 de AGENTS.md para incluir a verificação de preflight do host na rotina de bootstrap automático de início de sessão dos assistentes.
> **Status:** [EM EXECUCAO]
> **Auditoria por reproducao real (11-09-2026):** NAO-FEITO. AGENTS.md secao 0 nao menciona preflight-host.

---

## Contexto já investigado

- A rotina de bootstrap de sessão checava apenas `dependencia verify` de skills, mas não alertava sobre ausência de Node/Docker.

## Definição de Pronto

1. Atualizar a instrução do AGENTS.md §0 para executar `python ecossistema.py preflight-host --json`.
2. Se houver dependência de sistema crítica ausente, instruir o assistente a alertar o usuário em uma frase objetiva.
3. Preservar o caráter silencioso e não invasivo quando tudo estiver em conformidade.

## Critério de saída

- Assistentes de IA realizam verificação completa de host e skills no primeiro contato.
- Testes reais passando sem stubs falsos.
- Gates de integridade aprovados.

## Prompt de Execução (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Você vai implementar o Item: atualizar-agents-md-bootstrap-preflight-sessao.
Siga rigorosamente a Definição de Pronto acima:
1. Atualizar a instrução do AGENTS.md §0 para executar `python ecossistema.py preflight-host --json`.
2. Se houver dependência de sistema crítica ausente, instruir o assistente a alertar o usuário em uma frase objetiva.
3. Preservar o caráter silencioso e não invasivo quando tudo estiver em conformidade.
Garanta exit 0 nos testes e gates pertinentes.
```

## Prompt de Execução — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item: atualizar-agents-md-bootstrap-preflight-sessao.
Strictly follow the Definition of Done above:
1. Atualizar a instrução do AGENTS.md §0 para executar `python ecossistema.py preflight-host --json`.
2. Se houver dependência de sistema crítica ausente, instruir o assistente a alertar o usuário em uma frase objetiva.
3. Preservar o caráter silencioso e não invasivo quando tudo estiver em conformidade.
Ensure exit code 0 across relevant tests and gates.
```
