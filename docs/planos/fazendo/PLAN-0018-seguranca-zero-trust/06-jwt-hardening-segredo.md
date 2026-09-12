# Item — jwt-hardening-segredo-prod-exp-obrigatorio

> **Escopo:** Blindar o serviço JWT: proibir segredo padrão hardcoded em ambiente de produção (fail-fast), exigir campo exp obrigatório e integrar verificação de revogação.
> **Status:** [FEITO]
> **Auditoria por reproducao real (12-09-2026):** FEITO. As 3 exigencias confirmadas com reproducao independente nesta sessao (script proprio, sem depender so dos testes ja existentes): (1) processo Python novo com `ENVIRONMENT=production` e sem `JWT_SECRET_KEY` (ou com o valor padrao) aborta o boot com `RuntimeError`, `exit != 0`; com chave forte, `exit 0`; (2) token montado a mao sem a claim `exp` e rejeitado no decode; (3) token valido para de ser aceito apos `JWTService.revoke(token)`. As 6 copias espelhadas de `security.py` (`componentes/compartilhado/src-core` + 3 em `tools/aidd-master` + 3 em `tools/aidd-enterprise`, os `templates/core` e `templates/v2` inclusos) sao byte-a-byte identicas ao arquivo canonico (`diff` real, sem drift). `tests/unit/test_jwt_hardening.py` (8 testes, identico nos dois projetos): 8/8 passando nos dois. Suite completa: aidd-master 334 passed/3 skipped/0 failed; aidd-enterprise 311 passed/3 skipped/0 failed — sem a instabilidade registrada na sessao anterior. Gate `G_SEGURANCA` (20 checks): 18 aprovados/0 falha/2 alertas (nginx/Dockerfile ausentes na raiz, fora de escopo) nos dois projetos. `python ecossistema.py audit`: todos os gates aprovados, incluindo `G_TESTES_REAIS` (suite completa das 5 ferramentas de `tools/`, que na sessao anterior tinha dado instavel — desta vez passou limpo).

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
