# Backlog de Invariantes: Leis Invioláveis em Estado "Sem Gate" (ISSUE-0010)

> **Data de Levantamento:** 19/09/2026  
> **Status:** Ativo e Auditado via `gates/G_LEI_DECLARA_PORTAO.py`  
> **Referência:** `AGENTS.md` §2 e `docs/issues/10-cada-lei-declara-seu-portao.md`  

---

## 1. Visão Geral e Mapa de Força de Enforcement

Em conformidade com a **ISSUE-0010** e a **Lei #8 (Honestidade de Rótulo)**, nenhuma lei do ecossistema pode ter enforcement presumido ou silencioso. Cada lei declara explicitamente se possui portão verificador (`provado` ou `nao-provado`) ou se opera como `sem gate — cumprimento por convenção` (`sem-gate`).

| Lei | Nome | Portão Declarado | Força | Status da Cobertura |
| :---: | :--- | :--- | :---: | :--- |
| **01** | Determinism First | `sem gate — cumprimento por convenção` | `sem-gate` | No Backlog (Ver Item 2.1) |
| **02** | Binary Quality | `sem gate — cumprimento por convenção` | `sem-gate` | No Backlog (Ver Item 2.2) |
| **03** | Structured Persistence | `sem gate — cumprimento por convenção` | `sem-gate` | No Backlog (Ver Item 2.3) |
| **04** | Extreme Token Economy | `sem gate — cumprimento por convenção` | `sem-gate` | Mitigação via ISSUE-0012 |
| **05** | Zero Stubs / Zero Mocks | `gates/G_TESTES_REAIS.py` | `provado` | Coberto e testado (exit 1) |
| **06** | Agnostic Supremacy | `gates/G_COMPONENTE_AGNOSTICO.py` | `provado` | Coberto e testado (exit 1) |
| **07** | Developer in Control | `gates/G_ZERO_HEADLESS.py` | `provado` | Coberto e testado (exit 1) |
| **08** | Label Honesty | `gates/G_HONESTIDADE_ROTULO.py` | `provado` | Coberto e testado (exit 1) |
| **09** | Tool Testing Discipline | `sem gate — cumprimento por convenção` | `sem-gate` | No Backlog (Ver Item 2.4) |
| **10** | Quarteto Sine Qua Non Dinâmico | `sem gate — cumprimento por convenção` | `sem-gate` | No Backlog (Ver Item 2.5) |
| **11** | Padrão-Ouro de Stack Tecnológica | `sem gate — cumprimento por convenção` | `sem-gate` | No Backlog (Ver Item 2.6) |
| **12** | Anti-Docs Rot & Canonical Ingestion | `gates/G_DOCS_ROT.py` | `provado` | Coberto e testado (exit 1) |
| **13** | Todo Portão Deve Provar que Morde | `gates/G_PORTAO_PROVA_QUE_MORDE.py` | `provado` | Coberto e testado (exit 1) |

---

## 2. Detalhamento do Backlog: Leis Sem Portão

### 2.1 Lei #1 — Determinism First
- **Exigência:** Uso de scripts determinísticos, AST, regex ou JSON Schema. Proibição de uso de LLM para tarefas puramente mecânicas.
- **Gap Atual:** O ecossistema possui `G_LLM_PROMPT_SHIELD.py` que audita sanitização de prompts, mas não existe um analisador estático que determine se uma chamada a LLM é "mecânica" versus "heurística/cognitiva".
- **Ação Futura:** Especificar heurística de AST que detecte chamadas de modelo em pipelines mecânicos sem decisão de alto nível, ou manter formalmente sob verificação arquitetural humana.

### 2.2 Lei #2 — Binary Quality
- **Exigência:** Toda mudança deve passar por Quality Gates (`python ecossistema.py audit`, exit 0 = passa, exit 1 = bloqueia).
- **Gap Atual:** A qualidade binária é imposta pelo orquestrador de pre-commit e pelo runner `cmd_audit`. Não existe um portão que audite se os próprios scripts terminam estritamente com `sys.exit(0)` ou `sys.exit(1)` (sem retorno numérico ambíguo).
- **Ação Futura:** Criar um lint estático (`G_SAIDA_BINARIA.py`) que inspecione todos os arquivos em `gates/` e asserte via AST que os únicos pontos de saída sejam chamadas a `sys.exit(0)` ou `sys.exit(1)`.

### 2.3 Lei #3 — Structured Persistence
- **Exigência:** Persistência de estado em arquivos estruturados (JSON, SQLite WAL), nunca na memória volátil da conversa.
- **Gap Atual:** O motor de orquestração salva em `flight_plan.json` e logs em `.jsonl`. Não há portão estático global garantindo que nenhum script mantenha estado apenas em variáveis de processo transitórias.
- **Ação Futura:** Criar gate `G_ESTRUTURA_ESTADO.py` validando os schemas JSON de persistência das ferramentas.

### 2.4 Lei #4 — Extreme Token Economy
- **Exigência:** Prompts minimalistas, regras em inglês compacto, respostas densas em PT-BR apenas quando solicitadas.
- **Gap Atual:** Nenhum dos 27 gates atuais analisa o idioma dos arquivos de regras centrais (`AGENTS.md`).
- **Mitigação Planejada:** Já formalizada na **ISSUE-0012** (`docs/issues/12-gate-de-idioma-lei-4.md`), que construirá o gate determinístico de idioma e concisão.

### 2.5 Lei #9 — Tool Testing Discipline
- **Exigência:** Ciclo de cinco passos do `docs/protocolos/PROTOCOLO-TESTES-FERRAMENTAS.md` antes de declarar conformidade de ferramenta.
- **Gap Atual:** A disciplina de 5 passos é procedimental e executada interativamente pelo desenvolvedor/agente; não é checada no pre-commit.
- **Ação Futura:** Criar verificação em CI que audite se a data/hash do relatório em `docs/teste-end-to-end/` coincide com o último commit que tocou a ferramenta.

### 2.6 Lei #10 — Quarteto Sine Qua Non Dinâmico
- **Exigência:** Todo projeto gerado ou evoluído DEVE nascer nativamente com 4 pilares: Swagger Studio, Webhook Studio, MCP Studio e Guia do Utilizador.
- **Gap Atual:** Existe `gates/G_PROTOCOL_FALLBACK.py` (que valida paridade REST vs MCP quando ambos existem) e `tools/aidd-planner/scripts/gates/G_PLANNER_SINE_QUA_NON.py` (local do planner). Porém, falta um gate na raiz que audite deliverables gerados em testes ou saídas reais contra a presença obrigatória dos 4 pilares.
- **Ação Futura:** Promover `G_PLANNER_SINE_QUA_NON.py` ou criar `G_QUARTETO_SINE_QUA_NON.py` no nível raiz.

### 2.7 Lei #11 — Padrão-Ouro de Stack Tecnológica
- **Exigência:** Todo fluxo deve gerar Frontend em Next.js + TypeScript + Tailwind CSS (Backend Python + SQLite WAL, API OpenAPI 3.1).
- **Gap Atual:** O ecossistema possui `gates/G_FRONTEND_LAYERS.py` (que valida separação de camadas dumb components vs fetch), mas não há gate que reprove a existência de frameworks não autorizados no frontend quando gerado.
- **Ação Futura:** Criar gate `G_STACK_FRONTEND_PADRAO.py` validando dependências de frontend (`package.json` gerado) contra Next.js, React, Tailwind CSS e TypeScript.
