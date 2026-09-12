# Item — jwt-hardening-segredo-prod-exp-obrigatorio

> **Escopo:** Blindar o serviço JWT: proibir segredo padrão hardcoded em ambiente de produção (fail-fast), exigir campo exp obrigatório e integrar verificação de revogação.
> **Status:** [EM EXECUCAO]
> **Auditoria por reproducao real (11-09-2026):** NAO-FEITO. componentes/compartilhado/src-core/security.py faz o oposto do exigido: quando JWT_SECRET_KEY esta vazia, ele cai num default embutido (DEV_ONLY_INSECURE_SECRET_CHANGE_BEFORE_DEPLOY) em vez de abortar o boot.

---

## Contexto já investigado

- security.py contém segredo default hardcoded em fallback [SEC-11] e aceita tokens sem expiração.

## Definição de Pronto

1. Lançar erro fatal no boot em ambiente de produção se JWT_SECRET_KEY for o default ou estiver vazio.
2. Rejeitar tokens sem claim `exp` explícito no decode.
3. Ligar o mecanismo de revogação de token na verificação padrão.

## Critério de saída

- Zero risco de tokens forjados com segredo de desenvolvimento em produção.
- Testes reais passando sem stubs falsos.
- Gates de integridade aprovados.

## Prompt de Execução (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Você vai implementar o Item: jwt-hardening-segredo-prod-exp-obrigatorio.
Siga rigorosamente a Definição de Pronto acima:
1. Lançar erro fatal no boot em ambiente de produção se JWT_SECRET_KEY for o default ou estiver vazio.
2. Rejeitar tokens sem claim `exp` explícito no decode.
3. Ligar o mecanismo de revogação de token na verificação padrão.
Garanta exit 0 nos testes e gates pertinentes.
```

## Prompt de Execução — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item: jwt-hardening-segredo-prod-exp-obrigatorio.
Strictly follow the Definition of Done above:
1. Lançar erro fatal no boot em ambiente de produção se JWT_SECRET_KEY for o default ou estiver vazio.
2. Rejeitar tokens sem claim `exp` explícito no decode.
3. Ligar o mecanismo de revogação de token na verificação padrão.
Ensure exit code 0 across relevant tests and gates.
```
