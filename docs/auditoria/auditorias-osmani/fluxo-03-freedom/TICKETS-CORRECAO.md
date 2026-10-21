# Backlog Consolidado de Micro-Tickets de Correção da Máquina — AIDD-Osmani (Fluxo Freedom)

> **Origem:** Auditoria Factual dos 10 Micropipelines da Máquina Geradora (`ecossistema-aidd`).  
> **Diretiva:** Lei #5 (Zero Stubs), Lei #1 (Determinismo), Lei #11 (Padrão-Ouro Stack) e Lei #13 (Todo Portão Deve Provar que Morde).  
> **Total de Tickets:** 7 Micro-Tickets Priorizados e Lapidados  

---

## Matriz de Priorização de Tickets

| Ticket ID | Etapa / Ferramenta | Descrição Resumida | Severidade | Status | Evidência / Teste |
| :--- | :--- | :--- | :---: | :---: | :---: |
| **`TCK-FORGE-01`** | 01. FORGE | Resolver `sys.path` no template `scripts/aidd.py` para execução local autônoma | Baixa | **RESOLVIDO** | `python scripts/aidd.py audit` retorna exit 0 |
| **`TCK-PLAN-01`** | 02. PLANNER | Injetar automaticamente `--mobbin 1` no modo autônomo do orquestrador | Média | **RESOLVIDO** | `scripts/orquestrador_sincrono.py` calibrado com mobbin=1 |
| **`TCK-PLAN-02`** | 02. PLANNER | Sintetizador determinístico de `grill.md` e `spec.md` com critérios binários válidos | Média | **RESOLVIDO** | `test_intake.py` aprovado (20 passed in 9.91s) |
| **`TCK-ENG-01`** | 05. ENGINE (Freedom) | Usar caminhos relativos e `-o testpaths` no Pytest para suportar paths com `[]` | Alta | **RESOLVIDO** | `G_TESTES.py` aprovado no piloto (8 passed in 1.54s) |
| **`TCK-UI-01`** | 07. FRONTEND | **O Nó Central do Visual:** Injetar primitivos corporativos (DataTable, Kanban, MetricCard, tokens OKLCH) | **CRÍTICA** | **RESOLVIDO** | Componentes criados em `templates/frontend-tanstack/` e validados via Playwright |
| **`TCK-UI-02`** | 07. FRONTEND | Eliminar bypass em `orquestrador_sincrono.py` e forçar casca TanStack padrão-ouro | Alta | **RESOLVIDO** | TanStack exporter ativo sem supressão |
| **`TCK-GATE-01`** | 10. GATES | Criar Quality Gate de Craft Visual determinístico que reprova UIs amadoras ou sem tokens | Alta | **RESOLVIDO** | `G_CRAFT_VISUAL.py` provado que morde (4 passed in 2.28s) |

---

## Detalhamento das Resoluções Factuais

### [TCK-FORGE-01] Normalizar `sys.path` no Script Gerado `scripts/aidd.py`
- **Arquivo Alvo:** `modulos/03-plataforma-e-entrega/fatiamento-master/aidd-master/scripts/aidd.py`
- **Implementação:** Busca inteligente ascendente de `application` com fallback robusto no `sys.path` e injeção em projetos gerados.
- **Evidência:** `python scripts/aidd.py audit` no projeto piloto executou e passou com `exit code 0`.

### [TCK-PLAN-01] Injeção Automática de `--mobbin 1` no Modo Autônomo
- **Arquivo Alvo:** `scripts/orquestrador_sincrono.py`
- **Implementação:** Injeção automática de `--mobbin 1` no despacho do `aidd-planner` quando rodando em modo autônomo.
- **Evidência:** Planejador avança deterministicamente sem requerer prompts interativos pendentes.

### [TCK-PLAN-02] Sintetizador Autônomo de BDD para `grill.md` e `spec.md`
- **Arquivo Alvo:** `modulos/01-governanca-e-qualidade/core/aidd-planner/src/core_planner/intake.py`
- **Implementação:** Função `sintetizar_intake_autonomo` gera seções BDD completas com regex matching de `exit code 0` e `assert`.
- **Evidência:** `pytest modulos/01-governanca-e-qualidade/core/aidd-planner/tests/test_intake.py` aprovou 20 testes unitários.

### [TCK-ENG-01] Isolamento Relativo no Coletor de Testes do Pytest
- **Arquivo Alvo:** `componentes/compartilhado/gates/G_TESTES.py`
- **Implementação:** Substituição de caminhos absolutos por caminhos relativos normalizados com `os.path.relpath` e injeção de `-o testpaths={rel_test_dir}` para evitar conflito com pastas contendo colchetes (ex.: `[TESTE]`).
- **Evidência:** Execução limpa dos testes das fatias verticais VSA (`users`, `task_lists`, `tasks`) no projeto piloto (`8 passed in 1.54s`).

### [TCK-UI-01] Injeção de Componentes Corporativos Reais no Template `frontend-tanstack`
- **Arquivo Alvo:** `componentes/compartilhado/templates/frontend-tanstack/src/`
- **Implementação:**
  1. `src/components/DataTable.tsx`: Tabela densa com busca inline, ordenação, badges de status e contadores de registro.
  2. `src/components/KanbanBoard.tsx`: Quadro responsivo full-width com 3 colunas, cartões de alta densidade e estados vazios sutis.
  3. `src/components/MetricCard.tsx`: Cartões de KPIs corporativos com suporte a tendências (up/down/neutral), ícones estilizados e valor tipográfico destacado.
  4. `src/tokens.css`: Variáveis OKLCH em paleta ardósia escura (Dark Slate) com contraste WCAG 2.2 AA.
  5. `src/components/index.ts`: Barrel export canônico.
- **Evidência Visual:** Capturas de tela Playwright em 1440x900 provando transformação visual de padrão tutorial amador para nível Linear/Raycast/Asana.

### [TCK-UI-02] Remoção de Bypass no Orquestrador Síncrono
- **Arquivo Alvo:** `scripts/orquestrador_sincrono.py:465`
- **Implementação:** O orquestrador agora executa a blindagem e injeção do padrão-ouro TanStack sem pular a auditoria quando a pasta `frontend` já existe.
- **Evidência:** Template `frontend-tanstack` exportado e atualizado no app de destino.

### [TCK-GATE-01] Quality Gate Automatizado de Craft Visual
- **Arquivo Alvo:** `modulos/01-governanca-e-qualidade/gates/G_CRAFT_VISUAL.py` e `tests/test_g_craft_visual.py`
- **Implementação:** Quality Gate determinístico que inspeciona:
  1. Ausência de emojis Unicode em arquivos de UI (forçando SVGs Lucide).
  2. Presença de tokens de cor perceptualmente uniformes (OKLCH).
  3. Proibição de layouts amadores confinados (`max-w-xs min-h-screen`).
  4. Bloqueio de opacidades extremas violando contraste WCAG 2.2 AA.
- **Evidência:** 
  - `pytest tests/test_g_craft_visual.py` aprovou 4/4 testes comprovando que o gate morde sob violação sintética (Lei #13).
  - Execução no frontend piloto retornou `exit code 0` com `[PASS] 100% conforme`.
  - Registrado em `AGENTS.md` (Lei #11) e `MAPA-GATES.json`.
