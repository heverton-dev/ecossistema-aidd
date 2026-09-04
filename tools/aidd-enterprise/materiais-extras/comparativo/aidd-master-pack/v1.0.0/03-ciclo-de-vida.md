# Ciclo de Vida Completo de Uso — AIDD Master Pack `v1.0.0`

> **Tag analisada:** `v1.0.0` (commit `729ce3e`)
> Este documento descreve o ciclo de vida **real**, reconstruído a partir do que os scripts de `scripts/`, `templates/` e `examples/` da tag efetivamente fazem — não um processo idealizado.

---

## Visão geral das fases

| # | Fase | Comando/ação | Artefato de entrada | Artefato de saída |
|---|---|---|---|---|
| 1 | Instalação da skill | Copiar pacote para `~/.agents/skills/aidd-master-pack/` | Pacote da tag `v1.0.0` | Skill disponível para o agente de IA |
| 2 | Provisionamento do projeto | `scripts/provision_project.py "<descrição>"` (ou `aidd.py init`) | Texto livre com o nome/descrição do projeto | Pasta nova com esqueleto de código |
| 3 | Geração de módulo vertical | `python scripts/add_module.py <nome>` | Nome do módulo | `models.py`, `services.py`, `routes.py`, componente HTML, teste unitário |
| 4 | Implementação manual | Edição humana/agente dos arquivos gerados | Esqueleto do módulo | Regra de negócio real |
| 5 | Testes | `python scripts/aidd.py test [unit\|load\|e2e\|all]` | Código do módulo + teste gerado | Resultado `pytest`/Locust no console |
| 6 | Auditoria de gates | `python scripts/aidd.py audit` | Árvore de arquivos `.py` do projeto | Exit 0/1 + mensagens `[OK]`/`[FAIL]` no console |
| 7 | Deploy | `python scripts/aidd.py deploy [docker\|vps\|vercel]` | `Dockerfile` + `docker-compose.yml` (se existirem) | Container rodando localmente ou instrução para rodar `deploy.sh` na VPS |
| 8 | Inspeção de status | `python scripts/aidd.py status` | `PLANO-EXECUCAO-ESTRUTURADO.json` (se existir) | Resumo impresso no console |

---

## Fase 1 — Obtenção e instalação

A tag `v1.0.0` não possui instalador. O README apenas instrui a estrutura de pastas esperada:

```
aidd-master-pack-v1/
├── scripts/    (aidd.py, add_module.py, gates/)
├── templates/  (gates/, rules/, v2/)
├── examples/   (12 projetos de referência)
├── README.md
└── SKILL.md
```

Na prática, `provision_project.py` espera encontrar essa árvore em `~/.agents/skills/aidd-master-pack/` (caminho hard-coded), de onde copia `aidd.py`, `add_module.py`, os gates e o "shared kernel" (`templates/v2/`) para cada novo projeto. Não há `pip install`, `npm install` ou empacotamento — é cópia direta de arquivos Python.

## Fase 2 — Provisionamento (`aidd.py init` → `provision_project.py`)

Ao rodar `provision(descricao)`, o script:
1. Gera um *slug* a partir das 3 primeiras palavras da descrição.
2. Cria a árvore `src/{core,shared,modules}`, `src/static/components`, `tests/{unit,load}`, `scripts/gates`.
3. Copia do shared kernel (`templates/v2/`) os arquivos `database.py`, `events.py`, `openapi.py`, `webhooks.py` para `src/core/`, e a pasta `shared/` inteira.
4. Copia `Dockerfile`, `docker-compose.yml`, `deploy.sh` e `locustfile.py` (load test) para o projeto.
5. Copia `aidd.py` e `add_module.py` para `scripts/` do novo projeto (o projeto passa a ter sua própria cópia do CLI).
6. Copia os 3 gates (`G_QUALIDADE.py`, `G_SEGREDOS.py`, `G_HARNESS_COMPAT.py`).
7. Roda `git init` na pasta, se ainda não for repositório git.

Nenhum arquivo `requirements.txt`, `.env.example` ou pipeline de CI é criado nesta fase — confirmado pela ausência desses arquivos em todos os 12 projetos de referência da tag.

## Fase 3 — Geração de módulo vertical (`add_module.py`)

Para cada módulo (ex.: `financeiro`, `produtos`), o gerador cria, a partir de *string templates* Python (concatenação de texto, sem motor de template como Jinja2):
- `src/modules/<slug>/models.py` — schema SQLite (`CREATE TABLE IF NOT EXISTS mod_<slug>...`).
- `src/modules/<slug>/services.py` — classe `<Slug>Service` com `listar`, `criar`, `deletar`, emitindo eventos (`<slug>_criado`, `<slug>_deletado`) via `EventBus` se disponível.
- `src/modules/<slug>/routes.py` — 3 rotas REST (`GET /api/<slug>`, `POST /api/<slug>`, `POST /api/<slug>/deletar`) registradas no `RouteRegistry`.
- `src/static/components/<slug>.html` — card de UI com input, botão "Adicionar" e container de listagem (JS de integração fica a cargo de quem editar depois).
- `tests/unit/test_<slug>.py` — teste `pytest` que cria banco temporário, valida criar/listar/deletar e a emissão de evento.

Esse gerador **não** integra automaticamente o módulo no `server.py` principal — a ligação (`import`, registro do schema, registro de rotas) é feita manualmente depois, como se vê comparando `add_module.py` com o `src/server.py` real de `examples/catalogo-digital-v3`, que faz os imports e chamadas de inicialização à mão para cada módulo.

## Fase 4 — Implementação manual

Nesta fase, o agente de IA (ou humano) edita o esqueleto gerado para conter a regra de negócio real: adiciona campos além de `titulo`/`dados_json`, conecta o módulo ao `server.py`, ajusta o componente de UI (adiciona JavaScript de fetch, já que o `add_module.py` só gera o HTML estático do card). Documentos de regra (`templates/rules/01_layers.md` a `04_security.md`) orientam o agente a: não usar o chat principal como terminal, evitar emojis na UI, usar hash de senha PBKDF2 e queries parametrizadas, e sempre passar por `impl → test → validate → verify`.

## Fase 5 — Testes (`aidd.py test`)

- `unit` (default): roda `pytest -v` na raiz do projeto.
- `load`: roda Locust headless por 5 segundos contra `tests/load/locustfile.py` (se existir), simulando 10 usuários com taxa de 2/s contra `http://localhost:3000` — presume que o servidor já esteja rodando manualmente em paralelo.
- `e2e`: aceito como opção de CLI, mas **sem implementação correspondente** no código de `cmd_test` — nenhum passo é executado para esse tipo.
- `all`: roda `unit` + `load` em sequência.

## Fase 6 — Auditoria de gates (`aidd.py audit`)

Executa, em sequência, via `subprocess`:
1. `G_SEGREDOS.py` — scan de regex + entropia de Shannon.
2. `G_QUALIDADE.py` — `py_compile` recursivo em todo `.py`.
3. `G_HARNESS_COMPAT.py` — gate de fachada, sempre retorna sucesso.

Qualquer `returncode != 0` interrompe a auditoria com `sys.exit(1)`. Importante: **o `pytest` não é chamado dentro de `audit`** — testes e gates são trilhas independentes que precisam ser rodadas separadamente (`test` e `audit`).

## Fase 7 — Deploy (`aidd.py deploy`)

- `docker` (default): roda `docker compose up -d --build` diretamente na máquina local.
- `vps`: apenas imprime a instrução `Execute no seu servidor: bash deploy.sh` — não executa nada remotamente, não faz SSH, não copia arquivos.
- `vercel`: aceito como opção de CLI, mas **sem nenhuma implementação** — nenhuma ação corresponde a esse alvo no código de `cmd_deploy`.

O `deploy.sh` copiado para o projeto (via shared kernel) assume que o projeto já está em um repositório git remoto e faz `git pull origin main && docker compose down && docker compose build --no-cache && docker compose up -d` — ou seja, pressupõe uma VPS onde o repositório já foi clonado manualmente uma vez.

## Fase 8 — Status (`aidd.py status`)

Lê `PLANO-EXECUCAO-ESTRUTURADO.json` na raiz do projeto, se existir, e imprime nome, versão e status do projeto, além de listar as subpastas de `src/modules/`. **Este arquivo não é gerado automaticamente por nenhum script da tag** — dos 12 projetos de referência, apenas 5 o possuem, sugerindo que ele é criado manualmente (ou pelo agente de IA em prosa livre) em alguns fluxos, não em todos. Se o arquivo não existir, `status` simplesmente não imprime nada sobre o projeto.

---

## Entrega final típica

Ao final do ciclo, para um projeto como `examples/catalogo-digital-v3`, o resultado observável é: um servidor HTTP único-processo (`python src/server.py`), servindo uma SPA estática (`src/static/index.html`) e uma API REST própria, com banco SQLite local (`loja.db`), documentação Swagger opcional (`src/static/docs.html`), testes `pytest` que passam, e um `docker-compose.yml` pronto para subir o mesmo serviço em container — mas sem `requirements.txt` funcional, sem CI, e sem garantias de consistência entre "o que os gates checam" e "o que realmente funciona em produção".
