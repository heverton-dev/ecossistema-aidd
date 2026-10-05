# Template de Auditoria de Ferramenta (Lens 15-D)

Este documento descreve a estrutura canônica para auditar qualquer ferramenta (Skill/Tool) do ecossistema, dissecando sua arquitetura através do framework Lens 15-D (The Agentic Anatomical Matrix).

## 1. Identificação da Ferramenta
- **Nome da Ferramenta:** `aidd-planner-runner`
- **Descrição Breve:** Motor de intake SDD/BDD/DDD e geração determinística de blueprint canônico da aplicação (PLANNER.json) com validação de esquema, quarteto sine qua non e compilação de VSA.
- **Comando de Gatilho:** `/aidd-planner`, `planner`, `python ecossistema.py planner`

## 2. A Matriz Anatômica (Lens 15-D)

### Fase 1: Governança e Blindagem
- **D1. Contratos e Regras:** Regras formalizadas em `schemas/planner_schema.json` e `SKILL.md` (SDD, BDD com Given/When/Then, DDD com bounded contexts, Quarteto Sine Qua Non e proibição de stubs/TODOs). Validado em `G_PLANNER_SCHEMA.py`, `G_PLANNER_SINE_QUA_NON.py` e `G_PLANNER_COERENCIA_FLUXO.py`.
- **D2. Input e Gatilhos:** Interface determinística de linha de comando exposta via `python ecossistema.py planner` (`init`, `validate`, `export`, `audit`). Validação estrita de flags `--fluxo`, `--nome`, `--pasta`, `--dominio`, `--slug`.
- **D3. Raio de Impacto e Isolamento:** FAILED: Not implemented. Não há classe de isolamento de escrita em Python (`PlanWorktreeManager` ou sandbox de I/O) confinando arquivos gerados a sandbox ou Git Worktree efêmera. Os artefatos são gravados diretamente no caminho fornecido pelo usuário.
- **D4. Componentes e Fractalidade:** Biblioteca estruturada com CLI desacoplada em `tools/aidd-planner/src/cli.py` e `planner_engine.py`, exportando contratos e sincronizada via `componentes/compartilhado/skills/aidd-planner/`.

### Fase 2: O Chão de Fábrica (Workflow Agêntico)
- **D5. Visão e Escopo:** Gerar o blueprint arquitetural soberano de aplicações com precisão matemática para alimentar os motores de geração da Tríade.
  - **[Estágio 1 - Inicialização e Scaffold] D6. O que o Estágio Faz:** Gera o scaffold de `PLANNER.json`, `HANDOFF_PLANNER_ENGINE.json` e `DESIGN-SYSTEM.json`.
  - **[Estágio 1 - Inicialização e Scaffold] D7. O que o Estágio Recebe:** Flags de fluxo, nome do projeto, pasta de destino, domínio e slug.
  - **[Estágio 1 - Inicialização e Scaffold] D8. O que o Estágio Processa:** `planner_engine.PlannerEngine.init()` monta os contratos iniciais em disco.
  - **[Estágio 1 - Inicialização e Scaffold] D9. O que o Estágio Entrega:** Arquivos JSON canônicos gravados no diretório do projeto.
  - **[Estágio 2 - Validação e Auditoria] D6. O que o Estágio Faz:** Valida schema JSON, coerência de fluxo e Quarteto Sine Qua Non.
  - **[Estágio 2 - Validação e Auditoria] D7. O que o Estágio Recebe:** Caminho do `PLANNER.json`.
  - **[Estágio 2 - Validação e Auditoria] D8. O que o Estágio Processa:** Quality Gates locais executam asserções com `jsonschema` e regex de stubs.
  - **[Estágio 2 - Validação e Auditoria] D9. O que o Estágio Entrega:** Exit code 0 ou 1 com relatório de erros de esquema.
- **D10. Orquestração e Topologia:** Pipeline procedural em fases estritas (`init` -> `validate` -> `export` -> `audit`), com checagens binárias automatizadas.

### Fase 3: Resiliência e Economia (Engenharia Operacional)
- **D11. Tratamento de Exceções e Fallback:** FAILED: Not implemented. Erros durante a geração ou colisão de pasta levantam exceções diretas ou retornam exit 1 sem resolução automatizada de nomes concorrentes ou fallback de recuperação.
- **D12. Observabilidade e Frugalidade:** FAILED: Not implemented. Não há módulo coletando telemetria estruturada do blueprint gerado (total de bounded contexts, entidades, endpoints e estimativa de tokens do blueprint).

### Fase 4: O Inspetor e a Expedição (Validação)
- **D13. Quality Gates (Portões):** Implementados `G_PLANNER_SCHEMA.py`, `G_PLANNER_SINE_QUA_NON.py` e `G_PLANNER_COERENCIA_FLUXO.py` sob a Lei #13 (reprovação binária exit 0 / exit 1).
- **D14. Critério de Rejeição (Rollback):** FAILED: Not implemented. Não há rollback automático ou limpeza de artefatos residuais em caso de falha de validação ou exceção durante o `init`.
- **D15. Output Consolidado e Handoff:** FAILED: Not implemented. Embora emita `HANDOFF_PLANNER_ENGINE.json`, não emite assinatura criptográfica HMAC-SHA256 ou manifesto formal com hash SHA-256 consolidado de todos os artefatos de saída.

---

## 3. Matriz de Avaliação da Execução
- [ ] A ferramenta isolou seu raio de impacto corretamente?
- [ ] O workflow seguiu as fases sem alucinações de LLM em tarefas mecânicas?
- [ ] O output final passou em todos os Quality Gates e emitiu o Handoff?
