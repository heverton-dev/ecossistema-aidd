# Ciclo de Vida Completo de Uso — AIDD Master Pack v4.1.0

> **Tag documentada:** `v4.1.0` (commit `1daf757`, 31/08/2026)
> Este documento descreve o ciclo de vida **real**, baseado exclusivamente nos scripts contidos no snapshot da tag `v4.1.0` (`scripts/aidd.py`, `scripts/provision_project.py`, `scripts/add_module.py`, `scripts/compose_suite.py`) e nos gates em `templates/gates/`. Não reflete comandos ou fases introduzidos em tags posteriores (ex.: `plan`, `apply`, `bench`, `heal`, que só existem a partir de v5.x).

---

## 1. Visão Geral do Ciclo

```
┌───────────────────────────────────────────────────────────────────────────┐
│ FASE 0 — OBTENÇÃO DO PACOTE                                                │
│ Skill instalado em ~/.agents/skills/aidd-master-pack/ (SKILL.md + scripts) │
│ ou repositório clonado localmente na tag v4.1.0                            │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ FASE 1 — PROVISIONAMENTO INICIAL                                           │
│ $ python scripts/aidd.py init "<descrição do projeto>"                     │
│ -> chama provision_project.provision(nome)                                 │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ FASE 2 — COMPOSIÇÃO DA SUÍTE (opcional, cross-project)                     │
│ $ python scripts/compose_suite.py <destino> <nome_suite> crm erp ...       │
│ -> copia apenas o Shared Kernel (database/events/webhooks/security/openapi)│
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ FASE 3 — GERAÇÃO DE MÓDULOS (fatias verticais)                             │
│ $ python scripts/aidd.py add-module <nome> [--descricao "..."]             │
│ -> gera models.py, services.py, routes.py, componente HTML, teste unitário │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ FASE 4 — VALIDAÇÃO MECÂNICA (GATES)                                        │
│ $ python scripts/aidd.py audit                                             │
│ -> G_SEGREDOS.py -> G_QUALIDADE.py -> G_HARNESS_COMPAT.py                  │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ FASE 5 — TESTES                                                            │
│ $ python scripts/aidd.py test [unit|load|all]                              │
│ -> pytest -v  /  locust headless (tests/load/locustfile.py)                │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ FASE 6 — DEPLOY                                                            │
│ $ python scripts/aidd.py deploy [docker|vps|vercel]                        │
│ -> docker compose up -d --build  /  bash deploy.sh                         │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ FASE 7 — OPERAÇÃO E INSPEÇÃO                                               │
│ $ python scripts/aidd.py status                                            │
│ -> lê PLANO-EXECUCAO-ESTRUTURADO.json (se existir) e lista módulos ativos  │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Detalhamento de Cada Fase (com evidência de código)

### Fase 0 — Obtenção do Pacote
O pacote é distribuído como uma "skill" (`SKILL.md` na raiz) destinada a ser instalada em `~/.agents/skills/aidd-master-pack/`. Isso é confirmado pelo fato de `scripts/provision_project.py` referenciar explicitamente esse caminho global (`os.path.join(os.path.expanduser('~'), '.agents', 'skills', 'aidd-master-pack', ...)`) para copiar o Shared Kernel, os scripts auxiliares e os gates para o novo projeto. Um simples `git clone` isolado do repositório, sem essa instalação global, **não é suficiente** para que `aidd.py init` funcione corretamente — os arquivos do kernel não serão copiados se o caminho `~/.agents/skills/aidd-master-pack/templates/v2` não existir.

### Fase 1 — Provisionamento Inicial (`aidd.py init`)
`cmd_init()` delega para `provision_project.provision(nome)`, que:
1. Deriva um slug do nome/descrição do projeto (primeiras 3 palavras).
2. Cria a árvore de diretórios: `src/core`, `src/shared`, `src/modules`, `src/static/components`, `tests/unit`, `tests/load`, `scripts/gates`.
3. Copia do hub global: `database.py`, `events.py`, `openapi.py`, `webhooks.py` (kernel), a pasta `shared/` inteira, `Dockerfile`, `docker-compose.yml`, `deploy.sh` e `locustfile.py`.
4. Copia `aidd.py` e `add_module.py` para dentro do novo projeto (auto-replicação do CLI).
5. Copia todos os `.py` de `templates/gates/` para `scripts/gates/` do novo projeto.
6. Roda `git init` no diretório do projeto, se ainda não for um repositório.

O destino do projeto é fixo em `C:\Users\trcnologia\orca\workspaces\PROJETOS Criados com IA\proj_<slug>` por padrão (parâmetro `base_dir` com valor hardcoded) — o que evidencia que este script foi escrito para uso em uma máquina/ambiente específico, não como ferramenta genérica publicável.

### Fase 2 — Composição de Suíte Cross-Project (`compose_suite.py`, opcional)
Usado quando se deseja unir múltiplos domínios em um monólito único. Na prática, o script apenas:
- Cria a árvore `src/core`, `src/shared/ui`, `src/static`, `src/modules`, `tests`.
- Copia `database.py`, `events.py`, `webhooks.py`, `security.py`, `openapi.py` de `templates/v2/` para `src/core/`.
- Copia os arquivos de `templates/v2/shared/ui/` (motor de feedback/toasts).

Ele **não** gera `src/server.py`, **não** gera código específico dos domínios passados como argumento (`crm`, `erp`, etc. são apenas impressos no console) — a montagem final de rotas, módulos de domínio e do próprio servidor precisa ser feita manualmente ou por um agente de IA em cima do esqueleto copiado.

### Fase 3 — Geração de Módulos (`add-module`)
`add_module.criar_modulo(nome, descricao)` gera, por módulo:
- `models.py` com schema SQLite (`CREATE TABLE mod_<slug>` com colunas `id`, `titulo`, `dados_json`, `ativo`, `criado_em`, mais um índice em `ativo`).
- `services.py` com uma classe `<Slug>Service` contendo `listar()`, `criar()` e `deletar()` — **sem `atualizar()`**.
- `routes.py` registrando 3 rotas via `RouteRegistry`: `GET /api/<slug>`, `POST /api/<slug>` e `POST /api/<slug>/deletar` — **sem rota de atualização**.
- Um componente HTML de card em `src/static/components/<slug>.html`.
- Um teste unitário `tests/unit/test_<slug>.py` cobrindo criar → listar → deletar (com verificação de emissão de evento via `EventBus`).

### Fase 4 — Validação Mecânica (`audit`)
`cmd_audit()` executa sequencialmente 3 gates (interrompendo no primeiro que falhar, `exit 1`):
1. `G_SEGREDOS.py` — regex de prefixos de chave conhecidos + entropia de Shannon (limiar 4.6).
2. `G_QUALIDADE.py` — `py_compile` de todo arquivo `.py` do projeto.
3. `G_HARNESS_COMPAT.py` — **gate vazio**, sempre retorna sucesso sem checagem real.

### Fase 5 — Testes (`test [tipo]`)
- `unit` (padrão) ou `all`: roda `pytest -v`.
- `load` ou `all`: se `tests/load/locustfile.py` existir, roda Locust em modo headless por 5 segundos, 10 usuários, contra `http://localhost:3000` (valores fixos no código, não parametrizáveis via CLI).
- `e2e`: aceito como opção de argumento, mas **não há nenhuma implementação** de testes E2E no `cmd_test()` desta tag — a opção existe no parser mas não executa nada.

### Fase 6 — Deploy (`deploy [alvo]`)
- `docker` (padrão): `docker compose up -d --build`.
- `vps`: apenas imprime instrução para rodar `bash deploy.sh` manualmente no servidor — o script não executa deploy remoto por si.
- `vercel`: aceito como opção do parser, mas **sem implementação** — nenhuma lógica de deploy para Vercel existe no código desta tag.

Para deploy com a nova infraestrutura desta tag (Nginx + SSL), o fluxo documentado em `templates/rules/05_production_vps.md` é: clonar na VPS → `python nginx/ssl/generate_ssl.py` → `docker compose up -d --build` → `docker compose ps` / `docker compose logs -f`.

### Fase 7 — Operação e Inspeção (`status`)
Lê `PLANO-EXECUCAO-ESTRUTURADO.json` (se presente na raiz do projeto) e imprime nome, versão e status do projeto, além de listar os diretórios dentro de `src/modules`. **Nenhum script desta tag gera esse arquivo JSON** — ele precisa já existir (criado manualmente ou por um agente de IA durante o planejamento) para que `status` produza uma saída útil; caso contrário, `status` só lista os módulos existentes em `src/modules`.

---

## 3. Observação sobre Governança de Sessão (arquivos de contexto)

Cada projeto de exemplo desta tag inclui arquivos de instrução para agentes de IA na sua raiz (`CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, `.cursorrules`), todos com o mesmo conteúdo essencial: papel de "Auditor/Orquestrador", uso de Worktrees ORCA para tarefas pesadas, "thinking" em inglês comprimido com resposta ao usuário em PT-BR, e o ciclo `/implementacao` (`impl → test → validate → verify`). Isso não é gerado automaticamente por nenhum script desta tag — são arquivos estáticos copiados/mantidos manualmente nos exemplos.
