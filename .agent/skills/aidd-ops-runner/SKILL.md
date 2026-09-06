---
name: aidd-ops-runner
description: Meta-Orquestrador Agêntico de Infraestrutura — governança reconhecida, implementação funcional em construção (Pacote 3).
---

# AIDD-Ops Runner

Esta skill referencia a ferramenta `aidd-ops`, o Meta-Orquestrador Agêntico de Infraestrutura do Ecossistema AIDD.

**Status atual:** A ferramenta possui reconhecimento formal na camada de governança (AGENTS.md, gates, manifesto de harnesses). A implementação funcional do MVP (Fases 1-3 do pipeline: Intake, Curadoria, Sizing) será entregue no Pacote 3 da integração.

## Como Usar

Quando o MVP estiver implementado, no chat do assistente:
```text
/ops <requisito>
```

Via CLI Python (Pacote 3):
```bash
python ecossistema.py ops "<requisito>"
```

## Referências
- Plano de integração: `docs/planos/integracao-aidd-ops/00-PROCESSO-E-DECISOES.md`
- Plano arquitetural: `docs/features/PLANO ARQUITETURAL NOVA FEATURE AIDD-OPS.md`
