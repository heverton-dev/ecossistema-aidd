# Item 04: Fase 7 — Gerador de Webhooks

## Escopo
Implementar `scripts/phases/07_webhooks.py` que gera endpoints e contratos de webhook entre servicos.

## Definicao de Pronto
- [ ] `07_webhooks.py` implementado com delegacao LLM
- [ ] Mapeamento de integracoes em `data/integracoes.json`:
  - Quais pares de servicos se comunicam
  - Payload schema por tipo de evento
  - Endpoints de webhook por servico
- [ ] Para cada par: gera payload schema (JSON), webhook receiver, webhook sender config
- [ ] Output: `webhooks/` com contratos e handlers
- [ ] Valida: JSON schemas validos
- [ ] Gate G_FACTORY_WEBHOOKS.py verifica contratos
- [ ] Testes: fixture clinicas gera webhooks para Typebot->Twenty, Chatwoot->Cal.com

## Dependencias
- Item 01 (templates)
- PLAN-0027 item 02 (analisador)

## Evidencia
- v2 doc §4.3 Fase 7: "1 chamada LLM, ~2k tokens"
- `componentes/compartilhado/src-core/webhooks.py` existe (reutilizavel)
- Cada nicho tem fluxos de integracao especificos no v2 doc §6
