# Manual de Uso — AIDD Master Pack v4.0.1

> **Tag analisada:** `v4.0.1` do repositório `heverton-dev/aidd-master-pack`.
> Este manual descreve exclusivamente o que existe e funciona nesta tag específica — não a versão mais recente do repositório (`v5.1+`).

---

## 1. O Que É

O **AIDD Master Pack v4.0.1** é um micro-framework de scaffolding (geração de código estrutural) para sistemas web modulares em Python, distribuído como uma **skill agêntica** — ou seja, um conjunto de scripts e instruções (`SKILL.md`) pensado para ser usado por um assistente de IA (Antigravity, Cursor, Claude, etc.) ou diretamente por um desenvolvedor via linha de comando.

Segundo o próprio `SKILL.md` desta tag, o pacote se autodescreve como:

> "AIDD v4.0 — Cross-Project Enterprise Monolith Suite (Unificação de 5 Domínios: CRM, ERP, Helpdesk, Cursos e Catálogo com EventBus Cross-Domain e Super-App UI)."

Nesta tag, ele entrega:
- Uma CLI (`scripts/aidd.py`) com comandos para iniciar projetos, gerar módulos, testar, auditar e implantar.
- Um Shared Kernel reutilizável (banco de dados, eventos, API documentada, webhooks, utilitários de UI/segurança/formatação).
- Três gates (verificações) mecânicas de qualidade.
- Nove projetos de exemplo prontos em `examples/`, que servem como referência de padrões avançados (CRM, ERP financeiro, Helpdesk, Catálogo com WhatsApp, Logística com MCP, Plataforma de Membros, Suíte Enterprise com EventBus cross-domínio).

---

## 2. Pré-Requisitos

- **Python 3** instalado (os scripts usam apenas a biblioteca padrão do Python — nenhuma dependência externa é necessária para `aidd.py`, `add_module.py`, `provision_project.py` e os gates).
- **Git** instalado (para clonar o repositório e para o `git init` automático de novos projetos).
- **Docker e Docker Compose** (opcional, apenas se for usar o comando de deploy `docker`).
- **pytest** instalado (opcional, apenas se for usar `aidd.py test`).
- **Locust** instalado (opcional, apenas se for usar `aidd.py test load`).

---

## 3. Obtendo o Projeto Nesta Tag Específica

Como esta tag não é a versão mais recente do repositório, é necessário clonar o repositório e depois mudar explicitamente para a tag `v4.0.1`:

```bash
git clone https://github.com/heverton-dev/aidd-master-pack.git
cd aidd-master-pack
git checkout v4.0.1
```

Após o `checkout`, o repositório local ficará no estado exato ("detached HEAD") em que estava quando a tag `v4.0.1` foi criada — com a estrutura de pastas `scripts/`, `templates/`, `examples/`, `README.md`, `SKILL.md` e `LICENSE` descrita neste manual.

> **Dica:** se quiser voltar depois para a versão mais recente do repositório, basta rodar `git checkout main` (ou o nome do branch principal).

---

## 4. Estrutura de Pastas Desta Tag

```
aidd-master-pack-v4/            (raiz do repositório na tag v4.0.1)
├── README.md                    Especificação técnica resumida do pacote (v4.0.0)
├── SKILL.md                     Skill agêntica — instrui o agente de IA sobre como usar o framework
├── LICENSE
├── scripts/
│   ├── aidd.py                  Micro-CLI: init, add-module, test, audit, deploy, status
│   ├── add_module.py            Gerador atômico de módulos verticais (models/services/routes/UI/teste)
│   └── provision_project.py     Provisionamento de um novo projeto (chamado por `aidd.py init`)
├── templates/
│   ├── gates/                   G_SEGREDOS.py, G_QUALIDADE.py, G_HARNESS_COMPAT.py
│   ├── rules/                   01_layers.md, 02_golden_rules.md, 03_impeccable.md, 04_security.md
│   └── v2/                      Shared Kernel: database.py, events.py, openapi.py, webhooks.py,
│                                 Dockerfile, docker-compose.yml, deploy.sh, locustfile.py, shared/
└── examples/                    9 projetos de referência completos (ver seção 8)
```

---

## 5. Instalação / Setup

Não há instalador. Existem dois caminhos de uso:

### Caminho A — Usar como skill de um agente de IA
Copie (ou aponte) a pasta do repositório para o diretório de skills usado pelo seu agente (por exemplo, `~/.agents/skills/aidd-master-pack/`). O `SKILL.md` será lido pelo agente para orientar como ele deve construir sistemas seguindo as regras do framework.

> **Atenção:** `scripts/provision_project.py`, nesta tag, tem um caminho de hub de templates fixo (`~/.agents/skills/aidd-master-pack/templates/v2` e `~/.agents/skills/aidd-master-pack/templates/gates`) e um diretório de destino padrão fixo (`C:\Users\...\orca\workspaces\PROJETOS Criados com IA`, um caminho específico da máquina do autor original). Para usar em outra máquina/ambiente, você precisará colocar o pacote exatamente nesse caminho de skills esperado, ou editar `provision_project.py` para apontar para os caminhos corretos do seu ambiente.

### Caminho B — Usar diretamente via linha de comando
A partir da raiz do repositório clonado (ou de dentro de um projeto onde os scripts foram copiados), rode os comandos da CLI diretamente com `python scripts/aidd.py <comando>`.

---

## 6. Como Usar — Passo a Passo

### 6.1 Criar um novo projeto

```bash
python scripts/aidd.py init "nome ou descricao do projeto"
```

Isso executa `provision_project.py`, que cria a estrutura de pastas do novo projeto (`src/core`, `src/shared`, `src/modules`, `src/static/components`, `tests/unit`, `tests/load`, `scripts/gates`), copia o Shared Kernel, os scripts e os gates, e inicializa um repositório Git dentro da nova pasta.

### 6.2 Criar um módulo (fatia vertical) dentro do projeto

Dentro da pasta do projeto recém-criado:

```bash
python scripts/aidd.py add-module financeiro --descricao "Controle financeiro de contas a pagar e receber"
```

Isso gera, de uma só vez, `models.py`, `services.py`, `routes.py`, um componente HTML e um teste unitário para o módulo `financeiro` em `src/modules/financeiro/`.

Repita esse comando para cada módulo que o sistema precisar (ex.: `crm`, `pedidos`, `clientes`).

### 6.3 Rodar os testes

```bash
python scripts/aidd.py test          # roda pytest (padrão: unit)
python scripts/aidd.py test load     # roda teste de carga com Locust (5s headless)
python scripts/aidd.py test all      # roda unit + load
```

### 6.4 Auditar a qualidade do código

```bash
python scripts/aidd.py audit
```

Executa, em sequência, `G_SEGREDOS.py` (vazamento de credenciais), `G_QUALIDADE.py` (sintaxe) e `G_HARNESS_COMPAT.py` (compatibilidade de ambiente). Para no primeiro gate que falhar.

### 6.5 Publicar o sistema (deploy)

```bash
python scripts/aidd.py deploy docker   # sobe via docker compose up -d --build
python scripts/aidd.py deploy vps      # orienta a rodar deploy.sh manualmente no servidor
```

### 6.6 Consultar o status do projeto

```bash
python scripts/aidd.py status
```

Mostra nome, versão e status do projeto e lista os módulos ativos — **desde que** um arquivo `PLANO-EXECUCAO-ESTRUTURADO.json` já exista na raiz do projeto (esta tag não o gera automaticamente; veja `plano-de-execucao.md` para detalhes).

### 6.7 Rodar os gates isoladamente (opcional)

Também é possível rodar cada verificação separadamente:

```bash
python scripts/gates/G_SEGREDOS.py
python scripts/gates/G_QUALIDADE.py
python scripts/gates/G_HARNESS_COMPAT.py
```

---

## 7. O Que Você Obtém ao Final (Entregáveis)

- **Código-fonte modular** em `src/modules/<nome>/`, com camada de dados, regras de negócio e rotas separadas por módulo.
- **API REST documentada e testável** — ao subir o servidor do projeto (`src/server.py`, presente nos exemplos, ou o servidor que você construir sobre o Shared Kernel) e acessar a rota de documentação, você tem o **Swagger Studio**: uma página com 3 colunas (lista de endpoints, documentação de cada rota, playground de teste ao vivo com geração de snippet em cURL/JavaScript/Python) e exportação do contrato em `openapi.json` (OpenAPI 3.1.0).
- **Componentes de tela prontos** em `src/static/components/*.html`, com visual consistente (dark theme, sem emojis, toasts/modais customizados no lugar de `alert()`/`confirm()`).
- **Testes automatizados** por módulo em `tests/unit/`.
- **Arquivos de infraestrutura** (`Dockerfile`, `docker-compose.yml`, `deploy.sh`) prontos para publicar o sistema.
- **Relatório de auditoria em texto no terminal** (não em arquivo) ao rodar `aidd.py audit`, indicando `[OK]` ou `[FAIL]` por gate.

---

## 8. Explorando os Projetos de Exemplo

A pasta `examples/` desta tag contém 9 projetos de referência já construídos, úteis para estudar padrões mais avançados que não são gerados automaticamente pelos scripts:

| Exemplo | Do que trata | Destaques |
| :--- | :--- | :--- |
| `catalogo-digital-v3` | Catálogo e loja com checkout via WhatsApp | Módulos `produtos`, `pedidos_whatsapp`, `configuracao` |
| `catalogo-digital-whatsapp` | Variante do catálogo com WhatsApp | — |
| `crm-omnichannel-v2` / `v3` | CRM com múltiplos canais de atendimento | Docker, deploy.sh |
| `erp-financeiro-v2` / `v3` | ERP financeiro (contas a pagar/receber) | Docker, deploy.sh |
| `helpdesk-sla-v2` / `v3` | Sistema de chamados com SLA | Docker, deploy.sh |
| `enterprise-suite-v4` | Suíte unificando CRM + ERP + Catálogo | **Servidor MCP** (`mcp_server.py`) e orquestração cross-domínio via EventBus (ex.: lead ganho no CRM gera lançamento automático no ERP) |
| `logistica-hub-v4` | Hub de logística | Também traz `mcp_server.py` e `security.py` |
| `plataforma-de-membros` / `plataforma-membros-v3` | Plataforma de assinaturas/membros | Docker, deploy.sh |
| `plataforma-modular-assinaturas` | Plataforma modular de assinaturas | Docker, deploy.sh |

Para estudar como implementar um recurso avançado (como um servidor MCP ou orquestração entre módulos), copie manualmente o padrão do exemplo correspondente — nesta tag não existe um comando de CLI que gere isso automaticamente.

---

## 9. Boas Práticas Recomendadas por Esta Tag (`templates/rules/`)

- Não use o chat principal do agente de IA como terminal para rodar testes/builds — rode-os localmente.
- Para frentes grandes de trabalho, use "Worktrees" isoladas (ORCA) em vez de sobrecarregar uma única sessão.
- Nunca use emojis em botões, títulos, cards ou badges — use apenas ícones SVG vetoriais.
- Senhas devem ser armazenadas com PBKDF2-HMAC-SHA256 e comparadas com `hmac.compare_digest` (função utilitária já disponível em `shared/utils/crypto.py`).
- Todas as consultas ao banco de dados devem usar parâmetros preparados (nunca concatenar strings em SQL).

---

## 10. Limitações a Ter em Mente Nesta Versão

- O comando `init` depende de caminhos fixos de máquina em `provision_project.py` — pode exigir ajuste manual em outros ambientes.
- `G_HARNESS_COMPAT.py` não faz uma verificação real (sempre aprova).
- Não há geração automática do arquivo de plano de execução, nem de servidor MCP, nem de autenticação/RBAC — esses recursos, quando presentes nos exemplos, foram feitos manualmente.
- As opções `e2e` (em `test`) e `vercel` (em `deploy`) existem na CLI mas não têm nenhuma lógica implementada nesta tag.

Para mais detalhes técnicos, consulte `analise-tecnica.md`, `matriz-de-qualidade.md`, `ciclo-de-vida.md` e `plano-de-execucao.md` nesta mesma pasta.

---

*Manual elaborado a partir do conteúdo real extraído da tag `v4.0.1` via `git archive v4.0.1`, sem inferências de versões posteriores do repositório.*
