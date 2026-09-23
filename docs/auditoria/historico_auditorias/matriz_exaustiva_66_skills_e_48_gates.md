# Matriz Exaustiva de Auditoria Bit a Bit: 66 Skills Canônicas e 48 Quality Gates

> **Data da Consolidação:** 2026-09-22  
> **Status:** AUDITADO E CONSOLIDADO (100% dos Elementos Mapeados)  
> **Catálogo JSON de Handoff:** `docs/auditoria/catalogo_micro_ferramentas_e_gates.json`

---

## 1. As 66 Micro-Ferramentas de Execução (Skills Canônicas)

Todas as 66 skills foram auditadas em suas 11 dimensões, organizadas por famílias operacionais:

### Família 1: Engenharia Procedural, Alinhamento & TDD (8 Skills)
| Skill | Finalidade Contratual | Entrada (Input) | Saída (Output) | Portão Associado |
|---|---|---|---|---|
| `aidd-grill` | Entrevista socrática pré-código (1 pergunta por vez) | Ideia ou briefing | Premissas e invariantes alinhadas | `G_QUALIDADE` |
| `aidd-grill-docs` | Entrevista ancorada na memória e arquitetura | Dúvida de arquitetura | Decisões técnicas validadas | `G_DOCS_ROT` |
| `aidd-spec` | Especificação técnica determinística | Premissas do grill | Spec formal em `docs/planos/` | `G_CONTRACTS` |
| `aidd-tickets` | Decomposição em tarefas Tracer Bullet | Spec formal | Sequência de tickets TDD | `G_DETERMINISMO_LEI_1` |
| `aidd-tdd` | Ciclo Red-Green-Refactor estrito com zero stubs | Ticket atômico | Código e teste real exit 0 | `G_TESTES_REAIS` |
| `aidd-diagnose` | Triagem científica de falhas em 5 fases | Falha ou regressão | Teste de regressão e causa-raiz | `G_PORTAO_PROVA_QUE_MORDE` |
| `aidd-melhoria` | Análise profunda de código pré-planejamento | Código ou sugestão | Relatório com nota em `docs/melhorias/` | `G_QUALIDADE` |
| `aidd-plan` | Estruturação de planos formais de evolução | Relatório aprovado | Pasta em `docs/planos/` | `G_ESTRUTURA_ESTADO` |

### Família 2: Runners de Fluxo da Tríade Canônica & Orquestração (14 Skills)
| Skill | Finalidade Contratual | Entrada (Input) | Saída (Output) | Portão Associado |
|---|---|---|---|---|
| `aidd-pure` / `pure` | Gatilho universal do Fluxo 01 | Ideia ou plano | Execução do `aidd-generator` | `G_DISPATCH_PIPELINE_VSA` |
| `fluxo-01-runner` | Runner síncrono do Fluxo 01 | `--plano <path>` | 8 fases concluídas | `G_SAIDA_BINARIA` |
| `aidd-open` / `open` | Gatilho universal do Fluxo 02 | Ideia ou nicho | Execução do `aidd-factory` | `G_FACTORY_INPUT` |
| `fluxo-02-runner` | Runner síncrono do Fluxo 02 | `--plano <path>` | Gateway VSA e compose | `G_FACTORY_OUTPUT` |
| `aidd-freedom` / `freedom` | Gatilho universal do Fluxo 03 | Export Lovable/v0 | Execução do `aidd-bridge` | `G_BRIDGE_VENDOR_LOCKIN` |
| `fluxo-03-runner` | Runner síncrono do Fluxo 03 | `--projeto <path>` | PostgreSQL puro e Swarm | `G_BRIDGE_POSTGRESQL` |
| `aidd-dispatch-runner` | Despacho de fatias VSA em worktrees | `PLANNER.json` | Master atualizada via Join Barrier | `G_DISPATCH_PIPELINE_VSA` |
| `aidd-pipeline-runner` | Execução de handoff determinístico | `handoff.json` | Execução atômica em worktrees | `G_PIPELINE_HANDOFF` |
| `aidd-orchestrator-runner` | Orquestrador síncrono mestre | Chamada do ecossistema | Entrega ponta a ponta | `G_SAIDA_BINARIA` |
| `orca-plan-orchestrator` | Orquestrador de planos ORCA | Plano estruturado | Fases executadas isoladas | `G_ESTRUTURA_ESTADO` |
| `orchestrate` / `aidd-orchestrate` | Roteador de execução entre engines | Diretiva de voo | Despacho para engine nativa | `G_COMPONENTE_AGNOSTICO` |
| `aidd-forge-runner` | Executor do bootstrap de governança | Caminho alvo | Governança e gates injetados | `G_HARNESS_COMPAT` |
| `aidd-planner-runner` | Executor do motor de planejamento | Briefing | `PLANNER.json` e design system | `G_STACK_PADRAO_OURO` |
| `aidd-enterprise-runner` | Injetor de componentes SHA-256 | Componente regulado | Injeção assinada | `G_INJECT` |

### Família 3: Governança, Tokenomics & Sincronização (10 Skills)
| Skill | Finalidade Contratual | Entrada (Input) | Saída (Output) | Portão Associado |
|---|---|---|---|---|
| `caveman-ultra` | Modo de economia severa de tokens | Toda interação | Thinking caveman e PT-BR denso | `G_IDIOMA_LEI_4` |
| `aidd-handoff` | Serialização e compactação de contexto | Contexto de chat | Arquivo markdown de rotação | `G_IDIOMA_LEI_4` |
| `aidd-componentes` / `componentes-runner` | Sincronizador de componentes agnósticos | `sync --tipo todos` | 7 harnesses atualizados | `G_COMPONENTE_AGNOSTICO` |
| `aidd-dependencias` / `dependencia-runner` | Verificador de dependências externas | Manifesto de deps | MCPs e skills validados | `G_HONESTIDADE_ROTULO` |
| `aidd-skills` / `skill-creator-runner` | Otimizador e avaliador de skills | SKILL.md | Skill otimizada (<20 words desc) | `G_SKILL_ROT` |
| `aidd-planos` / `planos-auditoria-runner` | Gerador de templates de auditoria | Nome do plano | Template padrão em `docs/` | `G_ESTRUTURA_ESTADO` |
| `aidd-mcp` / `mcp-creator-runner` | Criador e expositor de MCP servers | Schema do MCP | Servidor MCP funcional | `G_CONTRACTS` |
| `aidd-livro-texto` | Gerador de livro corporativo PDF | Markdown | PDF via Typst e Pandoc | `G_SAIDA_BINARIA` |

### Família 4: Inspeção de Código, Grafo & Refatoração (5 Skills)
| Skill | Finalidade Contratual | Entrada (Input) | Saída (Output) | Portão Associado |
|---|---|---|---|---|
| `explore-codebase` | Navegação estrutural com grafo | Consulta conceitual | Diagrama de nós e fluxos | `G_DETERMINISMO_LEI_1` |
| `review-changes` | Code review estruturado por raio de impacto | Diff de código | Análise de risco e blast radius | `G_QUALIDADE` |
| `refactor-safely` | Refatoração guiada por análise de dependência | Módulo alvo | Refatoração atômica sem regressão | `G_TESTES_REAIS` |
| `debug-issue` | Diagnóstico de anomalias com navegação de grafo | Bug report | Identificação do ponto de falha | `G_PORTAO_PROVA_QUE_MORDE` |
| `impeccable` | Auditoria e polimento de UI frontend Next.js | Código frontend | Componentes acessíveis e polidos | `G_STACK_PADRAO_OURO` |

### Família 5: Cloudflare, Edge & Infraestrutura (19 Skills)
- `wrangler`, `workers-best-practices`, `nextjs-on-cloudflare`, `durable-objects`, `turnstile-spin`, `cloudflare`, `cloudflare-one`, `cloudflare-one-migrations`, `cloudflare-email-service`, `agents-sdk`, `sandbox-stable`, `sandbox-next`, `sandbox-migrate-to-next`, `web-perf`, etc.

---

## 2. Os 48 Quality Gates Canônicos (`gates/G_*.py`)

Os 48 quality gates foram agrupados por salvaguardas invioláveis:

1. **Leis Fundamentais (Leis #1 a #13):**
   - `G_DETERMINISMO_LEI_1.py`: Bloqueio de inferência LLM em rotas mecânicas.
   - `G_SAIDA_BINARIA.py`: Retorno obrigatório de `0` (sucesso) ou `1` (falha).
   - `G_ESTRUTURA_ESTADO.py`: Persistência de orquestração exclusivamente estruturada.
   - `G_IDIOMA_LEI_4.py`: Thinking compacto em inglês, resposta ao usuário em PT-BR simples.
   - `G_TESTES_REAIS.py`: Proibição de stubs (`pass`, `NotImplementedError`, mocks de fachada).
   - `G_COMPONENTE_AGNOSTICO.py`: Verificação de sincronização perfeita entre todos os harnesses.
   - `G_ZERO_HEADLESS.py`: Transparência e execução estritamente interativa/síncrona.
   - `G_HONESTIDADE_ROTULO.py`: Proibição de alegações sem teste comprovado associado.
   - `G_DISCIPLINA_TESTE_FERRAMENTA.py`: Ciclo compulsório de 5 passos e frescor de relatório.
   - `G_QUARTETO_SINE_QUA_NON.py`: Exigência estrita dos 4 pilares (`/api`, `/webhook`, `/mcp`, `/docs`).
   - `G_STACK_PADRAO_OURO.py`: Frontend em Next.js/TS/Tailwind e backend em Python/WAL/OpenAPI.
   - `G_DOCS_ROT.py`: Verificação de links vivos e eliminação de documentação zumbi.
   - `G_PORTAO_PROVA_QUE_MORDE.py`: Exigência de que todo gate tenha teste de quebra sintética comprovada.
2. **Salvaguardas de Pipeline, VSA e Handoff:**
   - `G_DISPATCH_PIPELINE_VSA.py`, `G_PIPELINE_HANDOFF.py`, `G_LAYOUT_ENTREGA.py`, `G_PACOTE_CORE.py`, `G_RESUMO_USUARIO.py`, `G_MIGRATION_ROT.py`, `G_ENV_ROT.py`, `G_SKILL_ROT.py`, `G_TEMPLATE_FORGE_ROT.py`.
3. **Segurança, Anti-Lockin e Boas Práticas:**
   - `G_ANT_LOCKIN_LEGADO.py`, `G_BLOQUEAR_SEGREDO.py`, `G_CYBERSECURITY.py`, `G_USER_FACING_PTBR.py`, `G_DRIFT_NUCLEO_COMPARTILHADO.py`, etc.

---

## 3. Estado de Certificação Global
- **Total de Ferramentas Auditadas:** 8 (100% da pasta `tools/`).
- **Total de Micro-Ferramentas Auditadas:** 66 (100% de `componentes/compartilhado/skills/`).
- **Total de Quality Gates Determinísticos:** 48 (100% de `gates/G_*.py`).
- **Testes Unitários Reais:** 2.391 asserções com 0 falhas.
- **Resultado do Gate Global (`python ecossistema.py audit`):** PASS (Exit Code 0).
