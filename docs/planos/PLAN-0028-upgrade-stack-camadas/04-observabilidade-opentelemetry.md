# 04 — Observabilidade: OpenTelemetry SDK

## Nota Atual: 7/10 | Nota Alvo: 9/10 | Prioridade: ALTA

## Evidência da Nota Atual
- Metrics: prometheus_client (implementado)
- Audit: SHA-256 chained log (brilhante)
- Tracing: @trace_span decorator (NIH, básico)
- Logging: print-based (gap crítico)
- Sem distributed tracing

## O que será implementado
1. Adicionar `opentelemetry-api` + `opentelemetry-sdk` + `opentelemetry-exporter-otlp`
2. Auto-instrumentação para FastAPI (`opentelemetry-instrumentation-fastapi`)
3. Structured logging via `structlog` (substituir prints)
4. Trace spans para operações de banco (SQLAlchemy)
5. Export para Jaeger/Zipkin (configurável via env)

## Arquivos afetados
- `requirements.txt` (adicionar deps OpenTelemetry)
- `tools/aidd-master/templates/v2/server_fastapi.py` (adicionar instrumentação)
- `tools/aidd-master/templates/v2/` (novo: `logging_config.py`)

## Critério de aceitação
- [ ] Traces aparecem no Jaeger/Zipkin
- [ ] Logs estruturados (JSON) em produção
- [ ] Métricas Prometheus + traces correlacionados

## Estimativa
- Esforço: Alto (~2-3 dias)
- Impacto: +2 pontos (7→9)
