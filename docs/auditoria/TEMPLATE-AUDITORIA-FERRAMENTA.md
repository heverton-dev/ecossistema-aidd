# Template de Auditoria de Ferramenta (Lens 15-D)

Este documento descreve a estrutura canônica para auditar qualquer ferramenta (Skill/Tool) do ecossistema, dissecando sua arquitetura através do framework Lens 15-D (The Agentic Anatomical Matrix).

## 1. Identificação da Ferramenta
- **Nome da Ferramenta:** `<nome-da-skill/cli>`
- **Descrição Breve:** `<o que ela se propõe a fazer>`
- **Comando de Gatilho:** `<comando cli ou slash command>`

## 2. A Matriz Anatômica (Lens 15-D)

### Fase 1: Governança e Blindagem
- **D1. Contratos e Regras:** (Leis do ecossistema e contratos `SKILL.md` que a regem).
- **D2. Input e Gatilhos:** (Payload exato de entrada e requisitos de estado).
- **D3. Raio de Impacto e Isolamento:** (Fronteira de risco, ex: Git Worktree efêmera, acesso a banco).
- **D4. Componentes e Fractalidade:** (MCP Servers, Hooks e Micro-skills que ela recruta internamente).

### Fase 2: O Chão de Fábrica (Workflow Agêntico)
- **D5. Visão e Escopo:** (A transformação central pretendida).
*(Para cada estágio da execução, detalhe D6 a D9)*
  - **[Estágio X] D6. O que o Estágio Faz:** (Ação atômica).
  - **[Estágio X] D7. O que o Estágio Recebe:** (Insumo injetado).
  - **[Estágio X] D8. O que o Estágio Processa:** (Onde atua a inteligência vs motor).
  - **[Estágio X] D9. O que o Estágio Entrega:** (Artefato unitário do fim da etapa).
- **D10. Orquestração e Topologia:** (Como os dados são transportados de um estágio para o outro).

### Fase 3: Resiliência e Economia (Engenharia Operacional)
- **D11. Tratamento de Exceções e Fallback:** (Retry loop autônomo, aborto imediato, auto-correção).
- **D12. Observabilidade e Frugalidade:** (Gestão de tokens, logs limpos em `secoes/`).

### Fase 4: O Inspetor e a Expedição (Validação)
- **D13. Quality Gates (Portões):** (Scripts determinísticos como `G_*.py` que validam a saída).
- **D14. Critério de Rejeição (Rollback):** (O que força o gate a descartar o trabalho - `exit 1`).
- **D15. Output Consolidado e Handoff:** (A entrega blindada e o bastão para a próxima ferramenta).

---

## 3. Matriz de Avaliação da Execução
- [ ] A ferramenta isolou seu raio de impacto corretamente?
- [ ] O workflow seguiu as fases sem alucinações de LLM em tarefas mecânicas?
- [ ] O output final passou em todos os Quality Gates e emitiu o Handoff?
