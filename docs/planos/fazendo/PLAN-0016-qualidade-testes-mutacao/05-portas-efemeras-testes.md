# Item — portas-efemeras-testes-integracao-servidor

> **Escopo:** Substituir a porta fixa 3000 nos testes de integração de servidor por alocação dinâmica de porta efêmera (bind 0).
> **Status:** [CONCLUIDO — verificado por reproducao real]
> **Auditoria por reproducao real (11-09-2026):** FEITO. _find_free_port() com bind em porta 0 nos testes de test_database_adapter.py e test_events_driver.py, com a porta obtida repassada a servidor e cliente.

---

## Contexto já investigado

- test_add_module_server_wiring.py e test_compose_suite.py usam porta fixa 3000 [TS-10], colidindo com serviços locais.

## Definição de Pronto

1. Utilizar socket bind 0 para obter porta efêmera livre do SO.
2. Passar porta dinâmica para servidor e cliente.
3. Validar isolamento sem conflito.

## Critério de saída

- Zero dependência da porta fixa 3000 nos testes.
- Testes reais passando sem stubs falsos.
- Gates de integridade aprovados.

## Prompt de Execução (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Você vai implementar o Item: portas-efemeras-testes-integracao-servidor.
Siga rigorosamente a Definição de Pronto acima:
1. Utilizar socket bind 0 para obter porta efêmera livre do SO.
2. Passar porta dinâmica para servidor e cliente.
3. Validar isolamento sem conflito.
Garanta exit 0 nos testes e gates pertinentes.
```

## Prompt de Execução — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item: portas-efemeras-testes-integracao-servidor.
Strictly follow the Definition of Done above:
1. Utilizar socket bind 0 para obter porta efêmera livre do SO.
2. Passar porta dinâmica para servidor e cliente.
3. Validar isolamento sem conflito.
Ensure exit code 0 across relevant tests and gates.
```
