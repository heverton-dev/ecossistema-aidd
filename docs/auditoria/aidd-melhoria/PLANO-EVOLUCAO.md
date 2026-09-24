# Plano de Evolução (Fase 2) - aidd-melhoria

Este plano foi gerado pelo Arquiteto (Fase 2) do Pipeline Linear de Auditoria 4F, com o objetivo de readequar a ferramenta `aidd-melhoria` em conformidade com o Laudo 15-D e a Definição de Pronto (DoD).

## Estratégia de Execução
Todos os tickets abaixo requerem ciclo TDD estrito (Red-Green-Refactor). Para cada requisito funcional, testes automatizados (exit 0 / exit 1) devem ser criados antes da implementação real.

### Ticket 1: Isolamento de Raio de Impacto e Worktree (Refere-se a D3 / DoD 5)
- **Falha 15-D:** `D3. Raio de Impacto e Isolamento`
- **Artefato de Handoff:** `.agents/skills/aidd-melhoria/scripts/isolamento.py`
- **Requisito TDD (Red):** Criar um teste que reprove (exit 1) se a ferramenta tentar modificar arquivos fora da pasta `docs/` ou fora de uma Git Worktree efêmera isolada.
- **Implementação Técnica:**
  - Codificar rotina na infraestrutura da skill (`.agents/skills/aidd-melhoria/scripts/`) para realizar a análise dentro de um VSA (Git Worktree isolado).
  - Bloquear acessos de I/O de escrita no repositório root (exceção para `docs/melhorias/`).
- **Verificação (Green):** Teste de ambiente passa após garantir a sandboxing de execução.
- **Construtor Prompt (EN):**
  - Write test first: fail with exit 1 when tool writes outside docs/ or outside ephemeral Git Worktree.
  - Implement .agents/skills/aidd-melhoria/scripts/isolamento.py. Run analysis inside isolated Git Worktree.
  - Block write I/O on repo root. Allow only docs/melhorias/.
  - Run tests/test_melhoria_isolamento.py. Assert exit 0.

### Ticket 2: Componentes, Fractalidade e CLI Fallback (Refere-se a D4 / DoD 1)
- **Falha 15-D:** `D4. Componentes e Fractalidade`
- **Artefato de Handoff:** `.agents/skills/aidd-melhoria/scripts/cli.py`
- **Requisito TDD (Red):** Executar `python ecossistema.py melhoria --manifest dummy.json` deve falhar por falta de implementação do fallback CLI.
- **Implementação Técnica:**
  - Estruturar a skill com micro-skills ou scripts locais em Python em vez de apenas prompts no `.agents`.
  - Integrar a interface CLI `ecossistema.py melhoria --manifest <json>` mapeando a entrada para acionar a pipeline da ferramenta, sem depender unicamente de interpretação de prompt de chat.
- **Verificação (Green):** Execução do CLI retorna sucesso e processo o manifesto de entrada adequadamente.
- **Construtor Prompt (EN):**
  - Write test first: python ecossistema.py melhoria --manifest dummy.json must fail while CLI fallback missing.
  - Implement .agents/skills/aidd-melhoria/scripts/cli.py. Use local Python scripts, not chat-prompt-only logic.
  - Wire ecossistema.py melhoria --manifest <json> to run tool pipeline.
  - Run tests/test_melhoria_cli_manifest.py. Assert exit 0 and manifest processed.

### Ticket 3: Processamento Analítico Determinístico (Refere-se a D8 / DoD 4)
- **Falha 15-D:** `D8. O que o Estágio Processa`
- **Artefato de Handoff:** `.agents/skills/aidd-melhoria/scripts/analisador.py`
- **Requisito TDD (Red):** Testar parser JSON do motor analítico com resposta malformada ou texto puro para confirmar crash esperado (exit 1).
- **Implementação Técnica:**
  - Substituir o processamento dependente 100% de LLM de bate-papo por um motor determinístico interno.
  - A consulta à LLM (para classificar/sugerir melhorias) DEVE ser envelopada em JSON Schema Estrito, rejeitando respostas não estruturadas e extraindo o relatório de forma serializável (ex: `{"relatorio": "..."}`).
- **Verificação (Green):** A resposta passa pelo validador JSON interno antes de prosseguir.
- **Construtor Prompt (EN):**
  - Write test first: feed malformed JSON or plain text to analytic parser. Assert exit 1.
  - Implement .agents/skills/aidd-melhoria/scripts/analisador.py. Replace chat-only processing with deterministic engine.
  - Wrap LLM call in strict JSON Schema. Reject unstructured replies. Extract serializable report, e.g. {"relatorio": "..."}.
  - Run tests/test_melhoria_motor_deterministico.py. Assert exit 0.

### Ticket 4: Tratamento de Exceções e Fallback Operacional (Refere-se a D11)
- **Falha 15-D:** `D11. Tratamento de Exceções e Fallback`
- **Artefato de Handoff:** `.agents/skills/aidd-melhoria/scripts/fallback.py`
- **Requisito TDD (Red):** Simular falha na leitura de manifesto ou timeout na LLM; o sistema deve propagar erro abrupto no estado atual.
- **Implementação Técnica:**
  - Implementar lógica de retry backoff autônomo.
  - Criar fallbacks de resposta gracefully e interrupção do pipeline no código Python do `aidd-melhoria`, documentando a falha sem perder o estado.
- **Verificação (Green):** Os testes de stress/falha mostram os logs de fallback/retry sendo acionados.
- **Construtor Prompt (EN):**
  - Write test first: simulate manifest read failure or LLM timeout. Current code must crash abruptly.
  - Implement .agents/skills/aidd-melhoria/scripts/fallback.py. Add autonomous retry with backoff.
  - Add graceful fallback and pipeline stop. Record failure without losing state.
  - Run tests/test_melhoria_excecoes_fallback.py. Assert retry and fallback logs appear.

### Ticket 5: Observabilidade e Frugalidade (Refere-se a D12)
- **Falha 15-D:** `D12. Observabilidade e Frugalidade`
- **Artefato de Handoff:** `.agents/skills/aidd-melhoria/scripts/observabilidade.py`
- **Requisito TDD (Red):** Testar a ausência de emissão de logs ou métricas pós-execução (falha esperada de conformidade).
- **Implementação Técnica:**
  - Instrumentar scripts da skill para logar orçamentos de tokens usados (fictício/estimado ou real se API for usada) ou tempo de execução.
  - O log deverá ser padronizado e gravado em `secoes/` ou exposto em console durante a execução do processo via CLI.
- **Verificação (Green):** Artefatos de log persistem com os metadados solicitados ao fim da execução.
- **Construtor Prompt (EN):**
  - Write test first: assert failure when run emits no logs or metrics.
  - Implement .agents/skills/aidd-melhoria/scripts/observabilidade.py. Log token budget (estimated or real) and run time.
  - Write standardized log to secoes/ or print it during CLI run.
  - Run tests/test_melhoria_observabilidade.py. Assert log artifacts persist with required metadata.

### Ticket 6: Quality Gates Determinísticos e Rótulo Honesto (Refere-se a D13 / DoD 3 / DoD 6)
- **Falha 15-D:** `D13. Quality Gates (Portões)`
- **Artefato de Handoff:** `gates/G_amelhoria.py`
- **Requisito TDD (Red):** Submeter saída onde o relatório afirme "Refatoração concluída"; `gates/G_amelhoria.py` deve falhar (exit 1).
- **Implementação Técnica:**
  - Desenvolver o Quality Gate `gates/G_amelhoria.py`.
  - Este portão validará a presença de "Sugestão de refatoração..." (honesto), vetando afirmações imperativas ilusórias. Validação via regex ou parse de texto.
  - O portão deve integrar-se na barreira de saída da CLI.
- **Verificação (Green):** Teste do gate passa (exit 0) ao inspecionar relatórios corretos e barra (exit 1) afirmações não validadas.
- **Construtor Prompt (EN):**
  - Write test first: submit output claiming refactor done. gates/G_amelhoria.py must exit 1.
  - Implement gates/G_amelhoria.py. Require honest wording (refactor suggestion). Reject unverified imperative claims via regex or text parse.
  - Hook gate into CLI output barrier.
  - Run gate test. Assert exit 0 on valid reports. Assert exit 1 on unverified claims.

### Ticket 7: Critério de Rejeição, Limpeza e Rollback (Refere-se a D14)
- **Falha 15-D:** `D14. Critério de Rejeição (Rollback)`
- **Artefato de Handoff:** `.agents/skills/aidd-melhoria/scripts/rollback.py`
- **Requisito TDD (Red):** Injetar um erro no meio da análise (ex. parser crash). Se os arquivos intermediários permanecem em disco, o teste deve reprovar.
- **Implementação Técnica:**
  - Estabelecer a rotina `finally` ou context manager no motor Python.
  - Em caso de saída não-zero (`exit 1`), o código DEVE excluir artefatos parciais (limpeza) e reverter mudanças de ambiente (rollback).
- **Verificação (Green):** O crash no meio do processo deixa zero rastro temporário ou corrupção no repositório.
- **Construtor Prompt (EN):**
  - Write test first: inject parser crash mid-analysis. Fail if intermediate files remain on disk.
  - Implement .agents/skills/aidd-melhoria/scripts/rollback.py. Use finally block or context manager.
  - On non-zero exit delete partial artifacts and revert environment changes.
  - Run tests/test_melhoria_rollback.py. Assert crash leaves zero temp files or corruption.

### Ticket 8: Output Consolidado e Handoff Estruturado (Refere-se a D15 / DoD 2 / DoD 7 / DoD 8)
- **Falha 15-D:** `D15. Output Consolidado e Handoff`
- **Artefato de Handoff:** `docs/teste-end-to-end/aidd-melhoria.md`
- **Requisito TDD (Red):** Testar pipeline com execução completa e checar ausência do `./handoff-melhoria.json` (deve falhar a transição).
- **Implementação Técnica:**
  - Alterar o final da execução da skill para produzir e assinar estruturadamente o artefato `./handoff-melhoria.json`, relatando sucesso ou falha.
  - Atualizar/gerar `docs/teste-end-to-end/aidd-melhoria.md` comprovando o fluxo (Ciclo de 5 passos).
  - Incluir no PR de entrega a justificativa técnica obrigatória de que `aidd-melhoria` não terá Quarteto Sine Qua Non por ser ferramenta CLI sem servidor/UI.
- **Verificação (Green):** `handoff-melhoria.json` emitido corretamente, habilitando o pipeline (orchestrator) a consumir e transitar de fase.
- **Construtor Prompt (EN):**
  - Write test first: run full pipeline. Fail transition when ./handoff-melhoria.json missing.
  - Emit and sign structured ./handoff-melhoria.json at end of run, reporting success or failure.
  - Create or update docs/teste-end-to-end/aidd-melhoria.md proving 5-step cycle.
  - Add PR justification: aidd-melhoria has no Quarteto Sine Qua Non; CLI tool without server or UI.
  - Run tests/test_melhoria_handoff.py. Assert handoff emitted and consumable by orchestrator.
