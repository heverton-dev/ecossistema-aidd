# 03 — Testes: Hypothesis Property-Based

## Nota Atual: 7/10 | Nota Alvo: 9/10 | Prioridade: MÉDIA

## Evidência da Nota Atual
- pytest 9.1.1 + pytest-cov 7.1.0 + pytest-asyncio
- 16 Quality Gates determinísticos (zero mocks)
- mutmut 2.4.4 nas dependências mas não integrado nos gates
- Sem property-based testing

## O que será implementado
1. Adicionar `hypothesis` em `requirements.txt`
2. Criar testes property-based para:
   - DatabaseAdapter (SQLite/Postgres tradução de queries)
   - JWTService (encode/decode roundtrip)
   - EventBus (pub/sub delivery guarantee)
   - Transactional Outbox (idempotência)
3. Integrar mutmut nos gates existentes

## Arquivos afetados
- `requirements.txt` (adicionar `hypothesis`)
- `tests/` (novos testes property-based)
- `gates/G_TESTES_REAIS.py` (adicionar mutmut)

## Critério de aceitação
- [ ] `pytest tests/ --hypothesis-seed=0` passa
- [ ] Pelo menos 10 propriedades testadas
- [ ] mutmut roda semmutações sobreviventes

## Estimativa
- Esforço: Médio (~1-2 dias)
- Impacto: +2 pontos (7→9)
