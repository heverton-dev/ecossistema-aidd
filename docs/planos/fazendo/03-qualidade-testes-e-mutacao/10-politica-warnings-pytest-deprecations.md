# Item — politica-warnings-pytest-deprecations

> **Escopo:** Revogar o silenciamento global de DeprecationWarning no pytest.ini da raiz e definir política explícita de tratamento de warnings por categoria.
> **Status:** [RASCUNHO — Aguardando Aprovação Humana]
> **Auditoria por reproducao real (11-09-2026):** NAO-FEITO. grep -rn error::UserWarning em pytest.ini / pyproject.toml / setup.cfg nao retorna nada. O filtro generico de deprecations continua.

---

## Contexto já investigado

- pytest.ini da raiz contém filterwarnings = ignore::DeprecationWarning [TS-13], mascarando quebras iminentes de API.

## Definição de Pronto

1. Remover filtro genérico de ignorar todas as deprecations.
2. Tratar warnings de código próprio como erro (-W error::UserWarning).
3. Permitir apenas deprecations pontuais de terceiros com justificativa.

## Critério de saída

- Pytest passando com zero warnings não tratados.
- Testes reais passando sem stubs falsos.
- Gates de integridade aprovados.

## Prompt de Execução (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Você vai implementar o Item: politica-warnings-pytest-deprecations.
Siga rigorosamente a Definição de Pronto acima:
1. Remover filtro genérico de ignorar todas as deprecations.
2. Tratar warnings de código próprio como erro (-W error::UserWarning).
3. Permitir apenas deprecations pontuais de terceiros com justificativa.
Garanta exit 0 nos testes e gates pertinentes.
```

## Prompt de Execução — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item: politica-warnings-pytest-deprecations.
Strictly follow the Definition of Done above:
1. Remover filtro genérico de ignorar todas as deprecations.
2. Tratar warnings de código próprio como erro (-W error::UserWarning).
3. Permitir apenas deprecations pontuais de terceiros com justificativa.
Ensure exit code 0 across relevant tests and gates.
```
