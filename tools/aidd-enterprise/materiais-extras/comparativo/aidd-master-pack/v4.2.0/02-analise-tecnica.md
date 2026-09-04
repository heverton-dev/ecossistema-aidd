# Análise Técnica e Posicionamento Realista — AIDD Master Pack v4.2.0

> **Tag analisada:** `v4.2.0`
> **Fonte:** snapshot extraído via `git archive v4.2.0` (não é o HEAD atual do repositório, que já está em v5.1.0).
> **Objetivo:** descrever com precisão o que o código desta tag realmente entrega, com evidências extraídas dos próprios arquivos (`README.md`, `SKILL.md`, `scripts/*.py`, `templates/*`, `examples/*`).

---

## 1. O que a v4.2.0 é, de fato

Segundo o `SKILL.md` da própria tag, o pacote se autodenomina:

> "AIDD v4.0 — Cross-Project Enterprise Monolith Suite (Unificação de Fatias Verticais Cross-Domain com EventBus, Webhooks, Swagger Studio OpenAPI 3.1, Servidor Nativo MCP e Super-App UI)."

Nota curiosa: o campo `version` do frontmatter do `SKILL.md` está fixado em `4.0.0`, mesmo na tag `v4.2.0` — ou seja, o pacote não atualiza o número de versão interno do skill a cada tag Git; a numeração `v4.2.0` é apenas do repositório, não do artefato instalado.

Na prática, a v4.2.0 é um **kit de scaffolding em Python puro** (sem dependências externas de build) composto por:

- `scripts/aidd.py` — micro-CLI com 6 subcomandos: `init`, `add-module`, `test`, `audit`, `deploy`, `status`.
- `scripts/provision_project.py` — cria a estrutura inicial de um projeto (copiando o *shared kernel* de `templates/v2`).
- `scripts/compose_suite.py` — compõe uma suíte cross-domain unindo múltiplos módulos em um único monólito.
- `scripts/add_module.py` — gera uma fatia vertical (módulo) com `models.py`, `services.py`, `routes.py`, um componente HTML e um teste unitário.
- `scripts/gates/G_SEGURANCA.py` — gate mecânico de auditoria de segurança (a principal novidade desta tag, ver seção 2).
- `templates/gates/{G_QUALIDADE, G_SEGREDOS, G_HARNESS_COMPAT}.py` — gates copiados para cada projeto provisionado.
- `templates/v2/*` — *shared kernel* (banco, eventos, segurança, OpenAPI, webhooks) e infraestrutura de deploy (Dockerfile, docker-compose, nginx, deploy.sh, locustfile).
- `templates/rules/*.md` — regras curtas de governança (camadas, regras de ouro, segurança, cross-project, VPS).
- `examples/` — 13 projetos de exemplo já montados (CRM, ERP, Helpdesk, Logística, Catálogo, Membros, Enterprise Suite etc.), servindo como referência funcional.

---

## 2. A novidade real desta tag: G_SEGURANCA.py

O histórico do repositório indica que a v4.2.0 adicionou o "Gate Oficial de Segurança G_SEGURANCA.py e Documentação Técnica de Blindagem Militar". Isso se confirma no código: `scripts/gates/G_SEGURANCA.py` (258 linhas) implementa **7 camadas de auditoria determinística**:

1. Headers OWASP (`X-Content-Type-Options`, `X-Frame-Options`, CSP, HSTS etc.) via `SecurityService.get_security_headers()`.
2. Motor criptográfico JWT HS256: geração/decodificação, detecção de token adulterado (tampering), validação de expiração e hashing de senha PBKDF2-HMAC-SHA256 (100k rounds) com `hmac.compare_digest`.
3. Varredura estática por regex contra padrões de SQL Injection em todo `src/*.py`.
4. Auditoria de `nginx.conf` (rate limiting, `limit_conn_zone`, TLS 1.2/1.3, `server_tokens off`).
5. Auditoria do `Dockerfile` (usuário não-root, `HEALTHCHECK`).
6. Verificação de modo WAL do SQLite e existência da tabela `logs_auditoria`.
7. Verificação de `securitySchemes.bearerAuth` no spec OpenAPI 3.1 gerado.

Ao final, o gate imprime um "Score de Blindagem" e concede uma "Certificação" textual se `failed == 0`. É um gate real e funcional — não um placeholder — mas seu escopo é auditoria estática e de configuração; não substitui pentest dinâmico nem SAST/DAST de terceiros.

### Limitação real e verificável: G_SEGURANCA não está integrado ao pipeline automático

Analisando `scripts/aidd.py`, a função `cmd_audit()` só executa três gates:

```python
gates = ["scripts/gates/G_SEGREDOS.py", "scripts/gates/G_QUALIDADE.py", "scripts/gates/G_HARNESS_COMPAT.py"]
```

`G_SEGURANCA.py` **não** está nessa lista — ou seja, `python scripts/aidd.py audit` não o executa. Ele precisa ser chamado manualmente (`python scripts/gates/G_SEGURANCA.py`), como o próprio README e o SKILL.md documentam separadamente.

Além disso, `provision_project.py` (comando `init`) só copia gates de `templates/gates/` (que contém `G_HARNESS_COMPAT.py`, `G_QUALIDADE.py`, `G_SEGREDOS.py`) para o novo projeto. `G_SEGURANCA.py` vive em `scripts/gates/` do pacote-mestre, fora de `templates/gates/`, e **não é copiado automaticamente** para projetos recém-provisionados. A evidência empírica confirma isso: dos 13 projetos em `examples/`, apenas 2 (`enterprise-suite-v4` e `logistica-hub-v4` — os dois exemplos "flagship" citados no README) possuem `G_SEGURANCA.py` em `scripts/gates/`; os outros 11 exemplos têm apenas os 3 gates padrão. Isso indica que o gate de segurança foi inserido manualmente nesses dois projetos de vitrine, e não distribuído pelo mecanismo de provisionamento automatizado da própria versão.

**Conclusão prática:** a "blindagem militar" existe como código funcional de alta qualidade, mas nesta tag ela é um recurso opcional e manual, não um gate obrigatório do ciclo de vida padrão (`init` → `add-module` → `audit`).

---

## 3. Outras limitações técnicas reais identificadas no código

| # | Limitação | Evidência no código |
| :---: | :--- | :--- |
| 1 | **CRUD gerado é incompleto** | `add_module.py` gera `services.py` com apenas `listar()`, `criar()` e `deletar()`. Não há `atualizar()`/`update`, `obter_por_id()` nem `obter_metricas()`. O `routes.py` gerado expõe só `GET /api/<mod>`, `POST /api/<mod>` e `POST /api/<mod>/deletar` — sem rota de atualização. Isso contradiz a promessa de "Full CRUD Diligente em 100% dos Módulos" do `SKILL.md`. |
| 2 | **Caminho de provisionamento hardcoded** | `provision_project.py` usa `base_dir=r'C:\Users\trcnologia\orca\workspaces\PROJETOS Criados com IA'` como valor padrão — um caminho absoluto específico da máquina do autor, não portátil entre usuários/SOs sem edição manual. |
| 3 | **Servidor MCP não faz parte do shared kernel reutilizável** | `templates/v2/` (o kernel copiado por `compose_suite.py`) contém `database.py`, `events.py`, `webhooks.py`, `security.py`, `openapi.py` — mas **não** contém `mcp_server.py`. O documento `templates/rules/04_cross_project.md` descreve `mcp_server.py` como parte da "estrutura canônica", mas o arquivo só existe manualmente em 2 dos 13 exemplos (`enterprise-suite-v4`, `logistica-hub-v4`). Ou seja, o "Servidor Nativo Universal MCP" não é gerado automaticamente pelos scripts desta tag. |
| 4 | **EventBus é volátil e sem envelope padronizado** | `templates/v2/events.py` tem 16 linhas: um `defaultdict(list)` de listeners com `.on()`/`.emit()`. Não há `event_id`, timestamp, origem ou persistência — qualquer evento em trânsito se perde se o processo cair. |
| 5 | **Sem gates de estrutura, testes ou contratos** | Só existem 3 gates automáticos (`G_QUALIDADE` valida apenas `py_compile`; `G_SEGREDOS` varre entropia de Shannon; `G_HARNESS_COMPAT` apenas imprime "OK"). Não há gate que **obrigue** a execução de `pytest` (isso só ocorre via `aidd.py test`, comando separado e não bloqueante), nem linter anti-acoplamento entre módulos, nem verificação de snapshot de contratos OpenAPI. |
| 6 | **Persistência simples** | `templates/v2/database.py` (23 linhas) ativa `PRAGMA journal_mode=WAL` e `synchronous=NORMAL`, mas não define `busy_timeout`, `foreign_keys=ON`, soft-delete ou tabela de migrações de schema. Suporte a PostgreSQL existe, mas depende de `psycopg2` estar instalado manualmente (não é dependência do pacote). |
| 7 | **Multi-IDE não é gerado por script** | Os arquivos `CLAUDE.md`, `AGENTS.md`, `GEMINI.md` e `.cursorrules` aparecem em alguns exemplos (ex.: `catalogo-digital-v3`), mas nenhum script da tag (`provision_project.py`, `add_module.py`, `compose_suite.py`) os gera — são artefatos incluídos manualmente nos exemplos, não uma funcionalidade automatizada do framework nesta versão. |

---

## 4. O que evoluiu depois (referência rápida, sem aprofundar)

Comparando com o estado atual do repositório (v5.1.0, ver `ANALISE_TECNICA_E_POSICIONAMENTO_REALISTA.md` no HEAD), versões posteriores (v4.3+ e v5.x) endereçam justamente as lacunas listadas acima:

- Gates crescem de 3–4 para **7 gates** (`G_ESTRUTURA`, `G_QUALIDADE`, `G_TESTES`, `G_CONTRACTS`, `G_SEGREDOS`, `G_HARNESS_COMPAT`, `G_SEGURANCA`), todos integrados ao ciclo de auditoria.
- CRUD passa a ser explicitamente "5 métodos reais" (`listar`, `obter_por_id`, `criar`, `atualizar`, `deletar`) mais `obter_metricas()`.
- Surge `Result Pattern`, soft-delete, `_schema_migrations`, `JobQueue` assíncrona, snapshot SHA-256 de contratos e sincronização multi-IDE automatizada.
- `PLANO-EXECUCAO-ESTRUTURADO.json` passa a ser gerado como manifesto formal do ciclo de planejamento (ver `plano-de-execucao.md` neste mesmo diretório para o que já existe — de forma não automatizada — na v4.2.0).

Este roadmap não é aprofundado aqui; o objetivo deste documento é apenas registrar, com base em código real, o estado exato da v4.2.0.
