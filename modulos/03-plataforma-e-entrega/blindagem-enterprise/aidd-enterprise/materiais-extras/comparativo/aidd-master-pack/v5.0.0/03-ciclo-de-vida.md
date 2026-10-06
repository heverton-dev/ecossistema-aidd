# Ciclo de Vida Completo de Uso — AIDD Master Pack

> **Tag/versão documentada:** `v5.0.0`
> **Fonte primária:** `CICLO_VIDA_COMPLETO_V4.md` (documento versionado dentro desta própria tag) cruzado com o comportamento real de `scripts/aidd.py`, `scripts/compose_suite.py` e `scripts/gates/*.py` extraídos via `git archive v5.0.0`.

Este documento descreve as fases reais pelas quais um projeto passa ao usar o AIDD Master Pack nesta tag, desde a obtenção do pacote até a entrega de uma aplicação operacional.

---

## Visão geral em 4 fases

```
FASE 0 → Acesso e instalação no ambiente do usuário
FASE 1 → Entrada do usuário (linguagem natural ou comando declarativo)
FASE 1.5 → Especificação e alinhamento arquitetural (SPEC Gate)
FASE 2 → Processamento mecânico (scaffolding + gates)
FASE 3 → Saída entregue e operacional (servidor com múltiplos portais)
```

---

## FASE 0 — Acesso, instalação e diagnóstico do ambiente

1. **Obtenção do pacote:** clone do repositório (`git clone` + `git checkout v5.0.0`) ou cópia de pasta local.
2. **Diagnóstico e bootstrap automático:** o comando `python scripts/aidd.py setup`:
   - Reporta a versão do Python em uso.
   - Instala `requirements.txt` se ele existir na raiz do pacote (nesta tag esse arquivo não está presente na raiz, então cai no fallback).
   - Fallback: `ensure_environment()` verifica se `pytest` e `requests` estão instalados e os instala via `pip` sob demanda caso faltem.
   - Detecta se o binário `git` está disponível no `PATH`.
   - Detecta se o binário `orca` (ORCA ADE) está disponível: se sim, assume "Modo A" (mesas de trabalho isoladas); se não, assume "Modo B" (subagentes nativos / git worktrees).
3. Ao final, imprime confirmação de que o ambiente está pronto para compor projetos.

---

## FASE 1 — Entrada do usuário (zero atrito)

Existem duas formas equivalentes de disparar a criação de um projeto:

- **Modo A — linguagem natural direta:** `python scripts/aidd.py "Crie uma aplicação de CRM e ERP de faturamento"`. Internamente, `main()` detecta que o primeiro argumento não é um subcomando conhecido (`setup`, `init`, `plan`, `apply`, `compose`, `add-module`, `test`, `audit`, `bench`, `heal`, `deploy`, `status`, `export-frontend`, `refine-module`, `scaffold-infra`) e trata a linha inteira como um prompt, chamando `parse_natural_language_intent()`.
- **Modo B — comando declarativo explícito:** `python scripts/aidd.py plan "Crie um CRM e ERP"`.

Ambos os caminhos convergem para a mesma função `cmd_plan()`.

### Como o prompt é interpretado (mecânica real, não IA generativa)

`cmd_plan()` faz correspondência textual do prompt contra uma lista fixa de domínios conhecidos (`KNOWN_DOMAINS`): `crm`, `erp`, `faturamento`, `financeiro`, `vendas`, `helpdesk`, `suporte`, `logistica`, `estoque`, `membros`, `cursos`, `catalogo`, `produtos`, `pedidos`, `whatsapp`, `afiliados`, `assinaturas`, `fiscal`, `analytics`, `lead(s)`, `campanhas`, `marketing`, `tickets` — com normalização de sinônimos (`lead`/`leads` → `crm`; `suporte`/`tickets` → `helpdesk`). Se nenhum domínio conhecido for encontrado, o script extrai palavras de 4+ letras do prompt (ignorando stop-words como "crie", "sistema", "para") e usa até 4 delas como módulos. Não há chamada a nenhum modelo de linguagem nesta etapa — é reconhecimento de padrões determinístico em Python puro.

---

## FASE 1.5 — Especificação e alinhamento arquitetural (SPEC Gate)

Ainda dentro de `cmd_plan()`, dois artefatos são gerados automaticamente no diretório `app_<módulos>-suite/`:

1. **`SPEC-ARQUITETURA.md`** — especificação em 3 níveis:
   - **Nível 1 (Negócio):** para cada domínio detectado, define entidade principal, casos de uso primários (Cadastrar, Consultar por ID, Listar com filtro/busca, Atualizar, Excluir com soft-delete) e os 3 eventos de domínio obrigatórios (`<modulo>_criado`, `<modulo>_atualizado`, `<modulo>_deletado`).
   - **Nível 2 (Back-end/Contratos):** rotas REST previstas (`/listar`, `/metricas`, `/obter`, `/criar`, `/atualizar`, `/deletar`), ferramentas MCP correspondentes (`mod_<m>_listar`, etc.) e a tabela SQLite WAL prevista.
   - **Nível 3 (Front-end/UX):** design system Impeccable UI, componente isolado por módulo, requisitos de acessibilidade WCAG 2.1 e composição do dashboard (KPIs, tabela paginada, modais).
2. **`PLANO-EXECUCAO-ESTRUTURADO.json`** — manifesto de máquina com status inicial `"PLANEJADO"` (estrutura detalhada no relatório `plano-de-execucao.md`).

O usuário revisa esses dois arquivos (ou o resumo apresentado pelo agente que orquestra a chamada) e só avança para a fase seguinte ao dar sinal de aprovação em linguagem natural ("Aprovado", "Pode criar", "OK"), que dispara `python scripts/aidd.py apply --dir <pasta>`.

Se `cmd_plan()` for chamado com `--apply`, a Fase 2 é disparada imediatamente sem esperar aprovação manual — mas o fluxo conversacional descrito no `SKILL.md` desta tag prevê sempre uma pausa para confirmação humana antes de aplicar.

---

## FASE 2 — Processamento mecânico (scaffolding + gates)

Disparada por `aidd.py apply` (que lê o manifesto e chama `compose_suite()`) ou diretamente por `aidd.py compose <dir> <nome> <módulos...>`. Etapas realizadas por `scripts/compose_suite.py` e `scripts/add_module.py`, confirmadas pelo `CICLO_VIDA_COMPLETO_V4.md` desta mesma tag:

1. Linter AST anti-acoplamento: bloqueia imports diretos entre módulos irmãos (ex.: `modules.crm` importando `modules.erp`).
2. Scaffolding do Shared Kernel: `src/core/database.py` (SQLite WAL + `busy_timeout=5000` + soft-delete), `src/core/result.py` (padrão `Result.ok`/`Result.fail`), `src/core/jobs.py` (fila assíncrona).
3. Controle de migrações via tabela interna `_schema_migrations`.
4. Geração atômica de cada fatia vertical (`models.py`, `services.py`, `routes.py`, componente HTML, teste `pytest`), com seed fixtures determinísticas (2 registros de exemplo por módulo).
5. EventBus pub/sub com envelope padronizado (`event_id`, `event_name`, `timestamp` ISO UTC, `origin_module`, `data`) e tracing por UUID.
6. Geração de `src/server.py` dinâmico, com fallback de porta (tenta 3000 até 3025) e middleware CORS/preflight.
7. Geração de testes unitários com asserção de mutação de estado real (`assert item_antes != item_depois`).
8. Linter de acessibilidade / Impeccable UI (proibição de `alert()`/`confirm()`/`prompt()`, exigência de `aria-label`, ícones SVG Lucide).
9. Snapshot SHA-256 dos contratos OpenAPI e MCP (usado depois pelo `G_CONTRACTS` para detectar quebras acidentais).
10. Sincronização de regras para múltiplos IDEs (`.cursor/rules/`, `.claude/`, `.agent/rules/`).
11. Geração do grafo de memória `CONTEXTO-PROJETO.md`.
12. Execução da bateria de **7 Quality Gates determinísticos** via `python scripts/aidd.py audit --report` (`G_ESTRUTURA`, `G_QUALIDADE`, `G_TESTES`, `G_CONTRACTS`, `G_SEGREDOS`, `G_HARNESS_COMPAT`, `G_SEGURANCA` — este último incluído condicionalmente se o arquivo `G_SEGURANCA.py` existir no diretório de gates). Cada gate roda como subprocesso isolado (`python <gate>.py --dir <alvo>`) e precisa devolver exit code 0.
13. Benchmark de concorrência opcional: `python scripts/aidd.py bench -n 100` dispara N operações concorrentes contra o SQLite WAL e o EventBus via `ThreadPoolExecutor`, reportando taxa de sucesso, latência média e RPS.

Se qualquer gate falhar, `cmd_audit()` encerra com exit code 1 e a mensagem "`[BLOQUEADO]: O projeto NÃO passou em todos os gates determinísticos`" — não há entrega parcial "aprovada por engano".

### Auto-remediação (`heal`)

`python scripts/aidd.py heal` relê `PLANO-EXECUCAO-ESTRUTURADO.json` e reexecuta `compose_suite()` sobre o mesmo diretório, útil para recompor artefatos corrompidos ou desatualizados sem recomeçar do zero.

---

## FASE 3 — Saída entregue e operacional

Ao final da Fase 2, o projeto gerado pode ser iniciado com `python src/server.py` (ou `python <app>/src/server.py`), expondo, na primeira porta livre entre 3000 e 3025:

| Portal | Rota | Conteúdo |
| :--- | :--- | :--- |
| Aplicação (Super-App UI) | `/` | SPA com dashboard, KPIs, tabelas paginadas e modais de CRUD |
| Swagger Studio | `/docs` | Documentação OpenAPI 3.1 interativa, com testador de rotas ao vivo |
| Webhook Studio | `/webhooks` | Cadastro de endpoints, secret HMAC e histórico de disparos |
| MCP nativo | `/mcp` | Servidor JSON-RPC 2.0 (`tools/list`, `tools/call`) para agentes de IA |
| Especificação crua | `/openapi.json` | JSON OpenAPI 3.1 gerado dinamicamente pelo `RouteRegistry` |
| Métricas | `/metrics` | Exposição no formato Prometheus (`http_requests_total`, `http_request_duration_seconds`) |

Junto com o servidor ativo, o artefato de auditoria `RELATORIO-AUDITORIA.json` (gerado por `aidd audit --report`) documenta, por gate, status (`PASS`/`FAIL`), exit code e duração em milissegundos — servindo como comprovação factual do estado do projeto no momento da entrega.

---

## Comandos adicionais disponíveis nesta tag (uso opcional, fora do fluxo principal)

| Comando | Efeito |
| :--- | :--- |
| `aidd.py add-module <nome> -d "<descrição>"` | Adiciona uma nova fatia vertical a um projeto já composto, sem recompor os demais módulos. |
| `aidd.py test [unit\|contracts\|load\|all]` | Executa a suíte de testes unitários (`pytest`), o gate de contratos isoladamente, ou um teste de carga Locust headless de 5s. |
| `aidd.py refine-module <modulo> --spec features/<modulo>.feature` | Executa `behave` sobre um arquivo de cenários Gherkin; falha (exit ≠ 0) se algum cenário não passar. A implementação da lógica que faz o cenário passar cabe a um agente externo, não a este comando. |
| `aidd.py export-frontend --stack nextjs` | Gera `frontend/types.ts` e um projeto Next.js 14 mínimo a partir do `RouteRegistry` já composto. |
| `aidd.py scaffold-infra` | Gera `infra/terraform/main.tf` e um Helm chart completo em `infra/helm/` (não executa `terraform`/`helm`). |
| `aidd.py status` | Inspeciona o manifesto, lista módulos ativos e gates presentes, sem executar nada. |
| `aidd.py deploy [docker\|vps]` | Para `docker`, roda `docker compose up -d --build`; para `vps`, apenas orienta a executar `deploy.sh` no servidor de produção. |

---

*Ciclo de vida reconstruído a partir de `CICLO_VIDA_COMPLETO_V4.md` desta tag e validado linha a linha contra `scripts/aidd.py` e `scripts/compose_suite.py` extraídos de `git archive v5.0.0`.*
