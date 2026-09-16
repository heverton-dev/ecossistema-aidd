# Referência Completa da CLI

> **Versão:** 1.1
> **Última atualização:** 2026-09-15
> **Ponto de entrada:** `python ecossistema.py <comando> [args]`

> ⚠️ **Onde rodar isto, de verdade (achado real, testado em 2026-09-15):**
> `ecossistema.py` é um ARQUIVO dentro da pasta clonada do toolbox (`ecossistema-aidd/`).
> Ele **não** é um comando global — rodar `python ecossistema.py ...` de dentro do SEU
> projeto (fora do clone) falha com `can't open file 'ecossistema.py'`.
> Regra fixa: fique sempre dentro da pasta `ecossistema-aidd/` clonada e passe o
> **caminho absoluto do seu projeto** como argumento:
> ```bash
> cd ecossistema-aidd
> python ecossistema.py forge init "C:\caminho\completo\para\seu-projeto"
> ```
> Só depois que `forge init` rodar uma vez apontando pro seu projeto é que os slash
> commands `/forge` e `/aidd-init` aparecem DENTRO dele (numa sessão nova do Claude
> Code aberta com esse projeto como pasta raiz). Antes disso, `/forge` simplesmente
> não existe lá — não é bug, é a ordem certa das coisas.

---

## Comandos Globais

| Comando | Descrição | Exemplo |
|:---|:---|:---|
| `status` | Resumo do estado do ecossistema | `python ecossistema.py status` |
| `audit` | Roda os 16 Quality Gates globais | `python ecossistema.py audit` |

---

## Forge — Governança

```bash
python ecossistema.py forge init [caminho]
python ecossistema.py forge inject <tipo> <nome>
```

| Subcomando | Parâmetros | Descrição |
|:---|:---|:---|
| `init` | `[caminho]` (default: `.`) | Injeta governança completa |
| `inject` | `<tipo> <nome>` | Materializa componente: `skill`, `mcp`, `rule`, `spec`, `roteiro` |

---

## Generate — Fábrica de Software

```bash
python ecossistema.py generate "<ideia>" --pasta ./destino [opções]
```

| Opção | Tipo | Descrição |
|:---|:---|:---|
| `--pasta` | `<caminho>` | Diretório de destino (obrigatório) |
| `--implementar-codigo` | flag | Ativa Fase 8 (geração via LLM) |
| `--interativo` | flag | Modo interativo |

---

## Master — Módulos Verticais

```bash
python ecossistema.py master add-module <nome>
python ecossistema.py master compose-orca <mod1> <mod2> ...
```

| Subcomando | Parâmetros | Descrição |
|:---|:---|:---|
| `add-module` | `<nome>` | Cria nova fatia vertical |
| `compose-orca` | `<mod1> <mod2> ...` | Compõe módulos em deploy isolado |

---

## Enterprise — Componentes Certificados

```bash
python ecossistema.py enterprise inject <tipo> <nome>
```

| Subcomando | Parâmetros | Descrição |
|:---|:---|:---|
| `inject` | `<tipo> <nome>` | Injeta componente certificado SHA-256. Tipos: `skill`, `mcp`, `hook`, `rule` |

---

## Ops — Infraestrutura

```bash
python ecossistema.py ops plan "<descrição>"
python ecossistema.py ops deploy <ambiente> [--dry-run]
```

### Pipeline principal

| Subcomando | Parâmetros | Descrição |
|:---|:---|:---|
| `plan` | `"<descrição>"` | Dimensiona stack para o nicho |
| `deploy` | `<ambiente>` | Faz deploy (`--dry-run` para simulação) |

### Monitoramento

```bash
python scripts/pipeline_ops.py monitor export
python scripts/pipeline_ops.py monitor check
```

### Cofre de credenciais

```bash
python scripts/pipeline_ops.py cofre init --chave <caminho-chave>
python scripts/pipeline_ops.py cofre encrypt --env <arquivo> --saida <destino>
python scripts/pipeline_ops.py cofre up --servico <pasta> --chave-privada <caminho>
```

### Coolify

```bash
python scripts/pipeline_ops.py coolify health
python scripts/pipeline_ops.py coolify status <app>
python scripts/pipeline_ops.py coolify create <app>
python scripts/pipeline_ops.py coolify setenv <app> --env-file <arquivo>
python scripts/pipeline_ops.py coolify deploy <app>
```

### Helm

```bash
python scripts/pipeline_ops.py helm lint
python scripts/pipeline_ops.py helm template --values <arquivo>
```

---

## Bridge — Low-Code → VPS

```bash
python ecossistema.py bridge <subcomando> [args]
```

| Subcomando | Parâmetros | Descrição |
|:---|:---|:---|
| `scan` | `<caminho>` | Escaneia projeto React+Vite+Tailwind+Supabase |
| `convert-db` | `<caminho>` | Supabase SQL → PostgreSQL puro |
| `merge` | `<app1> <app2> ...` `--output <destino>` | Unifica apps em monorepo |
| `pack` | `<caminho>` `--domain <domínio>` | Gera Docker Compose + SSL |
| `migrate-auth` | `--source <pg>` `--target <pg>` `[--apply]` | Migra contas (senhas preservadas) |
| `destroy` | `<nome>` `--domain <domínio>` `[--yes]` | Remove stack da VPS |

---

## Components — Sincronização

```bash
python ecossistema.py components sync --tipo <tipo> [--ferramenta <nome>] [--dry-run] [--force]
python ecossistema.py components verify --tipo <tipo> [--ferramenta <nome>]
```

| Opção | Descrição |
|:---|:---|
| `--tipo` | Tipo de componente ou `todos` |
| `--ferramenta` | Ferramenta alvo (opcional) |
| `--dry-run` | Simulação sem escrita |
| `--force` | Restaura destinos divergentes |

---

## Dependencia — Skills e MCPs

```bash
python ecossistema.py dependencia bootstrap [--tipo <tipo>] [--dry-run]
python ecossistema.py dependencia add-skill --nome <n> --pacote <p> --instalar <i> --verificar <v>
python ecossistema.py dependencia add-mcp --nome <n> --pacote <p> [--tipo stdio|remote]
python ecossistema.py dependencia list
python ecossistema.py dependencia verify
```

---

## Orchestrate — Multi-Frente

```bash
python ecossistema.py orchestrate <plano> [opções]
```

| Opção | Descrição |
|:---|:---|
| `--dry-run` | Gera Flight Plan sem executar |
| `--resume` | Retoma plano interrompido |
| `--yes` | Pula confirmação |
| `--ambiente` | `orca`, `subagent` ou `gitworktree` |
| `--harness` | `mimo`, `opencode`, `claude`, `agy` |
| `--from-flight-plan` | Usa JSON de plano já compilado |

---

## Auto-Bootstrap

Se as dependências não estiverem instaladas:

```bash
python ecossistema.py --auto-bootstrap <comando>
```

Instala automaticamente `requirements.txt` antes de executar.

---

## Exige

- Python >= 3.10
- Dependências de `requirements.txt` (instaláveis via `pip install -r requirements.txt`)
- Para Ops/Ansible: Linux ou WSL
- Para Bridge/Helm: Docker instalado
