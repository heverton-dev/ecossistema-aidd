---
name: aidd-ops-runner
description: Meta-Orquestrador Agêntico de Infraestrutura — governança reconhecida, MVP funcional.
---

# AIDD-Ops Runner

Esta skill referencia a ferramenta `aidd-ops`, o Meta-Orquestrador Agêntico de Infraestrutura do Ecossistema AIDD.

**Status atual:** A ferramenta possui reconhecimento formal na camada de governança (AGENTS.md, gates, manifesto de harnesses). O MVP funcional está implementado com pipeline de provisionamento, SSH runner, Docker/Cloudflare MCPs e 56+ testes.

## Como Usar

No chat do assistente:
```text
/ops <requisito>
```

Via CLI Python:
```bash
python ecossistema.py ops "<requisito>"
```

## Referências
- Plano de integração: `docs/planos/feitos/integracao-aidd-ops/00-PROCESSO-E-DECISOES.md`
- Plano arquitetural: `docs/features/PLANO ARQUITETURAL NOVA FEATURE AIDD-OPS.md`
