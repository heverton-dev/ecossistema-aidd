# Item — pin-exato-e-hashes-requirements-lockfile

> **Escopo:** Migrar dependências Python para versões exatas fixadas com hashes criptográficos (lockfile via uv/pip-tools) e impor instalação segura com --require-hashes no CI.
> **Status:** [FEITO]
> **Auditoria por reproducao real (12-09-2026):** FEITO. requirements.txt e requirements-dev.txt migrados para pin exato (`==`); requirements.lock e requirements-dev.lock gerados via `uv pip compile --generate-hashes` (todo pacote com >=1 --hash=sha256); `.github/workflows/audit.yml` instala com `pip install --require-hashes -r requirements-dev.lock`; gate novo `gates/G_DEPENDENCIAS_PIN_HASH.py` (10/10 no `audit`) rejeita qualquer regressao (especificador solto, lockfile sem hash, CI sem --require-hashes). Instalação real validada em venv limpo (pip padrão e uv) com exit 0. 88/88 testes de gates passando; `python ecossistema.py audit` 10/10 gates aprovados.

---

## Contexto já investigado

- requirements.txt usa `>=` solto [SEC-4], permitindo que versões novas corrompidas ou comprometidas sejam baixadas automaticamente a qualquer build.

## Definição de Pronto

1. Gerar lockfile determinístico (`uv.lock` ou `requirements.lock` com `--generate-hashes`).
2. Atualizar pre-commit e CI para instalar com `--require-hashes`.
3. Criar gate determinístico que rejeita arquivos de dependência sem pins exatos.

## Critério de saída

- Dependências instaladas exclusivamente com verificação de hash criptográfico.
- Testes reais passando sem stubs falsos.
- Gates de integridade aprovados.

## Prompt de Execução (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Você vai implementar o Item: pin-exato-e-hashes-requirements-lockfile.
Siga rigorosamente a Definição de Pronto acima:
1. Gerar lockfile determinístico (`uv.lock` ou `requirements.lock` com `--generate-hashes`).
2. Atualizar pre-commit e CI para instalar com `--require-hashes`.
3. Criar gate determinístico que rejeita arquivos de dependência sem pins exatos.
Garanta exit 0 nos testes e gates pertinentes.
```

## Prompt de Execução — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item: pin-exato-e-hashes-requirements-lockfile.
Strictly follow the Definition of Done above:
1. Gerar lockfile determinístico (`uv.lock` ou `requirements.lock` com `--generate-hashes`).
2. Atualizar pre-commit e CI para instalar com `--require-hashes`.
3. Criar gate determinístico que rejeita arquivos de dependência sem pins exatos.
Ensure exit code 0 across relevant tests and gates.
```
