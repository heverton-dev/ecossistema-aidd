---
name: aidd-forge-runner
description: Executa o bootstrap e blindagem de governança AIDD em qualquer projeto alvo usando o aidd-forge.
---

# AIDD Forge Runner

Esta skill dispara a ferramenta `aidd-forge` para injetar a infraestrutura completa de AI-Driven Development:
- Orquestração de subagentes efêmeros com Context-Purge.
- Quality Gates determinísticos e git hooks.
- Regras de economia extrema de tokens (Caveman Ultra).
- Fatiamento de fases com micro-ambientes isolados.

## Como Usar
No chat do assistente:
```text
/forge [caminho]
```

Via CLI Python:
```bash
python ecossistema.py forge init [caminho]
```

Se o caminho não for especificado, utiliza o diretório atual (`.`).
