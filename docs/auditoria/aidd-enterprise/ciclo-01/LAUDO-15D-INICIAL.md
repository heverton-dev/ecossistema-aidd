# Template de Auditoria de Ferramenta (Lens 15-D)

Este documento descreve a estrutura canônica para auditar qualquer ferramenta (Skill/Tool) do ecossistema, dissecando sua arquitetura através do framework Lens 15-D (The Agentic Anatomical Matrix).

## 1. Identificação da Ferramenta
- **Nome da Ferramenta:** `aidd-enterprise`
- **Descrição Breve:** Injeta e audita componentes de missão crítica com validação JSON Schema, integridade criptográfica SHA-256 e rollback automático para os tipos `skill`, `rule`, `mcp`, `spec`, `config`, `hook` e `agent`.
- **Comando de Gatilho:** `python ecossistema.py enterprise inject <type> <name>` ou slash command `/enterprise <type> <name>`

## 2. A Matriz Anatômica (Lens 15-D)

### Fase 1: Governança e Blindagem
- **D1. Contratos e Regras:** O frontmatter YAML em `.agents/skills/aidd-enterprise/SKILL.md` define `name: aidd-enterprise` e uma descrição sumária de sua proposta ("Injects and audits mission-critical components with JSON Schema validation, SHA-256 integrity and automatic rollback..."). Contudo, a pasta `.agents/skills/aidd-enterprise/` não contém contratos executáveis, esquemas JSON Schema de validação empacotados localmente, asserções normativas nem tipagem estrita local para garantir as Leis Canônicas do `AGENTS.md` (como Lei #1 de Determinismo, Lei #3 de Persistência Estruturada e Lei #5 de Zero Mocks/Stubs).
- **D2. Input e Gatilhos:** Recebe como gatilho o comando CLI `python ecossistema.py enterprise inject <type> <name>` ou o slash command `/enterprise <type> <name>`. Requisitos de entrada esperados: `<type>` pertencente ao enum de componentes válidos (`skill`, `rule`, `mcp`, `spec`, `config`, `hook`, `agent`) e `<name>` identificando o componente. Requisitos de estado: não há validação prévia estruturada na pasta da skill para verificar existência de manifesto de componentes, diretórios de destino dos harnesses ou permissões de I/O antes da chamada externa.
- **D3. Raio de Impacto e Isolamento:** FAILED: Not implemented. Não há isolamento de raio de impacto implementado no código de `.agents/skills/aidd-enterprise/`. A execução da skill realiza operações diretamente sobre a árvore de trabalho de destino, sem encapsulamento em Git Worktree efêmera, sandbox temporária ou isolamento de contenção no escopo da skill.
- **D4. Componentes e Fractalidade:** FAILED: Not implemented. A pasta `.agents/skills/aidd-enterprise/` consiste exclusivamente no arquivo `SKILL.md` (819 bytes). Não há scripts auxiliares locais em `scripts/`, hooks pré ou pós-execução, nem configuração explícita de recrutamento de MCP Servers ou micro-skills internas para apoiar o fluxo da skill.

### Fase 2: O Chão de Fábrica (Workflow Agêntico)
- **D5. Visão e Escopo:** A transformação central pretendida é a injeção transacional e auditoria contínua de componentes essenciais do ecossistema, garantindo conformidade estrita contra JSON Schema, cálculo e verificação de hashes SHA-256 contra adulteração (anti-drift), criação de snapshot pré-injeção e restauração (rollback) imediata caso ocorra qualquer divergência ou falha.
*(Para cada estágio da execução, detalhe D6 a D9)*
  - **[Estágio 1 - Injeção Transacional de Componente] D6. O que o Estágio Faz:** Invoca o motor de injeção (`ecossistema.py enterprise inject <type> <name>`), delegando a execução para a camada de aplicação de `tools/aidd-enterprise`.
  - **[Estágio 1 - Injeção Transacional de Componente] D7. O que o Estágio Recebe:** Argumentos de linha de comando `<type>` (tipo do componente) e `<name>` (nome do componente).
  - **[Estágio 1 - Injeção Transacional de Componente] D8. O que o Estágio Processa:** FAILED: Not implemented. Não há lógica de processamento analítico, checagem criptográfica ou scripts locais dentro da pasta `.agents/skills/aidd-enterprise/`. O processamento depende integralmente da delegação externa para `tools/aidd-enterprise/scripts/aidd.py` ou da interpretação conversacional da LLM caso a CLI não seja executada deterministamente.
  - **[Estágio 1 - Injeção Transacional de Componente] D9. O que o Estágio Entrega:** Componente injetado nos diretórios de harness, registro atualizado no inventário de capabilities e confirmação de hash sem divergência ("the command exits 0 with no hash divergence reported").
- **D10. Orquestração e Topologia:** FAILED: Not implemented. A skill opera em chamada única monostágio sem encadeamento de etapas, sem validação intermediária de integridade de dados e sem transporte formal de estado persistido entre fases.

### Fase 3: Resiliência e Economia (Engenharia Operacional)
- **D11. Tratamento de Exceções e Fallback:** FAILED: Not implemented. Apesar da menção textual em `SKILL.md` sobre "snapshot and automatic rollback on inconsistency", inexiste implementação executável de rotinas de recuperação, retry loops com backoff exponencial ou mecanismos de rollback na pasta `.agents/skills/aidd-enterprise/`.
- **D12. Observabilidade e Frugalidade:** FAILED: Not implemented. A skill não implementa medição ou controle de consumo de tokens, não persiste logs estruturados de auditoria em `secoes/`, nem registra telemetria de latência e taxa de sucesso da injeção.

### Fase 4: O Inspetor e a Expedição (Validação)
- **D13. Quality Gates (Portões):** FAILED: Not implemented. A pasta `.agents/skills/aidd-enterprise/` não possui Quality Gate determinístico próprio (`gates/G_aidd_enterprise.py` ou equivalente) na raiz de gates que valide com asserção binária `exit 0` / `exit 1` a integridade estrutural, a conformidade de schemas e o comportamento funcional da própria skill.
- **D14. Critério de Rejeição (Rollback):** FAILED: Not implemented. Não há critério formalizado de rejeição com rollback automático operacionalizado no escopo da skill para descartar trabalho (`exit 1`) ou reverter modificações em caso de divergência de hash SHA-256 ou falha de validação estrutural.
- **D15. Output Consolidado e Handoff:** FAILED: Not implemented. A skill não produz manifesto formal assinado de máquina nem emite handoff estruturado para a próxima ferramenta ou etapa do ecossistema.

---

## 3. Matriz de Avaliação da Execução
- [ ] A ferramenta isolou seu raio de impacto corretamente?
- [ ] O workflow seguiu as fases sem alucinações de LLM em tarefas mecânicas?
- [ ] O output final passou em todos os Quality Gates e emitiu o Handoff?
