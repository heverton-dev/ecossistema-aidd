# Plano de Evolução (Fase 2) - aidd-grill

Este plano foi gerado pelo Arquiteto (Fase 2) do Pipeline Linear de Auditoria 4F, com o objetivo de readequar a ferramenta `aidd-grill` em conformidade com o Laudo 15-D (`LAUDO-15D-INICIAL.md`, nota 3/10) e a Definição de Pronto (`DOD.md`).

## Estratégia de Execução
Todos os tickets abaixo requerem ciclo TDD estrito (Red-Green-Refactor). Para cada requisito funcional, testes automatizados (exit 0 / exit 1) devem ser criados antes da implementação real. Toda alteração no `SKILL.md` é feita na fonte `componentes/compartilhado/skills/aidd-grill/SKILL.md` e propagada pelo mecanismo oficial; `python gates/G_HARNESS_COMPAT.py` deve continuar com exit 0.

### Ticket 1: CLI Determinística e Contrato de Entrada (Refere-se a D2 / DoD 1)
- **Falha 15-D:** `D2. Input e Gatilhos`
- **Artefato de Handoff:** `.agents/skills/aidd-grill/scripts/cli.py`
- **Requisito TDD (Red):** `python ecossistema.py grill validar --arquivo "rodada.md"` retorna exit 1 ("comando desconhecido"); o teste deve exigir exit 0 e retorno de status formatado.
- **Implementação Técnica:**
  - Criar `.agents/skills/aidd-grill/scripts/cli.py` com subcomandos `validar --arquivo <path>`, `consolidar --arquivo <path>`, `exportar --arquivo <path> --output <json>`.
  - Registrar o comando `grill` no CLI principal `ecossistema.py`.
- **Verificação (Green):** Execução do CLI `ecossistema.py grill validar` funciona e retorna exit 0 para rodada socrática válida.
- **Construtor Prompt (EN):**
  - Create .agents/skills/aidd-grill/scripts/cli.py supporting subcommands: validar, consolidar, exportar.
  - Register grill command in ecossistema.py delegating to scripts/cli.py.
  - Test: python ecossistema.py grill validar --arquivo <path>. Assert exit 0 on valid socratic round markdown.

### Ticket 2: Isolamento da Execução e Validação de Escrita (Refere-se a D3 / DoD 2)
- **Falha 15-D:** `D3. Raio de Impacto e Isolamento`
- **Artefato de Handoff:** `.agents/skills/aidd-grill/scripts/isolamento.py`
- **Requisito TDD (Red):** Teste reprova com exit 1 quando exportações de premissas tentarem escrever fora de diretórios autorizados (`docs/` ou worktrees efêmeras).
- **Implementação Técnica:**
  - Criar `GrillWorktreeManager` em `scripts/isolamento.py` restringindo escritas a `docs/` e pastas temporárias.
- **Verificação (Green):** Escritas não autorizadas são bloqueadas com `SandboxViolationError`.
- **Construtor Prompt (EN):**
  - Create .agents/skills/aidd-grill/scripts/isolamento.py with GrillWorktreeManager.
  - Block writes outside authorized paths (docs/ and ephemeral worktrees).
  - Test: attempt write outside authorized directory. Assert exit 1 or SandboxViolationError raised.

### Ticket 3: Parser Canônico de Rodadas e Perguntas Socráticas (Refere-se a D4 / DoD 3)
- **Falha 15-D:** `D4. Componentes e Fractalidade`
- **Artefato de Handoff:** `.agents/skills/aidd-grill/scripts/parser.py`
- **Requisito TDD (Red):** Teste reprova com exit 1 se o parser aceitar rodadas com perguntas sem numeração ou sem bloco de recomendação explicitado.
- **Implementação Técnica:**
  - Implementar parser estrutural e regex para capturar rodadas socráticas, perguntas numeradas (1, 2, 3...) e bloco de recomendação (`Recomendado:` ou `Recommended:`).
- **Verificação (Green):** Rodadas bem formatadas com perguntas numeradas e recomendações são aprovadas (exit 0); documentos sem perguntas numeradas ou sem recomendação são rejeitados com erro explícito.
- **Construtor Prompt (EN):**
  - Create .agents/skills/aidd-grill/scripts/parser.py parsing numbered questions and recommended answer blocks.
  - Extract and validate: question number, question text, options, and recommended option.
  - Test: parse round missing numbered questions or recommendations. Assert validation fails with exit 1.

### Ticket 4: Motor de Validação de Recomendações e Justificativas (Refere-se a D8 / DoD 3)
- **Falha 15-D:** `D8. O que o Estágio Processa`
- **Artefato de Handoff:** `.agents/skills/aidd-grill/scripts/motor.py`
- **Requisito TDD (Red):** Teste falha com exit 1 quando perguntas socráticas contiverem recomendações vazias, sem justificativa (ex: apenas "Recomendado: A" sem explicar o porquê) ou perguntas factuais já respondidas pelo repositório.
- **Implementação Técnica:**
  - Implementar validador determinístico em `scripts/motor.py` exigindo justificativa explícita na recomendação (deve conter conectivos causais: "porque", "pois", "devido a", "because", "since", etc.).
  - Rejeitar recomendações secas sem justificativa técnica.
- **Verificação (Green):** Perguntas com recomendação justificada são validadas com sucesso; recomendações sem justificativa são rejeitadas com exit 1.
- **Construtor Prompt (EN):**
  - Create .agents/skills/aidd-grill/scripts/motor.py validating recommended answers and justifications.
  - Enforce rule: recommendations must contain an explicit causal justification (because, pois, etc.).
  - Test: provide recommendation without rationale. Assert validation fails with exit 1.

### Ticket 5: Fallback e Resiliência Operacional Headless (Refere-se a D11 / DoD 4)
- **Falha 15-D:** `D11. Tratamento de Exceções e Fallback`
- **Artefato de Handoff:** `.agents/skills/aidd-grill/scripts/fallback.py`
- **Requisito TDD (Red):** Em modo autônomo/headless ou com entrada truncada, a ferramenta falha ou trava sem gerar o bloco canônico `### Consolidated Assumptions`.
- **Implementação Técnica:**
  - Implementar síntese autônoma de premissas em `scripts/fallback.py` convertendo automaticamente as recomendações das perguntas abertas em premissas consolidadas estruturadas caso não haja intervenção humana.
- **Verificação (Green):** Modo headless gera premissas consolidadas válidas de forma determinística e resiliente.
- **Construtor Prompt (EN):**
  - Create .agents/skills/aidd-grill/scripts/fallback.py.
  - Implement headless autonomous fallback synthesizing ### Consolidated Assumptions from open question recommendations.
  - Test: feed open questions in headless mode. Assert consolidated assumptions generated cleanly.

### Ticket 6: Observabilidade e Métricas de Entrevista Socrática (Refere-se a D12 / DoD 5)
- **Falha 15-D:** `D12. Observabilidade e Frugalidade`
- **Artefato de Handoff:** `.agents/skills/aidd-grill/scripts/observabilidade.py`
- **Requisito TDD (Red):** Execução do grill não emite métricas quantitativas de total de perguntas, rodadas realizadas, premissas consolidadas ou tempo de análise.
- **Implementação Técnica:**
  - Implementar `RastreadorGrill` calculando: total de perguntas formuladas, total de opções mapeadas, perguntas com recomendação justificada, premissas consolidadas e duração da entrevista.
- **Verificação (Green):** Métricas consolidadas gravadas em JSON com todas as chaves quantitativas preenchidas.
- **Construtor Prompt (EN):**
  - Create .agents/skills/aidd-grill/scripts/observabilidade.py with RastreadorGrill.
  - Compute: total questions, total rounds, justified recommendations count, consolidated assumptions count, processing duration.
  - Test: run metrics calculation on grill session. Assert all metric keys populated.

### Ticket 7: Quality Gate Próprio e Rótulo Honesto (Refere-se a D13 / DoD 6)
- **Falha 15-D:** `D13. Quality Gates (Portões)`
- **Artefato de Handoff:** `gates/G_aidd_grill.py`
- **Requisito TDD (Red):** Não existe `gates/G_aidd_grill.py` nem teste comprovando que ele reprova (exit 1) diante de perguntas sem numeração ou recomendações sem justificativa (Lei #13).
- **Implementação Técnica:**
  - Criar `gates/G_aidd_grill.py` que valida a estrutura canônica da entrevista socrática, perguntas numeradas e recomendações justificadas.
  - Criar `gates/test_g_aidd_grill.py` provando que o gate morde diante de rodada defeituosa e aprova rodada íntegra.
  - Registrar no portão canônico de auditoria e no AGENTS.md.
- **Verificação (Green):** `python gates/G_aidd_grill.py` executa e `test_g_aidd_grill.py` passa comprovando exit 1 em mutação e exit 0 em caso íntegro.
- **Construtor Prompt (EN):**
  - Create gates/G_aidd_grill.py verifying socratic rounds, numbered questions, and justified recommendations.
  - Create gates/test_g_aidd_grill.py proving gate bites (exit 1 on invalid round, exit 0 on clean round per Law 13).
  - Register in AGENTS.md and ecossistema.py.
  - Test: run test_g_aidd_grill.py. Assert exit 0.

### Ticket 8: Limpeza, Rollback e Handoff Assinado (Refere-se a D14 / DoD 7 e DoD 8)
- **Falha 15-D:** `D14. Critério de Rejeição (Rollback)`
- **Artefato de Handoff:** `.agents/skills/aidd-grill/scripts/handoff.py`
- **Requisito TDD (Red):** Falta mecanismo de rollback para descartar artefatos de rodadas socráticas inválidas e ausência de manifesto de handoff assinado HMAC-SHA256 para `/aidd-spec`.
- **Implementação Técnica:**
  - Criar `.agents/skills/aidd-grill/scripts/rollback.py` limpando saídas geradas quando a validação da rodada falhar.
  - Criar `.agents/skills/aidd-grill/scripts/handoff.py` emitindo manifesto JSON de premissas consolidadas assinado com HMAC-SHA256.
- **Verificação (Green):** Validação com erro executa rollback limpando artefatos parciais; validação bem-sucedida gera manifesto de handoff assinado íntegro.
- **Construtor Prompt (EN):**
  - Create .agents/skills/aidd-grill/scripts/rollback.py to clean partial outputs on validation failure.
  - Create .agents/skills/aidd-grill/scripts/handoff.py producing HMAC-SHA256 signed assumptions manifest for aidd-spec.
  - Test: run rollback on failure, assert target path cleaned.
  - Test: run handoff on success, assert valid HMAC signature.
