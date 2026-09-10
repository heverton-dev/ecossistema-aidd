# Comando /ops

Dispara o Meta-Orquestrador Agêntico de Infraestrutura (AIDD-Ops) para orquestrar stacks self-hosted a partir de requisitos em linguagem natural.

## Uso:
```text
/ops <requisito>
```

## Ação:
Executa a skill `skills/aidd-ops-runner` para orquestrar o provisionamento de infraestrutura (sizing VPS, hardening SSH, Docker, Cloudflare, deploy).

Equivalente CLI: `python ecossistema.py ops "<requisito>"`
