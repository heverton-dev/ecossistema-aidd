---
name: aidd-master-runner
description: Cria e integra novas fatias verticais modulares (Vertical Slices) no aidd-master.
---

# AIDD Master Runner

Esta skill permite compor e estender a arquitetura de monólitos modulares da suíte `aidd-master`:
- Cria fatias verticais autocontidas em `src/modules/<modulo>/`.
- Gera modelos, serviços, rotas HTTP/REST, testes de contrato e componentes visuais.
- Assegura integração limpa com o Shared Kernel e o DatabaseAdapter poliglota.

## Como Usar
No chat do assistente:
```text
/master <modulo>
```

Via CLI Python:
```bash
python ecossistema.py master add-module <modulo>
```
