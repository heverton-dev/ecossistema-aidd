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

### Ticket 1: Adoção Universal de Exit Codes Determinísticos nos Quality Gates
*   **Ação:** Integrar taxonomia canônica de 0 a 5 (`scripts/exit_codes.py`) e envelopes padronizados na execução dos quality gates do monorepo.
*   **Arquivos:** `scripts/exit_codes.py`, `scripts/test_exit_codes.py`, `gates/G_DETERMINISMO_LEI_1.py`, `docs/protocolos/CONVENCAO-EXIT-CODES-DETERMINISTICOS.md`.
*   **DoD:** Validação de 0 a 5 sem retorno solto de exceção não tratada em gates.
*   **Status:** [x] CONCLUÍDO

### Ticket 2: Lazy Dynamic Import (`importlib`) em `ecossistema.py` para Boot Acelerado
*   **Ação:** Mover imports globais de módulos pesados (`click`, `dotenv`, analisadores) para dentro dos comandos específicos disparados via lazy loading.
*   **Arquivos:** `ecossistema.py`.
*   **DoD:** Redução no tempo de boot da CLI e desacoplamento do carregamento estático.
*   **Status:** [x] CONCLUÍDO (Commit `34ccd2f`).

### Ticket 3: Gatilhos de Micro-Gates no Pre-Commit Baseados em `git diff` por Fatia
*   **Ação:** Implementar runner seletivo de micro-gates com disparo condicional atrelado à fatia modificada via `git diff --cached`.
*   **Arquivos:** `scripts/micro_gates.py`, `.pre-commit-config.yaml`.
*   **DoD:** Verificação direcionada em tempo recorde sem dispensar a bateria de segurança integral.
*   **Status:** [x] CONCLUÍDO (Commit `5577a94`).

### Ticket 4: Fronteiras Arquiteturais Estritas via AST (`interface.py` e `__all__`)
*   **Ação:** Validar via AST de imports que acoplamentos entre fatias só ocorram através de contratos formais declarados.
*   **Arquivos:** `gates/G_AST_BOUNDED_CONTEXT.py`, `gates/test_g_ast_bounded_context.py`.
*   **DoD:** Varredura em todas as fatias detectando e bloqueando imports cruzados diretos; contraprova negativa assertando exit 1.
*   **Status:** [x] CONCLUÍDO (Commit `324d86e`).

### Ticket 5: Desacoplamento dos Proxies Legados de `tools/` em Prol de Imports Diretos da Fatia
*   **Ação:** Migrar dependências e referências nos módulos para importar diretamente de `modulos/` em vez de transitar por redirecionadores em `tools/`.
*   **Arquivos:** `modulos/`, `tools/`.
*   **DoD:** Redução gradual da dependência de ponte com validação 100% verde nos gates.
*   **Status:** [x] CONCLUÍDO (Commit `998b87d`).

### Ticket 6: Particionamento de Domínio do `codebase-memory-mcp` em Subgrafos Federados
*   **Ação:** Estruturar particionamento lógico por domínio nos scripts de memória e indexação da base de código.
*   **Arquivos:** `componentes/compartilhado/src-core/`.
*   **DoD:** Resolução e consulta isoladas por bounded context sem contaminação global de grafo.
*   **Status:** [x] CONCLUÍDO (Commit `78bfd80`).

### Ticket 7: Escopo Preguiçoso e Poda de Contexto em Skills de Módulos
*   **Ação:** Aplicar poda dinâmica de contexto e carregamento sob demanda para skills locais de fatias.
*   **Arquivos:** `modulos/**/skills/`.
*   **DoD:** Otimização severa de consumo de tokens em execuções de subagentes locais.
*   **Status:** [x] CONCLUÍDO (Commit `d99382d`).
