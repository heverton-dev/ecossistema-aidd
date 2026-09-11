# Item — gate-owasp-sobre-output-fase-08

> **Escopo:** Conectar o scanner de segurança estático G_CYBERSECURITY_OWASP para inspecionar o código gerado pela Fase 8 antes de permitir a execução do gate I4.
> **Status:** [PARCIAL — parte ja implementada, ver auditoria abaixo]
> **Auditoria por reproducao real (11-09-2026):** PARCIAL. O gate tools/aidd-generator/scripts/gates/G_CYBERSECURITY_OWASP.py existe, mas nao esta plugado: grep -n G_CYBERSECURITY_OWASP scripts/phases/verificar_gates.py nao retorna nada. Ou seja, ele nao bloqueia a Fase 08.

---

## Contexto já investigado

- Nenhum gate de segurança roda sobre output/ do generator [SEC-3/17]. Código malicioso gerado é executado no smoke-test I4 sem qualquer pré-varredura.

## Definição de Pronto

1. Integrar G_CYBERSECURITY_OWASP no pipeline da Fase 08 (`verificar_gates.py`).
2. Bloquear a execução se o código gerado contiver chamadas de alto risco (`os.system`, `eval`, `subprocess` sem shell=False).
3. Adicionar relatório de conformidade no index da Fase 08.

## Critério de saída

- Código gerado com chamadas perigosas é bloqueado antes da execução.
- Testes reais passando sem stubs falsos.
- Gates de integridade aprovados.

## Prompt de Execução (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Você vai implementar o Item: gate-owasp-sobre-output-fase-08.
Siga rigorosamente a Definição de Pronto acima:
1. Integrar G_CYBERSECURITY_OWASP no pipeline da Fase 08 (`verificar_gates.py`).
2. Bloquear a execução se o código gerado contiver chamadas de alto risco (`os.system`, `eval`, `subprocess` sem shell=False).
3. Adicionar relatório de conformidade no index da Fase 08.
Garanta exit 0 nos testes e gates pertinentes.
```

## Prompt de Execução — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item: gate-owasp-sobre-output-fase-08.
Strictly follow the Definition of Done above:
1. Integrar G_CYBERSECURITY_OWASP no pipeline da Fase 08 (`verificar_gates.py`).
2. Bloquear a execução se o código gerado contiver chamadas de alto risco (`os.system`, `eval`, `subprocess` sem shell=False).
3. Adicionar relatório de conformidade no index da Fase 08.
Ensure exit code 0 across relevant tests and gates.
```
