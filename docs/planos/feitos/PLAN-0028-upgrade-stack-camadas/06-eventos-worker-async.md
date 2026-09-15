# 06 — Eventos: Worker Async BLPOP

## Nota Atual: 7/10 | Nota Alvo: 8/10 | Prioridade: BAIXA

## Evidência da Nota Atual
- EventBus InMemory (default) + Redis Streams (distribuído)
- Transactional Outbox com claim atômico
- OutboxWorker polling-based (sleep entre ciclos)
- WebhookDispatcher com HMAC SHA-256

## O que será implementado
1. Substituir polling do OutboxWorker por `BLPOP` (Redis) ou `LISTEN/NOTIFY` (Postgres)
2. Adicionar dead-letter queue para eventos com falha repetida
3. Retry com exponential backoff configurável
4. Consumer lag monitoring via métricas Prometheus

## Arquivos afetados
- `tools/aidd-master/templates/v2/outbox_worker.py` (refatorar para async)
- `tools/aidd-master/templates/v2/events.py` (adicionar dead-letter)

## Critério de aceitação
- [ ] Worker processa eventos em < 100ms (vs. polling de 1-5s)
- [ ] Dead-letter queue funciona para eventos com 3+ falhas
- [ ] Métricas de lag expostas em /metrics

## Estimativa
- Esforço: Médio (~1-2 dias)
- Impacto: +1 ponto (7→8)
