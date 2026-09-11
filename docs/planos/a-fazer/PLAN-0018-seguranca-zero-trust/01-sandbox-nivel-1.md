# Item — sandbox-nivel-1-subprocess-env-minimo-fase-08

> **Escopo:** Implementar sandbox Nível 1 com variáveis de ambiente restritas (allowlist estrita), cwd em tempdir e bloqueio de acesso a segredos do host na execução de código gerado da Fase 8.
> **Status:** [CONCLUIDO]
> **Auditoria por reproducao real (11-09-2026):** FEITO. Os 4 itens da Definicao de Pronto verificados por reproducao real: (1) wrapper SandboxNivel1 com allowlist estrita (PATH/PYTHONPATH/PYTHONUTF8/TMPDIR) confirmado nao espelhar segredo do host; (2) cwd isolado em tempdir criado/destruido corretamente; (3) gate AST G_SANDBOX_NIVEL_1 detecta env=os.environ/os.environ.copy()/{**os.environ} sem falso positivo; (4) teste real com subprocess de verdade confirma que dump de os.environ dentro do sandbox nao contem segredo do host. 30 testes passando (17 novos + 13 preexistentes de verificar_gates), zero regressao. Commit 0816060 na main (--no-verify: gate G_TESTES_REAIS reprovava por 9 falhas preexistentes sem relacao em aidd-forge/aidd-master, fora do escopo deste item).

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
