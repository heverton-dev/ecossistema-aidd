# Template de Auditoria de Ferramenta (Lens 15-D)

Este documento descreve a estrutura canônica para auditar qualquer ferramenta (Skill/Tool) do ecossistema, dissecando sua arquitetura através do framework Lens 15-D (The Agentic Anatomical Matrix).

## 1. Identificação da Ferramenta
- **Nome da Ferramenta:** `code-review-graph` (`debug-issue`, `review-changes`, `refactor-safely`, `explore-codebase`)
- **Descrição Breve:** Dependência externa oficial (pacote pip e servidor MCP) para geração de grafo de conhecimento de código, análise de impacto e suporte contextual a debug, revisão e refatoração.
- **Comando de Gatilho:** `/debug-issue`, `/review-changes`, `/refactor-safely`, `/explore-codebase`, MCP tools `code-review-graph`

## 2. A Matriz Anatômica (Lens 15-D)

### Fase 1: Governança e Blindagem
- **D1. Contratos e Regras:** Contrato formalizado no manifesto soberano `gates/dependencias_externas.json`, definindo pacote pip, comando de instalação determinístico e integridade de artefatos fixada via SHA-256 (`ead883c2ff2ff76e239f208afaca2a7a7fa79db1a012ce7411d28772019e964b`). Regras operacionais descritas nas skills em `.claude/skills/`.
- **D2. Input e Gatilhos:** Comandos via CLI determinística do ecossistema `python ecossistema.py dependencia verify` e `python ecossistema.py dependencia bootstrap`, além da chamada sob demanda das ferramentas MCP expostas nos harnesses.
- **D3. Raio de Impacto e Isolamento:** Banco de dados SQLite e índices isolados em `.code-review-graph/` dentro da raiz do repositório, com exclusões mapeadas e confinamento de queries em modo read-only no grafo durante operações de exploração e review.
- **D4. Componentes e Fractalidade:** Dependência desacoplada da árvore soberana do monorepo conforme deliberação de `PROPOSTA-NOMES-SKILLS.md`. Gerenciada centralmente pelo `scripts/gestor_dependencias.py`, com suporte multiplataforma e registro padronizado.

### Fase 2: O Chão de Fábrica (Workflow Agêntico)
- **D5. Visão e Escopo:** Prover inteligência estrutural sobre o repositório através de AST (Tree-sitter) e algoritmos de grafo (Leiden, BFS/DFS, betweenness centrality) para otimizar o consumo de contexto em reviews e manutenções.
  - **[Estágio 1 - Verificação e Bootstrap] D6. O que o Estágio Faz:** Verifica presença do pacote e integridade das skills nos harnesses.
  - **[Estágio 1 - Verificação e Bootstrap] D7. O que o Estágio Recebe:** Manifesto `gates/dependencias_externas.json`.
  - **[Estágio 1 - Verificação e Bootstrap] D8. O que o Estágio Processa:** Checagem de hash SHA-256 do artefato verificado.
  - **[Estágio 1 - Verificação e Bootstrap] D9. O que o Estágio Entrega:** Exit code 0 ou 1 determinístico.
  - **[Estágio 2 - Consulta e Análise Estrutural] D6. O que o Estágio Faz:** Executa queries no grafo de código para guiar a atuação do agente.
  - **[Estágio 2 - Consulta e Análise Estrutural] D7. O que o Estágio Recebe:** Parâmetros da ferramenta MCP (ex: task, changed_files, query).
  - **[Estágio 2 - Consulta e Análise Estrutural] D8. O que o Estágio Processa:** AST traversal, cálculo de raio de impacto e centralidade.
  - **[Estágio 2 - Consulta e Análise Estrutural] D9. O que o Estágio Entrega:** Contexto estruturado e pontuação de risco.
- **D10. Orquestração e Topologia:** Topologia descentralizada sob demanda: atua como barramento de telemetria estática consultado pelos harnesses no início da sessão ou durante triagens e diagnósticos sem interferência no ciclo de vida de código.

### Fase 3: Resiliência e Economia (Engenharia Operacional)
- **D11. Tratamento de Exceções e Fallback:** Fallback gracioso implementado nos prompts e nas ferramentas: caso o servidor MCP não esteja ativo ou o grafo não esteja construído, as skills indicam degradação para inspeção textual tradicional via Grep/Glob sem quebrar a sessão.
- **D12. Observabilidade e Frugalidade:** Otimização severa de tokens com a regra obrigatória `get_minimal_context(task=...)` em D12, instruindo chamadas com `detail_level='minimal'` para garantir orçamentos inferiores a 800 tokens por análise.

### Fase 4: O Inspetor e a Expedição (Validação)
- **D13. Quality Gates (Portões):** Validado pelo gate soberano `gates/G_dependencias_externas.py` e integrado a `python ecossistema.py dependencia verify`, garantindo paridade binária (exit 0 / exit 1).
- **D14. Critério de Rejeição (Rollback):** Falha no hash SHA-256 ou corrupção no manifesto aborta a execução no início da sessão e força re-bootstrap determinístico.
- **D15. Output Consolidado e Handoff:** Manifesto `gates/dependencias_externas.json` assina o estado das dependências com SHA-256 canônico, assegurando procedência auditável das ferramentas externas.

---

## 3. Matriz de Avaliação da Execução
- [x] A ferramenta isolou seu raio de impacto corretamente? Sim, gerenciada como dependência externa isolada.
- [x] O workflow seguiu as fases sem alucinações de LLM em tarefas mecânicas? Sim, checagem e bootstrap 100% determinísticos via Python.
- [x] O output final passou em todos os Quality Gates e emitiu o Handoff? Sim, validado por `G_dependencias_externas.py` com exit 0.
