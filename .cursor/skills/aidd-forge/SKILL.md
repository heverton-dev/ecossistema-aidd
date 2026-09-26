---
name: aidd-forge
description: Bootstraps and hardens a target repository with the aidd-forge governance kit (quality gates, git hooks, token-economy rules, phase isolation). Use when the user asks to bootstrap, initialize or harden a project, or says "forge", "/forge", "blindar projeto", "inicializar governança".
---

# aidd-forge

Injects the full AI-Driven Development kit into a target repository:
- ephemeral subagent orchestration with context purge;
- deterministic quality gates and git hooks;
- extreme token-economy rules (Caveman Ultra);
- phase slicing with isolated micro-environments.

## Run

```bash
python ecossistema.py forge init [path]
```

Slash command: `/forge [path]`. Without a path it uses the current directory.

Done when: the command exits 0 and the target contains the injected gates and hooks.
