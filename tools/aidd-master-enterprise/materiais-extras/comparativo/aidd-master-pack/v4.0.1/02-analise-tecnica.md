# Análise Técnica e Posicionamento Realista — AIDD Master Pack v4.0.1

> **Documento:** Posicionamento Factual e Limitações Técnicas Reais.
> **Tag analisada:** `v4.0.1` (commit `3e40a91`, 31/08/2026 — "feat(v4): Release v4.0.0 com Swagger Studio 3-Colunas, UI Feedback (Toasts/Modals), Scrollbar 4px e Botao 1-linha").
> **Nota de versionamento:** o `README.md` e o `SKILL.md` desta própria tag ainda se autodeclaram `version: 4.0.0` — a tag `v4.0.1` no Git é um patch release que adiciona a UI "Swagger Studio" (3 colunas), o sistema de feedback (Toasts/Modals) e o Shared Kernel expandido em cima do conteúdo de `v4.0.0`, sem bump do número interno do pacote.
> **Objetivo:** Documentar com precisão o que o pacote entrega nesta tag, distinguindo o que é automatizado por script do que é apenas padrão de referência demonstrado nos exemplos.

---

## 1. O Que o Pacote v4.0.1 É (Posicionamento Factual)

O **AIDD v4.0.1** é um **micro-framework de scaffolding em Python puro** (sem dependências externas nos scripts principais) que:

1. Fornece uma CLI mínima (`scripts/aidd.py`) com seis comandos (`init`, `add-module`, `test`, `audit`, `deploy`, `status`) para provisionar projetos e gerar módulos verticais.
2. Gera fatias verticais desacopladas (`models.py`, `services.py`, `routes.py`, componente HTML, teste unitário) por módulo, via `scripts/add_module.py`.
3. Oferece um **Shared Kernel** (`templates/v2/`) reutilizável entre projetos: `database.py` (SQLite WAL / Postgres opcional), `events.py` (EventBus em memória), `openapi.py` (gerador de rotas + Swagger Studio 3 colunas + JSON OpenAPI 3.1.0), `webhooks.py` (disparo assíncrono via thread), mais utilitários de criptografia, formatação, validação e feedback de UI (toasts/modais, sem `alert()`/`confirm()` nativos).
4. Executa três **gates mecânicos determinísticos** (sintaxe, segredos, compatibilidade de harness) via `scripts/aidd.py audit`.
5. Traz **9 projetos de exemplo** em `examples/` (CRM, ERP, Helpdesk, Catálogo, Logística, Plataforma de Membros, Enterprise Suite) que demonstram, de forma manual/hand-crafted, padrões avançados como EventBus cross-domain e um servidor MCP (Model Context Protocol) — mas que **não são gerados automaticamente pelos scripts do pacote**.

Em resumo: nesta tag, o pacote é essencialmente um **gerador de CRUD SQLite + API REST documentada + UI básica**, acompanhado de uma biblioteca de exemplos de referência mais sofisticados que servem de "norte" para o agente de IA copiar manualmente ao construir sistemas maiores.

---

## 2. Limitações Técnicas Reais Identificadas no Código desta Tag

| # | Limitação Técnica Real | Evidência no Código | Impacto Prático |
| :---: | :--- | :--- | :--- |
| **1** | **`provision_project.py` tem caminhos absolutos "hardcoded" da máquina do autor** | `base_dir=r'C:\Users\trcnologia\orca\workspaces\PROJETOS Criados com IA'` e `os.path.join(os.path.expanduser('~'), '.agents', 'skills', 'aidd-master-pack', ...)` | O comando `init` só funciona corretamente na máquina/instalação original; em outro ambiente, precisa de ajuste manual do `base_dir` e da skill instalada em `~/.agents/skills/aidd-master-pack/`. Não é portátil "out of the box". |
| **2** | **Sem gerador de manifesto de execução (`PLANO-EXECUCAO-ESTRUTURADO.json`) nos scripts do pacote** | `scripts/aidd.py cmd_status` apenas *lê* um `PLANO-EXECUCAO-ESTRUTURADO.json` se ele já existir no projeto — nenhum script desta tag o *escreve* | Diferente de versões futuras, o planejamento estruturado em JSON não é automatizado; quando presente (visto nos `examples/`), foi escrito manualmente/pelo agente de IA, com um esquema simples de 2 campos (`projeto`, `fases`). |
| **3** | **Apenas 3 gates de qualidade, nenhum bloqueia lógica de negócio ou testes automaticamente no fluxo de `add-module`** | `templates/gates/`: `G_QUALIDADE.py` (só `py_compile`), `G_SEGREDOS.py` (regex + entropia de Shannon), `G_HARNESS_COMPAT.py` (sempre retorna sucesso, sem checagem real) | `G_HARNESS_COMPAT.py` imprime "[OK]" incondicionalmente — é um stub funcional, não uma verificação real de compatibilidade de harness. Não existem gates de estrutura (`G_ESTRUTURA`), contratos (`G_CONTRACTS`), testes (`G_TESTES`) nem segurança (`G_SEGURANCA`) nesta tag. |
| **4** | **EventBus e Webhooks apenas em memória / thread simples, sem garantias de entrega** | `templates/v2/events.py` é um `defaultdict(list)` de callbacks síncronos; `webhooks.py` dispara requisição HTTP numa `threading.Thread` sem fila, retry ou assinatura HMAC | Qualquer falha de rede no webhook é apenas logada (`WEBHOOK_WARN`); não há *at-least-once delivery*, outbox pattern ou verificação de assinatura no destino. |
| **5** | **Testes unitários gerados são triviais e não fazem parte do `audit`** | `add_module.py` gera 1 teste padrão (criar/listar/deletar) em `tests/unit/`; `cmd_audit` em `aidd.py` **não** executa pytest — só os 3 gates. Pytest só roda via `aidd.py test unit` | A cobertura de teste depende de execução manual separada (`python scripts/aidd.py test`), não é parte do gate de auditoria. |
| **6** | **MCP Server, cross-domain EventBus e Swagger Studio "3 colunas" só existem como exemplo manual, não como gerador** | `examples/enterprise-suite-v4/src/core/mcp_server.py` e a orquestração cross-domínio em `examples/enterprise-suite-v4/src/server.py` não têm script correspondente em `scripts/` que os gere automaticamente | Construir um servidor MCP, orquestração de eventos entre módulos "CRM → ERP" ou o portal `/mcp` exige que o agente de IA copie manualmente o padrão do exemplo — não há comando `aidd.py add-mcp` ou equivalente nesta tag. |
| **7** | **Ausência de autenticação/RBAC no Shared Kernel** | `templates/v2/shared/utils/crypto.py` só fornece hashing PBKDF2 e geração de token; não há módulo `security.py`, JWT ou middleware de autorização no kernel desta tag | Qualquer sistema de login/permissões precisa ser escrito do zero pelo agente por cima do kernel — o pacote não fornece essa camada. |
| **8** | **Sem suporte a migrações de schema versionadas** | `add_module.py` gera apenas `CREATE TABLE IF NOT EXISTS` direto em `models.py`, sem tabela `_schema_migrations` ou versionamento | Alterações de schema em produção exigem gerenciamento manual; não há mecanismo de migração incremental nesta tag. |

---

## 3. O Que Está Bem Resolvido Nesta Tag

- **Zero dependências externas nos scripts do núcleo** (`aidd.py`, `add_module.py`, gates) — rodam com Python puro da stdlib.
- **Scanner de segredos com entropia de Shannon** (`G_SEGREDOS.py`) já é uma heurística razoavelmente sofisticada para uma tag "0.0.1" — combina regex de prefixos conhecidos (`sk-`, `AIza`, `ghp_`, `xox`) com cálculo de entropia (limiar 4.6 bits).
- **Gerador de OpenAPI 3.1 dinâmico com Swagger Studio 3 colunas** (`templates/v2/openapi.py`, ~1000 linhas) já é o recurso mais maduro da tag: sidebar navegável, playground interativo (cURL/JS/Python) e exportação de `openapi.json` — tudo em um único arquivo HTML autocontido, sem build step.
- **Design System "Impeccable"** consistente entre os exemplos: scrollbar de 4px, zero emojis em UI, toasts/modais customizados substituindo diálogos nativos do navegador.

---

## 4. Roadmap Observado em Tags Posteriores (Referência Breve, Sem Aprofundar)

Sem entrar no código dessas tags (fora do escopo deste relatório), os nomes e a progressão semântica das tags seguintes (`v4.1.0`, `v4.2.0`, `v4.3.0`, `v5.0.0`, `v5.1.0`) e os documentos hoje presentes no HEAD do repositório (ex.: `ANALISE_TECNICA_E_POSICIONAMENTO_REALISTA.md`, referenciando "7 Quality Gates", MCP nativo, RBAC, Result Pattern, migrações de schema e SPEC em 3 níveis) indicam que essas limitações — ausência de `G_ESTRUTURA`/`G_TESTES`/`G_CONTRACTS`/`G_SEGURANCA`, falta de geração automática do manifesto de plano, ausência de RBAC/migrações — foram endereçadas em versões posteriores ao v4.0.1. Este relatório não afirma *como* foram resolvidas, apenas registra que, na tag v4.0.1, elas ainda são lacunas reais.

---

*Este relatório reflete exclusivamente o conteúdo extraído da tag `v4.0.1` do repositório `heverton-dev/aidd-master-pack`, via `git archive v4.0.1`.*
