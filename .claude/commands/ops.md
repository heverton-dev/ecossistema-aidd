# Comando /ops

Dispara o Meta-Orquestrador Agêntico de Infraestrutura (AIDD-Ops) para orquestrar stacks self-hosted a partir de requisitos em linguagem natural.

## Status atual

A ferramenta possui reconhecimento formal na camada de governança. A implementação funcional do MVP (Fases 1-3 do pipeline) será entregue no Pacote 3 da integração. O comando `/ops` não está funcionalmente disponível até lá.

## Uso (planejado)
```text
/ops <requisito>
```

## Ação (planejada)
Executa a skill `skills/aidd-ops-runner` para orquestrar o provisionamento de infraestrutura.
Equivalente CLI (planejado): `python ecossistema.py ops "<requisito>"`
