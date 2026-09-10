---
name: aidd-bridge-runner
description: Extrai, unifica e empacota projetos Low-Code (Lovable, v0, Bolt) para VPS própria com PostgreSQL nativo, PostgREST e Docker Compose.
---

# AIDD Bridge Runner

Esta skill comanda a ferramenta `aidd-bridge` para libertar projetos criados no Lovable e hospedá-los em infraestrutura própria:
- Ingestão e escaneamento de repositórios Lovable/Vite/React.
- Sanitização de migrações Supabase para PostgreSQL puro e PostgREST.
- Fusão de múltiplos apps (2 a 4) em um único monorepo com Tailwind unificado.
- Geração de Dockerfile, Docker Compose e Proxy Reverso Caddy com HTTPS automático.

## Como Usar
No chat do assistente:
```text
/bridge scan <caminho>
/bridge convert-db <caminho>
/bridge merge <app1> <app2> --output <destino>
/bridge pack <caminho> [--domain meusite.com]
```

Via CLI Python:
```bash
python ecossistema.py bridge scan [caminho]
python ecossistema.py bridge convert-db [caminho]
python ecossistema.py bridge merge [app1] [app2] --output [destino]
python ecossistema.py bridge pack [caminho] --domain meusite.com
```