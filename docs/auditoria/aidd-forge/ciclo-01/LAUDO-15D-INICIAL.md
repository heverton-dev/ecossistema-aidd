# Template de Auditoria de Ferramenta (Lens 15-D)

Este documento descreve a estrutura canônica para auditar qualquer ferramenta (Skill/Tool) do ecossistema, dissecando sua arquitetura através do framework Lens 15-D (The Agentic Anatomical Matrix).

## 1. Identificação da Ferramenta
- **Nome da Ferramenta:** `aidd-forge`
- **Descrição Breve:** Injeta o kit completo de governança AIDD em um repositório alvo (orquestração efêmera de subagentes com context purge, quality gates determinísticos, git hooks, regras de economia extrema de tokens e fatiamento de fases com microambientes isolados).
- **Comando de Gatilho:** `python ecossistema.py forge init [path]` ou slash command `/forge [path]`

## 2. A Matriz Anatômica (Lens 15-D)

### Fase 1: Governança e Blindagem
- **D1. Contratos e Regras:** O frontmatter YAML em `.agents/skills/aidd-forge/SKILL.md` define nome (`aidd-forge`) e uma descrição sumária de sua proposta ("Bootstraps and hardens a target repository..."). Contudo, a pasta `.agents/skills/aidd-forge/` não contém contratos executáveis, esquemas JSON Schema de validação, asserções normativas nem tipagem estrita para garantir a aplicação integral das 13 Leis Canônicas do `AGENTS.md` (como Lei #1 de Determinismo, Lei #5 de Zero Mocks/Stubs e Lei #6 de Supremacia Agnóstica).
- **D2. Input e Gatilhos:** Recebe como gatilho o comando CLI `python ecossistema.py forge init [path]` ou o slash command `/forge [path]`. Se omitido o argumento `[path]`, assume o diretório atual. Requisitos de estado: não há validação prévia estruturada para verificar se o diretório alvo é um repositório git inicializado, se possui estrutura de branches limpa ou permissões adequadas de I/O antes da execução.
- **D3. Raio de Impacto e Isolamento:** FAILED: Not implemented. Não há isolamento de raio de impacto implementado no código de `.agents/skills/aidd-forge/`. A execução da skill realiza operações diretamente sobre a árvore de trabalho de destino, sem encapsulamento em Git Worktree efêmera, contêiner temporário ou sandbox de contenção prévia.
- **D4. Componentes e Fractalidade:** FAILED: Not implemented. A pasta `.agents/skills/aidd-forge/` consiste exclusivamente no arquivo `SKILL.md` (831 bytes). Não há scripts auxiliares locais em `scripts/`, hooks pré ou pós-execução, nem configuração explícita de recrutamento de MCP Servers ou micro-skills internas para apoiar o fluxo da skill.

### Fase 2: O Chão de Fábrica (Workflow Agêntico)
- **D5. Visão e Escopo:** A transformação central pretendida é blindar e configurar um projeto de software com a infraestrutura e governança do ecossistema AIDD, materializando os Quality Gates essenciais, githooks de integridade, instruções normativas (`AGENTS.md`, `CLAUDE.md`, regras de harness) e parâmetros de context-purge.
*(Para cada estágio da execução, detalhe D6 a D9)*
  - **[Estágio 1 - Inicialização e Injeção de Governança] D6. O que o Estágio Faz:** Invoca o motor de injeção da governança (`ecossistema.py forge init [path]`), gerando a infraestrutura inicial de governança, gates e hooks.
  - **[Estágio 1 - Inicialização e Injeção de Governança] D7. O que o Estágio Recebe:** Argumento de caminho `[path]` (opcional, default diretório corrente).
  - **[Estágio 1 - Inicialização e Injeção de Governança] D8. O que o Estágio Processa:** FAILED: Not implemented. Não há lógica de processamento analítico ou scripts locais dentro da pasta `.agents/skills/aidd-forge/`. O processamento depende integralmente da delegação externa para `tools/aidd-forge` ou da interpretação conversacional da LLM caso a CLI não seja executada deterministamente.
  - **[Estágio 1 - Inicialização e Injeção de Governança] D9. O que o Estágio Entrega:** Diretório alvo populado com arquivos de governança, templates e githooks configurados, encerrando na condição descrita em `SKILL.md`: "Done when: the command exits 0 and the target contains the injected gates and hooks".
- **D10. Orquestração e Topologia:** FAILED: Not implemented. A skill opera em chamada única monostágio sem encadeamento de etapas, sem validação intermediária de integridade de dados e sem transporte formal de estado persistido entre fases.

### Fase 3: Resiliência e Economia (Engenharia Operacional)
- **D11. Tratamento de Exceções e Fallback:** FAILED: Not implemented. Inexistência de rotinas de retry com backoff exponencial, recuperação autônoma de falhas, tratamento de permissões de disco negadas ou mecanismos de fallback na pasta `.agents/skills/aidd-forge/`.
- **D12. Observabilidade e Frugalidade:** FAILED: Not implemented. A skill não implementa medição ou controle de consumo de tokens, não persiste logs estruturados em `secoes/`, nem registra telemetria de latência e taxa de sucesso da injeção.

### Fase 4: O Inspetor e a Expedição (Validação)
- **D13. Quality Gates (Portões):** FAILED: Not implemented. A pasta `.agents/skills/aidd-forge/` não possui Quality Gate determinístico próprio (`gates/G_aidd_forge.py`) que valide com `exit 0` / `exit 1` a integridade estrutural e funcional da própria skill (conforme exigido pelo DoD 6 da auditoria). O gate existente no repositório (`gates/G_TEMPLATE_FORGE_ROT.py`) avalia unicamente templates em `tools/aidd-forge/`, e não a completude da skill.
- **D14. Critério de Rejeição (Rollback):** FAILED: Not implemented. Não há critério formalizado de rejeição com rollback automático para limpar arquivos parcialmente gravados ou desfazer modificações em caso de interrupção ou falha durante o bootstrap.
- **D15. Output Consolidado e Handoff:** FAILED: Not implemented. A skill não produz manifesto formal de máquina (JSON assinado com hashes SHA-256 dos componentes injetados), nem emite handoff estruturado para a próxima ferramenta da Tríade (`aidd-planner`).

---

## 3. Matriz de Avaliação da Execução
- [ ] A ferramenta isolou seu raio de impacto corretamente?
- [ ] O workflow seguiu as fases sem alucinações de LLM em tarefas mecânicas?
- [ ] O output final passou em todos os Quality Gates e emitiu o Handoff?
