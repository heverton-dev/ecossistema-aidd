# Item 06: Fase 9 — Validacao Cross-Service

## Escopo
Implementar `scripts/phases/09_integracao.py` que valida todos os artefatos gerados como um todo.

## Definicao de Pronto
- [ ] `09_integracao.py` implementado com 100% determinismo
- [ ] Valida docker-compose.yml com `docker compose config`
- [ ] Valida portas sem colisao (reutiliza `compose_preflight.py` do aidd-ops)
- [ ] Valida .env completeness (todas as variaveis dos templates preenchidas)
- [ ] Valida healthcheck chain (depends_on aponta para services existentes)
- [ ] Valida openapi.json e JSON valido
- [ ] Gera relatorio de validacao com pass/fail por artefato
- [ ] Gate G_FACTORY_INTEGRATION.py (ja existe) estendido com novas checks
- [ ] Testes: fixture clinicas passa em todas as validacoes

## Dependencias
- Itens 01-05 (todos os anteriores)

## Evidencia
- v2 doc §4.3 Fase 9: "100% deterministico"
- `compose_preflight.py` do aidd-ops ja valida YAML e portas
- `preflight.py` do aidd-ops ja tem HTTP healthcheck
