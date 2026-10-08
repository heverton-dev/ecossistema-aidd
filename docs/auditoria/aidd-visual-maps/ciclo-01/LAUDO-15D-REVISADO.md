# Laudo 15-D Revisado — `aidd-visual-maps`

> Auditoria de retorno de 2026-10-08 (Fase 4 — Inspetor Retorno, branch `audit/auditoria-aidd-visual-maps-ciclo-01`, HEAD `f8cda24f`).
> Todo veredito tem um comando rodado nesta sessão, com o exit code capturado por redirecionamento para arquivo (`cmd > log 2>&1; echo $?`), nunca por pipe. `TEMP=TMP=C:\Users\trcnologia\aidd-tmp` em todas as execuções.
> Mutações e regeneração só em cópias do repositório (`tests/_repo_mapas.copiar_repo` + `git init` + commit): `aidd-tmp\r4\sb` (mutações) e `aidd-tmp\r4\sb2` (`visual-maps gerar`). Scripts de reprodução: `aidd-tmp\r4\repro.sh` e `aidd-tmp\r4\repro_gerar.sh`.
> Mapeamento graph-first (Lei #14): `list_projects`, `get_architecture` (`path=scripts`), `search_graph` (scripts da skill) e `get_code_snippet` (`G_mapa_pecas.auditar_mapas_visuais`), no codebase-memory-mcp, antes de qualquer grep. O índice disponível era o da worktree do Construtor (`…-Fase_3_Construtor`), com o mesmo conteúdo do HEAD auditado.

## Antes de tudo: o relatório do Construtor não existe

`docs/auditoria/aidd-visual-maps/ciclo-01/RELATORIO-CONSTRUTOR.md` **não existe** (`ls` da pasta do ciclo). O trabalho do Construtor está no commit `f8cda24f` ("backup completo T15 do agente que parou antes de relatar"): 118 arquivos, +14.624/−8.802. Por isso este laudo não usa nenhuma afirmação do Construtor. Cada ticket foi reproduzido do zero, e a medição de tempo do portão que o Ticket 15 mandava registrar no relatório foi feita aqui (ver R1).

## 1. Identificação da Ferramenta
- **Nome da Ferramenta:** `aidd-visual-maps`
- **Descrição Breve:** Gera mapas HTML (técnico e não técnico) de cada tipo de peça do ecossistema a partir de um molde PT-BR com `{{MARCADORES}}` mais o catálogo `docs/auditoria/mapa-pecas/catalogo-pecas.json`, com índice, manual de montagem, livro e manifesto de handoff.
- **Comando de Gatilho:** `/aidd-visual-maps` + `python ecossistema.py visual-maps catalogo|mapa <tipo>|gerar|check` (alias `aidd-visual-maps`) + scripts locais `scripts/mapa_visual.py <tipo> [--check|--saida|--fragmento]`.

### Comandos obrigatórios (estado real do repositório)

| Comando | Exit | Saída |
|---|---|---|
| `python scripts/catalogo_pecas.py --check` | **0** | `[OK] … catalogo-pecas.json em dia com o código.` |
| `python scripts/mapa_visual.py <tipo> --check`, 16 tipos de `GERADORES` (guardas, skills, indice, encaixes, ferramentas, comandos, conexoes, leis, lente15d, oficina, scripts, moldes, harnesses, pipelines, modulos, agentes) | **0 em todos (16/16)** | `[OK] … em dia com o catálogo.` |
| `python -m pytest tests/test_mapa_visual.py tests/test_catalogo_pecas.py -q -p no:cacheprovider` | **0** | 62 passed |
| `python modulos/04-nucleo-compartilhado/gates/G_mapa_pecas.py` | **0** | APROVADO (100% OK), 5 s |
| `python modulos/04-nucleo-compartilhado/gates/G_aidd_visual_maps.py` | **0** | APROVADO, 6 s |
| `python scripts/livro_mapas.py --check` | **0** | Partes do livro em dia |
| `python ecossistema.py visual-maps check` / `aidd-visual-maps check` | **0 / 0** | catálogo, mapas, livro e manifesto em dia, 6 s |
| `pre-commit run g-aidd-visual-maps --all-files` | **0** | Passed, 6 s |
| pytest dos 15 arquivos novos (`tests/test_visual_maps_*.py`, `test_g_aidd_visual_maps.py`, `test_g_mapa_pecas_conteudo.py`) + `gates/test_g_mapa_pecas.py` + `test_livro_mapas.py` + `test_mapas_e_livros_em_dia.py` | **0** | 89 passed em **569,88 s** |
| `pytest modulos/04-nucleo-compartilhado/gates/test_g_aidd_visual_maps.py` (sozinho) | **0** | 2 passed |
| os dois arquivos `test_g_aidd_visual_maps.py` na mesma chamada | **2** | `import file mismatch` (ver R2) |

### Achados iniciais F1–F6: reprodução de retorno

| ID | Veredito | Prova (comando → exit) |
|---|---|---|
| F1 | **FIXED** | Repositório real: `catalogo_pecas.py --check` → 0, catálogo sem `handoff_vsa`/`rollback_vsa`/`G_AST_BOUNDED_CONTEXT`/`G_modularizacao_vsa` (contagem 0/0/0/0). Sandbox com `git rm scripts/contar_duplicatas.py`: `catalogo_pecas.py --check` → 1, `mapa_visual.py scripts --check` → 1, `mapa_visual.py leis --check` → 1, `livro_mapas.py --check` → 1, `G_aidd_visual_maps.py` → 1, `cli.py check` → 1, `status_mapa('scripts')` = `desatualizado` (assert → 0) |
| F2 | **FIXED** | `G_mapa_pecas.py --mapas-dir aidd-tmp\r4\lixo` (32 HTML-lixo de 330 B + manual) → **1** (32 motivos). `--catalogo cat_falso.json` (ferramentas/skills/leis/encaixes vazios) → **1** (7 motivos). Mutante M5 (`auditar_mapas_visuais` → `return []`) no sandbox: `pytest tests/test_g_mapa_pecas_conteudo.py` → **1** (`test_html_lixo_com_nomes_oficiais_reprova` FAILED): **mutante morto** |
| F3 | **FIXED** | `git ls-files docs/mapas-visuais/tecnicos \| wc -l` → 0. Sandbox: `docs/mapas-visuais/solto.html` criado → `G_aidd_visual_maps.py` → **1** ("HTML órfão") |
| F4 | **FIXED** | Catálogo real com `pipelines` (9), `modulos` (4) e `agentes` (9). `MAPAS_PREVISTOS` tem 15 tipos, incluindo pipelines/modulos/agentes. `agent_architect` aparece 5× em `mapa-15-agentes.html`. `--check` de `pipelines`/`modulos`/`agentes` → 0 |
| F5 | **FIXED** | `mcps.internos_das_ferramentas` real: 5 itens, incluindo `mobbin_mcp` (`componentes/compartilhado/mcps/mobbin_mcp/server.py`, `registrado_em_config: true`). `hooks`: 5 (3 "ligado no settings.json" + `aidd_session_auto_hook.py` e `regra10_check.py` "sem gatilho no settings.json") = os 5 `.py` de `.claude/hooks/` |
| F6 | **FIXED** | Regex `Use when\|Use this\|Builds\|Runs\|Records` em `nao-tecnicos/*.html` → **0** ocorrências (eram 124). `compilar_mapas_nao_tecnicos.py:82` usa `mv.aplicar_molde`, e não há mais `mv.GERADORES` no arquivo. Sandbox: "Use when…" injetado em `nao-tecnicos/mapa-05-skills.html` → `G_aidd_visual_maps.py` → **1** |

### Achados N1–N9: reprodução de retorno

| ID | Veredito | Prova |
|---|---|---|
| N1 | **FIXED** | `mapa-10-scripts` aparece 1× no manual (e `mapa-15-agentes` também). Sandbox: link do mapa-10 trocado → `G_aidd_visual_maps.py` → **1** |
| N2 | **FIXED** | `totais.leis` = 14; `nao-tecnicos/mapa-01-leis.html` tem "14 leis" 1× e "13 leis" 0×. Sandbox: `<p>As 13 leis…` acrescentado ao molde → `G_aidd_visual_maps.py` → **1** ("contagem digitada: moldes-nao-tecnicos/leis.html:50: 13 leis"). A primeira tentativa desta auditoria não aplicou a mutação (o `sed` procurava `</body>`, que o molde não tem) e deu 0; foi refeita com a linha acrescentada |
| N3 | **FIXED** | Sandbox: `rm moldes-nao-tecnicos/guardas.html`; `mapa_visual.py guardas` → **1**, com `[ERRO] …guardas.html: [Errno 2]` + linha JSON e sem `Traceback`; `md5sum -c` do técnico → 0 (intacto); 0 `*.tmp` sobrando |
| N4 | **FIXED** | Sandbox com script apagado: `livro_mapas.py --check` → **1** |
| N5 | **FIXED** | `.pre-commit-config.yaml:482-488`: `g-aidd-visual-maps` com `always_run: true`. O portão chama `catalogo_em_dia`, o que cobre o `--check` de frescor. `pre-commit run g-aidd-visual-maps --all-files` → 0 |
| N6 | **FIXED** | `aplicar_molde` (`scripts/mapa_visual.py:828`) é usada pelas duas versões (`:850` e `compilar_mapas_nao_tecnicos.py:82`). O caminho do catálogo é declarado 1× em código (`catalogo_pecas.py:44 SAIDA_PADRAO`); as outras ocorrências são docstring/help/lista de fontes |
| N7 | **FIXED** | Regex de contagem fixa nos moldes e em `scripts/mapa_visual.py` → 0 achados; `G_mapa_pecas.py` sem "13 mapas" |
| N8 | **FIXED** | `grep -c aidd-visual-maps AGENTS.md` → 2 (linhas 101 e 220); `G_aidd_visual_maps.py` existe e roda (exit 0) |
| N9 | **FIXED** | ver F5: 5/5 hooks |

### Tickets do PLANO-EVOLUCAO: reprodução de retorno

| Ticket | Veredito | Comando → exit |
|---|---|---|
| 1 Catálogo conferido contra o repositório | **FIXED** | ver F1 (sandbox: 6 conferências → 1; real → 0) |
| 2 G_mapa_pecas confere conteúdo | **FIXED** | ver F2 (lixo → 1, listas vazias → 1, M5 morto, real → 0) |
| 3 Pasta órfã e barreira de órfãos | **FIXED** | ver F3 (0 versionados; HTML solto → 1) |
| 4 Coletores de hooks e MCPs | **FIXED** | ver F5 |
| 5 Mapas de pipelines, módulos e agentes | **FIXED** | ver F4; os 16 `--check` → 0 |
| 6 Não técnico PT-BR e montagem sem cópia | **FIXED** | ver F6/N6 |
| 7 Nenhuma contagem digitada | **FIXED** | ver N2/N7 |
| 8 Manual liga todos os mapas | **FIXED** | ver N1 |
| 9 Gravação atômica e rollback | **FIXED** | ver N3. `gravar_lote` (`scripts/gravacao_atomica_mapas.py`) grava em `.<nome>.<pid>.tmp`, faz `os.replace` com `com_retry` e restaura a cópia em memória quando falha |
| 10 Escopo de escrita | **FIXED** | Sandbox: `mapa_visual.py leis --saida AGENTS.md` → **1** "[ERRO] escrita fora do escopo"; `catalogo_pecas.py --saida AGENTS.md` → **1**; `md5sum -c AGENTS.md` → 0 (intacto, 2×); `--saida aidd-tmp\r4\leis_saida.html` → **0** (com `TMPDIR` também apontado para `aidd-tmp`, ver R6) |
| 11 Retry com backoff e falha estruturada | **FIXED** | Script próprio (`aidd-tmp\r4\t11.txt`) → 0: `PermissionError` 2× e sucesso na 3ª tentativa, esperas `[0.2, 0.4]`; `FileNotFoundError` tentado 1× (não repete); falha permanente → `[ERRO]` + JSON com `estagio/tipo/arquivo/tentativas=3/erro` (validação → 0) |
| 12 Telemetria persistida | **FIXED** (ressalva R4) | Sandbox com `AIDD_MEDICOES_DIR=aidd-tmp\r4\med2`: `mapa_visual.py leis --saida …` → 0, com a linha `{"estagio":"mapa","tipo":"leis","duracao_ms":4.4,"arquivos_gravados":1,"hash_catalogo":"53df…","exit_code":0,"llm_tokens":0}`; `catalogo_pecas.py --check` também grava a sua linha (assert → 0) |
| 13 CLI unificada e ordem do pipeline | **FIXED** | `python ecossistema.py visual-maps check` → 0. Sandbox `sb2`: `git rm scripts/contar_duplicatas.py` + commit, então `catalogo_pecas.py --check` → 1; `cli.py gerar` → **0** ("9 arquivo(s) promovido(s)"); `cli.py check` → **0**; catálogo sem `contar_duplicatas` → 0; ordem `[ETAPA]` = `catalogo_pecas.py` primeiro, `mapa_visual.py indice` penúltimo, `livro_mapas.py` último (assert → 0); `git worktree list` sem a worktree efêmera; 0 `.tmp` |
| 14 Manifesto, handoff ao livro e contrato | **FIXED** (ressalva R5) | `MANIFESTO-MAPAS.json`: 32 entradas (16 tipos × 2 versões), todas `concluido`, `handoff_livro.build.exit_code = 0` com sha256 do PDF. Sandbox: 1 byte trocado em `mapa-01-leis.html` → `cli.py check` **1**, `G_aidd_visual_maps.py` **1**, `G_mapa_pecas.py` **1**. As 7 cópias do `SKILL.md` têm o mesmo md5 `1b7863a4…`, e as 7 cópias do `cli.py` também (`0adbd689…`) |
| 15 Portão no pre-commit e AGENTS.md | **FIXED** (ressalvas R1, R2) | Portão real → 0; as fixtures ilusórias reproduzidas aqui (catálogo velho, órfão, inglês, contagem, link, manifesto) → 1 cada; HTML-lixo → 1 no `G_mapa_pecas` (o `G_aidd_visual_maps` delega o conteúdo, como diz a docstring dele); pre-commit → 0; AGENTS.md → 2 |

### Achados novos do retorno (R1–R7)

| ID | Gravidade | Achado | Prova |
|---|---|---|---|
| R1 | Média | O Construtor não entregou `RELATORIO-CONSTRUTOR.md`, e o trabalho entrou como "backup" de um agente que parou antes de relatar. Faltou a medição de tempo do portão exigida no Ticket 15 | `ls ciclo-01/` sem o arquivo; `git show --stat f8cda24f`. Medição feita aqui: portão 6 s, `G_mapa_pecas` 5 s |
| R2 | Média | Dois arquivos de teste com o mesmo nome: `tests/test_g_aidd_visual_maps.py` e `modulos/04-nucleo-compartilhado/gates/test_g_aidd_visual_maps.py`. Na mesma chamada do pytest, a coleta quebra | `pytest … modulos/04-…/gates/test_g_aidd_visual_maps.py tests/test_g_aidd_visual_maps.py` → **exit 2** "import file mismatch"; cada um sozinho → 0 |
| R3 | Média | Custo: os 89 testes levam 569,88 s (9,5 min). Cada `mapa_visual.py <tipo> --check` refaz o catálogo inteiro em memória (cerca de 5 s), então 16 checks somam cerca de 80 s | `duracao_ms` das linhas de telemetria (≈5.200 ms por `--check`); saída do pytest |
| R4 | Baixa | O `--check`, que é só leitura, grava telemetria por padrão em `secoes/medicoes/aidd-visual-maps.jsonl` no checkout (pasta ignorada pelo git). É a única escrita da ferramenta que não passa por `garantir_escopo` | 1ª rodada desta auditoria criou `secoes/medicoes/` (110 linhas); `git check-ignore` → `.gitignore:141`. O arquivo foi copiado para `aidd-tmp\r4` como evidência e apagado do checkout |
| R5 | Baixa | `SKILL.md` (Failure Modes): diz "`G_mapa_pecas` fails at pre-commit: a required map or manual link is missing". O `G_mapa_pecas` só exige que o manual exista; quem confere cada link é o `G_aidd_visual_maps` (`links_faltando_no_manual`) | `G_mapa_pecas.py:125-156` (sem checagem de `href`); sandbox N1 → só o `G_aidd_visual_maps` aponta "manual sem link" |
| R6 | Baixa (ambiente) | No Git Bash, `TMPDIR` (AppData\Local\Temp) prevalece sobre `TEMP`/`TMP`. Com isso, `garantir_escopo` recusa `--saida` em `aidd-tmp`, e `tmp_path`/worktree efêmera continuam no %TEMP% que o limpador apaga | `python -c "tempfile.gettempdir()"` com `TEMP=aidd-tmp` → `AppData\Local\Temp`; `--saida aidd-tmp\…` → 1, e com `TMPDIR` também → 0 |
| R7 | Baixa | Acoplamento circular entre `cli.py` e `handoff.py` (`handoff` importa `cli`; `cli` importa `handoff` dentro de `cmd_gerar`/`cmd_check`) | `componentes/compartilhado/skills/aidd-visual-maps/scripts/handoff.py:24-25`, `cli.py` (`import handoff  # import tardio`) |

## 2. A Matriz Anatômica (Lens 15-D)

### Fase 1: Governança e Blindagem
- **D1. Contratos e Regras:** — **Nota Inicial 5 -> Nota Revisada 8.** As três afirmações falsas do laudo inicial agora são verdadeiras e foram provadas:
  - (a) o manual liga todos os mapas: N1, e o teste `test_visual_maps_manual_links.py` + o portão barram link faltando;
  - (b) o portão barra mapa ruim: F2 e T14 (1 byte trocado → `G_mapa_pecas` 1);
  - (c) o índice só mostra "concluído" com catálogo em dia: F1, com `status_mapa` → `desatualizado`.

  A Stopping Checklist ganhou `visual-maps check`. A skill está no `AGENTS.md`. As 7 cópias do `SKILL.md` têm o mesmo hash. Resíduo: R5, um Failure Mode atribui ao `G_mapa_pecas` a checagem de link que é do `G_aidd_visual_maps`.
- **D2. Input e Gatilhos:** — **Nota Inicial 5 -> Nota Revisada 8.** Agora há CLI unificada: `ecossistema.py visual-maps` e o alias `aidd-visual-maps` → `catalogo | mapa <tipo> | gerar | check` (exit 0 ok, 1 desvio, 2 subcomando inválido). O catálogo em disco já não é aceito sem conferência: todo `--check` chama primeiro `catalogo_em_dia`. **DoD 1: atendido.**
- **D3. Raio de Impacto e Isolamento:** — **Nota Inicial 4 -> Nota Revisada 8.**
  - `garantir_escopo` (`scripts/escopo_escrita_mapas.py`) só aceita `docs/mapas-visuais/`, `docs/auditoria/mapa-pecas/`, `docs/livros/mapas-aidd/` ou o diretório temporário: `--saida AGENTS.md` → 1 e o arquivo fica intacto (T10).
  - O `gerar` roda numa worktree efêmera e promove só as pastas permitidas, num lote. Removeu a worktree depois (`git worktree list` → sem ela).
  - A pasta órfã `tecnicos/` foi apagada (F3).
  - Ressalva R4: a telemetria grava em `secoes/medicoes/` sem passar por `garantir_escopo` (pasta ignorada pelo git).

  **DoD 2: atendido, com ressalva R4.**
- **D4. Componentes e Fractalidade:** — **Nota Inicial 4 -> Nota Revisada 8.**
  - Coletores completos: 5 MCPs internos (com `mobbin_mcp` e `mcp-gatekeeper`) e 5 hooks, inclusive os "sem gatilho". O catálogo não lê `settings.local.json`, como decidido no plano.
  - Peças novas: `escopo_escrita_mapas`, `gravacao_atomica_mapas`, `resiliencia_mapas`, `telemetria_mapas`, `cli.py`, `handoff.py`, `G_aidd_visual_maps`.
  - Resíduo R7: acoplamento circular entre `cli` e `handoff`.

### Fase 2: O Chão de Fábrica (Workflow Agêntico)
- **D5. Visão e Escopo:** — **Nota Inicial 5 -> Nota Revisada 8.** Cobertura nova:
  - `mapa-13-pipelines` (9 pipelines);
  - `mapa-14-modulos` (4 áreas);
  - `mapa-15-agentes` (9 grupos de templates, idênticos agrupados por hash; `agent_architect` 5×).

  `MAPAS_PREVISTOS` tem 15 tipos e o manifesto registra 32 arquivos, todos `concluido`. O catálogo bate com o repositório e "14 leis" está correto.
- **[Estágio 1 — Coleta] D6. O que o Estágio Faz:** — **Nota Inicial 6 -> Nota Revisada 8.** `catalogo_pecas.py` ganhou `coletar_pipelines`, `coletar_modulos`, `coletar_agentes`, coletores de hooks/MCPs completos e `catalogo_em_dia(raiz, caminho)`.
- **[Estágio 2 — Montagem] D6. O que o Estágio Faz:** — `montar` usa `aplicar_molde` (`mapa_visual.py:828-850`) e monta as duas versões em memória antes de gravar.
- **[Estágio 3 — Não técnico] D6. O que o Estágio Faz:** — `compilar_nao_tecnico` usa a mesma `aplicar_molde` com descrições PT-BR (comando slash ou `descricoes-pt.json`). **[Estágio 4 — Livro] / [Estágio 5 — Handoff]** `livro_mapas.py` grava via `gravar_lote`; `handoff.compilar_livro` roda o build do aidd-textbook e `emitir_manifesto` fecha o lote.
- **[Estágio 1→5] D7. O que o Estágio Recebe:** — **Nota Inicial 4 -> Nota Revisada 8.** Os estágios 2 a 5 continuam lendo o JSON em disco, mas agora cada elo confere esse JSON contra o repositório (`catalogo_em_dia`). Prova: com um script apagado, os 6 pontos de conferência (catálogo, 2 mapas, livro, portão, `cli check`) dão 1 (F1). Totais e listas reais sem resíduo do ecossistema antigo.
- **[Estágio 1→5] D8. O que o Estágio Processa:** — **Nota Inicial 6 -> Nota Revisada 8.** Continua 100% determinístico, sem LLM: `llm_tokens: 0` registrado em cada linha de telemetria (**DoD 3: atendido**). O não técnico tem 0 frases-padrão em inglês (eram 124) e os moldes têm 0 contagens digitadas. O caminho do catálogo é declarado uma vez em código. Resíduo de custo, R3: cada `--check` refaz a varredura inteira (~5 s).
- **[Estágio 1→5] D9. O que o Estágio Entrega:** — **Nota Inicial 4 -> Nota Revisada 8.**
  - 16 mapas técnicos e 16 não técnicos (com índice), manual com link para todos, livro (8 partes + PDF) e `MANIFESTO-MAPAS.json`.
  - `--check` 16/16 → 0. Nenhum órfão.
- **D10. Orquestração e Topologia:** — **Nota Inicial 3 -> Nota Revisada 8.** O `gerar` impõe a ordem catálogo → mapas → índice → livro → build do aidd-textbook → manifesto. Prova: os `[ETAPA]` do sandbox `sb2` saem nessa ordem, e o `gerar` com catálogo velho deixa o `check` seguinte em 0. O `check` confere a cadeia toda, inclusive o catálogo contra o repositório, que era o elo que faltava no laudo inicial.

### Fase 3: Resiliência e Economia (Engenharia Operacional)
- **D11. Tratamento de Exceções e Fallback:** — **Nota Inicial 3 -> Nota Revisada 8.**
  - `com_retry` com backoff `0,2·2^n` só para `PermissionError`/`OSError`; não repete `FileNotFoundError` nem `ValueError` (T11, provado com relógio injetado).
  - `relatar_falha` sempre dá `[ERRO]` + linha JSON + exit 1, sem traceback cru (N3).

  **DoD 4: atendido.**
- **D12. Observabilidade e Frugalidade:** — **Nota Inicial 1 -> Nota Revisada 7.**
  - `telemetria_mapas.medir` grava uma linha JSONL por estágio, com `estagio/tipo/duracao_ms/arquivos_gravados/hash_catalogo/exit_code/llm_tokens`, inclusive nos `--check`. O destino pode ser trocado por `AIDD_MEDICOES_DIR` (T12). **DoD 5: atendido.**
  - Não passa de 7 por dois motivos: R4 (um "check" que grava no checkout) e R3 (a telemetria mostra cerca de 5 s por `--check` e 9,5 min na suíte nova).

### Fase 4: O Inspetor e a Expedição (Validação)
- **D13. Quality Gates (Portões):** — **Nota Inicial 2 -> Nota Revisada 8.**
  - `G_aidd_visual_maps.py` existe e reaproveita as funções dos tickets, sem reimplementar regra.
  - Cada fixture ilusória reproduzida aqui dá exit 1: catálogo velho, órfão, inglês, contagem, link e manifesto.
  - `G_mapa_pecas` agora compara cada mapa byte a byte com o gerador (lixo → 1, listas vazias → 1, M5 morto).
  - Os dois portões estão no pre-commit (`always_run`), com 6 s + 5 s medidos.

  **DoD 6: atendido.** Resíduos: R2 (nome de teste duplicado quebra a coleta conjunta) e R1 (tempo do portão não relatado pelo Construtor).
- **D14. Critério de Rejeição (Rollback):** — **Nota Inicial 2 -> Nota Revisada 8.**
  - `gravar_lote` grava tudo ou nada: no cenário N3, o técnico fica intacto e não sobra `.tmp`.
  - Escrita fora do escopo é barrada antes de gravar.
  - No `gerar`, uma etapa com erro faz com que nada volte ao repositório, e a worktree efêmera é removida no `finally`.
  - Os critérios de `exit 1` agora disparam diante do estado real (F1).

  **DoD 7: atendido.**
- **D15. Output Consolidado e Handoff:** — **Nota Inicial 3 -> Nota Revisada 8.**
  - `MANIFESTO-MAPAS.json` é determinístico, sem data/hora. Tem o hash do catálogo, sha256 e status por mapa nas duas versões, e um `handoff_livro` para o aidd-textbook com as partes e o resultado do build (`exit_code 0`, sha256 do PDF).
  - `conferir_manifesto` pega 1 byte trocado (T14).
  - Este laudo é validado pelo `G_auditoria_15D.py`.

  **DoD 8: atendido.** Resíduo R1: falta o relatório do Construtor, que é o handoff interno do ciclo.

### Notas por dimensão (Inicial -> Revisada)

| D1 | D2 | D3 | D4 | D5 | D6 | D7 | D8 | D9 | D10 | D11 | D12 | D13 | D14 | D15 | Média |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 5→8 | 5→8 | 4→8 | 4→8 | 5→8 | 6→8 | 4→8 | 6→8 | 4→8 | 3→8 | 3→8 | 1→7 | 2→8 | 2→8 | 3→8 | **3,8 → 7,9** |

### DoD — conferência critério a critério

| DoD | Status | Evidência |
|---|---|---|
| 1 CLI Fallback e Fractalidade (D4) | **Atendido** | `python ecossistema.py visual-maps check` → 0; alias → 0; scripts locais seguem funcionando |
| 2 Isolamento de Raio de Impacto (D3) | **Atendido (ressalva R4)** | `--saida AGENTS.md` → 1 e arquivo intacto; `gerar` em worktree efêmera removida; telemetria fora de `garantir_escopo` |
| 3 Motor Analítico Determinístico (D8) | **Atendido** | sem LLM; `llm_tokens: 0` em toda linha de telemetria |
| 4 Resiliência Operacional (D11) | **Atendido** | T11: retry 0,2/0,4 s, sem retry em erro de dado, JSON estruturado, exit 1 sem traceback |
| 5 Observabilidade e Frugalidade (D12) | **Atendido** | T12: linha JSONL com as 7 chaves por estágio, `--check` incluso |
| 6 Quality Gate e Rótulo Honesto (D13) | **Atendido** | `G_aidd_visual_maps.py` real → 0, 6 fixtures ilusórias → 1; `G_mapa_pecas` lixo → 1; M5 morto; pre-commit → 0 |
| 7 Limpeza e Rollback (D14) | **Atendido** | N3: técnico intacto (`md5sum -c` 0), 0 `.tmp`; `gerar` sem worktree sobrando |
| 8 Output Consolidado e Handoff (D15) | **Atendido (ressalva R1)** | `MANIFESTO-MAPAS.json` conferido; 1 byte trocado → `check` 1; este laudo EXIT 0 no `G_auditoria_15D.py`; relatório do Construtor ausente |

---

## 3. Matriz de Avaliação da Execução
- [x] A ferramenta isolou seu raio de impacto corretamente? — **Sim, com ressalva.** Escrita só nas 3 pastas permitidas ou no temporário (T10). O `gerar` usa worktree efêmera e lote atômico (T13, N3), e não há mais órfãos (F3). Ressalva R4: a telemetria do `--check` grava em `secoes/medicoes/` (pasta ignorada).
- [x] O workflow seguiu as fases sem alucinações de LLM em tarefas mecânicas? — **Sim.** O motor é 100% determinístico, com `llm_tokens: 0` medido. O catálogo é conferido contra o repositório em todo `--check`.
- [x] O output final passou em todos os Quality Gates e emitiu o Handoff? — **Sim.** `catalogo_pecas --check`, 16/16 `mapa_visual --check`, `livro_mapas --check`, `G_mapa_pecas`, `G_aidd_visual_maps`, `visual-maps check` e `pre-commit run g-aidd-visual-maps` → 0. O manifesto e o handoff ao aidd-textbook foram emitidos e conferidos. Pendências não bloqueantes: R1 (sem relatório do Construtor) e R2 (colisão de nome de teste).

### Comandos de reprodução (todos com `TEMP=TMP=C:\Users\trcnologia\aidd-tmp`)
```text
python scripts/catalogo_pecas.py --check                                        -> exit 0
python scripts/mapa_visual.py <cada um dos 16 tipos de GERADORES> --check       -> exit 0 (16/16)
python -m pytest tests/test_mapa_visual.py tests/test_catalogo_pecas.py -q -p no:cacheprovider -> exit 0 (62 passed)
python modulos/04-nucleo-compartilhado/gates/G_mapa_pecas.py                    -> exit 0
python modulos/04-nucleo-compartilhado/gates/G_aidd_visual_maps.py              -> exit 0
python scripts/livro_mapas.py --check                                           -> exit 0
python ecossistema.py visual-maps check                                         -> exit 0
pre-commit run g-aidd-visual-maps --all-files                                   -> exit 0
pytest (15 arquivos novos + test_g_mapa_pecas + livro + em_dia)                 -> exit 0 (89 passed, 569,88 s)
pytest dos dois test_g_aidd_visual_maps.py juntos                               -> exit 2 (R2)
G_mapa_pecas.py --mapas-dir aidd-tmp\r4\lixo                                    -> exit 1
G_mapa_pecas.py --catalogo aidd-tmp\r4\cat_falso.json                           -> exit 1
bash aidd-tmp\r4\repro.sh  (sandbox sb)                                         -> F1 6x exit 1; F3/F6/N1/T14 portão exit 1;
                                                                                   N3 exit 1 + md5 ok + 0 tmp; T10 fora exit 1;
                                                                                   M5 pytest exit 1 (mutante morto)
sandbox sb: molde leis + "13 leis"; G_aidd_visual_maps.py                       -> exit 1
sandbox sb: TMPDIR=aidd-tmp; mapa_visual.py leis --saida aidd-tmp\...            -> exit 0; telemetria JSONL ok
python aidd-tmp\r4 (script T11 com com_retry)                                   -> exit 0; JSON ok
bash aidd-tmp\r4\repro_gerar.sh (sandbox sb2, script apagado)                   -> gerar exit 0; check exit 0; ordem ok
```
