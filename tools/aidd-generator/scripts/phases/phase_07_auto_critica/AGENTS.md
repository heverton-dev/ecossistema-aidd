# Phase 07 — Auto-Crítica (Micro-Ambiente)

## Escopo
Auditoria final: score dinâmico em 6 dimensões, roadmap filtrado por score, investimento estimado.

## Restrições
- Pesos das 6 dimensões somam 100 (20+20+25+10+15+10)
- Score derivado de dados reais (nunca hardcoded)
- _gerar_roadmap() filtra fases já atingidas pelo score atual
- _calcular_investimento() tem premissas explícitas rotuladas como estimativa
- Detecta dinamicamente phase_8 quando presente

## Saída
- `_phase_07_index.json` em `.aidd/cache/data/`
- `relatorio_final.md` em `output/{nome}/`
