# Plano de Evolução (Fase 2) - aidd-handoff

Este plano foi gerado pelo Arquiteto (Fase 2) do Pipeline Linear de Auditoria 4F, com o objetivo de readequar a ferramenta `aidd-handoff` em conformidade com o Laudo 15-D e a Definição de Pronto (DoD).

## Estratégia de Execução
Todos os tickets abaixo requerem ciclo TDD estrito (Red-Green-Refactor). Para cada requisito funcional, testes automatizados (exit 0 / exit 1) devem ser criados antes da implementação real.

### Ticket 1: Isolamento de Raio de Impacto e Worktree (Refere-se a D3 / DoD 1)
- **Falha 15-D:** `D3. Raio de Impacto e Isolamento`
- **Artefato de Handoff:** `componentes/compartilhado/skills/aidd-handoff/scripts/isolamento.py`
- **Requisito TDD (Red):** Teste reprova com exit 1 quando tentativa de escrita ocorre fora de docs/secoes/ ou de worktree efemera.
- **Implementação Técnica:**
  - Criar `HandoffWorktreeManager` e `validar_caminho_escrita`.
  - Bloquear acessos de I/O de escrita no repositório fora de `docs/secoes/`.
- **Verificação (Green):** Teste `tests/test_handoff_isolamento.py` passa comprovando isolamento de escrita.
- **Construtor Prompt (EN):**
  - Write test first in tests/test_handoff_isolamento.py. Assert exit 1 when writing outside docs/secoes/ or outside ephemeral worktree.
  - Implement componentes/compartilhado/skills/aidd-handoff/scripts/isolamento.py with HandoffWorktreeManager and validar_caminho_escrita.
  - Block write I/O on repository root. Allow only docs/secoes/.
  - Run pytest tests/test_handoff_isolamento.py. Assert exit 0.

### Ticket 2: CLI Determinístico e Fallback de Terminal (Refere-se a D4 / DoD 2)
- **Falha 15-D:** `D4. Componentes e Fractalidade`
- **Artefato de Handoff:** `componentes/compartilhado/skills/aidd-handoff/scripts/cli.py`
- **Requisito TDD (Red):** Executar cli.py sem comandos validos ou com argumentos ausentes falha com exit 1.
- **Implementação Técnica:**
  - Criar roteador de linha de comando com subcomandos `gerar`, `validar` e `emitir`.
  - Integrar interface em `python ecossistema.py handoff`.
- **Verificação (Green):** Execução de `tests/test_handoff_cli.py` valida subcomandos e saída determinística.
- **Construtor Prompt (EN):**
  - Write test first in tests/test_handoff_cli.py. Assert exit 1 on missing arguments or invalid subcommands.
  - Implement componentes/compartilhado/skills/aidd-handoff/scripts/cli.py with subcommands gerar, validar, and emitir.
  - Wire CLI arguments to deterministic handlers.
  - Run pytest tests/test_handoff_cli.py. Assert exit 0.

### Ticket 3: Motor Determinístico de Serialização (Refere-se a D8 / DoD 3)
- **Falha 15-D:** `D8. O que o Estágio Processa`
- **Artefato de Handoff:** `componentes/compartilhado/skills/aidd-handoff/scripts/motor.py`
- **Requisito TDD (Red):** Teste reprova artefato markdown sem as 5 seções canônicas ou contendo código colado.
- **Implementação Técnica:**
  - Implementar validador das 5 seções obrigatórias: Initial Goal, Completed Work, Quality Gate State, Next Actions, Discovered Invariants & Gotchas.
  - Implementar detector AST/regex que rejeita blocos de código-fonte colados (`def`, `class`, `import`).
- **Verificação (Green):** Teste `tests/test_handoff_motor.py` passa validando extração de dados e conformidade das seções.
- **Construtor Prompt (EN):**
  - Write test first in tests/test_handoff_motor.py. Assert exit 1 when artifact misses mandatory sections or contains pasted source code.
  - Implement componentes/compartilhado/skills/aidd-handoff/scripts/motor.py to validate the 5 mandatory sections.
  - Add AST and regex check rejecting pasted code blocks with def, class, or import.
  - Run pytest tests/test_handoff_motor.py. Assert exit 0.

### Ticket 4: Tratamento de Exceções e Resolução de Conflitos (Refere-se a D11 / DoD 4)
- **Falha 15-D:** `D11. Tratamento de Exceções e Fallback`
- **Artefato de Handoff:** `componentes/compartilhado/skills/aidd-handoff/scripts/fallback.py`
- **Requisito TDD (Red):** Colisão de nome de arquivo ou erro de encoding deve causar falha tratada sem corromper estado anterior.
- **Implementação Técnica:**
  - Implementar detector de colisão de arquivos que anexa sufixo `-2` e previne sobrescrita acidental.
  - Implementar fallback para contexto pesado recuperando fatos diretamente via `git log` e `git diff --stat`.
- **Verificação (Green):** Teste `tests/test_handoff_fallback.py` valida resolução de conflito e recuperação resiliente.
- **Construtor Prompt (EN):**
  - Write test first in tests/test_handoff_fallback.py. Assert name collision handling and safe fallback without state corruption.
  - Implement componentes/compartilhado/skills/aidd-handoff/scripts/fallback.py with filename clash resolution appending suffix -2.
  - Add git log and git diff fallback extraction when conversation context is heavy.
  - Run pytest tests/test_handoff_fallback.py. Assert exit 0.

### Ticket 5: Observabilidade e Frugalidade (Refere-se a D12 / DoD 5)
- **Falha 15-D:** `D12. Observabilidade e Frugalidade`
- **Artefato de Handoff:** `componentes/compartilhado/skills/aidd-handoff/scripts/observabilidade.py`
- **Requisito TDD (Red):** Falta de telemetria ou ausência de métricas de tamanho de artefato deve falhar teste.
- **Implementação Técnica:**
  - Implementar `RastreadorHandoff` para mensurar contagem de seções, linhas totais, estimativa de tokens e latência de geração.
  - Persistir métricas em JSON estruturado para auditoria contínua.
- **Verificação (Green):** Teste `tests/test_handoff_observabilidade.py` valida geração correta do dicionário de métricas.
- **Construtor Prompt (EN):**
  - Write test first in tests/test_handoff_observabilidade.py. Assert failure when telemetry or size metrics are missing.
  - Implement componentes/compartilhado/skills/aidd-handoff/scripts/observabilidade.py with RastreadorHandoff.
  - Track section count, total lines, token estimates, and runtime latency into structured telemetry.
  - Run pytest tests/test_handoff_observabilidade.py. Assert exit 0.

### Ticket 6: Quality Gate Determinístico (Refere-se a D13 / DoD 6)
- **Falha 15-D:** `D13. Quality Gates (Portões)`
- **Artefato de Handoff:** `gates/G_aidd_handoff.py`
- **Requisito TDD (Red):** Gate deve retornar exit 1 para arquivos markdown inválidos ou sem seções obrigatórias.
- **Implementação Técnica:**
  - Criar `gates/G_aidd_handoff.py` que lê o arquivo alvo, valida as 5 seções, verifica inexistência de código colado e confere integridade do caminho.
  - Retornar exit 0 em caso de sucesso e exit 1 em caso de inconformidade.
- **Verificação (Green):** Teste `gates/test_g_aidd_handoff.py` comprova assertividade binária do gate.
- **Construtor Prompt (EN):**
  - Write test first in gates/test_g_aidd_handoff.py. Assert exit 1 on invalid markdown or missing sections.
  - Implement gates/G_aidd_handoff.py to inspect target file for 5 mandatory sections and no pasted code.
  - Ensure strict binary exit 0 on success and exit 1 on failure.
  - Run pytest gates/test_g_aidd_handoff.py. Assert exit 0.

### Ticket 7: Critério de Rejeição e Rollback (Refere-se a D14 / DoD 7)
- **Falha 15-D:** `D14. Critério de Rejeição (Rollback)`
- **Artefato de Handoff:** `componentes/compartilhado/skills/aidd-handoff/scripts/rollback.py`
- **Requisito TDD (Red):** Falha durante escrita ou validação deve descartar arquivo temporário sem deixar resíduo corrompido.
- **Implementação Técnica:**
  - Implementar gerenciador de contexto `executar_com_rollback` que remove arquivos parciais caso ocorra exceção.
- **Verificação (Green):** Teste `tests/test_handoff_rollback.py` valida limpeza determinística em falhas simuladas.
- **Construtor Prompt (EN):**
  - Write test first in tests/test_handoff_rollback.py. Assert partial or corrupted files are purged on failure.
  - Implement componentes/compartilhado/skills/aidd-handoff/scripts/rollback.py with executar_com_rollback context manager.
  - Purge temporary artifacts when validation raises an exception.
  - Run pytest tests/test_handoff_rollback.py. Assert exit 0.

### Ticket 8: Output Consolidado e Assinatura de Handoff (Refere-se a D15 / DoD 8)
- **Falha 15-D:** `D15. Output Consolidado e Handoff`
- **Artefato de Handoff:** `componentes/compartilhado/skills/aidd-handoff/scripts/handoff.py`
- **Requisito TDD (Red):** Handoff sem hash de integridade ou com assinatura inválida deve ser rejeitado com exit 1.
- **Implementação Técnica:**
  - Implementar gerador de manifesto de handoff assinado com HMAC-SHA256 (`handoff-sessao.json`).
  - Implementar validador de assinatura e integridade de conteúdo.
- **Verificação (Green):** Teste `tests/test_handoff_assinatura.py` comprova integridade criptográfica do manifesto.
- **Construtor Prompt (EN):**
  - Write test first in tests/test_handoff_assinatura.py. Assert exit 1 when HMAC signature is invalid or payload tampered.
  - Implement componentes/compartilhado/skills/aidd-handoff/scripts/handoff.py with HMAC-SHA256 manifest signer.
  - Add signature verification and integrity check for emitted session handoff.
  - Run pytest tests/test_handoff_assinatura.py. Assert exit 0.
