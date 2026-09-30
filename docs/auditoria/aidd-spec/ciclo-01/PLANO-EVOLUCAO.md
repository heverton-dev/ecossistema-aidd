# Plano de Evolução (Fase 2) - aidd-spec

Este plano foi gerado pelo Arquiteto (Fase 2) do Pipeline Linear de Auditoria 4F, com o objetivo de readequar a ferramenta `aidd-spec` em conformidade com o Laudo 15-D (`LAUDO-15D-INICIAL.md`, nota 3/10) e a Definição de Pronto (`DOD.md`).

## Estratégia de Execução
Todos os tickets abaixo requerem ciclo TDD estrito (Red-Green-Refactor). Para cada requisito funcional, testes automatizados (exit 0 / exit 1) devem ser criados antes da implementação real. Toda alteração no `SKILL.md` é feita na fonte `componentes/compartilhado/skills/aidd-spec/SKILL.md` e propagada pelo mecanismo oficial; `python gates/G_HARNESS_COMPAT.py` deve continuar com exit 0.

### Ticket 1: CLI Determinística e Contrato de Entrada (Refere-se a D2 / DoD 1)
- **Falha 15-D:** `D2. Input e Gatilhos`
- **Artefato de Handoff:** `.agents/skills/aidd-spec/scripts/cli.py`
- **Requisito TDD (Red):** `python ecossistema.py spec validar --arquivo "spec.md"` retorna exit 1 ("comando desconhecido"); o teste deve exigir exit 0 e retorno de status formatado.
- **Implementação Técnica:**
  - Criar `.agents/skills/aidd-spec/scripts/cli.py` com subcomandos `validar --arquivo <path>`, `compilar --arquivo <path>`, `exportar --arquivo <path> --output <json>`.
  - Registrar o comando `spec` no CLI principal `ecossistema.py`.
- **Verificação (Green):** Execução do CLI `ecossistema.py spec validar` funciona e retorna exit 0 para especificação válida.
- **Construtor Prompt (EN):**
  - Create .agents/skills/aidd-spec/scripts/cli.py supporting subcommands: validar, compilar, exportar.
  - Register spec command in ecossistema.py delegating to scripts/cli.py.
  - Test: python ecossistema.py spec validar --arquivo <path>. Assert exit 0 on valid specification markdown.

### Ticket 2: Isolamento da Execução e Validação de Escrita (Refere-se a D3 / DoD 2)
- **Falha 15-D:** `D3. Raio de Impacto e Isolamento`
- **Artefato de Handoff:** `.agents/skills/aidd-spec/scripts/isolamento.py`
- **Requisito TDD (Red):** Teste reprova com exit 1 quando exportações de especificações tentarem escrever fora de diretórios autorizados (`docs/` ou worktrees efêmeras).
- **Implementação Técnica:**
  - Criar `SpecWorktreeManager` em `scripts/isolamento.py` restringindo escritas a `docs/` e pastas temporárias.
- **Verificação (Green):** Escritas não autorizadas são bloqueadas com `SandboxViolationError`.
- **Construtor Prompt (EN):**
  - Create .agents/skills/aidd-spec/scripts/isolamento.py with SpecWorktreeManager.
  - Block writes outside authorized paths (docs/ and ephemeral worktrees).
  - Test: attempt write outside authorized directory. Assert exit 1 or SandboxViolationError raised.

### Ticket 3: Parser Canônico de Especificação e Validador das 5 Seções (Refere-se a D4 / DoD 3)
- **Falha 15-D:** `D4. Componentes e Fractalidade`
- **Artefato de Handoff:** `.agents/skills/aidd-spec/scripts/parser.py`
- **Requisito TDD (Red):** Teste reprova com exit 1 se o parser aceitar especificações faltando qualquer uma das 5 seções obrigatórias (Context & Explicit Non-Goals, Contracts & Typed Interfaces, Invariants & Business Rules, Binary Acceptance Criteria, Failure & Degradation Modes).
- **Implementação Técnica:**
  - Implementar parser estrutural e regex para capturar e validar as 5 seções canônicas de especificação técnica.
  - Validar presença de seções numeradas ou subtítulos markdown reconhecidos.
- **Verificação (Green):** Especificações com todas as 5 seções são aprovadas (exit 0); especificações incompletas são rejeitadas com erro explícito de seção faltante.
- **Construtor Prompt (EN):**
  - Create .agents/skills/aidd-spec/scripts/parser.py parsing the 5 canonical specification sections.
  - Extract and validate: Context/Non-Goals, Contracts/Interfaces, Invariants, Binary Acceptance Criteria, Failure Modes.
  - Enforce rule: All 5 sections are mandatory.
  - Test: parse spec missing a required section. Assert validation fails with exit 1.

### Ticket 4: Motor de Validação de Critérios Binários e Invariantes (Refere-se a D8 / DoD 3)
- **Falha 15-D:** `D8. O que o Estágio Processa`
- **Artefato de Handoff:** `.agents/skills/aidd-spec/scripts/motor.py`
- **Requisito TDD (Red):** Teste falha com exit 1 quando critérios subjetivos/vagos (ex: "o sistema deve ser rápido", "a UI deve ser bonita") forem aceitos como critérios binários.
- **Implementação Técnica:**
  - Implementar validador determinístico em `scripts/motor.py` exigindo critérios verificáveis mecanicamente (ex: menção a exit codes, status codes HTTP, assertions, tempos numéricos com unidade, ou verificações booleanas).
  - Rejeitar linguagem subjetiva e termos vagos sem métrica ou condição objetiva associada.
- **Verificação (Green):** Critérios binários explícitos são validados com sucesso; critérios subjetivos sem asserção objetiva são rejeitados com exit 1.
- **Construtor Prompt (EN):**
  - Create .agents/skills/aidd-spec/scripts/motor.py validating binary acceptance criteria and invariants.
  - Enforce mechanical verifiability: must contain verifiable conditions (status codes, exit codes, boolean assertions, exact thresholds).
  - Test: provide vague criteria without verifiable condition. Assert validation fails with exit 1.

### Ticket 5: Fallback e Resiliência Operacional (Refere-se a D11 / DoD 4)
- **Falha 15-D:** `D11. Tratamento de Exceções e Fallback`
- **Artefato de Handoff:** `.agents/skills/aidd-spec/scripts/fallback.py`
- **Requisito TDD (Red):** Teste quebra com exceção sem diagnóstico quando o arquivo markdown de especificação contiver encoding inválido, blocos markdown corrompidos ou tags truncadas.
- **Implementação Técnica:**
  - Implementar tratamento de fallback com recuperação resiliente em `scripts/fallback.py`, diagnosticando seções corrompidas e extraindo conteúdo válido com relatório de advertências.
- **Verificação (Green):** Arquivo corrompido é processado de forma segura, gerando relatório de anomalias sem interromper a execução do pipeline.
- **Construtor Prompt (EN):**
  - Create .agents/skills/aidd-spec/scripts/fallback.py.
  - Safely handle malformed input and corrupted encodings.
  - Test: feed corrupted spec content. Assert structured error report and graceful handling.

### Ticket 6: Observabilidade e Métricas de Especificação (Refere-se a D12 / DoD 5)
- **Falha 15-D:** `D12. Observabilidade e Frugalidade`
- **Artefato de Handoff:** `.agents/skills/aidd-spec/scripts/observabilidade.py`
- **Requisito TDD (Red):** Execução da especificação não emite métricas quantitativas de invariantes, critérios binários, contratos tipados ou tempo de análise.
- **Implementação Técnica:**
  - Implementar `RastreadorSpec` calculando: total de invariantes, total de critérios binários, total de interfaces/contratos, contagem de modos de falha e duração de análise.
- **Verificação (Green):** Métricas consolidadas gravadas em JSON com todas as chaves quantitativas preenchidas.
- **Construtor Prompt (EN):**
  - Create .agents/skills/aidd-spec/scripts/observabilidade.py with RastreadorSpec.
  - Compute: total invariants, total binary criteria, typed interfaces count, failure modes count, parsing duration.
  - Test: run metrics calculation on spec document. Assert all metric keys populated.

### Ticket 7: Quality Gate Próprio e Rótulo Honesto (Refere-se a D13 / DoD 6)
- **Falha 15-D:** `D13. Quality Gates (Portões)`
- **Artefato de Handoff:** `gates/G_aidd_spec.py`
- **Requisito TDD (Red):** Não existe `gates/G_aidd_spec.py` nem teste comprovando que ele reprova (exit 1) diante de especificação sem critérios binários ou sem as 5 seções obrigatórias (Lei #13).
- **Implementação Técnica:**
  - Criar `gates/G_aidd_spec.py` que valida a estrutura canônica da especificação, as 5 seções obrigatórias e os critérios binários.
  - Criar `gates/test_g_aidd_spec.py` provando que o gate morde diante de especificação defeituosa e aprova especificação íntegra.
  - Registrar no portão canônico de auditoria e no AGENTS.md.
- **Verificação (Green):** `python gates/G_aidd_spec.py` executa e `test_g_aidd_spec.py` passa comprovando exit 1 em mutação e exit 0 em caso íntegro.
- **Construtor Prompt (EN):**
  - Create gates/G_aidd_spec.py verifying spec canonical schema, 5 mandatory sections, and binary criteria.
  - Create gates/test_g_aidd_spec.py proving gate bites (exit 1 on invalid spec, exit 0 on clean spec per Law 13).
  - Register in AGENTS.md and ecossistema.py.
  - Test: run test_g_aidd_spec.py. Assert exit 0.

### Ticket 8: Limpeza, Rollback e Handoff Assinado (Refere-se a D14 / DoD 7 e DoD 8)
- **Falha 15-D:** `D14. Critério de Rejeição (Rollback)`
- **Artefato de Handoff:** `.agents/skills/aidd-spec/scripts/handoff.py`
- **Requisito TDD (Red):** Falta mecanismo de rollback para descartar artefatos de especificações inválidas e ausência de manifesto de handoff assinado HMAC-SHA256 para `/aidd-tickets` e `/aidd-planner`.
- **Implementação Técnica:**
  - Criar `.agents/skills/aidd-spec/scripts/rollback.py` limpando saídas geradas quando a validação da especificação falhar.
  - Criar `.agents/skills/aidd-spec/scripts/handoff.py` emitindo manifesto JSON da especificação assinado com HMAC-SHA256.
- **Verificação (Green):** Validação com erro executa rollback limpando artefatos parciais; validação bem-sucedida gera manifesto de handoff assinado íntegro.
- **Construtor Prompt (EN):**
  - Create .agents/skills/aidd-spec/scripts/rollback.py to clean partial outputs on validation failure.
  - Create .agents/skills/aidd-spec/scripts/handoff.py producing HMAC-SHA256 signed spec manifest.
  - Test: run rollback on failure, assert target path cleaned.
  - Test: run handoff on success, assert valid HMAC signature.
