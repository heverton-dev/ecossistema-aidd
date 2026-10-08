# Prompt de continuação — modularização VSA ciclo-03

Sessão nova: continuar o plano APROVADO do ciclo-03 da modularização VSA no ecossistema-aidd, a partir do próximo bloco pendente.

ESTADO (atualizado a cada bloco)
- Bloco 1 (Tickets 1–2): CONCLUÍDO e mergeado na main por fast-forward em e78ecdd (sem push). gate_final `python ecossistema.py audit` com exit 0, 64 gates, 1302 s.
- Linha de base de testes do ciclo: 3463 passando, 0 falhas, 13 pulados (G_TESTES_REAIS em AIDD_GATES_MODO=completo, 8 ferramentas + tests/). Gravada em ciclo-03/DIVERGENCIAS-TOOLS-MODULOS.json.
- Medido no Bloco 1: 28 arquivos divergentes tools x modulos, 31 só em tools (26 do planner + 5 .cursorrules de materiais-extras/examples do enterprise). G_COPIA_UNICA_VSA (aviso): 7 ferramentas, 97 gates (70 raiz x fatia), 4 skills.
- Bloco 2 (Tickets 3–6 + T16 antecipado): CONCLUÍDO e mergeado na main por fast-forward em bc73ec28 (sem push). gate_final `python ecossistema.py audit` com exit 0, 64 gates, 34m22s.
  - Commits: 1461b88a (T16), a5af9f18 (fix GIT_DIR), e679d7ad (T3), 501803f7 (T4), 1580f893 (T5), bc73ec28 (T6).
  - T5: tools/aidd-* removido (1860 arquivos); bateria completa 3477 passando, 0 falhas (baseline 3463).
  - T6: materiais-extras/ do enterprise arquivada em C:\Users\trcnologia\arquivo-historico\aidd-enterprise-materiais-extras (635/635) e removida; sandbox-forge-teste/, _destino_teste_almoxarifado e output-clinica/.aidd/cache removidos; 5 secoes/ internas movidas para docs/secoes/; 18 cascas só com __init__.py removidas; 60 entradas mortas saíram de gates/allowlist_fronteira.json e 8 cópias de CATALOGO.json.
  - Antes do merge, 7 arquivos gerados não commitados da outra sessão na main foram guardados em `git stash` ("outra-sessao: mapas gerados antes do merge VSA bloco 2"): catalogo-pecas.json e mapa-02/03/11 (técnico e não técnico). NÃO aplicar nem descartar sem perguntar ao usuário.
  - Worktree C:/Users/trcnologia/Desktop/aidd-wt/vsa-c03-bloco-2 e a branch só saem com confirmação do usuário.
- Bloco 3 (Tickets 7–9): CONCLUÍDO e mergeado na main por fast-forward em 4d8525d1 (sem push). gate_final `python ecossistema.py audit` com exit 0, 64 gates, 21m26s (G_SEGREDOS 6m40s, G_TESTES_REAIS 13m03s).
  - Commits: f369ecc9 (T7), 2e0e2722 (T8), 4d8525d1 (T9).
  - T7: MAPA-GATES.json em modulos/04-nucleo-compartilhado/contracts (72 gates, dono + caminho); leitor scripts/mapa_gates.py (verificar/sincronizar o .pre-commit-config.yaml); audit legado, G_SAIDA_BINARIA e G_PORTAO_PROVA_QUE_MORDE leem o mapa.
  - T8: gates/ da raiz extinta; 71 gates + testes na fatia dona, 146 cópias apagadas; helpers em 04/gates; allowlist_fronteira, manifesto_harnesses, dependencias_externas, allowlist_orfaos e baseline_nucleo em 04/contracts. Raiz de cada gate = pai de modulos/ (ou de gates/ em árvore sintética de teste). Decisão do usuário (07/10): G_COPIA_UNICA_VSA trata como peça os moldes de projeto (aidd_forge/templates/**, componentes/compartilhado/gates|injetor/**) e a evidência de docs/auditoria/**; gate interno do master renomeado para G_AST_IMPORT_GUARD. Bloqueio: 0 violações. Bateria: 8 ferramentas 2423 passed + tests 1121 passed.
  - T9: G_SEGREDOS usa cópia temporária da baseline (não regrava mais); atualizar = `python scripts/atualizar_baseline_segredos.py`.
  - Worktree C:/Users/trcnologia/Desktop/aidd-wt/vsa-c03-bloco-3 e a branch só saem com confirmação do usuário.
- Bloco 4 (Tickets 10–12): CONCLUÍDO e mergeado na main por fast-forward em 36c3c148 (sem push). gate_final `python ecossistema.py audit` com exit 0, 65 gates, 24m26s (G_SEGREDOS 6m38s, G_TESTES_REAIS 14m37s).
  - Commits: e9b790f9 (fix: atualizar_baseline_segredos estourava a linha de comando no Windows, WinError 206), 462532b0 (T10), d84bd472 (T11), 44267cd4 (T12), 52534f1c (registro do Ticket 23), 36c3c148 (fix pós-gate_final do T10).
  - T10: `interface.py` com `__all__` nas 7 fatias; fonte única das fatias em modulos/04-nucleo-compartilhado/contracts/MAPA-FATIAS.json. Decisão do usuário (07/10, opção B): caixas de layout `src`, `scripts`, `tests` não contam. Renomeados: planner `src/core`→`src/core_planner`, pure `scripts/core`→`scripts/core_pure`, open `src/core`→`src/core_open` e `scripts/phases`→`scripts/phases_open`, ops `src/core`→`src/core_ops` e `scripts/phases`→`scripts/phases_ops`. `allowlist_pacotes_repetidos.json` só com a cópia enterprise × master (alembic, application, core, modules, shared).
  - T11: `G_MODULO_FRONTEIRA` (04/gates) em modo aviso no pre-commit; `allowlist_modulo_fronteira.json` com teto 52 (só diminui; teto não pode subir acima do HEAD); variável AIDD_MODULO_FRONTEIRA_MODO no .env.example. Saíram G_AST_BOUNDED_CONTEXT, G_modularizacao_vsa, scripts/analisador_acoplamento_vsa.py e seus testes. AGENTS.md e docs/protocolos/AGENTS-REFERENCIA-COMPLETA.md apontam o gate novo; handoff-melhoria reassinado.
  - T12: `obter_peca` recusa destino em modulos/, componentes/ e na raiz do ecossistema (no vermelho a peça foi de fato copiada para a raiz).
  - Bateria do gate_final: forge 316, planner 48, pure 1016, master 414, enterprise 341, ops 198, freedom 75, open 21; tests 1133 passed, 1 skipped.
  - Worktree C:/Users/trcnologia/Desktop/aidd-wt/vsa-c03-bloco-4 e a branch só saem com confirmação do usuário.
- Bloco 5 (Tickets 13–15): CONCLUÍDO e mergeado na main por fast-forward em 86f22dfd (sem push). gate_final `python ecossistema.py audit` com exit 0, 65 gates, 22m43s (G_SEGREDOS 6m42s, G_TESTES_REAIS 13m09s).
  - Commits: a527938e (T13), 321666b6 (T14), c201d91a (T15), 86f22dfd (fix pós-gate_final do T13).
  - T13: `scripts/cli_modularizacao_vsa.py` real com inspect (fatias, arquivos, gates medidos), status medido, verify integrado a contratos/fractalidade/gates e subcomandos reconcile e index-subgraphs; `tests/test_vsa_cli_real.py`.
  - T14: scripts órfãos do ciclo-01 eliminados (`isolamento_vsa.py`, `resiliencia_vsa.py`, `observabilidade_vsa.py`, `rollback_vsa.py`, `handoff_vsa.py`, `validador_fatias_vsa.py`) com seus testes; `ERRATA.md` no ciclo-01; `tests/test_sem_orfaos_vsa.py`.
  - T15: `CONVENCAO-EXIT-CODES-DETERMINISTICOS.md` restringe 0-5 a scripts/CLIs e mantém saída binária 0/1 nos gates; `tests/test_convencao_exit_escopo.py`; G_SAIDA_BINARIA com 71 gates, exit 0.
  - 1º gate_final reprovou (G_TESTES_REAIS, tests/ 1129 passed, 4 failed): `tests/test_vsa_cli.py` exigia `verify == 0`, mas o verify real sai 1; e o G_MODULO_FRONTEIRA em bloqueio (chamado pelo verify) acusava o teste do T12 citando `fluxo-01-pure`. Corrigido em 86f22dfd (seção 47 do relatório E2E). As outras 3 falhas não se repetiram na reexecução isolada nem no 2º gate_final.
  - Antes do merge, `scripts/cli_modularizacao_vsa.py` não commitado da outra sessão foi guardado em `git stash` ("outra-sessao: cli_modularizacao_vsa index-subgraphs (supersedido pelo T13, ...)"), com autorização do usuário: a versão do T13 já contém o index-subgraphs. NÃO aplicar sem perguntar.
  - Worktree C:/Users/trcnologia/Desktop/aidd-wt/vsa-c03-bloco-5 e a branch só saem com confirmação do usuário.
- Bloco 6 (Ticket 16): CONCLUÍDO e mergeado na main por fast-forward (sem push). gate_final `python ecossistema.py audit` com exit 0, 65 gates, 33m29s (G_SEGREDOS 6m50s, G_TESTES_REAIS 24m59s).
  - Commits: d056f126 (T16), ded758e0 (fix da barreira do master), d58c6657 (DoD 6), e392ae28 (removido registro de sessão com ID inventado), 950bcc42 (esta atualização). Rebaseado sobre d132b337 (3 commits da outra sessão, sem arquivo em comum; o gate_final rodou sobre 4fb6f91a, e d132b337 só acrescenta docs/auditoria/aidd-visual-maps).
  - T16: `scripts/micro_gates.py` com um comando por subfatia (forge, planner, pure, open, freedom, enterprise, master, ops) + core-cli, `--rootdir=.`, `execucoes_da_fatia()`; `pytest.ini` novo em planner/open/ops e `tests/conftest.py` (limpa GIT_DIR) em planner/open/freedom/ops; `tests/test_micro_gates_fatias_verdes.py` roda os 9 comandos de verdade (20 passed, 779 s).
  - DoD 6 medido: 9 comandos 753 s → 693 s; suítes de um commit só no pure 147 s → 32 s; commit real só no master = 387 s; commit do T16 (5 subfatias) = 322 s.
  - Fix: `vsa_join_barrier.py` do master achava a raiz em modulos/03-plataforma-e-entrega e engolia o ImportError (micro-gates nunca rodavam); raiz = pai de modulos/ e sem micro-gates a barreira reprova. Seções 48 e 49 do relatório E2E.
  - Custo: o teste do T16 roda as 8 suítes dentro da bateria `tests/` e elevou o G_TESTES_REAIS de ~13 min para ~25 min. Reduzir depois se incomodar (usuário avisado).
  - Dívida do verify (não feita, decisão de estrutura): `cli_modularizacao_vsa.py verify` sai 1 por skills/tests ausentes em todas as fatias e core/gates/README.md ausentes em enterprise/master/ops; decisão do usuário (08/10): tratar no Bloco 7, junto dos T17/T18.
  - Push feito por autorização do usuário (08/10); worktree vsa-c03-bloco-6 e branch removidas.
- Bloco 7 (Tickets 17–19): CONCLUÍDO e mergeado na main por fast-forward em 98f08e00 (push feito às 11:47 junto de 88493e6a).
  - Commits: 4b463e8d (T17), 7bcd383f (T18), 61a799a4 (T19), 98f08e00 (atualização do prompt).
  - T17: AGENTS.md abaixo de 400 tokens e README.md abaixo de 500 por fatia; core/skills/gates só quando a fatia tem esse conteúdo, decisão do usuário de 08/10; README longo virou GUIA.md; tabela de despacho no AGENTS.md raiz; dívida do verify resolvida.
  - T18: components verify 73 -> 78; sync --tipo skill 44 -> 48; --ferramenta aidd-master 0 -> 2; as 4 cópias já tinham saído no T6.
  - T19: 6 nomes do padrão; codebase-memory 39 -> 8 projetos, ver REMOCAO-SUBGRAFOS.md.
  - Registro sem filtros do gate_final: o gate_final do Bloco 7 reprovou (audit às 10:42, AUDIT_EXIT=1, 64 aprovados e 1 reprovado em G_TESTES_REAIS: master tests/unit/test_nextjs_exporter.py::test_npm_install_e_build_funcionam_de_verdade e open tests/test_pipeline_factory.py::test_frontend_gerado_pelo_factory_compila_de_verdade). Causa provada: arquivos somem em AppData\Local\Temp no meio do npm install/build (limpador de TEMP); os 2 testes passam com a pasta temporária fora de AppData\Local\Temp. Mesmo com a reprovação, houve fast-forward na main às 11:03 e push às 11:47.
  - Audit na main pós-Bloco 7 (08/10, 2461 s com TEMP/TMP/TMPDIR=C:\Users\trcnologia\aidd-tmp): 60 aprovados e 5 reprovados. Diagnóstico factual: G_TESTES_REAIS teve 100% de aprovação nas 8 ferramentas (2432 passed, 0 failed, incluindo os 2 testes de npm install/build que antes falhavam), mas a bateria tests/ deu timeout de 900s (T16 elevou o tempo da suíte); G_ENV_ROT reprovou por AIDD_MEDICOES_DIR faltante em scripts/telemetria_mapas.py:34 (commit 5d55488d da outra sessão); G_PORTAO_PROVA_QUE_MORDE reprovou como cascata de G_ENV_ROT e mapas; G_mapa_pecas reprovou por divergência nos mapas visuais da outra sessão (mapa-00-indice.html, mapa-06-comandos.html); G_HANDOFF_MELHORIA reprovou por SHA-256 divergente em AGENTS.md.
- Bloco 8 (Novo): PRÓXIMO. Tickets 20–22 (Fechamento), conforme PLANO-EVOLUCAO.md e PLANO-EVOLUCAO-BLOCO-8.json. A tentativa de 08/10 às 11:50 não produziu nenhum commit.
- Bloco 9 (Ticket 23, novo): esqueleto único enterprise × master; registrado no PLANO-EVOLUCAO.md por decisão do usuário (07/10). Com o usuário (escolha do dono e remoções).
- Achados do Bloco 4: 44 arquivos de src/ e alembic/ idênticos entre enterprise e master fora do núcleo vendorizado (src/core = cópia proposital de componentes/compartilhado/src-core, vigiada pelo G_DRIFT_NUCLEO_COMPARTILHADO) → Ticket 23; `aidd_planner/core/*` é casca que reexporta de `src.core_planner` (duplicação dentro do planner); rodar `tests/` com AIDD_GATES_MODO=completo herdado reprova test_g_testes_reais_visibilidade (o gate tira a variável; não é falha real); a medição `echo "$(cmd) exit=$?"` zera o `$?` (fabricou o achado falso "G_OPS_MVP sai 0"); o corte por falta de memória do Claude Code mata comandos em segundo plano com a sessão ociosa: rodar o audit com monitor emitindo a cada 2 min e pedir ao usuário para fechar Chrome/Canva/Antigravity antes.
- Achados do Bloco 3: hook g-testes-reais tem `files: ^tools/` (pasta não existe mais, nunca dispara no commit; no audit roda); vsa_join_barrier.py do master calcula a raiz errado (micro-gates nunca rodam, ImportError engolido); package_usuario.py e core/anti_lockin.py ainda citam tools/; scripts/test_ecossistema_self_healing.py (ex-gates/) segue com 4 falhas antigas, fora do G_TESTES_REAIS; novos selos de handoff exigem catalogar o hash no .secrets.baseline (G_SEGREDOS) e reassinar handoff-melhoria quando AGENTS.md muda.
- Achados do Bloco 2: GIT_DIR do hook vazava para a suíte do forge e gravou core.bare=true + [user] forge-test no .git/config (reparado, fix em a5af9f18); pure-motor e open-motor --help quebravam rodando de modulos/ (corrigido no T4); gerador de mapas grava CRLF; testes do pure gravam .aidd/cache/_llm_request_*.json dentro de modulos/ (barrado por .gitignore; corrigir os testes é dívida); G_TESTES_REAIS pode reportar "JUnitXML não gerado" quando outra sessão limpa %TEMP% no meio (rerodar a suíte); teste test_g_layout_entrega falha só na bateria completa (passa sozinho); self_healing (4 testes) já falhava antes do ciclo.
- Achado do TMPDIR: o Python usa TMPDIR antes de TEMP/TMP; a sessão herda TMPDIR=AppData\Local\Temp; exportar TEMP no Git Bash não muda a pasta temporária.
- Armadilha: nunca converter CRLF em massa em docs/livros (tem PDF/PNG). aidd_forge editável agora aponta para modulos/ do repo principal.

LEIA ANTES
- docs/auditoria/modularizacao-vsa/ciclo-03/DIAGNOSTICO.md, DOD.md, PLANO-EVOLUCAO.md.
- Decisões fixas A, B e C (ver DIAGNOSTICO.md). Não rediscutir.

COMO EXECUTAR (definido pelo usuário)
- Direto nesta thread, sem subagentes e sem scripts/orquestrador_4f.py (ele abre agentes claude-9router externos).
- Uma worktree e uma branch por bloco: aidd/vsa-c03-bloco-N, criada a partir da main, em C:/Users/trcnologia/Desktop/aidd-wt/vsa-c03-bloco-N.
- Preparar a worktree: `python ecossistema.py components sync --tipo todos`; depois `git checkout -- .gemini/extensions` (o sync só troca LF por CRLF nesses 44 arquivos). Copiar da main os arquivos locais não versionados: .cursor/mcp.json, opencode.jsonc, .env (sem ele os testes do planner falham por falta de MOBBIN_API_KEY), .gemini/settings.json e .vscode/ (sem eles o G_UNIVERSAL_HARNESS reprova).
- TDD estrito por ticket: teste com exit 1 antes, exit 0 depois; o gate é o declarado no plano. Um commit por ticket.
- O pre-commit lê arquivos não rastreados do disco (G_ENV_ROT, G_PORTAO_PROVA_QUE_MORDE): ao commitar um ticket, tire do disco os arquivos do ticket seguinte ainda não commitados. Variável de ambiente nova precisa entrar no .env.example. O .pre-commit-config.yaml precisa estar staged se alterado.
- A bateria de testes regrava docs/relatorios/11-09-2026_relatorio-evolucao-plano-acao.{html,json}: rodar `git checkout -- docs/relatorios/` antes de commitar (achado: teste escrevendo dentro do repo).
- No fim do bloco: gate_final = `python ecossistema.py audit` (roda direto fora do orquestrador, cerca de 22–35 min; rode em segundo plano e acompanhe com um loop de espera, porque processo em segundo plano parado é morto quando falta memória). Rodar audit e testes com TEMP, TMP e TMPDIR = C:\Users\trcnologia\aidd-tmp (pelo PowerShell) e conferir antes com `python -c "import tempfile;print(tempfile.gettempdir())"`. Regra nova: gate_final com exit diferente de 0 = sem merge; corrigir ou rerodar até dar exit 0. Depois mostre o diff, faça o merge na main com `git merge --ff-only` e não faça push.
- Tickets 3, 5, 6 e 19: listar o que sai e para onde foi antes de apagar (registrar em arquivo do ciclo-03).
- Ticket 5: total de testes passando >= 3463.
- Ticket 13: incorporar o subcomando index-subgraphs que está no diff não commitado da main (scripts/cli_modularizacao_vsa.py, componentes/compartilhado/src-core/subgrafos_federados.py, tests/test_subgrafos_federados.py). Esses arquivos e os HTML em docs/mapas-visuais/ e docs/auditoria/mapa-pecas/catalogo-pecas.json são de outra sessão: não commitar sem perguntar.

REGRAS DURAS
- Proibido --no-verify, pular gate, simular verificação ou marcar [x] sem código no diff.
- Exit code real: redirecionar para arquivo e capturar $? na mesma linha; nunca depois de pipe.
- `unset GIT_DIR GIT_INDEX_FILE` antes de pytest/subshell; depois de cada commit conferir `git config --get core.bare` = false.
- Arquivo gravado por Python com newline='\n'.
- Não rodar `orca orchestration check`.
- Perguntas ao usuário em texto simples PT-BR, sem widget.

PRÓXIMO PASSO
- Começar pelo próximo bloco não marcado como CONCLUÍDO acima.
