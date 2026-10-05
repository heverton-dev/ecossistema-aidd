# Template de Auditoria de Ferramenta (Lens 15-D)

Este documento descreve a estrutura canônica para auditar qualquer ferramenta (Skill/Tool) do ecossistema, dissecando sua arquitetura através do framework Lens 15-D (The Agentic Anatomical Matrix).

## 1. Identificação da Ferramenta
- **Nome da Ferramenta:** `aidd-handoff`
- **Descrição Breve:** Serialização estruturada e compactação de estado de sessão em artefato Markdown para rotação de contexto ou transição entre agentes.
- **Comando de Gatilho:** `/aidd-handoff`, `/handoff`, `handoff`

## 2. A Matriz Anatômica (Lens 15-D)

### Fase 1: Governança e Blindagem
- **D1. Contratos e Regras:** Contrato preliminar declarado no frontmatter YAML de `SKILL.md` (nome `aidd-handoff` e descrição). Define invariantes textuais no corpo do arquivo (destino em `docs/secoes/sessao-<date>-<slug>.md`, 5 seções obrigatórias: Initial Goal, Completed Work, Quality Gate State, Next Actions, Discovered Invariants & Gotchas; economia extrema de tokens; guardrails negativos e stopping checklist). Ausência de módulo Python determinístico com asserções programáticas formais ligadas às Leis Fundamentais do `AGENTS.md`.
- **D2. Input e Gatilhos:** Gatilho conversacional no chat do assistente via `/aidd-handoff` ou termos como "passar o bastão", "salvar contexto". Requisitos de entrada declarados no texto: estado da sessão, histórico git (`git log`, `git diff --stat`) e exit codes de arquivos `.rc`. Não há CLI executável dedicada em `python ecossistema.py handoff` ou validação de schema de entrada por código.
- **D3. Raio de Impacto e Isolamento:** FAILED: Not implemented. Não há isolamento determinístico programático em Python na pasta da skill. A skill confia em instrução textual proibindo escrita fora de `docs/secoes/sessao-<date>-<slug>.md`, sem gerenciamento de Git Worktree efêmera ou sandbox de I/O em tempo de execução.
- **D4. Componentes e Fractalidade:** FAILED: Not implemented. A pasta `componentes/compartilhado/skills/aidd-handoff/` possui apenas `SKILL.md`. Não há subdiretório `scripts/` com módulos utilitários em Python, hooks pré/pós-execução, nem integração nativa com servidores MCP dedicados.

### Fase 2: O Chão de Fábrica (Workflow Agêntico)
- **D5. Visão e Escopo:** Preservar o estado consolidado da sessão em artefato estruturado Markdown sem degradação de contexto ou alucinação de aprovações.
  - **[Estágio 1 - Coleta e Serialização] D6. O que o Estágio Faz:** Lê o estado da conversa e histórico Git para gerar o relatório em `docs/secoes/sessao-<date>-<slug>.md`.
  - **[Estágio 1 - Coleta e Serialização] D7. O que o Estágio Recebe:** Contexto da sessão atual e saídas de comandos git.
  - **[Estágio 1 - Coleta e Serialização] D8. O que o Estágio Processa:** FAILED: Not implemented. Depende 100% de inferência conversacional da LLM; inexistência de motor determinístico em Python para extrair fatos git, parsear `.rc` ou gerar JSON/Markdown estruturado.
  - **[Estágio 1 - Coleta e Serialização] D9. O que o Estágio Entrega:** Arquivo Markdown `docs/secoes/sessao-<date>-<slug>.md` contendo as 5 seções canônicas.
- **D10. Orquestração e Topologia:** Fluxo procedural de passo único baseado em checklist de parada manual (`Stopping Checklist`), sem máquina de estados persistida programaticamente em disco.

### Fase 3: Resiliência e Economia (Engenharia Operacional)
- **D11. Tratamento de Exceções e Fallback:** FAILED: Not implemented. Orientações de fallback descritas apenas textualmente (conflito de arquivo no mesmo diretório, contexto pesado usando git log, gates desconhecidos marcados como "not run"), porém sem implementação de tratamento de exceções, circuit breaker ou retries em código.
- **D12. Observabilidade e Frugalidade:** FAILED: Not implemented. A regra de não colar código-fonte inteiro está expressa no prompt, mas não há rastreador programático de tokens, métricas de execução ou telemetria estruturada persistida em `secoes/`.

### Fase 4: O Inspetor e a Expedição (Validação)
- **D13. Quality Gates (Portões):** FAILED: Not implemented. Inexistência de Quality Gate determinístico `gates/G_aidd_handoff.py` que execute verificação mecânica das 5 seções, ausência de código colado e existência do arquivo. O checklist é manual por comandos bash.
- **D14. Critério de Rejeição (Rollback):** FAILED: Not implemented. Não há rotina de rollback automático ou limpeza de artefatos parciais/corrompidos caso a geração falhe.
- **D15. Output Consolidado e Handoff:** FAILED: Not implemented. A ferramenta gera um artefato de handoff textual, mas ela própria não emite um manifesto assinado criptograficamente (HMAC-SHA256 / SHA-256) nem valida integridade de envelope via schema JSON.

---

## 3. Matriz de Avaliação da Execução
- [ ] A ferramenta isolou seu raio de impacto corretamente?
- [ ] O workflow seguiu as fases sem alucinações de LLM em tarefas mecânicas?
- [ ] O output final passou em todos os Quality Gates e emitiu o Handoff?
