# Migração de Projeto Existente para o Ecossistema AIDD

> **Versão:** 1.0  
> **Última atualização:** 2026-09-14  
> **Escopo:** Guia passo a passo para trazer qualquer projeto existente para o ecossistema.

---

## 1. Tipos de Projeto

| Tipo | Exemplo | Fluxo Recomendado |
|:---|:---|:---|
| **Código próprio** (legado ou novo) | Flask, Django, FastAPI, Next.js, etc. | Forge → Master/Enterprise |
| **Low-code** (Lovable, v0, Bolt) | App React+Supabase em plataforma | Bridge → Forge → Master/Enterprise |
| **Já no ecossistema** | Projeto gerado pelo Generator | Master/Enterprise diretamente |

---

## 2. Fluxo A: Projeto de Código Próprio

### Passo 1 — Avaliação

Verifique se o projeto atende aos pré-requisitos:

```bash
# Python >= 3.10
python --version

# Git inicializado
git status

# Estrutura básica identificada
ls -la
```

### Passo 2 — Instalar Governança (`/forge`)

> ⚠️ **Testado de verdade em 2026-09-15:** `ecossistema.py` só existe dentro da pasta
> clonada do toolbox. Rodar `python ecossistema.py ...` de dentro do SEU projeto (se ele
> mora em outra pasta) falha com `can't open file`. Fique na pasta `ecossistema-aidd/`
> e passe o caminho do seu projeto como argumento (relativo ou absoluto):

```bash
# de dentro da pasta ecossistema-aidd/ clonada, apontando pro seu projeto:
python ecossistema.py forge init "C:\caminho\completo\para\seu-projeto"
```

O que acontece:
- `AGENTS.md` instalado na raiz
- `CLAUDE.md` e `GEMINI.md` criados como ponteiros
- 7 Quality Gates locais copiados para `gates/`
- `.gitattributes` com `eol=lf` (se não existir)
- `.gitignore` atualizado
- Skills canônicas materializadas

### Passo 3 — Validar

> ⚠️ Não confundir dois comandos de auditoria diferentes:
> - `python ecossistema.py audit` (sem argumento, rodado dentro de `ecossistema-aidd/`) audita
>   o TOOLBOX inteiro — é pesado (passou de 120s num teste real) e não serve pra validar seu projeto.
> - Para validar SEU projeto depois do `forge init`, use o audit do próprio forge, apontando
>   pro caminho do seu projeto:

```bash
# de dentro de ecossistema-aidd/, apontando pro seu projeto:
python ecossistema.py forge audit "C:\caminho\completo\para\seu-projeto" --format md --output relatorio-audit.md

# exit 0 = OK, exit 1 = corrigir antes de prosseguir (leia relatorio-audit.md, não suponha)
```

### Passo 4 — Adicionar Módulos (`/master`)

Para cada novo módulo de negócio:

```bash
python ecossistema.py master add-module <nome-do-modulo>
```

Estrutura criada:
```
src/modules/<nome-do-modulo>/
├── domain/          ← Entidades e regras
├── application/     ← Casos de uso
├── infrastructure/  ← SQL e adapters
├── interfaces/      ← Rotas HTTP
├── models.py
├── services.py
└── routes.py
```

### Passo 5 — Componentes Certificados (opcional)

Para componentes de segurança críticos:

```bash
python ecossistema.py enterprise inject skill auth-jwt-service
python ecossistema.py enterprise inject mcp <nome>
```

---

## 3. Fluxo B: Projeto Low-Code (Lovable/v0/Bolt)

### Passo 1 — Escanear

```bash
python ecossistema.py bridge scan ./meu-app-lovable
```

Gera `bridge-manifest.json` com mapeamento completo.

### Passo 2 — Converter Banco

```bash
python ecossistema.py bridge convert-db ./meu-app-lovable
```

Converte Supabase SQL → PostgreSQL puro. O frontend `@supabase/supabase-js` continua funcionando via PostgREST.

### Passo 3 — Migrar Contas (opcional)

```bash
# Preview (não grava nada)
python ecossistema.py bridge migrate-auth \
  --source postgres://supabase-host:5432/postgres \
  --target postgres://minha-vps:5432/postgres

# Aplicar migração real
python ecossistema.py bridge migrate-auth \
  --source postgres://supabase-host:5432/postgres \
  --target postgres://minha-vps:5432/postgres \
  --apply
```

### Passo 4 — Unificar Apps (opcional)

Se tiver múltiplos apps:

```bash
python ecossistema.py bridge merge ./app1 ./app2 ./app3 --output ./app-unificado
```

### Passo 5 — Empacotar

```bash
python ecossistema.py bridge pack ./meu-app --domain app.meudominio.com
```

Gera:
- `Dockerfile` multi-stage (~25MB com Nginx Alpine)
- `docker-compose.yml` com Web, PostgreSQL, PostgREST, Caddy/Traefik
- Certificados SSL automáticos via Let's Encrypt

### Passo 6 — Instalar Governança

```bash
cd meu-app
python ecossistema.py forge init .
```

### Passo 7 — Deploy

```bash
# Subir na VPS
docker stack deploy -c docker-compose.yml meu-app
```

---

## 4. Pós-Migração

### Validar Governança

```bash
python ecossistema.py audit
# Deve retornar exit 0 com todos os gates passando
```

### Sincronizar Componentes

```bash
python ecossistema.py components sync --tipo todos
```

### Rodar Testes

```bash
# Testes locais da ferramenta
pytest tests/ -v

# Gates globais
python ecossistema.py audit
```

---

## 5. Solução de Problemas Comuns

| Problema | Solução |
|:---|:---|
| `ModuleNotFoundError` ao rodar `ecossistema.py` | `python ecossistema.py --auto-bootstrap status` |
| `can't open file 'ecossistema.py'` | Você rodou o comando de dentro do SEU projeto. Volte pra pasta `ecossistema-aidd/` clonada e passe o caminho do seu projeto como argumento. |
| `/forge` no meu projeto dá `ModuleNotFoundError: No module named 'aidd_forge'` (**bug real confirmado em 2026-09-15**) | O slash command reinjetado roda `python -m aidd_forge.cli init` sem preparar o ambiente, e depende de uma instalação `pip -e` de `aidd-forge` que pode estar apontando pra uma pasta antiga/inexistente. Enquanto isso não é corrigido, não use o `/forge` reinjetado pra re-rodar — volte sempre pro toolbox e rode `python ecossistema.py forge init "<caminho>" --force` de lá. |
| Gates falhando após forge init | Verificar se `.gitattributes` existe com `eol=lf` |
| Bridge não encontra Supabase SQL | Verificar se `supabase/migrations/` existe no projeto |
| Master cria módulo com imports cruzados | Verificar `G_ARQUITETURA` — módulos devem se comunicar via EventBus |
| Enterprise rejeita componente | Hash SHA-256 não confere — componente pode ter sido adulterado |
