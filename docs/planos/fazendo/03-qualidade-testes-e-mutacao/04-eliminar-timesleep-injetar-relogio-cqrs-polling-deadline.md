# Item — eliminar-timesleep-injetar-relogio-cqrs-polling-deadline

> **Escopo:** Eliminar 20+ ocorrências de time.sleep em testes unitários e de integração, substituindo por injeção de relógio virtual em CQRS e polling determinístico com deadline.
> **Status:** [PARCIAL — parte ja implementada, ver auditoria abaixo]
> **Auditoria por reproducao real (11-09-2026):** PARCIAL. Criterio 1 (now_fn em ReadModelCache) FEITO em componentes/compartilhado/src-core/cqrs.py. Criterio 2 (helper de polling com deadline) FEITO mas duplicado: _aguardar_condicao foi copiado dentro de cada arquivo de teste, em vez de um helper compartilhado. Criterio 3 (remover time.sleep) NAO FEITO: grep -rn time.sleep tools/*/tests/unit/ ainda acha esperas fixas, incluindo dois sleep(1) em test_database_adapter.py e test_events_driver.py.

---

## Contexto já investigado

- test_cqrs_local_first.py e test_compose_suite.py usam time.sleep para esperar respostas [TS-9], gerando flakiness.

## Definição de Pronto

1. Expor parâmetro now_fn em ReadModelCache para testes de TTL sem dormir.
2. Criar helper assert_eventually para polling com deadline.
3. Remover time.sleep dos testes unitários.

## Critério de saída

- Zero time.sleep em testes unitários de CQRS e eventos.
- Testes reais passando sem stubs falsos.
- Gates de integridade aprovados.

## Prompt de Execução (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Você vai implementar o Item: eliminar-timesleep-injetar-relogio-cqrs-polling-deadline.
Siga rigorosamente a Definição de Pronto acima:
1. Expor parâmetro now_fn em ReadModelCache para testes de TTL sem dormir.
2. Criar helper assert_eventually para polling com deadline.
3. Remover time.sleep dos testes unitários.
Garanta exit 0 nos testes e gates pertinentes.
```

## Prompt de Execução — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item: eliminar-timesleep-injetar-relogio-cqrs-polling-deadline.
Strictly follow the Definition of Done above:
1. Expor parâmetro now_fn em ReadModelCache para testes de TTL sem dormir.
2. Criar helper assert_eventually para polling com deadline.
3. Remover time.sleep dos testes unitários.
Ensure exit code 0 across relevant tests and gates.
```
