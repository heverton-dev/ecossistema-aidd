# Plano Mestre de Auditoria 15-D (Mapa Topográfico do Ecossistema)

Este documento atua como o inventário exaustivo e a fila de execução oficial para a auditoria em massa de todas as ferramentas e fluxos do Ecossistema AIDD. 

A tática de ataque e engenharia reversa estabelecida é **Bottom-Up (Das fundações para o teto)**. O enxame auditor consumirá primeiro as fatias menores e autônomas antes de auditar as macro-ferramentas que as englobam.

---

## O Protocolo Restrito de Orquestração (Regra Inegociável)
Toda auditoria executada a partir deste plano deve OBRIGATORIAMENTE conter dois artefatos isolados dentro da sua respectiva pasta (ex: `docs/auditoria/nome-do-alvo/`):

1. **O Prompt de Comando (O Piloto):** 
   - Proibido o uso de variáveis vazias (`{}`) ou lacunas para intervenção humana. 
   - Deve ser um arquivo de texto fechado e telegráfico com os caminhos reais (relativos/absolutos).
   - Deve instruir a IA a: ler o `TEMPLATE-AUDITORIA`, ler os arquivos-fonte da skill alvo, gerar e salvar o relatório `.md`, e obrigatoriamente acionar o script de Quality Gate a seguir.
2. **O Script de Quality Gate (O Inspetor):**
   - Scripts python de auditoria JAMAIS devem atuar como disparadores ou montadores de string para LLMs.
   - Sua função é estritamente atuar como o **Gate Validador** (ex: `G_auditoria_15D.py`).
   - O Gate lê o artefato `.md` gerado pela LLM e aplica um `assert` implacável (exigindo a presença das tags D1 a D15). Retorna `exit 0` (sucesso) ou `exit 1` (forçando a IA a se auto-corrigir).

---

## 1. Fluxos Horizontais (Fundações Procedurais)
Ferramentas atômicas e táticas de apoio diário.
- [x] `aidd-melhoria` (Análise estruturada de código e refatoração) — [Laudo Retorno](aidd-melhoria/ciclo-02/LAUDO-15D-REVISADO.md)
- [x] `aidd-diagnose` (Triage de falhas científicas) — [Laudo Retorno](aidd-diagnose/ciclo-01/LAUDO-15D-REVISADO.md)
- [x] `aidd-tdd` (Ciclo restrito Red-Green-Refactor) — [Laudo Retorno](aidd-tdd/ciclo-01/LAUDO-15D-REVISADO.md)
- [x] `aidd-tickets` (Decomposição do escopo) — [Laudo Retorno](aidd-tickets/ciclo-01/LAUDO-15D-REVISADO.md)
- [x] `aidd-spec` (Geração de documento determinístico) — [Laudo Retorno](aidd-spec/ciclo-01/LAUDO-15D-REVISADO.md)
- [x] `aidd-grill` & `aidd-grill-docs` (Entrevistas Socráticas) — [Laudo Retorno](aidd-grill/ciclo-01/LAUDO-15D-REVISADO.md)
- [x] `aidd-handoff` (Compressão de contexto de sessão) — [Laudo Retorno](aidd-handoff/ciclo-01/LAUDO-15D-REVISADO.md)
- [x] `aidd-plan` & `aidd-planos` (Transformação de relatórios em planos estruturados) — [Laudo Retorno](aidd-plan/ciclo-01/LAUDO-15D-REVISADO.md)
- [x] `aidd-planner-runner` (Engine intake SDD/BDD) — [Laudo Retorno](aidd-planner-runner/ciclo-01/LAUDO-15D-REVISADO.md)
- [x] `debug-issue` / `review-changes` / `refactor-safely` (Apoio via Grafo) — [Laudo Retorno](code-review-graph/ciclo-01/LAUDO-15D-REVISADO.md)
- [x] `explore-codebase` / `resumo-sessao` — [Laudo Retorno](aidd-session/ciclo-01/LAUDO-15D-REVISADO.md)

## 2. Gestão de Ecossistema (Geradores de Estrutura)
Ferramentas responsáveis por criar e auditar outras micro-ferramentas.
- [x] `aidd-componentes` (Componentes Agnósticos) — [Laudo Retorno](aidd-componentes/ciclo-01/LAUDO-15D-REVISADO.md)
- [x] `aidd-dependencias` (Instalação e verificação de skills externas) — [Laudo Retorno](aidd-dependencias/ciclo-01/LAUDO-15D-REVISADO.md)
- [x] `aidd-skills` / `skill-creator-runner` (Motor de criação de Skills) — [Laudo Retorno](aidd-skills/ciclo-01/LAUDO-15D-REVISADO.md)
- [x] `aidd-mcp` / `mcp-creator-runner` (Exposição de servidores MCP) — [Laudo Retorno](aidd-mcp/ciclo-01/LAUDO-15D-REVISADO.md)
- [x] `aidd-livro-texto` (Gerador corporativo Auditable) — [Laudo Retorno](aidd-livro-texto/ciclo-01/LAUDO-15D-REVISADO.md)

## 3. Orquestradores de Chão de Fábrica (Middlewares)
Responsáveis pelo despacho para worktrees e roteamento determinístico.
- [x] `aidd-pipeline-runner` (Execução determinística linear) — [Laudo Retorno](aidd-pipeline-runner/ciclo-01/LAUDO-15D-REVISADO.md)
- [x] `aidd-dispatch-runner` (Despacho de fatias verticais VSA / DAG) — [Laudo Retorno](aidd-dispatch-runner/ciclo-01/LAUDO-15D-REVISADO.md)
- [x] `aidd-orchestrator-runner` (Orquestrador Mestre Síncrono) — [Laudo Retorno](aidd-orchestrator-runner/ciclo-01/LAUDO-15D-REVISADO.md)
- [x] `aidd-orca` / `aidd-orchestrate` (Execução Multi-fases ORCA) — [Laudo Retorno](aidd-orca/ciclo-01/LAUDO-15D-REVISADO.md)

## 4. Governança, Arquitetura e Infraestrutura (Camada Base)
- [x] `aidd-forge-runner` (Bootstrap e Governance Hardening) — [Laudo Retorno](aidd-forge-runner/ciclo-01/LAUDO-15D-REVISADO.md)
- [x] `aidd-master-runner` (Harmonização Monólito Modular / VSA) — [Laudo Retorno](aidd-master-runner/ciclo-01/LAUDO-15D-REVISADO.md)
- [x] `aidd-enterprise-runner` (Auditoria e resiliência SHA-256) — [Laudo Retorno](aidd-enterprise-runner/ciclo-01/LAUDO-15D-REVISADO.md)
- [x] `aidd-ops-runner` (Infraestrutura Agentic Meta-Orchestrator) — [Laudo Retorno](aidd-ops-runner/ciclo-01/LAUDO-15D-REVISADO.md)

## 5. Motores de Geração (As Fábricas Verticais Canônicas)
- [x] `aidd-pure-runner` (Engine do Fluxo Pure - 8 Fases) — [Laudo Retorno](aidd-pure-runner/ciclo-01/LAUDO-15D-REVISADO.md)
- [x] `aidd-open-runner` (Engine do Fluxo Open/Multi-service) — [Laudo Retorno](aidd-open-runner/ciclo-01/LAUDO-15D-REVISADO.md)
- [x] `aidd-freedom-runner` (Engine do Fluxo Freedom/Low-Code Package) — [Laudo Retorno](aidd-freedom-runner/ciclo-01/LAUDO-15D-REVISADO.md)

## 6. Wrappers End-to-End (A Tríade Final)
A orquestração invisível que liga o Planner ao Motor e desce para a Infraestrutura.
- [x] `fluxo-01-runner` (Do Zero Puro / Pure) — [Laudo Retorno](fluxo-01-runner/ciclo-01/LAUDO-15D-REVISADO.md)
- [x] `fluxo-02-runner` (Motores Open-Source / Open) — [Laudo Retorno](fluxo-02-runner/ciclo-01/LAUDO-15D-REVISADO.md)
- [x] `fluxo-03-runner` (Low-Code App / Freedom) — [Laudo Retorno](fluxo-03-runner/ciclo-01/LAUDO-15D-REVISADO.md)
