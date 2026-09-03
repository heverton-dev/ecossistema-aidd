---
name: aidd-enterprise-runner
description: Injeta e audita componentes regulados de missão crítica com validação SHA-256 no aidd-master-enterprise.
---

# AIDD Enterprise Runner

Esta skill automatiza a injeção transacional de componentes de missão crítica:
- Validação estrita de manifestos contra JSON Schema.
- Checagem criptográfica de integridade via hashes SHA-256.
- Snapshot e rollback automático em caso de inconsistência.
- Suporte a tipos: `skill`, `rule`, `mcp`, `spec`, `config`, `hook`, `agent`.

## Como Usar
No chat do assistente:
```text
/enterprise <tipo> <nome>
```

Via CLI Python:
```bash
python ecossistema.py enterprise inject <tipo> <nome>
```
