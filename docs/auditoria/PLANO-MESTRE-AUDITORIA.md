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
- [ ] `aidd-melhoria` (Análise estruturada de código e refatoração)
- [ ] `aidd-diagnose` (Triage de falhas científicas)
- [ ] `aidd-tdd` (Ciclo restrito Red-Green-Refactor)
- [ ] `aidd-tickets` (Decomposição do escopo)
- [ ] `aidd-spec` (Geração de documento determinístico)
- [ ] `aidd-grill` & `aidd-grill-docs` (Entrevistas Socráticas)
- [ ] `aidd-handoff` (Compressão de contexto de sessão)
- [ ] `aidd-plan` & `aidd-planos` (Transformação de relatórios em planos estruturados)
- [ ] `aidd-planner-runner` (Engine intake SDD/BDD)
- [ ] `debug-issue` / `review-changes` / `refactor-safely` (Apoio via Grafo)
- [ ] `explore-codebase` / `resumo-sessao`

## 2. Gestão de Ecossistema (Geradores de Estrutura)
Ferramentas responsáveis por criar e auditar outras micro-ferramentas.
- [ ] `aidd-componentes` (Componentes Agnósticos)
- [ ] `aidd-dependencias` (Instalação e verificação de skills externas)
- [ ] `aidd-skills` / `skill-creator-runner` (Motor de criação de Skills)
- [ ] `aidd-mcp` / `mcp-creator-runner` (Exposição de servidores MCP)
- [ ] `aidd-livro-texto` (Gerador corporativo Auditable)

## 3. Orquestradores de Chão de Fábrica (Middlewares)
Responsáveis pelo despacho para worktrees e roteamento determinístico.
- [ ] `aidd-pipeline-runner` (Execução determinística linear)
- [ ] `aidd-dispatch-runner` (Despacho de fatias verticais VSA / DAG)
- [ ] `aidd-orchestrator-runner` (Orquestrador Mestre Síncrono)
- [ ] `aidd-orca` / `aidd-orchestrate` (Execução Multi-fases ORCA)

## 4. Governança, Arquitetura e Infraestrutura (Camada Base)
- [ ] `aidd-forge-runner` (Bootstrap e Governance Hardening)
- [ ] `aidd-master-runner` (Harmonização Monólito Modular / VSA)
- [ ] `aidd-enterprise-runner` (Auditoria e resiliência SHA-256)
- [ ] `aidd-ops-runner` (Infraestrutura Agentic Meta-Orchestrator)

## 5. Motores de Geração (As Fábricas Verticais Canônicas)
- [ ] `aidd-generator-runner` (Engine do Fluxo Pure - 8 Fases)
- [ ] `aidd-factory-runner` (Engine do Fluxo Open/Multi-service)
- [ ] `aidd-bridge-runner` (Engine do Fluxo Freedom/Low-Code Package)

## 6. Wrappers End-to-End (A Tríade Final)
A orquestração invisível que liga o Planner ao Motor e desce para a Infraestrutura.
- [ ] `fluxo-01-runner` (Do Zero Puro / Pure)
- [ ] `fluxo-02-runner` (Motores Open-Source / Open)
- [ ] `fluxo-03-runner` (Low-Code App / Freedom)
