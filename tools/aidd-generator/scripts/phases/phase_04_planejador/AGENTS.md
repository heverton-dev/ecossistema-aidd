# Phase 04 — Planejador (Micro-Ambiente)

## Escopo
Divisão de tarefas e decisões GLOBAL vs LOCAL para skills, MCPs e hooks. Modal interativo ou heurística automática.

## Restrições
- input() real para modo interativo
- Heurística coerente para --nao-interativo (baseada em subagentes do design)
- Gate C2: Path.resolve().exists() real (não vacuamente True)

## Divisão de Tarefas
- O planejador DEVE decompor o design da Fase 3 em tarefas executáveis
- Cada tarefa DEVE ter: id, descrição, fase_alvo, dependencias[], criterio_aceitacao
- Tarefas DEVE respeitar a ordem topológica (dependências antes de dependentes)
- Decisões GLOBAL vs LOCAL: cada ferramenta/skill do design recebe escopo
  - GLOBAL: compartilhado entre todas as fases (ex: utils_delegacao.py)
  - LOCAL: exclusivo de uma fase (ex: linter AST da Fase 5)
- A config DEVE ser persistida como `config_global_local_phase4.json`

## Gates
- C1: Decisões válidas (GLOBAL/LOCAL para cada item)
- C2: Symlinks resolvem para caminhos reais existentes
- C3: Configuração completa (todas as decisões tomadas)

## Saída
- `_phase_04_index.json` em `.aidd/cache/data/`
- `config_global_local_phase4.json` em `.aidd/cache/data/`

## Tokens
- Consumo: ~3k (heurística ou interativo)
- Determinismo: 50% (heurística automática) / 0% (interativo)
