# Template de Auditoria de Ferramenta (Lens 15-D)

Este documento descreve a estrutura canônica para auditar qualquer ferramenta (Skill/Tool) do ecossistema, dissecando sua arquitetura através do framework Lens 15-D (The Agentic Anatomical Matrix).

## 1. Identificação da Ferramenta
- **Nome da Ferramenta:** `aidd-plan`
- **Descrição Breve:** Criação, validação, controle de notas e ciclo de vida de pastas de planos de melhoria/auditoria do ecossistema em docs/planos/.
- **Comando de Gatilho:** `/aidd-plan`, `/plan`, `plan`, `python ecossistema.py plan`

## 2. A Matriz Anatômica (Lens 15-D)

### Fase 1: Governança e Blindagem
- **D1. Contratos e Regras:** Contrato preliminar no frontmatter de `SKILL.md` e regras fixas textuais (nunca aprovar sozinho, tudo nasce em DRAFT, estrutura e fences checados por código, escopo explícito com "Ainda não especificado" e "Fora de escopo", proibição de commit/push). Ausência de módulo de contrato determinístico em `scripts/contrato.py` contendo asserções programáticas formais das invariantes canônicas.
- **D2. Input e Gatilhos:** Comandos via CLI determinística implementados em `scripts/gerenciador_planos.py` expostos via `python ecossistema.py plan` (`init`, `check-fences`, `aprovar`, `iniciar-execucao`, `ler-nota`, `atualizar-nota`). Validação estrita de flags e argumentos posicionais.
- **D3. Raio de Impacto e Isolamento:** FAILED: Not implemented. Não há classe de isolamento em Python na pasta da skill para confinar I/O ou executar em Git Worktree temporária. Embora os testes usem tempdir isolado, em produção a ferramenta manipula caminhos reais diretamente no repositório sem sandbox de escrita.
- **D4. Componentes e Fractalidade:** FAILED: Not implemented. A pasta `componentes/compartilhado/skills/aidd-plan/` possui apenas `SKILL.md`, `references/plan-structure.md` e `tests/test_gerenciador_planos.py`. A lógica de backend está acoplada na raiz em `scripts/gerenciador_planos.py`, sem empacotamento modular fractal em `componentes/compartilhado/skills/aidd-plan/scripts/`.

### Fase 2: O Chão de Fábrica (Workflow Agêntico)
- **D5. Visão e Escopo:** Estruturar e manter planos de iniciativa em `docs/planos/PLAN-NNNN-<nome>` com métricas reais auditadas e rastreabilidade estrita de aprovação do usuário.
  - **[Estágio 1 - Inicialização de Plano] D6. O que o Estágio Faz:** Cria a pasta `PLAN-NNNN-<slug>` com `00-PROCESSO-E-DECISOES.md` e arquivos `NN-<item>.md`.
  - **[Estágio 1 - Inicialização de Plano] D7. O que o Estágio Recebe:** Nome da iniciativa, lista de itens, notas atuais/alvo e evidências.
  - **[Estágio 1 - Inicialização de Plano] D8. O que o Estágio Processa:** `gerenciador_planos.cmd_init` numera sequencialmente a pasta e gera os templates Markdown com cercas válidas.
  - **[Estágio 1 - Inicialização de Plano] D9. O que o Estágio Entrega:** Diretório do plano populado com status inicial DRAFT.
  - **[Estágio 2 - Validação e Transição] D6. O que o Estágio Faz:** Valida fechamento de cercas Markdown e transiciona status dos itens.
  - **[Estágio 2 - Validação e Transição] D7. O que o Estágio Recebe:** Caminho do plano e comando de transição (`aprovar`, `iniciar-execucao`, `atualizar-nota`).
  - **[Estágio 2 - Validação e Transição] D8. O que o Estágio Processa:** `cmd_check_fences`, `cmd_aprovar` e `cmd_iniciar_execucao` validam sintaxe e reescrevem cabeçalhos.
  - **[Estágio 2 - Validação e Transição] D9. O que o Estágio Entrega:** Plano atualizado e index geral sincronizado via `scripts/atualizar_index_planos.py`.
- **D10. Orquestração e Topologia:** Fluxo procedural de transição de status gerenciado via CLI determinística (`init` -> `check-fences` -> `aprovar` -> `iniciar-execucao`), com barreira obrigatória de aprovação do usuário.

### Fase 3: Resiliência e Economia (Engenharia Operacional)
- **D11. Tratamento de Exceções e Fallback:** FAILED: Not implemented. Se o diretório já existe ou parâmetros falham, o script simplesmente retorna exit code 1 no terminal. Inexistência de módulo dedicado `fallback.py` com resolução resiliente de colisão ou estratégias automatizadas de recuperação.
- **D12. Observabilidade e Frugalidade:** FAILED: Not implemented. Não há módulo de observabilidade em tempo de execução calculando contagem de tokens do plano gerado, densidade de itens ou telemetria estruturada exportável.

### Fase 4: O Inspetor e a Expedição (Validação)
- **D13. Quality Gates (Portões):** FAILED: Not implemented. Não existe um Quality Gate formal de repositório `gates/G_aidd_plan.py` que valide a integridade mecânica das pastas em `docs/planos/` contra violações de esquema, notas sem evidência ou cercas corrompidas.
- **D14. Critério de Rejeição (Rollback):** FAILED: Not implemented. Não há gerenciador de contexto com rollback atômico em caso de falha durante a criação ou transição de múltiplos arquivos do plano.
- **D15. Output Consolidado e Handoff:** FAILED: Not implemented. A ferramenta gera arquivos Markdown, mas não emite um manifesto estruturado de handoff com hash SHA-256 / assinatura HMAC para garantir integridade e procedência do plano gerado.

---

## 3. Matriz de Avaliação da Execução
- [ ] A ferramenta isolou seu raio de impacto corretamente?
- [ ] O workflow seguiu as fases sem alucinações de LLM em tarefas mecânicas?
- [ ] O output final passou em todos os Quality Gates e emitiu o Handoff?
