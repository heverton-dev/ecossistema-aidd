---
name: fluxo-03-runner
description: Executa de ponta a ponta o Fluxo 03 (Low-Code / Apps Unificadas) da Tríade Canônica de forma estritamente síncrona.
---

# Fluxo 03 Runner — Desacoplamento Low-Code (Lovable / v0 / Bolt)

Esta skill executa o pipeline industrial de desmonte de vendor lock-in, normalização de banco e empacotamento:
`[FORGE -> PLANNER] -> BRIDGE -> [MASTER -> ENTERPRISE -> OPS]`

## Características Técnicas:
- **Fundação e Governança:** Blindagem inicial do ambiente e git hooks via `aidd-forge`.
- **Planejamento BDD/SDD:** Mapeamento de esquemas de dados e rotas via `aidd-planner`.
- **Engine Low-Code Bridge:** Scan anti-lockin, remoção de dependências Supabase e migração para PostgreSQL via `aidd-bridge`. Preserva estritamente a identidade visual original.
- **Harmonização VSA:** Conexão do frontend exportado à API modular em Python via `aidd-master`.
- **Blindagem Criptográfica:** Blindagem SHA-256 e detecção de drift via `aidd-enterprise`.
- **Infraestrutura:** Conteinerização completa com Nginx e banco de dados via `aidd-ops`.

## Como Usar
Via CLI Unificada:
```bash
python ecossistema.py run-fluxo --fluxo 3 --nome "App Hub" --slug app-hub --dominio saas --pasta ./projetos/app-hub --origem ./exports/lovable-app
```
Para simulação sem escrita no disco:
```bash
python ecossistema.py run-fluxo --fluxo 3 --nome "App Hub" --slug app-hub --dominio saas --pasta ./projetos/app-hub --origem ./exports/lovable-app --dry-run
```
