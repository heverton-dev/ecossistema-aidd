# PLANO DE EVOLUÇÃO (Migração VSA - Monólito Modular)

## Ciclo 01: Migração Estrutural (Concluído)

### Ticket 1: Migração do Núcleo de Governança (aidd-forge)
*   **Ação:** Mover `tools/aidd-forge/` para `modulos/01-governanca-e-qualidade/core/aidd-forge/`.
*   **Proxy:** Criar um script proxy em `tools/aidd-forge/__init__.py` e alias em `ecossistema.py`.
*   **Gate:** Passar nos testes unitários e `python ecossistema.py audit`.
*   **Status:** [x] CONCLUÍDO (Commit `21847f3`).

### Ticket 2: Migração da Tríade de Motores (Pure, Open, Freedom)
*   **Ação:** Mover `tools/aidd-pure`, `tools/aidd-open` e `tools/aidd-freedom` para `modulos/02-triade-motores/`.
*   **Proxy:** Redirecionadores leves em `tools/`.
*   **Gate:** Passar em todos os testes e testes de engine.
*   **Status:** [x] CONCLUÍDO (Commit `854a844`).

### Ticket 3: Migração de Plataforma (Master, Enterprise, Ops)
*   **Ação:** Mover `tools/aidd-master`, `tools/aidd-enterprise` e `tools/aidd-ops` para `modulos/03-plataforma-e-entrega/`.
*   **Proxy:** Redirecionadores em `tools/`.
*   **Gate:** Passar no gate de fatiamento.
*   **Status:** [x] CONCLUÍDO (Commit `44d7bad`).

### Ticket 4: Distribuição dos Portões (Gates) e Skills
*   **Ação:** Mover scripts de `gates/` para `modulos/**/gates/` e skills para fatias locais.
*   **Proxy:** Runner de gates varre `modulos/**/gates/`.
*   **Gate:** Executar gates com saída verde.
*   **Status:** [x] CONCLUÍDO (Commit `3622981`).

---

## Ciclo 02: As 7 Salvaguardas Mandatórias da Migração VSA

### Ticket 5: Convenção Universal de Exit Codes Determinísticos (0 a 5)
*   **Ação:** Implementar módulo canônico de exit codes determinísticos e envelope JSON padronizado.
*   **Arquivos:** `scripts/exit_codes.py`, `scripts/test_exit_codes.py`, `docs/protocolos/CONVENCAO-EXIT-CODES-DETERMINISTICOS.md`.
*   **DoD:** Exit codes `0` (Success), `1` (Rule Violation), `2` (Invalid Usage), `3` (Environment Error), `4` (IO/Timeout), `5` (Internal Bug) testados e validados.
*   **Status:** [x] CONCLUÍDO (Commit `f0a238f`).

### Ticket 6: Validador AST de Fronteiras Arquiteturais entre Fatias VSA
*   **Ação:** Criar gate e validador determinístico inspecionando a AST de imports em `modulos/` para proibir acoplamento ilegal direto entre fatias independentes.
*   **Arquivos:** `gates/G_AST_BOUNDED_CONTEXT.py`, `gates/test_g_ast_bounded_context.py`.
*   **DoD:** Varredura em todas as fatias detectando e bloqueando imports cruzados diretos; prova negativa comprovando exit 1.
*   **Status:** [x] CONCLUÍDO

### Ticket 7: Módulo e Engine Canônica de Self-Healing Determinístico
*   **Ação:** Desenvolver engine de self-healing resiliente com retry determinístico, fallback e circuit breaker para operações de IO/rede/processos.
*   **Arquivos:** `scripts/self_healing.py`, `scripts/test_self_healing.py`.
*   **DoD:** Testes comprovando recuperação determinística em falhas transitórias e encerramento com exit code apropriado sem loops infinitos.
*   **Status:** [x] CONCLUÍDO

### Ticket 8: Blindagem e Atualização Estrita do Baseline de Secrets
*   **Ação:** Sanear caminhos de arquivos migrados e manter `.secrets.baseline` rigorosamente sincronizado em UTF-8.
*   **Arquivos:** `.secrets.baseline`, `gates/G_SEGREDOS.py`.
*   **DoD:** Quality gate `G_SEGREDOS` 100% aprovado sem alertas não-triados ou drifts de número de linha.
*   **Status:** [x] CONCLUÍDO (Commit `d917293`).

### Ticket 9: Protocolo de Isolamento Hermético de Worktrees com Sanitização de Env
*   **Ação:** Implementar utilitário de gerenciamento seguro de worktree que previne vazamento de `GIT_DIR`, `GIT_INDEX_FILE` e realiza pre-sync automático.
*   **Arquivos:** `scripts/worktree_hermetico.py`, `scripts/test_worktree_hermetico.py`.
*   **DoD:** Criação, validação e deleção segura de worktrees com isolamento de variáveis de repositório.
*   **Status:** [x] CONCLUÍDO

### Ticket 10: Auditoria Completa de Paridade e Provas Negativas (Lei #13)
*   **Ação:** Validar que todo gate possui teste automatizado espelho que asserte exit 1 perante quebra proposital de invariante.
*   **Arquivos:** `gates/G_PORTAO_PROVA_QUE_MORDE.py`, `gates/test_g_*.py`.
*   **DoD:** Meta-gate `G_PORTAO_PROVA_QUE_MORDE` executado e aprovado com 100% de conformidade.
*   **Status:** [x] CONCLUÍDO

### Ticket 11: Certificação e Bateria Completa dos Quality Gates
*   **Ação:** Rodar auditoria ponta a ponta dos quality gates do ecossistema e certificar branch `main` limpa e sincronizada.
*   **Arquivos:** `.githooks/pre-push`, `scripts/medir_gates.py`.
*   **DoD:** Push para `origin/main` aprovado pelo pre-push determinístico sem bypass.
*   **Status:** [x] CONCLUÍDO (Commit `f0a238f`).
