# Template de Auditoria de Ferramenta (Lens 15-D)

Este documento descreve a estrutura canônica para auditar qualquer ferramenta (Skill/Tool) do ecossistema, dissecando sua arquitetura através do framework Lens 15-D (The Agentic Anatomical Matrix).

## 1. Identificação da Ferramenta
- **Nome da Ferramenta:** `aidd-dependencias` (`aidd-dependencies`, `dependencia-runner`)
- **Descrição Breve:** Gerenciamento, instalação, verificação e bootstrap determinístico de dependências externas de terceiros (skills de fornecedores e servidores MCP) através do manifesto soberano `gates/dependencias_externas.json`.
- **Comando de Gatilho:** `/aidd-dependencies`, `/dependencia`, `python ecossistema.py dependencia bootstrap|add-skill|add-mcp|list|verify`

## 2. A Matriz Anatômica (Lens 15-D)

### Fase 1: Governança e Blindagem
- **D1. Contratos e Regras:** Regras formalizadas em `gates/dependencias_externas.json` e `SKILL.md`: proibição de segredos/tokens em arquivos de manifesto, proibição de chaves de LLM como dependência externa (o modelo é sempre o próprio harness ativo), e obrigatoriedade de `--gitignore` para evitar tracking acidental de dependências de terceiros.
- **D2. Input e Gatilhos:** Interface via CLI do ecossistema `python ecossistema.py dependencia` com subcomandos determinísticos (`bootstrap`, `add-skill`, `add-mcp`, `list`, `verify`).
- **D3. Raio de Impacto e Isolamento:** I/O delimitado estritamente ao manifesto `gates/dependencias_externas.json` e aos arquivos de configuração de MCP dos harnesses suportados (`.mcp.json`, `opencode.jsonc`, `.cursor/mcp.json`, etc.).
- **D4. Componentes e Fractalidade:** Motor modular em `scripts/gestor_dependencias.py`, desacoplado e integrado na CLI unificada `ecossistema.py`.

### Fase 2: O Chão de Fábrica (Workflow Agêntico)
- **D5. Visão e Escopo:** Automatizar o ciclo de vida e a integridade de todas as ferramentas de terceiros utilizadas pelos agentes no monorepo, assegurando repetibilidade e prevenção de segredos.
  - **[Estágio 1 - Leitura do Manifesto] D6. O que o Estágio Faz:** Carrega o catálogo de dependências e valida a estrutura JSON.
  - **[Estágio 1 - Leitura do Manifesto] D7. O que o Estágio Recebe:** Caminho do manifesto `gates/dependencias_externas.json`.
  - **[Estágio 1 - Leitura do Manifesto] D8. O que o Estágio Processa:** Parsing estruturado e verificação de schemas de instalação.
  - **[Estágio 1 - Leitura do Manifesto] D9. O que o Estágio Entrega:** Dicionário validado de skills e servidores MCP.
  - **[Estágio 2 - Execução e Checagem] D6. O que o Estágio Faz:** Executa o bootstrap/instalação ou valida a presença física e o hash SHA-256.
  - **[Estágio 2 - Execução e Checagem] D7. O que o Estágio Recebe:** Flags de tipo e modo de execução.
  - **[Estágio 2 - Execução e Checagem] D8. O que o Estágio Processa:** Subprocessos de instalação, cálculo de hash SHA-256 e gravação em configs de harnesses.
  - **[Estágio 2 - Execução e Checagem] D9. O que o Estágio Entrega:** Relatório de status e exit code 0/1.
- **D10. Orquestração e Topologia:** Pipeline sequencial `load -> inspect -> install -> assert_hash` com travas binárias de interrupção em qualquer falha de integridade.

### Fase 3: Resiliência e Economia (Engenharia Operacional)
- **D11. Tratamento de Exceções e Fallback:** Detecção preventiva de ferramentas de linha de comando (`npx`, `docker`) ausentes no PATH (`_npx_disponivel()`) emitindo avisos acionáveis sem crash.
- **D12. Observabilidade e Frugalidade:** Execução determinística local em Python com saída textual resumida e telemetria precisa de status (instalado, ausente, hash divergente).

### Fase 4: O Inspetor e a Expedição (Validação)
- **D13. Quality Gates (Portões):** Validado pelos Quality Gates soberanos `gates/G_dependencias_externas.py` e `gates/G_SEGREDOS.py` (proibindo chaves ou dados sensíveis nos configs gerados).
- **D14. Critério de Rejeição (Rollback):** Divergência de hash SHA-256 ou variável de segredo exposta bloqueia a verificação com exit 1.
- **D15. Output Consolidado e Handoff:** Manifesto estruturado assinado com hashes das skills canônicas, servindo como baseline confiável de ambiente.

---

## 3. Matriz de Avaliação da Execução
- [x] A ferramenta isolou seu raio de impacto corretamente? Sim, estritamente mapeado pelo gestor de dependências.
- [x] O workflow seguiu as fases sem alucinações de LLM em tarefas mecânicas? Sim, motor 100% determinístico em Python.
- [x] O output final passou em todos os Quality Gates e emitiu o Handoff? Sim, validado por `G_dependencias_externas.py` e `dependencia verify` com exit 0.
