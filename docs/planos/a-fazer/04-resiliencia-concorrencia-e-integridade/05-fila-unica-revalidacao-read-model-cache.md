# Item — fila-unica-revalidacao-read-model-cache

> **Escopo:** Substituir o disparo descontrolado de threads daemon no ReadModelCache por uma fila única de revalidação com 1 worker coordenado.
> **Status:** [RASCUNHO — Aguardando Aprovação Humana]

---

## Contexto já investigado

- get_or_revalidate dispara thread daemon por cache miss concorrente [SQL-3], podendo exaurir o pool de conexões SQLite sem aviso.

## Definição de Pronto

1. Criar fila interna com 1 worker thread para revalidações assíncronas do read-model.
2. Descartar revalidações duplicadas para a mesma chave se já houver uma em processamento.
3. Instrumentar métricas de telemetria para tempo máximo de stale.

## Critério de saída

- Teste com 100 misses simultâneos mantém pool SQLite estável e fila única processando ordenadamente.
- Testes reais passando sem stubs falsos.
- Gates de integridade aprovados.

## Prompt de Execução (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Você vai implementar o Item: fila-unica-revalidacao-read-model-cache.
Siga rigorosamente a Definição de Pronto acima:
1. Criar fila interna com 1 worker thread para revalidações assíncronas do read-model.
2. Descartar revalidações duplicadas para a mesma chave se já houver uma em processamento.
3. Instrumentar métricas de telemetria para tempo máximo de stale.
Garanta exit 0 nos testes e gates pertinentes.
```

## Prompt de Execução — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item: fila-unica-revalidacao-read-model-cache.
Strictly follow the Definition of Done above:
1. Criar fila interna com 1 worker thread para revalidações assíncronas do read-model.
2. Descartar revalidações duplicadas para a mesma chave se já houver uma em processamento.
3. Instrumentar métricas de telemetria para tempo máximo de stale.
Ensure exit code 0 across relevant tests and gates.
```
