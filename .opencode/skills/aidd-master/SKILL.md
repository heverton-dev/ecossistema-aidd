---
name: aidd-master
description: Scaffolds and integrates self-contained vertical slices in the aidd-master modular monolith (models, services, REST routes, contract tests, UI). Use when the user wants a new module or slice, or says "master", "/master", "nova fatia vertical", "adicionar módulo".
---

# aidd-master

- Creates self-contained vertical slices in `src/modules/<module>/`.
- Generates models, services, HTTP/REST routes, contract tests and UI components.
- Keeps a clean integration with the Shared Kernel and the polyglot DatabaseAdapter.

## Run

```bash
python ecossistema.py master add-module <module>
```

Slash command: `/master <module>`.

Done when: the command exits 0 and the module's contract tests pass.
