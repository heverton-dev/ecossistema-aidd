---
name: aidd-generator
description: Runs the aidd-generator 8-phase pipeline that turns a natural-language idea into tested software. Use when the user wants to generate an app from an idea, or says "generate", "/generate", "gerar software", "gerar app a partir da ideia".
---

# aidd-generator

Pipeline phases:
1. Research and requirements
2. Analysis and decomposition
3. Architecture and design
4. Technical decisions
5. Artifacts and schemas (Draft 2020-12)
6. Full documentation
7. Self-critique and gate audit
8. Working implementation with automated tests

## Run

```bash
python ecossistema.py generate "<idea>"
```

Slash command: `/generate <idea>`.

Done when: the pipeline exits 0 and the phase 8 tests pass.
