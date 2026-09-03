# Manual de Uso — AIDD Master Pack `v4.3.0`

> **Tag documentada:** `v4.3.0` (última tag da série v4 do framework AIDD Master Pack)
> Este manual descreve exclusivamente o comportamento do código presente nesta tag, obtido via `git checkout v4.3.0`. Comandos e recursos de versões posteriores (v5.x) não são cobertos aqui.

---

## 1. O que é

O **AIDD Master Pack v4.3.0** é um framework de *scaffolding* (geração automática de código) em Python puro para construir monólitos modulares "Cross-Project": aplicações web com múltiplos domínios de negócio isolados (fatias verticais), comunicação entre eles via eventos, documentação de API viva (Swagger/OpenAPI 3.1), um portal para conectar agentes de IA (Model Context Protocol) e um painel de configuração de Webhooks. Não depende de Node.js, npm nem de um banco de dados externo para rodar — usa apenas a biblioteca padrão do Python e SQLite.

## 2. Pré-requisitos

- **Python 3.10+** instalado (o `Dockerfile` do pacote usa `python:3.12-slim`).
- **Git** instalado, para clonar o repositório.
- (Opcional) **Docker** e **Docker Compose**, apenas se for usar `aidd.py deploy docker`.
- (Opcional) **pytest** e **locust**, para os comandos de teste (`aidd.py test unit` / `aidd.py test load`) — **não vêm listados em nenhum `requirements.txt`** nesta tag (o pacote não possui esse arquivo), então precisam ser instalados manualmente: `pip install pytest locust`.

## 3. Obtendo o pacote nesta versão exata

```bash
git clone https://github.com/heverton-dev/aidd-master-pack.git
cd aidd-master-pack
git checkout v4.3.0
```

Isso deixa a working tree local exatamente no estado da tag `v4.3.0` — README.md, SKILL.md, `scripts/`, `templates/` e `examples/` correspondentes a essa versão.

## 4. Estrutura do pacote nesta tag

```
aidd-master-pack/  (na tag v4.3.0)
├── README.md
├── SKILL.md
├── LICENSE
├── scripts/
│   ├── aidd.py                 # CLI principal
│   ├── add_module.py           # gerador de módulo/fatia vertical
│   ├── compose_suite.py        # motor de composição de suíte
│   ├── provision_project.py    # provisionador legado
│   ├── test_live.py            # smoke test de produção/homologação
│   └── gates/
│       └── G_SEGURANCA.py      # gate de segurança de 7 camadas
├── templates/
│   ├── gates/                  # G_SEGREDOS.py, G_QUALIDADE.py, G_HARNESS_COMPAT.py
│   ├── rules/                  # regras determinísticas (01 a 05, em Markdown)
│   └── v2/                     # Shared Kernel: database.py, events.py, openapi.py,
│                                # security.py, webhooks.py, shared/ui, Docker, Nginx
├── src/
│   ├── server.py                # servidor de referência (espelho do exemplo logistica-hub-v4)
│   └── static/docs.html
└── examples/                    # 9 projetos de referência já gerados
    ├── logistica-hub-v4/        # suíte mais completa: frotas, entregas, WMS, financeiro, suporte
    ├── enterprise-suite-v4/     # suíte corporativa unificada
    ├── crm-omnichannel-v2 / v3
    ├── erp-financeiro-v2 / v3
    ├── helpdesk-sla-v2 / v3
    ├── catalogo-digital-v3
    ├── catalogo-digital-whatsapp
    ├── plataforma-de-membros / plataforma-membros-v3
    └── plataforma-modular-assinaturas
```

> **Atenção:** `src/server.py`, na raiz do pacote, importa de `core.database`, `core.events`, `core.mcp_server` etc., mas a raiz do pacote **não** possui uma pasta `src/core/`. Esse arquivo é uma cópia do servidor de `examples/logistica-hub-v4/src/server.py` e só roda de dentro daquele diretório de exemplo (que tem seu próprio `src/core/`). Rodar `python src/server.py` a partir da raiz do repositório vai falhar com `ModuleNotFoundError: No module named 'core'`.

## 5. Formas de usar

### 5.1 Explorar um exemplo pronto (caminho mais rápido, documentado no README original)

```bash
cd examples/logistica-hub-v4
python src/server.py
```

Isso sobe um servidor local na porta 3000. No navegador:
- **Aplicação principal:** `http://localhost:3000/`
- **Swagger Studio (documentação interativa da API):** `http://localhost:3000/docs`
- **Guia oficial de arquitetura:** `http://localhost:3000/docs/guia`
- **Portal MCP (conexão com IA):** `http://localhost:3000/mcp`
- **Webhook Configuration Studio v4:** `http://localhost:3000/webhooks`
- **Especificação OpenAPI crua:** `http://localhost:3000/openapi.json`

Login de demonstração usado nos testes do próprio pacote: `admin@logistica.com` / `admin` (`POST /api/auth/login`).

Para conferir rapidamente que tudo subiu certo (novidade desta tag):
```bash
python scripts/test_live.py
```
(ajuste o script/rode a partir do diretório do exemplo, pois ele assume o servidor já ativo em `http://localhost:3000`).

### 5.2 Compor uma suíte nova do zero

```bash
python scripts/compose_suite.py <pasta_destino> <nome_da_suite> crm erp helpdesk logistica
```
Isso cria a estrutura de pastas (`src/core`, `src/shared/ui`, `src/static`, `src/modules`, `tests`) e copia o *shared kernel* (banco de dados, eventos, webhooks, segurança, OpenAPI) para dentro da pasta destino. **Os módulos de negócio (`crm`, `erp` etc.) não são gerados automaticamente por este comando** — é preciso adicioná-los um a um (passo seguinte).

### 5.3 Adicionar um módulo de negócio (fatia vertical)

Dentro da pasta do projeto recém-composto:
```bash
python scripts/add_module.py faturamento "Módulo de faturamento e cobranças"
```
Isso cria `src/modules/faturamento/` com `models.py`, `services.py` (métodos `criar`, `listar`, `deletar` — **sem** `atualizar`), `routes.py` (rotas `GET`/`POST` correspondentes), um componente visual em `src/static/components/faturamento.html` e um teste em `tests/unit/test_faturamento.py`. Repita este comando para cada área de negócio desejada.

### 5.4 Rodar os gates de qualidade

```bash
python scripts/aidd.py audit
```
Executa em sequência `G_SEGREDOS.py`, `G_QUALIDADE.py` e `G_HARNESS_COMPAT.py`, parando no primeiro que falhar. Para o gate de segurança mais completo (7 camadas: OWASP, JWT, SQL Injection, Nginx, Docker, SQLite WAL, OpenAPI security schemes), rode manualmente:
```bash
python scripts/gates/G_SEGURANCA.py
```

### 5.5 Rodar os testes

```bash
python scripts/aidd.py test unit    # pytest -v
python scripts/aidd.py test load    # locust headless por 5s contra http://localhost:3000
python scripts/aidd.py test all     # unit + load
```

### 5.6 Consultar o status do projeto

```bash
python scripts/aidd.py status
```
Só retorna informações úteis se já existir um `PLANO-EXECUCAO-ESTRUTURADO.json` na raiz do projeto (ver `plano-de-execucao.md` para detalhes — nesta tag, esse arquivo não é gerado automaticamente por nenhum comando).

### 5.7 Deploy

```bash
python scripts/aidd.py deploy docker   # docker compose up -d --build
python scripts/aidd.py deploy vps      # apenas orienta a rodar deploy.sh manualmente na VPS
```
Para deploy em VPS "de verdade" (qualquer provedor: DigitalOcean, AWS, Hetzner, Oracle), o fluxo documentado em `templates/rules/05_production_vps.md` é:
```bash
git clone https://github.com/<usuario>/<sua-suite>.git
cd <sua-suite>
python nginx/ssl/generate_ssl.py
docker compose up -d --build
docker compose ps
docker compose logs -f
```

### 5.8 Conectar um agente de IA (MCP)

Os exemplos trazem `claude_desktop_config.json` e `mcp.json` prontos (ex.: `examples/enterprise-suite-v4/`) para apontar clientes como o Claude Desktop, Cursor ou Antigravity ao portal `/api/mcp/rpc` do servidor rodando localmente, permitindo que o agente de IA liste e execute as operações de cada módulo via JSON-RPC 2.0.

## 6. O que você recebe como entregável final

- Uma aplicação Python autocontida, rodando via `socketserver.ThreadingTCPServer` (multi-thread) na porta 3000.
- Banco de dados SQLite em modo WAL, persistido em arquivo (`suite.db` ou equivalente).
- Documentação OpenAPI 3.1 viva em `/docs`, testável diretamente pelo navegador.
- Painel de Webhooks (`/webhooks`) com CRUD completo de assinantes, catálogo de eventos, simulador de disparo com assinatura HMAC-SHA256 e histórico de logs com reenvio.
- Portal MCP (`/mcp`) para controle por agentes de IA.
- Relatório de aprovação/reprovação dos gates de qualidade rodados (`audit` e, se executado à parte, `G_SEGURANCA`).
- Opcionalmente, imagem Docker pronta para publicação (usuário não-root, healthcheck nativo).

## 7. Limitações a ter em mente ao usar esta versão específica

- Geração automática de CRUD cobre apenas Criar/Listar/Deletar — "Editar" precisa ser escrito à mão.
- O gate de segurança de 7 camadas não roda junto do `audit` padrão — precisa ser chamado manualmente.
- Não há arquivo de dependências (`requirements.txt`); `pytest` e `locust` precisam ser instalados manualmente antes de usar os comandos de teste.
- O `src/server.py` da raiz do pacote não é executável isoladamente (falta `src/core/`); use sempre os exemplos em `examples/<projeto>/src/server.py`, que são autocontidos.
- `scripts/provision_project.py` é um caminho legado com caminho absoluto do Windows hardcoded — prefira `compose_suite.py` + `add_module.py` para novos projetos.

Para mais detalhes técnicos, ver `analise-tecnica.md`, `matriz-de-qualidade.md`, `ciclo-de-vida.md` e `plano-de-execucao.md` nesta mesma pasta.
