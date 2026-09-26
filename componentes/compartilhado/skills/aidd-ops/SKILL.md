---
name: aidd-ops
description: Runs the aidd-ops agentic infrastructure pipeline (VPS sizing, SSH hardening, Docker, Cloudflare, deploy). Use when the user wants to provision or deploy infrastructure, or says "ops", "/ops", "infraestrutura", "subir na VPS", "provisionar".
---

# aidd-ops

Agentic infrastructure meta-orchestrator of the ecosystem: provisioning pipeline, SSH runner, Docker and Cloudflare MCPs. Its infrastructure plan feeds `aidd-factory`.

## Run

```bash
python ecossistema.py ops "<requirement>" --pasta <destination>
```

Slash command: `/ops <requirement>`.

Done when: the pipeline exits 0.

## References

- Integration plan: `docs/planos/feitos/PLAN-0004-integracao-aidd-ops/00-PROCESSO-E-DECISOES.md`
- Architecture: `docs/features/06-09-2026_feature-arquitetura-aidd-ops.md`
