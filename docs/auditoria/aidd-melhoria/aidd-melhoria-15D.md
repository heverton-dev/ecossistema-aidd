# Template de Auditoria de Ferramenta (Lens 15-D)

Este documento descreve a estrutura canônica para auditar qualquer ferramenta (Skill/Tool) do ecossistema, dissecando sua arquitetura através do framework Lens 15-D (The Agentic Anatomical Matrix).

## 1. Identificação da Ferramenta
- **Nome da Ferramenta:** `aidd-melhoria`
- **Descrição Breve:** Análise profunda pré-planejamento de melhorias no ecossistema AIDD, produzindo relatórios de avaliação estruturados.
- **Comando de Gatilho:** `/melhoria <pedido>` ou `python ecossistema.py melhoria init <nome> --pedido "<pedido>"`

## 2. A Matriz Anatômica (Lens 15-D)

### Fase 1: Governança e Blindagem
- **D1. Contratos e Regras:** Contrato declarado em alto nível no frontmatter YAML de `SKILL.md` (nome `aidd-melhoria` e descrição funcional) associado a uma tabela de fluxo de 3 etapas com parada obrigatória ("Deseja que eu gere o plano a partir disto?"). Não há vinculação formal explícita das Leis Fundamentais do `AGENTS.md` (como Lei #1 de Determinismo ou Lei #5 de Zero Mocks/Stubs) nem asserções normativas no código da skill.
- **D2. Input e Gatilhos:** Recebe no chat do assistente o comando `/melhoria <sua sugestão de melhoria ou refatoração>` ou via CLI `python ecossistema.py melhoria init <nome> --pedido "<pedido>"`. Requisitos de entrada: pedido em linguagem natural ou referência a um plano existente para reanálise.
- **D3. Raio de Impacto e Isolamento:** FAILED: Not implemented. Não há isolamento de raio de impacto implementado no código de `.agents/skills/aidd-melhoria/`. Inexistência de Git Worktrees efêmeras, contêineres ou sandboxes; a skill atua diretamente no workspace ativo.
- **D4. Componentes e Fractalidade:** FAILED: Not implemented. A pasta `.agents/skills/aidd-melhoria/` não contém scripts locais, hooks pré/pós-execução, nem configuração explícita de recrutamento de MCP Servers (como `code-review-graph`) ou micro-skills internas.

### Fase 2: O Chão de Fábrica (Workflow Agêntico)
- **D5. Visão e Escopo:** A transformação central pretendida é investigar o código real a partir de uma sugestão do usuário e consolidar um relatório de análise profunda com Nota Atual e evidências em `docs/melhorias/`, servindo de insumo qualificado para a geração de planos.
*(Para cada estágio da execução, detalhe D6 a D9)*
  - **[Estágio 1 - Análise Pré-Planejamento] D6. O que o Estágio Faz:** Recebe o pedido do usuário e orienta a geração do relatório em `docs/melhorias/` com Nota Atual e evidências apuradas.
  - **[Estágio 1 - Análise Pré-Planejamento] D7. O que o Estágio Recebe:** Pedido em linguagem natural (`<pedido>`) ou identificador de plano existente.
  - **[Estágio 1 - Análise Pré-Planejamento] D8. O que o Estágio Processa:** FAILED: Not implemented. Não há lógica ou script de processamento analítico dentro da pasta `.agents/skills/aidd-melhoria/`. O processamento investigativo depende 100% da interpretação conversacional da LLM sem motor determinístico local.
  - **[Estágio 1 - Análise Pré-Planejamento] D9. O que o Estágio Entrega:** Relatório de análise em `docs/melhorias/` contendo Nota Atual e evidências factuais, encerrando com o prompt de confirmação obrigatório: "Deseja que eu gere o plano a partir disto?".
- **D10. Orquestração e Topologia:** Topologia linear em 3 etapas com barreiras de decisão humana explícitas: Etapa 1 `/melhoria` → Etapa 2 `/plan` → Etapa 3 `/orchestrate`. O transporte de dados ocorre através de artefatos em disco (`docs/melhorias/` alimentando `docs/planos/`).

### Fase 3: Resiliência e Economia (Engenharia Operacional)
- **D11. Tratamento de Exceções e Fallback:** FAILED: Not implemented. Não existem mecanismos de retry autônomo, tratamento de exceções, rotinas de auto-correção ou fallbacks implementados em `.agents/skills/aidd-melhoria/`.
- **D12. Observabilidade e Frugalidade:** FAILED: Not implemented. Não há medição de orçamento de tokens, métricas de execução ou persistência de logs padronizados em `secoes/` embutidos no código da skill.

### Fase 4: O Inspetor e a Expedição (Validação)
- **D13. Quality Gates (Portões):** FAILED: Not implemented. A pasta `.agents/skills/aidd-melhoria/` não possui Quality Gates determinísticos (`G_*.py`), suite de testes unitários ou verificadores de saída implementados.
- **D14. Critério de Rejeição (Rollback):** FAILED: Not implemented. Inexistência de critérios de rejeição formalizados (`exit 1`) ou procedimentos de rollback e limpeza de arquivos em caso de falha.
- **D15. Output Consolidado e Handoff:** FAILED: Not implemented. O relatório de saída é direcionado para `docs/melhorias/`, com parada obrigatória para autorização do usuário antes da transição para a Etapa 2 (`/plan`). Contudo, o handoff estruturado com manifesto de máquina padronizado e assinado não está implementado na skill.

---

## 3. Matriz de Avaliação da Execução
- [ ] A ferramenta isolou seu raio de impacto corretamente?
- [ ] O workflow seguiu as fases sem alucinações de LLM em tarefas mecânicas?
- [ ] O output final passou em todos os Quality Gates e emitiu o Handoff?
