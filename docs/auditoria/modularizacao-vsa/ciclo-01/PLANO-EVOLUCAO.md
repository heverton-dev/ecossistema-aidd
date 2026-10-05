# Plano de Evolução (Fase 2) - modularizacao-vsa

Este plano foi gerado pelo Arquiteto (Fase 2) do Pipeline Linear de Auditoria 4F, com o objetivo de readequar a arquitetura `modularizacao-vsa` em conformidade com o Laudo 15-D e a Definição de Pronto (DoD).

## Estratégia de Execução
Todos os tickets abaixo requerem ciclo TDD estrito (Red-Green-Refactor). Para cada requisito funcional, testes automatizados (exit 0 / exit 1) devem ser criados antes da implementação real. O isolamento deve ser estritamente mantido em Git Worktree efêmera.

### Ticket 1: Contrato Estrutural e Manifesto de Módulos (Refere-se a D1 / DoD 8)
- **Falha 15-D:** `D1. Contratos e Regras`
- **Artefato de Handoff:** `docs/padroes/contratos/manifesto_modulos.py`
- **Gate do Ticket:** `python -m pytest -q -p no:cacheprovider tests/test_vsa_manifesto_modulos.py`
- **Requisito TDD (Red):** Criar teste `tests/test_vsa_manifesto_modulos.py` que falha com exit 1 ao validar schema ou estrutura incompleta de módulos sem os 4 macro-domínios canônicos.
- **Implementação Técnica:**
  - Implementar validador determinístico do manifesto de módulos VSA em `docs/padroes/contratos/manifesto_modulos.py`.
  - Definir estrutura formal dos 4 macro-módulos: `01-governanca-e-qualidade`, `02-triade-motores`, `03-plataforma-e-entrega` e `04-nucleo-compartilhado`.
  - Rejeitar qualquer definição que viole a invariante dos 4 domínios canônicos.
- **Verificação (Green):** Teste `tests/test_vsa_manifesto_modulos.py` passa comprovando validação estrutural do manifesto.
- **Construtor Prompt (EN):**
  - Write test first in tests/test_vsa_manifesto_modulos.py. Assert exit 1 when macro-modules are missing or schema is invalid.
  - Implement docs/padroes/contratos/manifesto_modulos.py with strict schema and domain validator.
  - Enforce the 4 canonical macro-modules: 01-governanca-e-qualidade, 02-triade-motores, 03-plataforma-e-entrega, 04-nucleo-compartilhado.
  - Run pytest tests/test_vsa_manifesto_modulos.py. Assert exit 0.

### Ticket 2: CLI Fallback e Despacho Modular (Refere-se a D2 / DoD 1)
- **Falha 15-D:** `D2. Input e Gatilhos`
- **Artefato de Handoff:** `scripts/cli_modularizacao_vsa.py`
- **Gate do Ticket:** `python -m pytest -q -p no:cacheprovider tests/test_vsa_cli.py`
- **Requisito TDD (Red):** Executar `python ecossistema.py modularizacao-vsa --help` ou `python scripts/cli_modularizacao_vsa.py` falha com exit 1 por ausência de implementação do subcomando na CLI raiz.
- **Implementação Técnica:**
  - Implementar CLI autônoma em `scripts/cli_modularizacao_vsa.py` com subcomandos de inspeção, verificação de limites e status dos módulos.
  - Conectar subcomando `modularizacao-vsa` na CLI raiz `ecossistema.py` apontando para o despachante modular com lazy import.
  - Garantir compatibilidade agnóstica de execução via linha de comando.
- **Verificação (Green):** Teste `tests/test_vsa_cli.py` passa validando despacho via `ecossistema.py modularizacao-vsa` e `scripts/cli_modularizacao_vsa.py`.
- **Construtor Prompt (EN):**
  - Write test first in tests/test_vsa_cli.py. Assert exit 1 when python ecossistema.py modularizacao-vsa is missing.
  - Implement scripts/cli_modularizacao_vsa.py supporting inspect, verify, and status subcommands.
  - Register modularizacao-vsa subcommand in ecossistema.py with lazy import dispatch.
  - Run pytest tests/test_vsa_cli.py. Assert exit 0.

### Ticket 3: Isolamento de Raio de Impacto e Worktree Efêmera (Refere-se a D3 / DoD 2)
- **Falha 15-D:** `D3. Raio de Impacto e Isolamento`
- **Artefato de Handoff:** `scripts/isolamento_vsa.py`
- **Gate do Ticket:** `python -m pytest -q -p no:cacheprovider tests/test_vsa_isolamento.py`
- **Requisito TDD (Red):** Teste `tests/test_vsa_isolamento.py` falha com exit 1 se mutações em código de módulos ocorrerem fora de Git Worktree efêmera ou tocarem caminhos não autorizados.
- **Implementação Técnica:**
  - Implementar `scripts/isolamento_vsa.py` com gerenciador de contexto `VSAWorktreeContext`.
  - Garantir que operações de reestruturação física e movimentação ocorram isoladas em worktrees efêmeras.
  - Bloquear mutações em diretórios do repositório root sem worktree ativa.
- **Verificação (Green):** Teste `tests/test_vsa_isolamento.py` passa comprovando isolamento estrito de I/O em worktree.
- **Construtor Prompt (EN):**
  - Write test first in tests/test_vsa_isolamento.py. Assert exit 1 when mutations happen outside ephemeral Git Worktree.
  - Implement scripts/isolamento_vsa.py with VSAWorktreeContext manager.
  - Restrict write operations to isolated worktree directories.
  - Run pytest tests/test_vsa_isolamento.py. Assert exit 0.

### Ticket 4: Autocontenção Fractal e Verificação de Submódulos (Refere-se a D4 / DoD 1)
- **Falha 15-D:** `D4. Componentes e Fractalidade`
- **Artefato de Handoff:** `scripts/validador_fractalidade_vsa.py`
- **Gate do Ticket:** `python -m pytest -q -p no:cacheprovider tests/test_vsa_fractalidade.py`
- **Requisito TDD (Red):** Teste `tests/test_vsa_fractalidade.py` falha com exit 1 quando um submódulo de capacidade não contiver estrutura fractal completa (`core/`, `skills/`, `gates/`, `tests/`, `README.md`).
- **Implementação Técnica:**
  - Implementar validador determinístico de fractalidade em `scripts/validador_fractalidade_vsa.py`.
  - Inspecionar submódulos verticais garantindo que cada fatia possua estrutura autocontida com `README.md` (< 500 tokens).
  - Validar princípio fractal nos fluxos dos motores (`pure`, `open`, `freedom`).
- **Verificação (Green):** Teste `tests/test_vsa_fractalidade.py` passa validando invariantes fractais em fatias modulares.
- **Construtor Prompt (EN):**
  - Write test first in tests/test_vsa_fractalidade.py. Assert exit 1 when a slice lacks core, skills, gates, tests, or README.md.
  - Implement scripts/validador_fractalidade_vsa.py to check fractal self-containment.
  - Enforce README.md token budget under 500 tokens per slice.
  - Run pytest tests/test_vsa_fractalidade.py. Assert exit 0.

### Ticket 5: Motor Analítico Determinístico de Acoplamento (Refere-se a D8 / DoD 3)
- **Falha 15-D:** `D8. O que o Estágio Processa`
- **Artefato de Handoff:** `scripts/analisador_acoplamento_vsa.py`
- **Gate do Ticket:** `python -m pytest -q -p no:cacheprovider tests/test_vsa_analisador_acoplamento.py`
- **Requisito TDD (Red):** Teste `tests/test_vsa_analisador_acoplamento.py` falha com exit 1 ao processar AST de arquivo com chamadas proibidas ou retorno sem envelope de schema JSON estrito.
- **Implementação Técnica:**
  - Implementar motor analítico determinístico baseado em `ast` em `scripts/analisador_acoplamento_vsa.py`.
  - Mapear chamadas de importação e dependências entre ferramentas e módulos sem depender de inferência livre de LLM.
  - Envelopar saídas analíticas com JSON Schema estrito, rejeitando formatos não estruturados.
- **Verificação (Green):** Teste `tests/test_vsa_analisador_acoplamento.py` passa validando análise de AST e conformidade de schema.
- **Construtor Prompt (EN):**
  - Write test first in tests/test_vsa_analisador_acoplamento.py. Feed cross-module import AST. Assert exit 1 without strict JSON envelope.
  - Implement scripts/analisador_acoplamento_vsa.py using Python ast module.
  - Validate output against strict JSON Schema. Reject non-deterministic responses.
  - Run pytest tests/test_vsa_analisador_acoplamento.py. Assert exit 0.

### Ticket 6: Tratamento de Exceções e Resiliência Operacional (Refere-se a D11 / DoD 4)
- **Falha 15-D:** `D11. Tratamento de Exceções e Fallback`
- **Artefato de Handoff:** `scripts/resiliencia_vsa.py`
- **Gate do Ticket:** `python -m pytest -q -p no:cacheprovider tests/test_vsa_resiliencia.py`
- **Requisito TDD (Red):** Teste `tests/test_vsa_resiliencia.py` falha com exit 1 se falha transitória ou colisão de arquivos interromper abruptamente sem retry com backoff nem captura de estado.
- **Implementação Técnica:**
  - Implementar utilitário de execução resiliente em `scripts/resiliencia_vsa.py`.
  - Incorporar política de retries exponenciais determinísticos para operações de sincronização e I/O de módulos.
  - Registrar erros em arquivo de diagnóstico sem perder estado do pipeline.
- **Verificação (Green):** Teste `tests/test_vsa_resiliencia.py` passa validando recuperação graciosa e logs estruturados de retry.
- **Construtor Prompt (EN):**
  - Write test first in tests/test_vsa_resiliencia.py. Simulate transient I/O failure. Assert exit 1 when retry logic missing.
  - Implement scripts/resiliencia_vsa.py with exponential backoff and retry policy.
  - Log failures gracefully without state corruption.
  - Run pytest tests/test_vsa_resiliencia.py. Assert exit 0.

### Ticket 7: Observabilidade, Métricas e Orçamento de Tokens (Refere-se a D12 / DoD 5)
- **Falha 15-D:** `D12. Observabilidade e Frugalidade`
- **Artefato de Handoff:** `scripts/observabilidade_vsa.py`
- **Gate do Ticket:** `python -m pytest -q -p no:cacheprovider tests/test_vsa_observabilidade.py`
- **Requisito TDD (Red):** Teste `tests/test_vsa_observabilidade.py` falha com exit 1 se execução do validador VSA não persistir telemetria de métricas (tempo de execução, nós verificados e tokens de contexto).
- **Implementação Técnica:**
  - Implementar módulo de rastreamento de métricas em `scripts/observabilidade_vsa.py`.
  - Registrar duração de análise, contagem de fatias verificadas e orçamento estimado de tokens por módulo.
  - Gravar relatório de observabilidade estruturado em formato JSON padronizado.
- **Verificação (Green):** Teste `tests/test_vsa_observabilidade.py` passa confirmando emissão e persistência de métricas auditáveis.
- **Construtor Prompt (EN):**
  - Write test first in tests/test_vsa_observabilidade.py. Assert failure when telemetry metrics are not persisted.
  - Implement scripts/observabilidade_vsa.py tracking duration, verified slice count, and token budget.
  - Persist structured JSON telemetry report.
  - Run pytest tests/test_vsa_observabilidade.py. Assert exit 0.

### Ticket 8: Quality Gate Determinístico de Fronteira VSA (Refere-se a D13 / DoD 6)
- **Falha 15-D:** `D13. Quality Gates (Portões)`
- **Artefato de Handoff:** `gates/G_modularizacao_vsa.py`
- **Gate do Ticket:** `python -m pytest -q -p no:cacheprovider tests/test_g_modularizacao_vsa.py`
- **Requisito TDD (Red):** Submeter código violando fronteiras verticais ou com afirmações ilusórias; `gates/G_modularizacao_vsa.py` deve falhar (exit 1). Submeter conformidade deve passar (exit 0).
- **Implementação Técnica:**
  - Desenvolver o Quality Gate determinístico `gates/G_modularizacao_vsa.py`.
  - Implementar verificação sintática via AST bloqueando importações cruzadas não autorizadas entre fatias verticais sem passar pela API pública (`interface.py` / `__all__`).
  - Assegurar saída estritamente binária (exit 0 / exit 1) cumprindo Lei #8 e Lei #13.
- **Verificação (Green):** Teste `tests/test_g_modularizacao_vsa.py` passa validando que o portão morde em violações e aprova saídas limpas.
- **Construtor Prompt (EN):**
  - Write test first in tests/test_g_modularizacao_vsa.py. Submit cross-boundary illegal import. Assert exit 1.
  - Implement gates/G_modularizacao_vsa.py checking AST import barriers between vertical slices.
  - Enforce binary exit 0 on clean code and exit 1 on unauthorized coupling.
  - Run pytest tests/test_g_modularizacao_vsa.py. Assert exit 0.

### Ticket 9: Limpeza Determinística e Rollback Transacional (Refere-se a D14 / DoD 7)
- **Falha 15-D:** `D14. Critério de Rejeição (Rollback)`
- **Artefato de Handoff:** `scripts/rollback_vsa.py`
- **Gate do Ticket:** `python -m pytest -q -p no:cacheprovider tests/test_vsa_rollback.py`
- **Requisito TDD (Red):** Injetar crash proposital durante operação de reestruturação modular; teste `tests/test_vsa_rollback.py` falha se resíduos temporários sobreviverem em disco.
- **Implementação Técnica:**
  - Implementar gerenciador transacional `TransacaoModularVSA` em `scripts/rollback_vsa.py`.
  - Registrar todas as criações e alterações de arquivos em pilha transacional.
  - Reverter integralmente o workspace e limpar arquivos órfãos em caso de saída não-zero (`exit 1`) ou exceção.
- **Verificação (Green):** Teste `tests/test_vsa_rollback.py` passa provando descarte de resíduos e restauração do workspace.
- **Construtor Prompt (EN):**
  - Write test first in tests/test_vsa_rollback.py. Inject failure mid-restructure. Fail if temp files survive.
  - Implement scripts/rollback_vsa.py with TransacaoModularVSA context manager.
  - Roll back file modifications and delete partial artifacts upon non-zero exit or exception.
  - Run pytest tests/test_vsa_rollback.py. Assert exit 0.

### Ticket 10: Output Consolidado e Handoff Estruturado (Refere-se a D15 / DoD 8)
- **Falha 15-D:** `D15. Output Consolidado e Handoff`
- **Artefato de Handoff:** `docs/auditoria/modularizacao-vsa/ciclo-01/MANIFESTO-VSA-MODULOS.json`
- **Gate do Ticket:** `python -m pytest -q -p no:cacheprovider tests/test_vsa_handoff.py`
- **Requisito TDD (Red):** Testar pipeline de modularização e falhar com exit 1 na ausência de emissão ou validação criptográfica do manifesto de handoff.
- **Implementação Técnica:**
  - Implementar emissor e assinador estruturado em `scripts/handoff_vsa.py`.
  - Produzir `docs/auditoria/modularizacao-vsa/ciclo-01/MANIFESTO-VSA-MODULOS.json` com mapa das fatias, hashes SHA-256 e status das dimensões 15-D.
  - Validar integridade e assinatura do manifesto para consumo seguro pelas etapas seguintes da auditoria.
- **Verificação (Green):** Teste `tests/test_vsa_handoff.py` passa confirmando emissão e integridade do manifesto de handoff.
- **Construtor Prompt (EN):**
  - Write test first in tests/test_vsa_handoff.py. Assert exit 1 when handoff manifest is missing or altered.
  - Implement scripts/handoff_vsa.py to produce and sign docs/auditoria/modularizacao-vsa/ciclo-01/MANIFESTO-VSA-MODULOS.json.
  - Include slice mapping, SHA-256 hashes, and 15-D dimension status in manifest.
  - Run pytest tests/test_vsa_handoff.py. Assert exit 0.
