# Backlog de Invariantes: Leis Invioláveis em Estado "Sem Gate" (ISSUE-0010)

> **Data de Levantamento:** 19/09/2026 (Revisado em 20/09/2026 — Leis #3, #9 e #10 ganharam portão parcial nas Sessões 12-15; gap residual de cada uma virou ticket próprio)
> **Status:** Ativo e Auditado via `gates/G_LEI_DECLARA_PORTAO.py`  
> **Referência:** `AGENTS.md` §2 e `docs/issues/10-cada-lei-declara-seu-portao.md`  

---

## 1. Visão Geral e Mapa de Força de Enforcement

Em conformidade com a **ISSUE-0010** e a **Lei #8 (Honestidade de Rótulo)**, nenhuma lei do ecossistema pode ter enforcement presumido ou silencioso. Cada lei declara explicitamente se possui portão verificador (`provado` ou `nao-provado`) ou se opera como `sem gate — cumprimento por convenção` (`sem-gate`).

| Lei | Nome | Portão Declarado | Força | Status da Cobertura |
| :---: | :--- | :--- | :---: | :--- |
| **01** | Determinism First | `gates/G_DETERMINISMO_LEI_1.py` | `provado` | Coberto para SDKs de LLM conhecidos em gates/ e rotas mecânicas; limite declarado (semântica cognitiva requer revisão humana) |
| **02** | Binary Quality | `gates/G_SAIDA_BINARIA.py` | `provado` | Coberto via AST: todo gate em gates/ termina estritamente em sys.exit(0) ou sys.exit(1) |
| **03** | Structured Persistence | `gates/G_MIGRATION_ROT.py`, `gates/G_ESTRUTURA_ESTADO.py` | `provado` | Migrações de app gerado (Sessão 15) e schemas de estado do orquestrador (Sessão 21) cobertos e provados |
| **04** | Extreme Token Economy | `.claude/hooks/regra10_check.py`, `gates/G_IDIOMA_LEI_4.py` | `provado` | Enforced no Claude (formato + idioma); indisponível em outros harnesses (Ver 2.4) |
| **05** | Zero Stubs / Zero Mocks | `gates/G_TESTES_REAIS.py` | `provado` | Coberto e testado (exit 1) |
| **06** | Agnostic Supremacy | `gates/G_COMPONENTE_AGNOSTICO.py` | `provado` | Coberto e testado (exit 1) |
| **07** | Developer in Control | `gates/G_ZERO_HEADLESS.py` | `provado` | Coberto e testado (exit 1) |
| **08** | Label Honesty | `gates/G_HONESTIDADE_ROTULO.py` | `provado` | Coberto e testado (exit 1) |
| **09** | Tool Testing Discipline | `gates/G_ENV_ROT.py`, `gates/G_SKILL_ROT.py`, `gates/G_DISCIPLINA_TESTE_FERRAMENTA.py` | `provado` | Env rot (Sessão 13), skill rot (Sessão 14) e frescor do relatório de teste em tools/ (Sessão 22) cobertos e provados |
| **10** | Quarteto Sine Qua Non Dinâmico | `gates/G_CONTRACT_ROT.py` | `provado (parcial)` | Divergência rota-vs-spec coberta (Sessão 12); presença dos 4 pilares num deliverable gerado ainda sem portão de raiz — ver Item 2.6, ticket aberto ISSUE-0024 |
| **11** | Padrão-Ouro de Stack Tecnológica | `sem gate — cumprimento por convenção` | `sem-gate` | No Backlog (Ver Item 2.7); ticket aberto ISSUE-0025 |
| **12** | Anti-Docs Rot & Canonical Ingestion | `gates/G_DOCS_ROT.py` | `provado` | Coberto e testado (exit 1) |
| **13** | Todo Portão Deve Provar que Morde | `gates/G_PORTAO_PROVA_QUE_MORDE.py` | `provado` | Coberto e testado (exit 1) |

---

## 2. Detalhamento do Backlog: Leis Sem Portão

### 2.1 Lei #1 — Determinism First (ISSUE-0020)
- **Exigência:** Uso de scripts determinísticos, AST, regex ou JSON Schema. Proibição de uso de LLM para tarefas puramente mecânicas.
- **Enforcement Implementado:** Quality gate `gates/G_DETERMINISMO_LEI_1.py` audita via AST caminhos mecânicos (`gates/*.py` e módulos declarados) e bloqueia importações e chamadas a SDKs de LLMs conhecidos (`anthropic`, `openai`, `google.generativeai`, `litellm`, `langchain`, etc.).
- **Limite Metrológico (Lei #8 / ISSUE-0020):** Nenhum analisador estático classifica de forma geral o uso "mecânico" versus "cognitivo" de um LLM em pipelines arbitrários. O portão cobre o subconjunto verificável de SDKs conhecidos em rotas determinísticas; a integridade semântica universal permanece sob convenção e revisão arquitetural humana. Concluído na Sessão 19.

### 2.2 Lei #2 — Binary Quality (ISSUE-0021)
- **Exigência:** Toda mudança deve passar por Quality Gates (`python ecossistema.py audit`, exit 0 = passa, exit 1 = bloqueia).
- **Enforcement Implementado:** Quality gate `gates/G_SAIDA_BINARIA.py` inspeciona via AST todos os arquivos em `gates/` e asserte que todos os pontos de saída utilizem estritamente `sys.exit(0)` ou `sys.exit(1)`, sem códigos numéricos ambíguos, sem bare returns e sem risco de fall-through no bloco `__main__`. Concluído na Sessão 20.

### 2.3 Lei #3 — Structured Persistence (ISSUE-0022)
- **Exigência:** Persistência de estado em arquivos estruturados (JSON, SQLite WAL), nunca na memória volátil da conversa.
- **Cobertura Dupla Implementada (Sessões 15 e 21):**
  1. `gates/G_MIGRATION_ROT.py`: prova, num banco SQLite descartável, que as migrações de banco dos apps gerados aplicam, revertem e reaplicam sem divergência.
  2. `gates/G_ESTRUTURA_ESTADO.py`: valida os schemas e integridade estruturada dos artefatos de estado do orquestrador (`.orca-flight-plan.json`, `flight_plan.json`, `.orca_state.json`, logs `*telemetry*.jsonl`).
- **Limite Metrológico (Lei #8 / ISSUE-0022):** A validação cobre estritamente o inventário declarado de artefatos de persistência de orquestração do ecossistema; a inexistência de variáveis voláteis arbitrárias fora do inventário permanece sob revisão arquitetural humana. Concluído na Sessão 21.

### 2.4 Lei #4 — Extreme Token Economy (ISSUE-0013)
- **Exigência:** Prompts minimalistas, regras em inglês compacto, respostas estritamente moldadas (Rule 10: 1 top sentence direta, corpo em bullets com fatos/números sem narrar passos, bloco final de sugestão/recomendação isolado; proibido preâmbulo, saudações, ou alternativas sem recomendação).
- **Enforcement Implementado:** O hook determinístico `.claude/hooks/regra10_check.py` (sincronizado universalmente via `componentes/compartilhado/hooks/regra10_check.py`) audita tanto termos técnicos não explicados quanto o shape determinístico da mensagem.
- **Limitação de Enforcement por Harness (Honestidade de Rótulo - Lei #8):**
  - **Claude Code:** Suporte total e ativo via Stop Hook no ciclo de vida da mensagem.
  - **Cursor, Gemini CLI / Antigravity, OpenCode, MimoCode, Qoder, CodeBuddy:** **Enforcement automatizado INDISPONÍVEL.** Esses ambientes não fornecem hook nativo de interceptação de resposta de chat (Stop hook). O hook físico é replicado nas pastas de hooks para integridade de distribuição, mas o cumprimento da regra opera exclusivamente por convenção e diretiva explícita nos arquivos ponteiro (`GEMINI.md`, `QODER.md`, `CODEBUDDY.md`, `.cursor/rules/aidd.md`). Nunca assumir cobertura automatizada nesses harnesses.

### 2.5 Lei #9 — Tool Testing Discipline (ISSUE-0023)
- **Exigência:** Ciclo de cinco passos do `docs/protocolos/PROTOCOLO-TESTES-FERRAMENTAS.md` antes de declarar conformidade de ferramenta.
- **Cobertura Tríplice Implementada (Sessões 13, 14 e 22):**
  1. `gates/G_ENV_ROT.py`: audita variáveis de ambiente não documentadas em `.env.example`.
  2. `gates/G_SKILL_ROT.py`: audita referências de arquivos e comandos quebrados em `SKILL.md`.
  3. `gates/G_DISCIPLINA_TESTE_FERRAMENTA.py`: bloqueia qualquer alteração sob `tools/<ferramenta>/` desacompanhada de atualização contemporânea do relatório de testes em `docs/teste-end-to-end/`.
- **Limite Metrológico (Lei #8 / ISSUE-0023):** A checagem automatizada audita a presença e o frescor do relatório de teste contra alterações em `tools/`; a integridade substancial dos resultados depende da aprovação das suítes de testes reais de cada ferramenta. Concluído na Sessão 22.

### 2.6 Lei #10 — Quarteto Sine Qua Non Dinâmico
- **Exigência:** Todo projeto gerado ou evoluído DEVE nascer nativamente com 4 pilares: Swagger Studio, Webhook Studio, MCP Studio e Guia do Utilizador.
- **Coberto (Sessão 12):** `gates/G_CONTRACT_ROT.py` prova, contra um servidor rodando de verdade, que as rotas batem com o `openapi.json` comitado.
- **Gap Residual:** O que o portão acima NÃO cobre: ele detecta divergência entre servidor e especificação, mas não audita se um deliverable gerado tem os 4 pilares presentes de fato. Existe também `gates/G_PROTOCOL_FALLBACK.py` (paridade REST vs MCP) e `tools/aidd-planner/scripts/gates/G_PLANNER_SINE_QUA_NON.py` (só local do planner) — nenhum roda na raiz contra uma saída gerada real.
- **Ação Futura:** Promover `G_PLANNER_SINE_QUA_NON.py` ou criar `G_QUARTETO_SINE_QUA_NON.py` no nível raiz — soma ao `G_CONTRACT_ROT.py`, não substitui. **Ticket aberto:** `docs/issues/24-gate-quarteto-sine-qua-non-lei-10.md` (ISSUE-0024).

### 2.7 Lei #11 — Padrão-Ouro de Stack Tecnológica
- **Exigência:** Todo fluxo deve gerar Frontend em Next.js + TypeScript + Tailwind CSS (Backend Python + SQLite WAL, API OpenAPI 3.1).
- **Gap Atual:** O ecossistema possui `gates/G_FRONTEND_LAYERS.py` (que valida separação de camadas dumb components vs fetch), mas não há gate que reprove a existência de frameworks não autorizados no frontend quando gerado.
- **Ação Futura:** Criar gate `G_STACK_FRONTEND_PADRAO.py` validando dependências de frontend (`package.json` gerado) contra Next.js, React, Tailwind CSS e TypeScript. **Ticket aberto:** `docs/issues/25-gate-stack-padrao-ouro-lei-11.md` (ISSUE-0025).
