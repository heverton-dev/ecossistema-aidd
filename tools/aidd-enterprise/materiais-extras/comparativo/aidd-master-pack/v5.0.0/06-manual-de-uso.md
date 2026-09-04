# Manual de Uso — AIDD Master Pack

> **Tag/versão documentada:** `v5.0.0`
> **Repositório:** `https://github.com/heverton-dev/aidd-master-pack`
> Este manual descreve exclusivamente o comportamento do código presente na tag `v5.0.0`, obtido via `git checkout v5.0.0`. Comandos, arquivos e caminhos citados foram verificados diretamente no código-fonte desta tag.

---

## 1. O que é

O **AIDD Master Pack** (nesta tag, internamente rotulado como "v4.1 Enterprise Anti-Fail" — ver `analise-tecnica.md` para o porquê dessa diferença de rótulo) é um framework de linha de comando, escrito em Python, que gera automaticamente aplicações web empresariais completas: banco de dados, back-end, front-end, documentação de API, integração com IA (MCP) e testes — a partir de uma descrição em linguagem natural ou de um comando estruturado.

O resultado é um **monólito modular**: uma única aplicação onde cada domínio de negócio (CRM, ERP, Helpdesk, Logística, etc.) vive isolado em sua própria "fatia vertical", comunicando-se apenas por eventos, nunca por chamadas diretas entre módulos.

---

## 2. Pré-requisitos

- **Python 3.9+** instalado e disponível no `PATH` (o script usa `f-strings`, `pathlib`-like patterns e `subprocess.run` com `capture_output`).
- **`pip`** funcional, para instalação automática de dependências.
- **Git**, para clonar o repositório (opcional, mas recomendado).
- Opcional: **Docker**, caso deseje usar o comando `aidd.py deploy docker`.
- Não é necessária nenhuma chave de API paga para o uso padrão ("Zero API Key Mode") — recursos avançados opcionais (SSO corporativo via OIDC, EventBus distribuído via Redis) exigem configuração adicional própria, detalhada na seção 7.

---

## 3. Obtendo o código desta tag exata

Como este manual documenta especificamente a tag `v5.0.0` (e não a versão mais recente do repositório), clone o projeto e faça checkout explícito dessa tag:

```bash
git clone https://github.com/heverton-dev/aidd-master-pack.git
cd aidd-master-pack
git checkout v5.0.0
```

Isso garante que os comandos e arquivos descritos neste manual correspondam exatamente ao que você tem em disco.

---

## 4. Instalação / setup do ambiente

Dentro da pasta do repositório, rode o diagnóstico e bootstrap automático:

```bash
python scripts/aidd.py setup
```

Esse comando:
1. Reporta a versão do Python detectada.
2. Tenta instalar `requirements.txt`, se presente na raiz (nesta tag esse arquivo não existe na raiz do pacote — o setup detecta a ausência e cai automaticamente no passo seguinte).
3. Garante, via `pip install`, que ao menos `pytest` e `requests` estejam disponíveis.
4. Detecta se `git` está instalado.
5. Detecta se a ferramenta `orca` (ORCA ADE) está disponível no `PATH`; se não estiver, opera em modo de subagentes nativos / git worktrees sem exigir nada extra.

Não há passo de configuração de banco de dados, variáveis de ambiente obrigatórias ou registro de conta — o pacote está pronto para uso imediatamente após este comando.

---

## 5. Criando sua primeira aplicação

### 5.1 Via linguagem natural (forma recomendada)

```bash
python scripts/aidd.py "Crie uma aplicação de CRM e ERP de faturamento"
```

Isso dispara a Fase 1.5 (planejamento): a ferramenta reconhece os domínios mencionados no texto e cria uma pasta nova, por exemplo `app_crm-erp-faturamento-suite/`, contendo:
- `SPEC-ARQUITETURA.md` — especificação legível em 3 níveis (negócio, back-end, front-end).
- `PLANO-EXECUCAO-ESTRUTURADO.json` — manifesto de máquina com status `"PLANEJADO"` (estrutura completa em `plano-de-execucao.md`).

Nada é construído ainda nesta etapa — é apenas a proposta de arquitetura.

### 5.2 Via comando declarativo explícito (equivalente)

```bash
python scripts/aidd.py plan "Crie um CRM e ERP de faturamento"
```

Produz exatamente o mesmo resultado do item 5.1.

### 5.3 Revisão e aprovação

Leia `SPEC-ARQUITETURA.md` gerado na pasta criada. Se o escopo estiver correto, aprove executando:

```bash
python scripts/aidd.py apply --dir "app_crm-erp-faturamento-suite"
```

Este comando lê o manifesto JSON gerado, monta o Shared Kernel, gera cada módulo (fatia vertical) com CRUD completo, testes, componente de UI, registra rotas OpenAPI/MCP e roda os **7 Quality Gates** automaticamente ao final da composição.

### 5.4 Composição direta (modo avançado, sem passar pelo planejamento em linguagem natural)

```bash
python scripts/aidd.py compose ./minha-pasta "Minha Suite" crm erp helpdesk logistica
```

Compõe imediatamente a suíte com os módulos informados na linha de comando, sem gerar `SPEC-ARQUITETURA.md`. Aceita `--db postgres` para direcionar o servidor gerado a usar `DATABASE_URL` em vez de SQLite (ver seção 7).

---

## 6. Verificando e operando o projeto gerado

| Objetivo | Comando |
| :--- | :--- |
| Rodar a suíte de testes unitários | `python scripts/aidd.py test --dir ./app_.../` |
| Rodar testes de contrato isolados | `python scripts/aidd.py test contracts --dir ./app_.../` |
| Rodar os 7 Quality Gates e salvar relatório | `python scripts/aidd.py audit --report --dir ./app_.../` |
| Ver status resumido do projeto | `python scripts/aidd.py status --dir ./app_.../` |
| Rodar benchmark de concorrência (100 operações) | `python scripts/aidd.py bench -n 100 --dir ./app_.../` |
| Recompor/auto-remediar módulos corrompidos | `python scripts/aidd.py heal --dir ./app_.../` |
| Adicionar um novo módulo a um projeto existente | `python scripts/aidd.py add-module faturamento -d "Faturamento e Boletos" --dir ./app_.../` |

O relatório `RELATORIO-AUDITORIA.json`, gerado por `audit --report` dentro da própria pasta do projeto, lista o resultado de cada um dos 7 gates (`G_ESTRUTURA`, `G_QUALIDADE`, `G_TESTES`, `G_CONTRACTS`, `G_SEGREDOS`, `G_HARNESS_COMPAT`, `G_SEGURANCA`), com status, exit code e duração em milissegundos.

---

## 7. Recursos avançados opcionais (exigem configuração manual)

Estes recursos existem no código desta tag, mas **não** são ativados automaticamente — precisam de ação explícita:

- **Banco Postgres em vez de SQLite:** exporte `DATABASE_URL=postgresql://usuario:senha@host:5432/banco` antes de subir o servidor gerado, ou componha com `--db postgres`.
- **EventBus distribuído (Redis Streams):** instale `pip install redis` e exporte `EVENTBUS_URL=redis://host:6379/0` no ambiente onde o servidor gerado for executado.
- **SSO corporativo (OAuth2/OIDC):** instale `pip install pyjwt cryptography` e configure as variáveis `OIDC_*` (client id/secret, endpoints do provedor) esperadas por `OIDCService` em `src/core/security.py`.
- **Exportar front-end Next.js/TypeScript:** `python scripts/aidd.py export-frontend --stack nextjs --dir ./app_.../` — gera `frontend/types.ts` e um projeto Next.js 14 mínimo a partir do OpenAPI já composto (não instala dependências Node nem builda automaticamente).
- **Gerar infraestrutura declarativa (Terraform + Helm):** `python scripts/aidd.py scaffold-infra --dir ./app_.../` — grava arquivos em `infra/terraform/` e `infra/helm/` (não executa `terraform`/`helm`; requer os binários instalados separadamente para validar/aplicar).
- **Refinar regras de negócio complexas via BDD:** crie um arquivo `features/<modulo>.feature` com cenários em Gherkin e rode `python scripts/aidd.py refine-module <modulo> --dir ./app_.../`. O comando instala `behave` automaticamente se necessário e executa os cenários; a implementação da lógica que faz os cenários passarem é feita por um agente de IA seguindo o guia em `templates/agents/agent_domain_refiner.md`, não pelo script isoladamente.

---

## 8. Ligando a aplicação gerada

```bash
python app_crm-erp-faturamento-suite/src/server.py
```

O servidor tenta a porta `3000` e, se estiver ocupada, avança automaticamente até `3025`. Ao subir, ele imprime os links de todos os portais disponíveis:

- `http://localhost:<porta>/` — aplicação (Super-App UI)
- `http://localhost:<porta>/docs` — Swagger Studio (documentação OpenAPI 3.1 interativa)
- `http://localhost:<porta>/webhooks` — Webhook Studio (cadastro de endpoints com assinatura HMAC SHA-256)
- `http://localhost:<porta>/mcp` — servidor MCP nativo (JSON-RPC 2.0) para agentes de IA
- `http://localhost:<porta>/openapi.json` — especificação OpenAPI 3.1 crua
- `http://localhost:<porta>/metrics` — métricas no formato Prometheus

---

## 9. Deploy

```bash
python scripts/aidd.py deploy docker
```

Executa `docker compose up -d --build` usando o `docker-compose.yml` gerado (ou presente) na pasta do projeto.

```bash
python scripts/aidd.py deploy vps
```

Apenas orienta a rodar `bash deploy.sh` diretamente no servidor de produção-alvo (o comando não faz o deploy remoto por si mesmo).

---

## 10. Entregáveis finais que você obtém

Ao final de um ciclo completo (planejar → aprovar → compor → auditar → iniciar), você tem, em disco:

- Um projeto Python completo em `src/` (core compartilhado + um pacote por módulo de domínio: `models.py`, `services.py`, `routes.py`, testes).
- Um banco SQLite já populado com dados de exemplo (`app.db` ou `suite.db`, conforme o gerador).
- Um front-end funcional em `src/static/` sem necessidade de build (`index.html` + componentes por módulo).
- Documentação de API pronta (`SPEC-ARQUITETURA.md`, especificação OpenAPI em `/openapi.json`, Swagger em `/docs`).
- Um manifesto de contexto para IA (`CONTEXTO-PROJETO.md`) e regras sincronizadas para múltiplos IDEs (`.cursor/`, `.claude/`, `.agent/`).
- Um relatório de auditoria factual (`RELATORIO-AUDITORIA.json`) comprovando aprovação nos 7 Quality Gates.
- Um servidor pronto para rodar localmente ou via Docker, com 6 portais ativos simultaneamente.

---

## 11. Onde buscar mais detalhes desta mesma tag

- `analise-tecnica.md` — o que a v5.0.0 realmente entrega e suas limitações reais.
- `ciclo-de-vida.md` — detalhamento fase a fase do fluxo interno.
- `matriz-de-qualidade.md` — o que cada um dos 7 gates valida, camada por camada.
- `plano-de-execucao.md` — schema completo do manifesto `PLANO-EXECUCAO-ESTRUTURADO.json`.
- `fases-de-execucao.md` — a mesma jornada explicada em linguagem simples, sem termos técnicos.

---

*Manual escrito a partir da leitura direta do código-fonte da tag `v5.0.0` (`git archive v5.0.0`), sem depender de documentação de versões posteriores.*
