# Plano de Evolução (Fase 2) - aidd-diagnose

Este plano foi gerado pelo Arquiteto (Fase 2) do Pipeline Linear de Auditoria 4F, com o objetivo de readequar a ferramenta `aidd-diagnose` em conformidade com o Laudo 15-D (`LAUDO-15D-INICIAL.md`, nota 4/10) e a Definição de Pronto (`DOD.md`).

## Estratégia de Execução
Todos os tickets abaixo requerem ciclo TDD estrito (Red-Green-Refactor). Para cada requisito funcional, testes automatizados (exit 0 / exit 1) devem ser criados antes da implementação real. Toda alteração no `SKILL.md` é feita na fonte `componentes/compartilhado/skills/aidd-diagnose/SKILL.md` e propagada pelo mecanismo oficial; `python gates/G_HARNESS_COMPAT.py` deve continuar com exit 0.

### Ticket 1: CLI Determinística e Contrato de Entrada (Refere-se a D2 / DoD 1)
- **Falha 15-D:** `D2. Input e Gatilhos`
- **Artefato de Handoff:** `.agents/skills/aidd-diagnose/scripts/cli.py`
- **Requisito TDD (Red):** `python ecossistema.py diagnose iniciar --sintoma "x"` hoje retorna exit 1 ("comando desconhecido"); o teste deve exigir exit 0 e a criação de uma sessão de diagnóstico em disco.
- **Implementação Técnica:**
  - Criar `.agents/skills/aidd-diagnose/scripts/cli.py` com os subcomandos `iniciar --sintoma <texto>` e `fase --numero <1-5>`, gravando o estado em `docs/diagnosticos/<data>_<slug>/sessao.json`.
  - Registrar `diagnose` em `ecossistema.py` delegando para esse script (mesmo padrão do `melhoria`).
  - Recusar `fase N` se a fase N-1 não estiver registrada como concluída (exit 1).
- **Verificação (Green):** CLI cria a sessão, avança fase a fase e reprova salto de fase com exit 1.
- **Construtor Prompt (EN):**
  - Create .agents/skills/aidd-diagnose/scripts/cli.py.
  - Add subcommand: iniciar --sintoma <text>. Write docs/diagnosticos/<date>_<slug>/sessao.json.
  - Add subcommand: fase --numero <1-5>. Reject phase N when phase N-1 not done. Exit 1.
  - Register command diagnose in ecossistema.py. Mirror melhoria delegation pattern.
  - Test: python ecossistema.py diagnose iniciar --sintoma "x". Assert exit 0. Assert sessao.json exists.
  - Test: skip phase. Assert exit 1.

### Ticket 2: Isolamento da Instrumentação em Worktree (Refere-se a D3 / DoD 2)
- **Falha 15-D:** `D3. Raio de Impacto e Isolamento`
- **Artefato de Handoff:** `.agents/skills/aidd-diagnose/scripts/isolamento.py`
- **Requisito TDD (Red):** Teste que reprova (exit 1) se a instrumentação temporária da Fase 4 for escrita no working tree principal em vez de uma Git Worktree efêmera.
- **Implementação Técnica:**
  - Criar a worktree efêmera `../worktrees_diagnose-<slug>/` ao entrar na Fase 4 e removê-la ao sair.
  - Bloquear escrita fora da worktree, exceto em `docs/diagnosticos/`.
  - Reaproveitar a lógica já testada de `.agents/skills/aidd-melhoria/scripts/isolamento.py` em vez de reescrever (DRY).
- **Verificação (Green):** A instrumentação só existe dentro da worktree; o repositório principal fica com `git status` limpo.
- **Construtor Prompt (EN):**
  - Create .agents/skills/aidd-diagnose/scripts/isolamento.py.
  - On phase 4 entry create ephemeral worktree ../worktrees_diagnose-<slug>/. Remove on exit.
  - Block writes outside worktree. Allow only docs/diagnosticos/.
  - Reuse .agents/skills/aidd-melhoria/scripts/isolamento.py logic. No copy-paste duplication.
  - Test: write instrumentation in main working tree. Assert exit 1.
  - Test: after phase 4 main tree git status clean. Assert exit 0.

### Ticket 3: Detecção de Grafo Desatualizado (Refere-se a D8 / DoD 3)
- **Falha 15-D:** `D8. O que o Estágio Processa`
- **Artefato de Handoff:** `.agents/skills/aidd-diagnose/scripts/cobertura_grafo.py`
- **Requisito TDD (Red):** Com o grafo de 2026-09-23, `get_impact_radius_tool(changed_files=["scripts/scaffold_auditoria.py"])` devolve `status: ok` com "0 nodes impacted" (158 de 1734 `.py` versionados sem nó). O teste deve reprovar quando um arquivo versionado sem nó no `.code-review-graph/graph.db` é tratado como "sem impacto".
- **Implementação Técnica:**
  - Antes da Fase 2, checar cada arquivo suspeito com `query_graph_tool(pattern="file_summary", target=<arquivo>)`; 0 resultados = grafo desatualizado para esse arquivo.
  - Com grafo desatualizado, rodar `code-review-graph update --repo .` uma vez; se continuar sem nó, marcar a Fase 2 como `fallback` (Ticket 4).
  - Investigar e registrar em `docs/diagnosticos/` a causa-raiz dos arquivos ausentes (update incremental vs `code-review-graph build` completo, com contagem antes/depois). Não alterar o pacote em site-packages.
  - Atualizar a Fase 2 do `SKILL.md` com essa checagem.
- **Verificação (Green):** Arquivo fora do grafo nunca sai como "0 impactados"; sai como "grafo desatualizado → fallback".
- **Construtor Prompt (EN):**
  - Create .agents/skills/aidd-diagnose/scripts/cobertura_grafo.py.
  - Before phase 2 query each suspect file: query_graph_tool(pattern="file_summary", target=<file>).
  - Zero results: mark graph stale for file. Run code-review-graph update --repo . once. Recheck.
  - Still zero: mark phase 2 mode fallback. Hand off to ticket 4 fallback.
  - Never report "0 impacted" for file without graph nodes.
  - Measure missing tracked .py files in .code-review-graph/graph.db before and after update and full build. Record counts and root cause in docs/diagnosticos/.
  - Do not modify site-packages.
  - Update phase 2 of componentes/compartilhado/skills/aidd-diagnose/SKILL.md. Propagate via official sync. Run python gates/G_HARNESS_COMPAT.py. Assert exit 0.

### Ticket 4: Fallback Operacional sem MCP (Refere-se a D11 / DoD 4)
- **Falha 15-D:** `D11. Tratamento de Exceções e Fallback`
- **Artefato de Handoff:** `.agents/skills/aidd-diagnose/scripts/fallback.py`
- **Requisito TDD (Red):** Simular MCP `code-review-graph` indisponível (reproduzido em 2026-09-23: `CONNECT_TIMEOUT ... after 30000ms`); hoje a Fase 2 não tem caminho alternativo e o teste deve reprovar.
- **Implementação Técnica:**
  - Retry com backoff na conexão ao MCP (o servidor sobe em ~11,3 s a frio).
  - Fallback Grep/Glob/Read: callers = busca pelo nome da função; callees = leitura do corpo; impacto = busca de imports do arquivo.
  - Registrar na sessão que a Fase 2 rodou em modo `fallback`.
  - Atualizar a Fase 2 do `SKILL.md` com o bloco "Fallback (MCP indisponível)", no mesmo espírito de `componentes/compartilhado/comandos/melhoria.md`.
- **Verificação (Green):** Com o MCP derrubado, a Fase 2 conclui via fallback e a sessão registra o modo usado.
- **Construtor Prompt (EN):**
  - Create .agents/skills/aidd-diagnose/scripts/fallback.py.
  - Retry MCP code-review-graph connection with backoff. Cold start takes about 11 s.
  - On failure use Grep/Glob/Read: callers by function name search, callees by body read, impact by import search.
  - Record phase 2 mode fallback in sessao.json.
  - Add block "Fallback (MCP unavailable)" to phase 2 of componentes/compartilhado/skills/aidd-diagnose/SKILL.md. Follow componentes/compartilhado/comandos/melhoria.md wording.
  - Test: simulate MCP down. Assert phase 2 completes via fallback. Assert mode recorded.

### Ticket 5: Relatório de Causa-Raiz e Observabilidade (Refere-se a D12 / DoD 5)
- **Falha 15-D:** `D12. Observabilidade e Frugalidade`
- **Artefato de Handoff:** `.agents/skills/aidd-diagnose/scripts/observabilidade.py`
- **Requisito TDD (Red):** Após um diagnóstico completo não existe nenhum arquivo com hipóteses, provas e tempos; o teste deve reprovar a ausência de `docs/diagnosticos/<data>_<slug>/RELATORIO-CAUSA-RAIZ.md`.
- **Implementação Técnica:**
  - Registrar por fase: início, fim, duração, comando de reprodução, hipóteses formuladas, hipóteses descartadas com a prova, e modo da Fase 2 (grafo ou fallback).
  - Gerar `RELATORIO-CAUSA-RAIZ.md` ao fim da Fase 5.
  - Reaproveitar `.agents/skills/aidd-melhoria/scripts/observabilidade.py` quando couber (DRY).
- **Verificação (Green):** O relatório existe e contém todas as fases com tempos e hipóteses.
- **Construtor Prompt (EN):**
  - Create .agents/skills/aidd-diagnose/scripts/observabilidade.py.
  - Log per phase: start, end, duration, repro command, hypotheses, discarded hypotheses with proof, phase 2 mode.
  - On phase 5 end write docs/diagnosticos/<date>_<slug>/RELATORIO-CAUSA-RAIZ.md.
  - Reuse .agents/skills/aidd-melhoria/scripts/observabilidade.py where it fits.
  - Test: full run without report. Assert exit 1. Full run with report. Assert all phases present.

### Ticket 6: Quality Gate Próprio e Rótulo Honesto (Refere-se a D13 / DoD 6)
- **Falha 15-D:** `D13. Quality Gates (Portões)`
- **Artefato de Handoff:** `gates/G_aidd_diagnose.py`
- **Requisito TDD (Red):** Relatório de causa-raiz sem comando de reprodução, com mais de uma hipótese ativa ao mesmo tempo, ou sem teste de regressão que falhou antes da correção deve fazer `gates/G_aidd_diagnose.py` reprovar (exit 1).
- **Implementação Técnica:**
  - Criar `gates/G_aidd_diagnose.py` e `gates/test_g_aidd_diagnose.py` (com asserção de exit 1, exigida pelo `G_PORTAO_PROVA_QUE_MORDE`).
  - O gate valida: comando de reprodução rodado N vezes com o mesmo resultado; uma hipótese ativa por vez; teste de regressão presente, com falha registrada antes do fix e passagem depois.
  - Corrigir a documentação que liga o aidd-diagnose ao `G_PORTAO_PROVA_QUE_MORDE` (`docs/auditoria/historico_auditorias/matriz_exaustiva_66_skills_e_48_gates.md:21`, `docs/auditoria/historico_auditorias/micro-ferramentas-evolucao-2026-09-22.md:18`, entrada `aidd-diagnose` de `catalogo_micro_ferramentas_e_gates.json`) e remover a promessa de `--fase <1-5>` se o Ticket 1 não a entregar nesse formato.
  - Documentar o gate novo em `AGENTS.md`.
- **Verificação (Green):** O gate aprova um relatório correto (exit 0) e barra os 3 casos inválidos (exit 1).
- **Construtor Prompt (EN):**
  - Create gates/G_aidd_diagnose.py and gates/test_g_aidd_diagnose.py.
  - Gate checks root cause report: repro command ran N times with same result; one active hypothesis at a time; regression test failed before fix and passed after.
  - Bite tests: missing repro, two active hypotheses, missing regression test. Each asserts exit 1.
  - Fix docs linking aidd-diagnose to G_PORTAO_PROVA_QUE_MORDE: docs/auditoria/historico_auditorias/matriz_exaustiva_66_skills_e_48_gates.md line 21, docs/auditoria/historico_auditorias/micro-ferramentas-evolucao-2026-09-22.md line 18, entry aidd-diagnose in docs/auditoria/historico_auditorias/catalogo_micro_ferramentas_e_gates.json.
  - Remove --fase <1-5> promise unless ticket 1 ships it.
  - Document new gate in AGENTS.md.
  - Run python gates/G_PORTAO_PROVA_QUE_MORDE.py. Assert exit 0.

### Ticket 7: Limpeza da Instrumentação e Rollback (Refere-se a D14 / DoD 7)
- **Falha 15-D:** `D14. Critério de Rejeição (Rollback)`
- **Artefato de Handoff:** `.agents/skills/aidd-diagnose/scripts/rollback.py`
- **Requisito TDD (Red):** Injetar uma linha marcada com `AIDD-DIAGNOSE-TEMP` e encerrar a Fase 5; se a linha sobreviver no diff, o teste deve reprovar.
- **Implementação Técnica:**
  - Toda instrumentação temporária da Fase 4 leva o marcador `AIDD-DIAGNOSE-TEMP`.
  - Ao fim da Fase 5 (ou em exceção), varrer o diff, remover o que tiver o marcador e descartar a worktree do Ticket 2.
  - Em qualquer saída não-zero, não deixar arquivo parcial em `docs/diagnosticos/`.
- **Verificação (Green):** Após sucesso ou crash no meio, `git diff` não contém `AIDD-DIAGNOSE-TEMP` e não há arquivo parcial.
- **Construtor Prompt (EN):**
  - Create .agents/skills/aidd-diagnose/scripts/rollback.py.
  - Tag every temporary phase 4 line with marker AIDD-DIAGNOSE-TEMP.
  - On phase 5 end or exception: scan diff, strip marked lines, drop ticket 2 worktree.
  - On non-zero exit leave zero partial files in docs/diagnosticos/.
  - Test: inject marked line, finish phase 5. Assert git diff has no marker.
  - Test: crash mid-run. Assert zero partial files.

### Ticket 8: Output Consolidado e Handoff Estruturado (Refere-se a D10 / D15 / DoD 8)
- **Falha 15-D:** `D15. Output Consolidado e Handoff`
- **Artefato de Handoff:** `.agents/skills/aidd-diagnose/scripts/handoff.py`
- **Requisito TDD (Red):** Após um diagnóstico completo não existe `handoff-diagnose.json`; o teste deve reprovar a transição para a próxima ferramenta.
- **Implementação Técnica:**
  - Emitir `docs/diagnosticos/<data>_<slug>/handoff-diagnose.json` com causa-raiz, arquivos alterados, teste de regressão, status do `G_aidd_diagnose` e próxima ferramenta sugerida (`aidd-tdd` ou `aidd-handoff`).
  - Persistir o estado entre as fases em `sessao.json` (Ticket 1), resolvendo também o D10 (hoje os dados passam só pela conversa).
  - Reaproveitar `.agents/skills/aidd-melhoria/scripts/handoff.py` quando couber (DRY).
- **Verificação (Green):** `handoff-diagnose.json` emitido e válido, habilitando o orquestrador a consumir o resultado.
- **Construtor Prompt (EN):**
  - Create .agents/skills/aidd-diagnose/scripts/handoff.py.
  - Emit docs/diagnosticos/<date>_<slug>/handoff-diagnose.json: root cause, changed files, regression test, G_aidd_diagnose status, next tool (aidd-tdd or aidd-handoff).
  - Persist state between phases in sessao.json from ticket 1.
  - Reuse .agents/skills/aidd-melhoria/scripts/handoff.py where it fits.
  - Test: full run without handoff file. Assert exit 1. With file. Assert valid JSON.
