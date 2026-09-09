# Item — eliminar-timesleep-injetar-relogio-cqrs-polling-deadline

> **Escopo:** Eliminar 20+ ocorrências de time.sleep em testes unitários e de integração, substituindo por injeção de relógio virtual em CQRS e polling determinístico com deadline.
> **Status:** [RASCUNHO — Aguardando Aprovação Humana]

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
