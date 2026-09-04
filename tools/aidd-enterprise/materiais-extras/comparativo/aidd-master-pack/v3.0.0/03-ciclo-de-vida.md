# Ciclo de Vida Completo de Uso — AIDD Master Pack v3.0.0

> **Tag analisada:** `v3.0.0`
> **Escopo:** Da obtenção do pacote até o output final entregue ao usuário, com base exclusivamente no comportamento real de `scripts/aidd.py`, `scripts/provision_project.py`, `scripts/add_module.py` e dos gates em `templates/gates/`.

---

## 1. Visão Geral do Ciclo

```
┌───────────────────────────────────────────────────────────────────────────┐
│ FASE 0: OBTENÇÃO DO PACOTE                                                 │
│ git clone https://github.com/heverton-dev/aidd-master-pack.git             │
│ git checkout v3.0.0                                                        │
│ (Não há script de bootstrap/instalação de dependências nesta tag.)         │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ FASE 1: PROVISIONAMENTO DE UM PROJETO NOVO                                 │
│ $ python scripts/aidd.py init "Minha Plataforma Modular"                   │
│  -> cmd_init() chama provision_project.provision(nome)                     │
│  1. Cria src/core, src/shared, src/modules, src/static/components,         │
│     tests/unit, tests/load, scripts/gates                                  │
│  2. Copia database.py, events.py, openapi.py, webhooks.py de templates/v2  │
│  3. Copia shared kernel (formatters, crypto, validators, icons)            │
│  4. Copia Dockerfile, docker-compose.yml, deploy.sh e locustfile.py        │
│  5. Copia scripts/aidd.py e scripts/add_module.py para o projeto novo      │
│  6. Copia os 3 gates (G_SEGREDOS, G_QUALIDADE, G_HARNESS_COMPAT)           │
│  7. Roda `git init` no diretório de destino                                │
│  (Destino default é fixo no código: pasta pessoal do autor no Windows)     │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ FASE 2: GERAÇÃO DE MÓDULOS SOB DEMANDA                                     │
│ $ python scripts/add_module.py cupons "Gerenciador de Cupons"              │
│  -> criar_modulo() gera em src/modules/<slug>/:                            │
│     - models.py   (schema SQLite com CREATE TABLE + índice)                │
│     - services.py (listar / criar / deletar + emissão de eventos)          │
│     - routes.py   (registra GET/POST no RouteRegistry)                     │
│  -> gera src/static/components/<slug>.html (card visual)                   │
│  -> gera tests/unit/test_<slug>.py (teste do fluxo criar->listar->deletar) │
│  (O desenvolvedor ainda precisa importar/registrar manualmente as rotas    │
│   e o schema em src/server.py — não há wiring automático.)                 │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ FASE 3: DESENVOLVIMENTO MANUAL COMPLEMENTAR                                │
│ - Escrita manual de src/server.py (registro de rotas, inicialização de     │
│   schema, ligação de eventos a webhooks)                                   │
│ - Escrita manual de src/static/index.html (SPA) e, opcionalmente,          │
│   src/static/docs.html + rota /docs/guia (documentação estilo GitBook —    │
│   feita à mão nos exemplos, sem gerador dedicado nesta tag)                │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ FASE 4: TESTES                                                             │
│ $ python scripts/aidd.py test unit   -> pytest -v                          │
│ $ python scripts/aidd.py test load   -> locust headless (10 users, 5s)     │
│ $ python scripts/aidd.py test all    -> unit + load                        │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ FASE 5: AUDITORIA DE QUALIDADE (GATES MECÂNICOS)                           │
│ $ python scripts/aidd.py audit                                             │
│  -> executa em sequência, cada um como processo Python isolado:            │
│     1. G_SEGREDOS.py       (regex + entropia de Shannon > 4.6 bits)        │
│     2. G_QUALIDADE.py      (py_compile em todos os .py do projeto)         │
│     3. G_HARNESS_COMPAT.py (verificação nominal, sempre aprova)            │
│  -> primeira falha interrompe o processo com exit code != 0                │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ FASE 6: DEPLOY                                                             │
│ $ python scripts/aidd.py deploy docker -> docker compose up -d --build     │
│ $ python scripts/aidd.py deploy vps    -> instrui rodar bash deploy.sh     │
│                                            no servidor (git pull + rebuild)│
│ (Build Docker exige requirements.txt e src/main.py, que a tag NÃO gera —   │
│  ver analise-tecnica.md, item 1 e 2 da tabela de limitações.)              │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ FASE 7: STATUS E OPERAÇÃO CONTÍNUA                                         │
│ $ python scripts/aidd.py status                                            │
│  -> lê PLANO-EXECUCAO-ESTRUTURADO.json (se existir na raiz do projeto)     │
│  -> imprime nome, versão, status do projeto e lista os módulos ativos      │
│     em src/modules/                                                        │
│ Saída ao vivo do servidor: http://localhost:<porta> com:                   │
│   /            -> SPA (index.html)                                         │
│   /api/<...>   -> rotas REST do(s) módulo(s)                               │
│   /docs        -> Swagger UI (via CDN)                                     │
│   /docs/guia   -> documentação GitBook (somente nos 3 exemplos que a têm)  │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Detalhamento dos Comandos Reais Disponíveis (`scripts/aidd.py`)

| Comando | Ação Real no Código | Observação |
| :---: | :--- | :--- |
| `init <nome>` | Chama `provision_project.provision()` | Destino default fixo no código-fonte (não configurável por flag). |
| `add-module <nome> [-d desc]` | Chama `add_module.criar_modulo()` | Gera 5 arquivos; não integra automaticamente ao servidor. |
| `test [unit\|load\|e2e\|all]` | Roda `pytest -v` e/ou `locust` headless | Opção `e2e` é aceita pelo parser mas **não tem lógica implementada** (nenhum branch trata `"e2e"`). |
| `audit` | Roda os 3 gates em sequência | Para no primeiro gate que falhar. |
| `deploy [docker\|vps\|vercel]` | `docker compose up` ou instrui `deploy.sh` | Opção `vercel` é aceita pelo parser mas **não tem lógica implementada** (nenhum branch trata `"vercel"` — cai silenciosamente no `print` final de "sucesso" sem executar nada). |
| `status` | Lê `PLANO-EXECUCAO-ESTRUTURADO.json` e `src/modules/` | Não faz nada se o JSON não existir (sem mensagem de erro). |

---

## 3. Observação Sobre o Ciclo Real vs. o Ciclo Ideal

Nesta tag, o ciclo de vida **não é totalmente automatizado de ponta a ponta**. As fases 0, 1, 2, 4, 5 e 6 têm comandos CLI reais e determinísticos. A fase 3 (integração do módulo gerado ao servidor, criação da SPA e da documentação GitBook) é **manual** — depende de um desenvolvedor (humano ou agente de IA operando o Harness) escrever `server.py`, `index.html` e, opcionalmente, `docs.html` à mão, seguindo as convenções descritas em `AGENTS.md`/`CLAUDE.md`/`GEMINI.md` de cada projeto de exemplo.
