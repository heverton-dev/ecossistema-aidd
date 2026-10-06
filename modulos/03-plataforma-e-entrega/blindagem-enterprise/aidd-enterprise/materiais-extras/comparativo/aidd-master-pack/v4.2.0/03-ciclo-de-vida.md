# Ciclo de Vida Completo — AIDD Master Pack v4.2.0

> **Tag analisada:** `v4.2.0` (snapshot via `git archive v4.2.0`).
> Todas as fases abaixo foram reconstruídas lendo o código real de `scripts/aidd.py`, `scripts/provision_project.py`, `scripts/add_module.py`, `scripts/compose_suite.py` e os gates em `scripts/gates/` e `templates/gates/`. Não há inferência de comandos que não existam no código desta tag.

---

## 1. Visão Geral do Ciclo

```
┌──────────────────────────────────────────────────────────────────────────┐
│ FASE 0: OBTENÇÃO E INSTALAÇÃO DO PACOTE                                  │
│  - git clone do repositório (ou cópia da pasta) na máquina do usuário    │
│  - Para o comando "init" funcionar, o pacote precisa estar disponível em │
│    ~/.agents/skills/aidd-master-pack/  (hub de templates)                │
└──────────────────────────────────┬───────────────────────────────────────┘
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ FASE 1: ESCOLHA DO MODO DE PROVISIONAMENTO                               │
│  Modo A — Projeto único:                                                 │
│    $ python scripts/aidd.py init "descrição do projeto"                  │
│  Modo B — Suite cross-project (múltiplos domínios):                      │
│    $ python scripts/compose_suite.py <destino> <nome> crm erp helpdesk   │
└──────────────────────────────────┬───────────────────────────────────────┘
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ FASE 2: SCAFFOLDING MECÂNICO (SEM CHAMADAS DE IA)                        │
│  1. Criação de diretórios: src/core, src/shared, src/modules,            │
│     src/static/components, tests/unit, tests/load, scripts/gates        │
│  2. Cópia do Shared Kernel (database.py, events.py, openapi.py,          │
│     webhooks.py, security.py) de templates/v2                            │
│  3. Cópia de infraestrutura de deploy (Dockerfile, docker-compose.yml,   │
│     deploy.sh) e do locustfile.py de carga                               │
│  4. Cópia dos scripts aidd.py e add_module.py para o novo projeto        │
│  5. Cópia dos 3 gates padrão (G_QUALIDADE, G_SEGREDOS, G_HARNESS_COMPAT) │
│  6. git init no diretório do novo projeto                                │
└──────────────────────────────────┬───────────────────────────────────────┘
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ FASE 3: GERAÇÃO DE FATIAS VERTICAIS (MÓDULOS)                            │
│  $ python scripts/add_module.py <nome_do_modulo>                         │
│  Gera, por módulo: models.py (schema SQLite genérico), services.py       │
│  (listar/criar/deletar), routes.py (GET/POST/POST-deletar), um           │
│  componente HTML de card e um teste unitário pytest.                     │
└──────────────────────────────────┬───────────────────────────────────────┘
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ FASE 4: EXECUÇÃO LOCAL E TESTES                                          │
│  $ python src/server.py            (sobe o servidor HTTP nativo)         │
│  $ python scripts/aidd.py test unit   -> pytest -v                      │
│  $ python scripts/aidd.py test load   -> locust headless (5s, 10 users)  │
└──────────────────────────────────┬───────────────────────────────────────┘
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ FASE 5: AUDITORIA MECÂNICA (GATES)                                       │
│  $ python scripts/aidd.py audit                                          │
│    -> executa em sequência: G_SEGREDOS -> G_QUALIDADE -> G_HARNESS_COMPAT│
│    -> aborta com exit code 1 no primeiro gate que falhar                 │
│  $ python scripts/gates/G_SEGURANCA.py   (execução manual, separada;     │
│    não roda como parte de "audit" nesta tag)                             │
└──────────────────────────────────┬───────────────────────────────────────┘
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ FASE 6: DEPLOY                                                           │
│  $ python scripts/aidd.py deploy docker  -> docker compose up -d --build │
│  $ python scripts/aidd.py deploy vps     -> instrui "bash deploy.sh"     │
│    no servidor de destino                                                │
└──────────────────────────────────┬───────────────────────────────────────┘
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ FASE 7: OBSERVABILIDADE PÓS-ENTREGA                                      │
│  $ python scripts/aidd.py status                                         │
│    -> lê PLANO-EXECUCAO-ESTRUTURADO.json (se existir no projeto) e lista │
│       nome, versão, status e módulos ativos em src/modules               │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Detalhamento de cada fase

### FASE 0 — Obtenção e Instalação
O código não contém um instalador dedicado. Dois caminhos coexistem nesta tag:

- **Uso como "hub de skill":** `provision_project.py` busca templates em `os.path.expanduser('~')/.agents/skills/aidd-master-pack/templates/...`. Isso significa que, para `python scripts/aidd.py init` funcionar, o pacote precisa estar copiado (ou symlinkado) nesse caminho fixo do usuário — um padrão comum quando o framework é distribuído como "skill" de um agente de IA local.
- **Uso direto do clone:** `compose_suite.py` resolve o caminho dos templates de forma relativa ao próprio arquivo (`os.path.dirname(os.path.dirname(os.path.abspath(__file__)))`), então funciona rodando diretamente de dentro do repositório clonado, sem depender do hub em `~/.agents/skills`.

### FASE 1 — Escolha do modo
`scripts/aidd.py` expõe apenas seis subcomandos (via `argparse`): `init`, `add-module`, `test`, `audit`, `deploy`, `status`. Não existem, nesta tag, comandos como `plan`, `setup`, `bench` ou `heal` (esses aparecem só em versões posteriores).

### FASE 2 — Scaffolding mecânico
`provision_project.provision()` faz literalmente: `os.makedirs` das pastas padrão, `shutil.copyfile`/`copytree` do shared kernel e dos gates, e `subprocess.run(['git', 'init'])`. Não há chamada de rede, não há geração de texto por IA nesta etapa — é 100% determinístico.

### FASE 3 — Geração de módulos
`add_module.criar_modulo()` escreve 4 arquivos por módulo (`models.py`, `services.py`, `routes.py`, um componente `.html`) mais 1 teste (`tests/unit/test_<modulo>.py`), todos a partir de templates de string Python com o nome do módulo interpolado. O CRUD gerado é parcial: cobre criar, listar e deletar — não gera rota/método de atualização.

### FASE 4 — Execução e testes
`cmd_test()` em `aidd.py` despacha para `pytest -v` (tipo `unit`) ou para `locust -f tests/load/locustfile.py --headless -u 10 -r 2 -t 5s` (tipo `load`). O tipo `e2e` é aceito pelo parser de argumentos mas não possui implementação correspondente no corpo da função — ou seja, `aidd.py test e2e` não executa nenhum teste real nesta tag.

### FASE 5 — Auditoria
`cmd_audit()` roda os 3 gates padrão em sequência e **para no primeiro erro** (`sys.exit(1)`). `G_SEGURANCA.py` (o gate de segurança de 7 camadas) fica de fora dessa automação e deve ser chamado manualmente — ver `analise-tecnica.md` para os detalhes dessa lacuna.

### FASE 6 — Deploy
`cmd_deploy()` apenas invoca `docker compose up -d --build` (alvo `docker`) ou imprime a instrução para rodar `deploy.sh` manualmente no servidor (alvo `vps`). O alvo `vercel` é aceito pelo parser, mas não possui lógica própria — cai no mesmo fluxo de impressão genérica de "Deploy finalizado", sem nenhuma integração real com a Vercel nesta tag.

### FASE 7 — Status
`cmd_status()` é somente leitura: abre `PLANO-EXECUCAO-ESTRUTURADO.json` (se o arquivo existir no diretório do projeto) e lista os subdiretórios de `src/modules`. Ele não valida integridade, não recalcula métricas e não atualiza o próprio JSON.

---

## 3. Saída final entregue ao usuário

Ao final do ciclo, o "produto" entregue por esta tag é:

- Um diretório de projeto Python autocontido, sem dependências de build front-end (HTML/CSS/JS vanilla servidos por `src/server.py` via `http.server`/`socketserver`).
- Um banco SQLite local em modo WAL.
- Endpoints REST por módulo (`/api/<modulo>`), documentação OpenAPI 3.1 dinâmica (quando o projeto usa `core/openapi.py`) e, nos exemplos "flagship" (`enterprise-suite-v4`, `logistica-hub-v4`), também um servidor MCP (`core/mcp_server.py`) e um `nginx/nginx.conf` de borda.
- Scripts de gates copiados para dentro do próprio projeto, permitindo auditoria offline sem depender do pacote-mestre.
