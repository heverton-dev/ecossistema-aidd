---
name: aidd-dependencias
description: Installs and verifies third-party skills and MCPs against dependencias_externas.json.
---

# AIDD Dependências — Gestão de MCPs e Skills Externas

Esta skill registra e instala dependências externas usadas pelo próprio agente de IA neste repositório (skills e MCPs de terceiros como Playwright, GitHub, Supabase, Cloudflare) governadas por `gates/dependencias_externas.json`.

## Como Usar

No chat do assistente:
```text
/dependencia bootstrap
/dependencia skill <nome>
/dependencia mcp <nome>
```

Via CLI Python:
```bash
python ecossistema.py dependencia bootstrap [--tipo skills|mcps|todos] [--dry-run]
python ecossistema.py dependencia verify
python ecossistema.py dependencia list
```
