# Plano de Evolução (Fase 2) - aidd-tickets

Este plano foi gerado pelo Arquiteto (Fase 2) do Pipeline Linear de Auditoria 4F, com o objetivo de readequar a ferramenta `aidd-tickets` em conformidade com o Laudo 15-D (`LAUDO-15D-INICIAL.md`, nota 3/10) e a Definição de Pronto (`DOD.md`).

## Estratégia de Execução
Todos os tickets abaixo requerem ciclo TDD estrito (Red-Green-Refactor). Para cada requisito funcional, testes automatizados (exit 0 / exit 1) devem ser criados antes da implementação real. Toda alteração no `SKILL.md` é feita na fonte `componentes/compartilhado/skills/aidd-tickets/SKILL.md` e propagada pelo mecanismo oficial; `python gates/G_HARNESS_COMPAT.py` deve continuar com exit 0.

### Ticket 1: CLI Determinística e Contrato de Entrada (Refere-se a D2 / DoD 1)
- **Falha 15-D:** `D2. Input e Gatilhos`
- **Artefato de Handoff:** `.agents/skills/aidd-tickets/scripts/cli.py`
- **Requisito TDD (Red):** `python ecossistema.py tickets validar --arquivo "x.md"` retorna exit 1 ("comando desconhecido"); o teste deve exigir exit 0 e retorno de status formatado.
- **Implementação Técnica:**
  - Criar `.agents/skills/aidd-tickets/scripts/cli.py` com subcomandos `validar --arquivo <path>`, `ordenar --arquivo <path>`, `exportar --arquivo <path> --output <json>`.
  - Registrar o comando `tickets` no CLI principal `ecossistema.py`.
- **Verificação (Green):** Execução do CLI `ecossistema.py tickets validar` funciona e retorna exit 0 para arquivo válido.
- **Construtor Prompt (EN):**
  - Create .agents/skills/aidd-tickets/scripts/cli.py supporting subcommands: validar, ordenar, exportar.
  - Register tickets command in ecossistema.py delegating to scripts/cli.py.
  - Test: python ecossistema.py tickets validar --arquivo <path>. Assert exit 0 on valid tickets markdown.

### Ticket 2: Isolamento da Execução e Validação de Escrita (Refere-se a D3 / DoD 2)
- **Falha 15-D:** `D3. Raio de Impacto e Isolamento`
- **Artefato de Handoff:** `.agents/skills/aidd-tickets/scripts/isolamento.py`
- **Requisito TDD (Red):** Teste reprova com exit 1 quando exportações de tickets tentarem escrever fora de diretórios autorizados (`docs/` ou worktrees efêmeras).
- **Implementação Técnica:**
  - Criar `TicketsWorktreeManager` em `scripts/isolamento.py` restringindo escritas a `docs/` e pastas temporárias.
- **Verificação (Green):** Escritas não autorizadas são bloqueadas com `SandboxViolationError`.
- **Construtor Prompt (EN):**
  - Create .agents/skills/aidd-tickets/scripts/isolamento.py with TicketsWorktreeManager.
  - Block writes outside authorized paths (docs/ and ephemeral worktrees).
  - Test: attempt write outside authorized directory. Assert exit 1 or SandboxViolationError raised.

### Ticket 3: Parser Canônico de Tickets e Validador de Schema (Refere-se a D4 / DoD 3)
- **Falha 15-D:** `D4. Componentes e Fractalidade`
- **Artefato de Handoff:** `.agents/skills/aidd-tickets/scripts/parser.py`
- **Requisito TDD (Red):** Teste reprova com exit 1 se o parser aceitar tickets sem `Validation Command`, sem `Target Files` ou sem ao menos um arquivo de teste declarado.
- **Implementação Técnica:**
  - Implementar parser regex estrito para capturar cabeçalhos `[TICKET-XX]`, `Target Files`, `Validation Command`, `Blocked by`.
  - Exigir que `Target Files` inclua obrigatoriamente pelo menos um arquivo de teste (`test_*.py`, `*.test.ts`, etc.).
- **Verificação (Green):** Tickets em formato correto são parseados com sucesso (exit 0); tickets sem arquivo de teste são rejeitados com erro claro.
- **Construtor Prompt (EN):**
  - Create .agents/skills/aidd-tickets/scripts/parser.py parsing [TICKET-XX] markdown headers.
  - Extract and validate: Target Files, Validation Command, Blocked by.
  - Enforce rule: Target Files must contain at least one test file.
  - Test: parse ticket without test file. Assert validation fails with exit 1.

### Ticket 4: Analisador de Grafo DAG e Detecção de Ciclos (Refere-se a D8 / DoD 3)
- **Falha 15-D:** `D8. O que o Estágio Processa`
- **Artefato de Handoff:** `.agents/skills/aidd-tickets/scripts/grafo_dag.py`
- **Requisito TDD (Red):** Teste falha com exit 1 quando dependências circulares entre tickets (deadlock) não forem detectadas e reportadas.
- **Implementação Técnica:**
  - Implementar ordenação topológica com algoritmo de Kahn.
  - Detectar ciclos de dependência e listar explicitamente os tickets em deadlock.
- **Verificação (Green):** DAG acíclico devolve ordem correta de execução; dependência circular é identificada e rejeitada com exit 1.
- **Construtor Prompt (EN):**
  - Create .agents/skills/aidd-tickets/scripts/grafo_dag.py implementing Kahn topological sort algorithm.
  - Detect dependency cycles (deadlocks) and return structured cycle path.
  - Test: provide tickets with circular dependency (T1 -> T2 -> T1). Assert cycle detected and exit 1.

### Ticket 5: Fallback e Resiliência Operacional (Refere-se a D11 / DoD 4)
- **Falha 15-D:** `D11. Tratamento de Exceções e Fallback`
- **Artefato de Handoff:** `.agents/skills/aidd-tickets/scripts/fallback.py`
- **Requisito TDD (Red):** Teste trava ou quebra sem diagnóstico quando arquivo markdown de entrada contém formatação corrompida ou caracteres inválidos.
- **Implementação Técnica:**
  - Implementar tratamento de fallback com recuperação parcial de tickets bem formados e relatório de linhas defeituosas.
- **Verificação (Green):** Arquivo corrompido é processado de forma resiliente, reportando linhas com defeito sem quebrar o processo.
- **Construtor Prompt (EN):**
  - Create .agents/skills/aidd-tickets/scripts/fallback.py.
  - Safely handle malformed input and corrupted encodings.
  - Test: feed corrupted ticket block. Assert structured error report and graceful handling.

### Ticket 6: Observabilidade e Métricas de Decomposição (Refere-se a D12 / DoD 5)
- **Falha 15-D:** `D12. Observabilidade e Frugalidade`
- **Artefato de Handoff:** `.agents/skills/aidd-tickets/scripts/observabilidade.py`
- **Requisito TDD (Red):** Execução não gera métricas quantitativas de fatias verticais, profundidade do grafo ou paralelismo máximo.
- **Implementação Técnica:**
  - Implementar `RastreadorTickets` calculando: total de tickets, profundidade máxima do DAG, grau de paralelismo, arquivos tocados e tempo de parsing.
- **Verificação (Green):** Métricas consolidadas gravadas em JSON com todos os campos quantitativos.
- **Construtor Prompt (EN):**
  - Create .agents/skills/aidd-tickets/scripts/observabilidade.py with RastreadorTickets.
  - Compute: total tickets, DAG depth, max parallel batches, distinct files touched, parsing duration.
  - Test: run metrics calculation on ticket list. Assert all metric keys populated.

### Ticket 7: Quality Gate Próprio e Rótulo Honesto (Refere-se a D13 / DoD 6)
- **Falha 15-D:** `D13. Quality Gates (Portões)`
- **Artefato de Handoff:** `gates/G_aidd_tickets.py`
- **Requisito TDD (Red):** Não existe `gates/G_aidd_tdd.py` nem teste comprovando que ele reprova (exit 1) diante de DAG circular ou ausência de testes nos tickets (Lei #13).
- **Implementação Técnica:**
  - Criar `gates/G_aidd_tickets.py` que valida integridade dos tickets e aciclicidade do grafo.
  - Criar `gates/test_g_aidd_tickets.py` provando que o gate morde diante de ciclo e aprova grafo válido.
  - Registrar no portão canônico de auditoria e no AGENTS.md.
- **Verificação (Green):** `python gates/G_aidd_tickets.py` executa e `test_g_aidd_tickets.py` passa comprovando exit 1 em mutação e exit 0 em caso íntegro.
- **Construtor Prompt (EN):**
  - Create gates/G_aidd_tickets.py verifying ticket schema, DAG validity and test file presence.
  - Create gates/test_g_aidd_tickets.py proving gate bites (exit 1 on cycle, exit 0 on clean DAG per Law 13).
  - Register in AGENTS.md and ecossistema.py.
  - Test: run test_g_aidd_tickets.py. Assert exit 0.

### Ticket 8: Limpeza, Rollback e Handoff Assinado (Refere-se a D14 / DoD 7 e DoD 8)
- **Falha 15-D:** `D14. Critério de Rejeição (Rollback)`
- **Artefato de Handoff:** `.agents/skills/aidd-tickets/scripts/handoff.py`
- **Requisito TDD (Red):** Falta mecanismo de rollback para descartar planos com deadlocks e ausência de manifesto de handoff assinado HMAC-SHA256 para o compilador de planos.
- **Implementação Técnica:**
  - Criar `.agents/skills/aidd-tickets/scripts/rollback.py` limpando saídas parciais se a validação do DAG falhar.
  - Criar `.agents/skills/aidd-tickets/scripts/handoff.py` emitindo manifesto JSON de tickets assinado com HMAC-SHA256.
- **Verificação (Green):** Validação falha limpa arquivos gerados; validação bem-sucedida gera handoff assinado íntegro.
- **Construtor Prompt (EN):**
  - Create .agents/skills/aidd-tickets/scripts/rollback.py to clean partial outputs on validation failure.
  - Create .agents/skills/aidd-tickets/scripts/handoff.py producing HMAC-SHA256 signed tickets manifest.
  - Test: run rollback on failure, assert directory clean.
  - Test: run handoff on success, assert valid HMAC signature.
