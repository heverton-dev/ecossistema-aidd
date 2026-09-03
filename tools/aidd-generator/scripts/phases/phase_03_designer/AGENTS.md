# Phase 03 — Designer (Micro-Ambiente)

## Escopo
Design com 5 subagentes paralelos (arquitetura, scripts, testes, tokens, stack).

## Restrições
- 5 subagentes via ThreadPoolExecutor (não sequencial)
- Cada subagente: prompt isolado com schema da Fase 2
- Consolidação mapeia cada subagente para chave correta do design
- Retry para subagentes com resposta vazia

## Schemas Draft 2020-12
- Todo design DEVE ser validado contra JSON Schema Draft 2020-12
- O schema de saída `design_aidd_phase3.json` DEVE declarar:
  - `camadas[]`: array de objetos com `numero`, `nome`, `responsabilidade`, `artefatos`
  - `scripts[]`: array com `camada`, `nome`, `responsabilidade`, `pseudocodigo`, `determinismo_percentual`, `teste`
  - `tokens`: objeto com `fases[]`, `total_tokens`, `percentual_determinismo`
  - `ferramentas[]`: array com `nome`, `tipo`, `proposito`, `escopo`, `justificativa`
  - `gates[]`: array com `gate_id`, `descricao`, `checklist`, `criterio_sucesso`, `retorno`
- Cada script DEVE ter pseudocódigo e teste associado
- Tipagem estática: Pydantic ou Dataclasses para validação em runtime

## Gates
- D1: Camadas AIDD completas (contratos, gates, persistência)
- D2: Scripts com responsabilidade e pseudocódigo
- D3: Determinismo mínimo ≥65% (4/6 fases determinísticas = 66.7%)

## MCPs
- Filesystem MCP (leitura de analise_phase2.json)

## Saída
- `_phase_03_index.json` em `.aidd/cache/data/`
- `design_aidd_phase3.json` em `.aidd/cache/data/`

## Tokens
- Consumo: ~15k (5 subagentes LLM)
- Determinismo: 0% (pura LLM)
