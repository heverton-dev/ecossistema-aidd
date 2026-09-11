# Item — sandbox-nivel-1-subprocess-env-minimo-fase-08

> **Escopo:** Implementar sandbox Nível 1 com variáveis de ambiente restritas (allowlist estrita), cwd em tempdir e bloqueio de acesso a segredos do host na execução de código gerado da Fase 8.
> **Status:** [RASCUNHO — Aguardando Aprovação Humana]
> **Auditoria por reproducao real (11-09-2026):** NAO-FEITO. Os unicos resultados de sanitiz no generator sao de sanitizacao de string JSON (utils_delegacao.py), assunto diferente. Nao ha wrapper de env sanitizado nem gate AST de heranca de ambiente.

---

## Contexto já investigado

- 08_implementador.py executa pytest e gate I4 herdando todo o os.environ [SEC-1/2], expondo chaves de API e JWT_SECRET_KEY ao código gerado por LLM.

## Definição de Pronto

1. Criar wrapper de execução com env sanitizado (apenas PATH, PYTHONPATH do projeto, PYTHONUTF8, TMPDIR).
2. Isolar cwd em diretório temporário restrito.
3. Criar gate AST verificando que subprocessos de código gerado nunca herdam os.environ completo.
4. Testar que código gerado com dump de variáveis não enxerga chaves de API.

## Critério de saída

- Subprocessos de teste rodam com env mínimo e zero vazamento de credenciais.
- Testes reais passando sem stubs falsos.
- Gates de integridade aprovados.

## Prompt de Execução (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Você vai implementar o Item: sandbox-nivel-1-subprocess-env-minimo-fase-08.
Siga rigorosamente a Definição de Pronto acima:
1. Criar wrapper de execução com env sanitizado (apenas PATH, PYTHONPATH do projeto, PYTHONUTF8, TMPDIR).
2. Isolar cwd em diretório temporário restrito.
3. Criar gate AST verificando que subprocessos de código gerado nunca herdam os.environ completo.
4. Testar que código gerado com dump de variáveis não enxerga chaves de API.
Garanta exit 0 nos testes e gates pertinentes.
```

## Prompt de Execução — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item: sandbox-nivel-1-subprocess-env-minimo-fase-08.
Strictly follow the Definition of Done above:
1. Criar wrapper de execução com env sanitizado (apenas PATH, PYTHONPATH do projeto, PYTHONUTF8, TMPDIR).
2. Isolar cwd em diretório temporário restrito.
3. Criar gate AST verificando que subprocessos de código gerado nunca herdam os.environ completo.
4. Testar que código gerado com dump de variáveis não enxerga chaves de API.
Ensure exit code 0 across relevant tests and gates.
```
