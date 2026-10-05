# Template de Auditoria de Ferramenta (Lens 15-D)

Este documento descreve a estrutura canônica para auditar qualquer ferramenta (Skill/Tool) do ecossistema, dissecando sua arquitetura através do framework Lens 15-D (The Agentic Anatomical Matrix).

## 1. Identificação da Ferramenta
- **Nome da Ferramenta:** `aidd-orchestrator-runner` (`aidd-orchestrate`, `orchestrate`)
- **Descrição Breve:** Orquestrador mestre síncrono para compilação e despacho de Planos de Voo (.orca-flight-plan.json) roteando planos aprovados para 3 ambientes: App ORCA, subagentes da sessão ou Git Worktrees nativas.
- **Comando de Gatilho:** `/orchestrate`, `/aidd-orchestrate`, `python ecossistema.py orchestrate`

## 2. A Matriz Anatômica (Lens 15-D)

### Fase 1: Governança e Blindagem
- **D1. Contratos e Regras:** Regras formalizadas no frontmatter de `SKILL.md`: transição melhoria -> plan -> orchestrate com barreira inegociável de aprovação humana, proibição de avançar fases automaticamente (Golden Rule #7) e separação estrita dos 3 formatos de Plano de Voo.
- **D2. Input e Gatilhos:** Interface via CLI do ecossistema `python ecossistema.py orchestrate <plan> --ambiente <orca|subagent|gitworktree> [--dry-run]`.
- **D3. Raio de Impacto e Isolamento:** Delimitação de escrita ao artefato `.orca-flight-plan.json` na pasta do plano durante o planejamento; isolamento por worktree dedicada em tempo de execução nativa ou mesas isoladas do app ORCA.
- **D4. Componentes e Fractalidade:** Implementação modular desacoplada em `tools/aidd-runner/` e scripts especializados (`orca_real_plan.py`, `subagent_plan.py`, `flight_plan.py`).

### Fase 2: O Chão de Fábrica (Workflow Agêntico)
- **D5. Visão e Escopo:** Transformar planos decompostos em planos de voo operacionais e coordenar o despacho para os ambientes de execução agêntica com controle humano soberano.
  - **[Estágio 1 - Compilação de Plano de Voo] D6. O que o Estágio Faz:** Compila os itens do plano para o formato do ambiente escolhido.
  - **[Estágio 1 - Compilação de Plano de Voo] D7. O que o Estágio Recebe:** Caminho do plano e ambiente de destino.
  - **[Estágio 1 - Compilação de Plano de Voo] D8. O que o Estágio Processa:** Geração de `.orca-flight-plan.json`.
  - **[Estágio 1 - Compilação de Plano de Voo] D9. O que o Estágio Entrega:** Manifesto de voo estruturado.
  - **[Estágio 2 - Portão de Aprovação] D6. O que o Estágio Faz:** Submete o plano de voo à aprovação explícita do usuário.
  - **[Estágio 2 - Portão de Aprovação] D7. O que o Estágio Recebe:** Confirmação humana direta no chat.
  - **[Estágio 2 - Portão de Aprovação] D8. O que o Estágio Processa:** Transição de status do plano para EM EXECUCAO.
  - **[Estágio 2 - Portão de Aprovação] D9. O que o Estágio Entrega:** Sinal verde para execução.
  - **[Estágio 3 - Despacho e Execução] D6. O que o Estágio Faz:** Aciona o ambiente selecionado.
  - **[Estágio 3 - Despacho e Execução] D7. O que o Estágio Recebe:** Plano de voo aprovado.
  - **[Estágio 3 - Despacho e Execução] D8. O que o Estágio Processa:** Invocação de worktrees, chamadas de subagente ou disparo via orca-cli.
  - **[Estágio 3 - Despacho e Execução] D9. O que o Estágio Entrega:** Execução concluída e auditada.
- **D10. Orquestração e Topologia:** Topologia procedural de 3 estágios (`compile -> human_gate -> dispatch`) com barreira intransponível de consentimento.

### Fase 3: Resiliência e Economia (Engenharia Operacional)
- **D11. Tratamento de Exceções e Fallback:** Falha em frente de subagente interrompe a fila antes do próximo disparo; no app ORCA, detecção de falha de idle no terminal cancela o envio seguro.
- **D12. Observabilidade e Frugalidade:** Compilação do plano de voo realizada inteiramente via scripts determinísticos Python sem gasto de tokens.

### Fase 4: O Inspetor e a Expedição (Validação)
- **D13. Quality Gates (Portões):** Exigência de auditoria de qualidade `python ecossistema.py audit` com exit 0 dentro da worktree/mesa antes de qualquer merge ou cherry-pick.
- **D14. Critério de Rejeição (Rollback):** Falha na auditoria de uma frente bloqueia a integração daquela fatia.
- **D15. Output Consolidado e Handoff:** Plano de voo `.orca-flight-plan.json` assinado e frentes integradas com sucesso.

---

## 3. Matriz de Avaliação da Execução
- [x] A ferramenta isolou seu raio de impacto corretamente? Sim, isolamento dependente do ambiente escolhido e compilado em `.orca-flight-plan.json`.
- [x] O workflow seguiu as fases sem alucinações de LLM em tarefas mecânicas? Sim, motor 100% determinístico em Python.
- [x] O output final passou em todos os Quality Gates e emitiu o Handoff? Sim, validado por gates locais e verificação do plano de voo.
