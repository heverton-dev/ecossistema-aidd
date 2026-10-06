# Plano de Evolução (Fase 2) - modularizacao-vsa ciclo-03

Plano para fechar de verdade a modularização VSA: **uma cópia só de cada peça**, gates no dono, fronteira que morde e nenhum stub.
Origem: `DIAGNOSTICO.md` (auditoria por reprodução real, 06/10/2026). Critérios: `DOD.md`. Decisões A, B e C do usuário: ver `DIAGNOSTICO.md`.

## Garantia de zero perda
1. **Tag de segurança** `pre-vsa-ciclo-03`, criada pelo usuário antes do Bloco 1.
2. **Inventário antes/depois** (`scripts/inventario_capacidades.py foto` e `comparar`): nada que exista em `tools/` some sem ter ido para `modulos/`. Exigido: "conteúdo único órfão = 0".
3. **Testes não diminuem:** o total de testes passando na bateria completa não cai em relação ao número medido no Ticket 1.
4. **Você confirma cada remoção** (Lei #7): os Tickets 3, 5, 6 e 19 mostram a lista do que sai antes de apagar.

## Estratégia de Execução
- TDD estrito: o teste que reprova (exit 1) vem antes da implementação.
- Cada ticket entrega um arquivo **novo** (o orquestrador pula o ticket se o arquivo já existir).
- Cada ticket tem o próprio `Gate do Ticket`, rodado pelo orquestrador.
- Worktree isolada por ticket; antes de qualquer pytest: `unset GIT_DIR GIT_INDEX_FILE`; worktree nova precisa `components sync --tipo todos` e cópia dos configs MCP locais.
- Proibido `--no-verify`, pular gate ou marcar `[x]` sem o diff do código.
- Aprovação do usuário no fim de cada bloco (`gate_final` verde + `--aprovar`).

| Bloco | Tickets | Como roda |
|---|---|---|
| 1 Medição | 1–2 | Autônomo |
| 2 Uma cópia só (decisão A) | 3–6 | Com o usuário nas remoções (3, 5, 6) |
| 3 Gates no dono (decisão C) | 7–9 | Autônomo |
| 4 Fronteira que morde | 10–12 | Autônomo |
| 5 Sem stubs (decisão B) | 13–15 | Autônomo |
| 6 Micro-gates | 16 | Autônomo |
| 7 Contexto enxuto | 17–19 | Com o usuário no 19 (apagar grafos) |
| 8 Fechamento | 20–22 | Autônomo |

**Desvio consciente do padrão (§7, salvaguarda 4):** não ficam proxies de código em `tools/`. Os nomes antigos de comando da CLI continuam como apelido; a pasta `tools/` deixa só um `LEIA-ME.md` por 1 ciclo. Motivo: proxy em pasta mantém a duplicação viva e confunde os gates.

**Padrão para o planner:** `aidd-planner` vai para `modulos/01-governanca-e-qualidade/core/aidd-planner/` (a planta baixa é governança, junto do forge). Se o usuário preferir outro lugar, muda só o Ticket 4.

## Bloco 1 — Medição (Tickets 1–2) · autônomo
> Passo humano antes: criar a tag `pre-vsa-ciclo-03`.

### Ticket 1: Relatório de divergência entre tools e modulos (Refere-se a D15 / DoD 1)
- **Falha 15-D:** `D15. Fonte Única e Sincronização`
- **Artefato de Handoff:** `scripts/reconciliar_copias_vsa.py`
- **Gate do Ticket:** `python -m pytest -q -p no:cacheprovider tests/test_reconciliar_copias_vsa.py`
- **Requisito TDD (Red):** Num repo temporário com `tools/x` e `modulos/.../x`, um arquivo diferente e um arquivo só em `tools/`, `reconciliar --exigir-zero` precisa sair com exit 1 e listar os dois. Medido em 06/10: 45 arquivos divergentes no repo real.
- **Implementação Técnica:**
  - Mapa fixo `tools/aidd-<x>` → pasta canônica em `modulos/` (as 7 ferramentas migradas + planner).
  - Para cada par: idênticos, só em `tools/`, só em `modulos/`, divergentes (comparação sem CRLF; ignora `__pycache__`, `.pytest_cache`, `node_modules`, `*.db-wal`, `*.db-shm`).
  - Grava `docs/auditoria/modularizacao-vsa/ciclo-03/DIVERGENCIAS-TOOLS-MODULOS.json`; com `--exigir-zero`, exit 1 se houver divergente ou só-em-tools não resolvido.
  - Registra também o número de testes passando na bateria completa (linha de base do ciclo).
- **Verificação (Green):** teste passa; o JSON real lista as 45 divergências.
- **Construtor Prompt (EN):**
  - Write tests/test_reconciliar_copias_vsa.py first. Build temp repo with tools/x and modulos/a/x. One file differs, one file exists only under tools. Assert reconciliar with flag --exigir-zero exits 1 and lists both files. Run. Assert exit 1.
  - Implement scripts/reconciliar_copias_vsa.py. Fixed map from each tools/aidd-* folder to its canonical folder under modulos, including aidd-planner target modulos/01-governanca-e-qualidade/core/aidd-planner.
  - Compare ignoring CRLF and cache folders. Classify identical, only_tools, only_modulos, differing. Write DIVERGENCIAS-TOOLS-MODULOS.json into docs/auditoria/modularizacao-vsa/ciclo-03.
  - Run on real repo. Run test. Assert exit 0.

### Ticket 2: Gate de cópia única, em modo aviso (Refere-se a D13 / DoD 1)
- **Falha 15-D:** `D13. Quality Gates (Portões)`
- **Artefato de Handoff:** `modulos/04-nucleo-compartilhado/gates/G_COPIA_UNICA_VSA.py`
- **Gate do Ticket:** `python -m pytest -q -p no:cacheprovider modulos/04-nucleo-compartilhado/gates/test_g_copia_unica_vsa.py`
- **Requisito TDD (Red):** Em repo temporário, a mesma ferramenta em `tools/` e em `modulos/`, ou o mesmo `G_*.py` em dois lugares, gera violação; exit 0 em `aviso`, exit 1 em `bloqueio`.
- **Implementação Técnica:**
  - Lê `git ls-files`; acusa ferramenta presente em `tools/` e `modulos/`, gate com o mesmo nome em dois lugares (exceto os moldes de projeto do almoxarifado em `aidd_forge/templates/gates/`, que são peças) e skill com o mesmo nome em `componentes/compartilhado/skills` e `modulos/**/skills`.
  - `AIDD_COPIA_UNICA_MODO=aviso|bloqueio` (padrão `aviso`). Saída binária 0/1 (Lei #2).
  - Hook novo no `.pre-commit-config.yaml` em modo aviso.
- **Verificação (Green):** teste passa; no repo real, em aviso, lista as 7 ferramentas e os 69 gates duplicados.
- **Construtor Prompt (EN):**
  - Write modulos/04-nucleo-compartilhado/gates/test_g_copia_unica_vsa.py first. Temp git repo with same tool under tools and modulos, and same G_X.py in two folders. Assert both reported. Assert exit 0 with AIDD_COPIA_UNICA_MODO=aviso and exit 1 with bloqueio. Run. Assert exit 1.
  - Implement modulos/04-nucleo-compartilhado/gates/G_COPIA_UNICA_VSA.py. Scan git ls-files. Skip project template gates under aidd_forge/templates/gates. Exit only 0 or 1.
  - Register warn mode hook in .pre-commit-config.yaml. Run test. Assert exit 0.

## Bloco 2 — Uma cópia só (Tickets 3–6) · com o usuário nas remoções

### Ticket 3: Juntar o conteúdo único de tools em modulos (Refere-se a D15 / DoD 1)
- **Falha 15-D:** `D15. Fonte Única e Sincronização`
- **Artefato de Handoff:** `docs/auditoria/modularizacao-vsa/ciclo-03/RECONCILIACAO.md`
- **Gate do Ticket:** `python scripts/reconciliar_copias_vsa.py --exigir-zero && python -m pytest -q -p no:cacheprovider tests/test_reconciliar_copias_vsa.py`
- **Requisito TDD (Red):** `reconciliar --exigir-zero` sai com exit 1 enquanto houver divergência (45 em 06/10).
- **Implementação Técnica:**
  - Para cada arquivo divergente, decidir a versão final em `modulos/` juntando o que só existe em cada lado; registrar a decisão em `RECONCILIACAO.md` (arquivo, lado escolhido, motivo, hash final).
  - Conflito em que os dois lados têm lógica diferente: mostrar ao usuário antes de fechar.
  - Lixo não migra: `_cache_fake_item2`, `node_modules`, `benchmarks`/`reports` gerados.
  - `aidd-planner`: copiar para `modulos/01-governanca-e-qualidade/core/aidd-planner/` (só cópia; a remoção é no Ticket 5).
- **Verificação (Green):** `--exigir-zero` exit 0; testes de cada ferramenta, rodados de `modulos/`, verdes.
- **Construtor Prompt (EN):**
  - Run scripts/reconciliar_copias_vsa.py with flag --exigir-zero. Assert exit 1.
  - For each differing file merge unique logic from both sides into the modulos copy. Ask the user when both sides hold different logic. Record file, chosen side, reason and final hash in RECONCILIACAO.md.
  - Do not migrate cache, node_modules or generated reports. Copy tools/aidd-planner into modulos/01-governanca-e-qualidade/core/aidd-planner.
  - Run each tool test suite from its modulos folder. Run reconciliar with --exigir-zero. Assert exit 0.

### Ticket 4: Reapontar tudo para modulos (Refere-se a D1 / DoD 1)
- **Falha 15-D:** `D1. Arquitetura e Fronteiras`
- **Artefato de Handoff:** `tests/test_sem_referencia_tools.py`
- **Gate do Ticket:** `python -m pytest -q -p no:cacheprovider tests/test_sem_referencia_tools.py && python ecossistema.py components verify`
- **Requisito TDD (Red):** O teste reprova enquanto existir referência a `tools/aidd-`, `"tools", "aidd-` ou `TOOLS_DIR` em código, configs, gates, testes e docs vivos (83 arquivos `.py` em 06/10), fora de `secoes/`, `docs/relatorios/` e relatórios de ciclos fechados.
- **Implementação Técnica:**
  - `ecossistema.py`: apontar cada comando direto para `modulos/` (sem fallback para `tools/`); nomes antigos de comando seguem como apelido.
  - Reinstalar `aidd_forge` editável a partir de `modulos/01-governanca-e-qualidade/core/aidd-forge` e garantir o import a partir da raiz.
  - Atualizar `CATALOGO.json`, `MAPA-DONOS-FERRAMENTAS.json`, `gates/allowlist_fronteira.json`, `G_FRONTEIRA_FERRAMENTAS`, `contar_duplicatas.py`, `micro_gates.py`, `e2e_foto.py`, harnesses e skills.
- **Verificação (Green):** teste passa; `python -m pytest modulos/01-governanca-e-qualidade/core/aidd-forge/tests/test_almoxarifado.py` roda da raiz com exit 0.
- **Construtor Prompt (EN):**
  - Write tests/test_sem_referencia_tools.py first. Scan git ls-files for tools/aidd- and TOOLS_DIR. Allow only secoes, docs/relatorios and closed cycle reports. Run. Assert exit 1.
  - Point every ecossistema.py command straight to modulos with no tools fallback. Keep old command names as aliases.
  - Reinstall aidd_forge editable from modulos/01-governanca-e-qualidade/core/aidd-forge. Assert import works from repo root.
  - Update CATALOGO.json, MAPA-DONOS-FERRAMENTAS.json, gates/allowlist_fronteira.json, G_FRONTEIRA_FERRAMENTAS, contar_duplicatas.py, micro_gates.py, e2e_foto.py, harness configs and skills.
  - Run test. Run components verify. Assert exit 0.

### Ticket 5: Remover tools com prova de zero perda (Refere-se a D15 / DoD 1)
- **Falha 15-D:** `D15. Fonte Única e Sincronização`
- **Artefato de Handoff:** `tests/test_tools_extinto.py`
- **Gate do Ticket:** `python -m pytest -q -p no:cacheprovider tests/test_tools_extinto.py && python scripts/inventario_capacidades.py comparar docs/auditoria/fronteiras-ferramentas/ciclo-01/INVENTARIO-ANTES.json`
- **Requisito TDD (Red):** O teste reprova enquanto `git ls-files tools` tiver qualquer arquivo além de `tools/LEIA-ME.md`.
- **Implementação Técnica:**
  - Mostrar ao usuário a lista do que sai e onde ficou o conteúdo (Lei #7); só então `git rm -r tools/aidd-*`.
  - Criar `tools/LEIA-ME.md` apontando cada ferramenta para a pasta nova (sai no próximo ciclo).
  - Bateria completa: total de testes passando ≥ linha de base do Ticket 1.
- **Verificação (Green):** teste passa; `comparar` dá zero órfão; `G_COPIA_UNICA_VSA` não acusa mais ferramenta duplicada.
- **Construtor Prompt (EN):**
  - Write tests/test_tools_extinto.py first. Assert git ls-files tools returns only tools/LEIA-ME.md. Run. Assert exit 1.
  - Show the user the removal list and where each unique piece now lives. Wait for explicit approval.
  - Run git rm on tools/aidd-* folders. Write tools/LEIA-ME.md mapping each old folder to its modulos folder.
  - Run inventario_capacidades.py comparar. Assert zero orphans. Run full test battery. Assert passed count not below Ticket 1 baseline.

### Ticket 6: Limpar lixo versionado e pastas casca (Refere-se a D4 / DoD 2)
- **Falha 15-D:** `D4. Componentes e Fractalidade`
- **Artefato de Handoff:** `tests/test_modulos_sem_lixo.py`
- **Gate do Ticket:** `python -m pytest -q -p no:cacheprovider tests/test_modulos_sem_lixo.py`
- **Requisito TDD (Red):** Reprova se `modulos/` versionar `sandbox-forge-teste/`, `secoes/`, `_destino_teste*`, `*.egg-info`, `*.db-wal`, `*.db-shm`, `materiais-extras/` ou pasta cujo único arquivo é `__init__.py` (Sparse Scaffolding).
- **Implementação Técnica:**
  - `materiais-extras/examples` (decisão D4 de fronteiras): arquivar fora do repo em `C:\Users\trcnologia\arquivo-historico\aidd-enterprise-examples\` e remover do git.
  - Remover `sandbox-forge-teste`, `secoes/` internas, `_destino_teste_almoxarifado`; apagar as cascas `04/cli`, `04/sync`, `04/contracts`, `04/scripts`, `03/quarteto-studios`, `03/contracts` (voltam quando tiverem código real).
  - Lista mostrada ao usuário antes de apagar; entradas no `.gitignore`.
- **Verificação (Green):** teste passa.
- **Construtor Prompt (EN):**
  - Write tests/test_modulos_sem_lixo.py first. Fail on tracked sandbox-forge-teste, secoes, _destino_teste, egg-info, db-wal, db-shm, materiais-extras or any folder whose only file is __init__.py. Run. Assert exit 1.
  - Show the user the removal list. Wait for approval.
  - Archive materiais-extras/examples outside the repo then git rm it. Remove the other junk and empty shell folders. Add ignore rules.
  - Run test. Assert exit 0.

## Bloco 3 — Gates no dono (Tickets 7–9) · autônomo

### Ticket 7: Mapa de donos dos gates e runner lendo o mapa (Refere-se a D13 / DoD 3)
- **Falha 15-D:** `D13. Quality Gates (Portões)`
- **Artefato de Handoff:** `modulos/04-nucleo-compartilhado/contracts/MAPA-GATES.json`
- **Gate do Ticket:** `python -m pytest -q -p no:cacheprovider tests/test_mapa_gates.py`
- **Requisito TDD (Red):** Reprova se algum `G_*.py` da bateria não estiver no mapa, se um gate tiver dois donos, ou se o `audit`, o `.pre-commit-config.yaml` e o `G_SAIDA_BINARIA` não lerem os caminhos do mapa.
- **Implementação Técnica:**
  - Cada gate com `dono` (fatia ou `04-nucleo` para transversal) e `caminho_final`.
  - Transversais (ex.: `G_SEGREDOS`, `G_SAIDA_BINARIA`, `G_HARNESS_COMPAT`, `G_ECOSSISTEMA_INTEGRIDADE`) → `modulos/04-nucleo-compartilhado/gates/`; específicos (ex.: `G_aidd_forge`, `G_MIGRATION_ROT`, `G_INFRA_COMPOSE`) → fatia dona.
  - `audit`, pre-commit e os gates que varrem "todos os gates" passam a ler o mapa (ainda sem mover arquivos).
- **Verificação (Green):** teste passa; `audit` igual ao de antes.
- **Construtor Prompt (EN):**
  - Write tests/test_mapa_gates.py first. Assert every G_*.py in the audit battery appears once in MAPA-GATES.json with one owner and one final path. Assert audit runner, pre-commit config and G_SAIDA_BINARIA read paths from the map. Run. Assert exit 1.
  - Create modulos/04-nucleo-compartilhado/contracts/MAPA-GATES.json. Cross-cutting gates go to modulos/04-nucleo-compartilhado/gates. Tool specific gates go to the owner slice.
  - Make the audit runner, pre-commit config and gate scanners read the map. Do not move files yet.
  - Run test. Run audit. Assert same result as before.

### Ticket 8: Mover cada gate para o dono e extinguir gates da raiz (Refere-se a D13 / DoD 3)
- **Falha 15-D:** `D13. Quality Gates (Portões)`
- **Artefato de Handoff:** `tests/test_gates_raiz_extinta.py`
- **Gate do Ticket:** `python -m pytest -q -p no:cacheprovider tests/test_gates_raiz_extinta.py && AIDD_COPIA_UNICA_MODO=bloqueio python modulos/04-nucleo-compartilhado/gates/G_COPIA_UNICA_VSA.py`
- **Requisito TDD (Red):** Reprova se existir `G_*.py` em `gates/` da raiz ou se algum gate existir em mais de um lugar (69 duplicados em 06/10).
- **Implementação Técnica:**
  - `git mv` de cada gate para o `caminho_final` do mapa; apagar as cópias em `modulos/*/gates` que não são o dono; reconciliar `G_PORTAO_PROVA_QUE_MORDE` (versões diferentes).
  - Testes `test_g_*.py` acompanham o gate; `allowlist_fronteira.json` e `manifesto_harnesses.json` vão para `04-nucleo-compartilhado/contracts/`.
- **Verificação (Green):** teste passa; `G_COPIA_UNICA_VSA` em bloqueio com exit 0; `audit` com o mesmo número de gates.
- **Construtor Prompt (EN):**
  - Write tests/test_gates_raiz_extinta.py first. Fail if any G_*.py remains under root gates folder or any gate name exists twice. Run. Assert exit 1.
  - git mv each gate to its final path from MAPA-GATES.json. Delete non-owner copies under modulos. Merge the two G_PORTAO_PROVA_QUE_MORDE versions.
  - Move gate tests with their gate. Move allowlist_fronteira.json and manifesto_harnesses.json to modulos/04-nucleo-compartilhado/contracts.
  - Run test. Run G_COPIA_UNICA_VSA in bloqueio mode. Run audit. Assert exit 0.

### Ticket 9: G_SEGREDOS estável e mais rápido (Refere-se a D13 / DoD 3)
- **Falha 15-D:** `D13. Quality Gates (Portões)`
- **Artefato de Handoff:** `modulos/04-nucleo-compartilhado/gates/test_g_segredos_idempotente.py`
- **Gate do Ticket:** `python -m pytest -q -p no:cacheprovider modulos/04-nucleo-compartilhado/gates/test_g_segredos_idempotente.py`
- **Requisito TDD (Red):** Rodar o hook `g-segredos` duas vezes seguidas deixa `.secrets.baseline` alterado e o pre-commit marca "files were modified" (exit 1 em 06/10, 8 min).
- **Implementação Técnica:**
  - O gate só lê a baseline; atualização da baseline vira comando explícito separado.
  - Excluir do escopo o que não é código do repo (arquivo histórico, caches) e rodar só sobre arquivos staged no modo padrão.
- **Verificação (Green):** teste passa; `audit` com `G_SEGREDOS` verde e tempo medido registrado.
- **Construtor Prompt (EN):**
  - Write modulos/04-nucleo-compartilhado/gates/test_g_segredos_idempotente.py first. Run the gate twice in a temp repo. Assert baseline file unchanged and git status clean. Run. Assert exit 1.
  - Make G_SEGREDOS read-only on the baseline. Add a separate explicit command to refresh the baseline. Limit default scope to staged files.
  - Run test. Run audit. Assert G_SEGREDOS passes. Record its duration.

## Bloco 4 — Fronteira que morde (Tickets 10–12) · autônomo

### Ticket 10: Interface pública por fatia e fim da colisão de pacote core (Refere-se a D1 / DoD 4)
- **Falha 15-D:** `D1. Arquitetura e Fronteiras`
- **Artefato de Handoff:** `tests/test_interfaces_fatias.py`
- **Gate do Ticket:** `python -m pytest -q -p no:cacheprovider tests/test_interfaces_fatias.py`
- **Requisito TDD (Red):** Reprova se alguma das 7 fatias não tiver `interface.py` com `__all__`, ou se dois pacotes de fatias diferentes tiverem o mesmo nome importável (hoje `core` em pure e open).
- **Implementação Técnica:**
  - `interface.py` em cada fatia expondo só o que outras fatias consomem (ex.: forge expõe `obter_peca`, `caminho_peca`).
  - Renomear os pacotes que colidem para nomes únicos por fatia, atualizando imports e testes.
- **Verificação (Green):** teste passa; `test_fronteira_factory.py` do open coleta e passa.
- **Construtor Prompt (EN):**
  - Write tests/test_interfaces_fatias.py first. Assert each of the 7 slices has interface.py with __all__. Assert no two slices expose the same top level package name. Run. Assert exit 1.
  - Add interface.py per slice exposing only what other slices consume.
  - Rename colliding core packages to unique per slice names. Update imports and tests.
  - Run test. Run open slice test_fronteira_factory.py. Assert exit 0.

### Ticket 11: G_MODULO_FRONTEIRA que enxerga sys.path e caminhos (Refere-se a D13 / DoD 4)
- **Falha 15-D:** `D13. Quality Gates (Portões)`
- **Artefato de Handoff:** `modulos/04-nucleo-compartilhado/gates/G_MODULO_FRONTEIRA.py`
- **Gate do Ticket:** `python -m pytest -q -p no:cacheprovider modulos/04-nucleo-compartilhado/gates/test_g_modulo_fronteira.py`
- **Requisito TDD (Red):** Em repo temporário com duas fatias, cada um destes casos gera violação: `sys.path.insert` apontando para outra fatia, caminho literal `modulos/<outra-fatia>/...` fora de `interface.py`, referência a `tools/`. Exit 1 em `bloqueio`.
- **Implementação Técnica:**
  - Varredura AST de `sys.path.insert/append`, `Path(...)`/`os.path.join` com segmentos de outra fatia e imports de pacotes de outra fatia que não passem por `interface`.
  - Allowlist datada em `04-nucleo-compartilhado/contracts/allowlist_modulo_fronteira.json` que só pode diminuir; modo `aviso` padrão; hook no pre-commit.
  - Remover `G_AST_BOUNDED_CONTEXT`, `G_modularizacao_vsa` e `scripts/analisador_acoplamento_vsa.py` (cegos), com seus testes.
- **Verificação (Green):** teste passa (prova que morde); no repo real, em aviso, lista os acoplamentos atuais.
- **Construtor Prompt (EN):**
  - Write modulos/04-nucleo-compartilhado/gates/test_g_modulo_fronteira.py first. Temp repo with two slices. Plant sys.path.insert to the other slice, a literal path into the other slice and a tools reference. Assert each reported. Assert exit 1 in bloqueio mode. Assert test fails if allowlist grows. Run. Assert exit 1.
  - Implement G_MODULO_FRONTEIRA.py with AST scan of sys.path calls, path joins and imports crossing slices outside interface.py. Exit only 0 or 1.
  - Seed dated allowlist. Register warn mode hook. Delete G_AST_BOUNDED_CONTEXT, G_modularizacao_vsa and analisador_acoplamento_vsa with their tests.
  - Run test. Assert exit 0.

### Ticket 12: Almoxarifado proíbe destino dentro de modulos (Refere-se a D3 / DoD 4)
- **Falha 15-D:** `D3. Raio de Impacto e Isolamento`
- **Artefato de Handoff:** `modulos/01-governanca-e-qualidade/core/aidd-forge/tests/test_almoxarifado_guarda_modulos.py`
- **Gate do Ticket:** `python -m pytest -q -p no:cacheprovider modulos/01-governanca-e-qualidade/core/aidd-forge/tests/test_almoxarifado_guarda_modulos.py`
- **Requisito TDD (Red):** `obter_peca(..., destino=<algo dentro de modulos/>)` hoje copia (prova: `_destino_teste_almoxarifado` versionado em 06/10); precisa levantar erro.
- **Implementação Técnica:** a guarda de `almoxarifado.py` passa a recusar destino dentro de `modulos/`, `componentes/` e da raiz do ecossistema; testes do forge usam `tmp_path`.
- **Verificação (Green):** teste passa; nenhuma escrita nova em `modulos/` depois da suíte do forge.
- **Construtor Prompt (EN):**
  - Write the guard test first. Call obter_peca with destination inside modulos, inside componentes and at repo root. Assert each raises a clear error. Run. Assert exit 1.
  - Extend the guard in almoxarifado.py. Make forge tests write only under tmp_path.
  - Run test. Run forge suite. Assert git status unchanged under modulos.

## Bloco 5 — Sem stubs (Tickets 13–15) · autônomo

### Ticket 13: CLI modularizacao-vsa de verdade (Refere-se a D2 / DoD 5)
- **Falha 15-D:** `D2. Input e Gatilhos`
- **Artefato de Handoff:** `tests/test_vsa_cli_real.py`
- **Gate do Ticket:** `python -m pytest -q -p no:cacheprovider tests/test_vsa_cli_real.py`
- **Requisito TDD (Red):** Numa árvore temporária com uma fatia quebrada (sem `README.md` e com acoplamento cruzado), `verify` hoje sai com exit 0 e `status` imprime "4 macro-módulos íntegros".
- **Implementação Técnica:**
  - `inspect`: lista fatias, contagem de arquivos, testes e gates, medidos.
  - `verify`: roda `manifesto_modulos`, `validador_fractalidade_vsa`, `G_MODULO_FRONTEIRA` e `G_COPIA_UNICA_VSA`; exit 1 se qualquer um reprovar.
  - `status`: resumo medido, nunca texto fixo. Escala 0–5 permitida aqui (decisão B).
  - Incorporar o subcomando `index-subgraphs` que já está em andamento no working tree.
- **Verificação (Green):** teste passa; `verify` no repo real dá o mesmo veredito dos gates.
- **Construtor Prompt (EN):**
  - Write tests/test_vsa_cli_real.py first. Temp tree with one broken slice missing README.md and with a cross slice path. Assert verify exits non zero. Assert status output contains measured counts, not fixed text. Run. Assert exit 1.
  - Make inspect list slices with measured file, test and gate counts. Make verify call manifesto_modulos, validador_fractalidade_vsa, G_MODULO_FRONTEIRA and G_COPIA_UNICA_VSA. Make status print measured data.
  - Keep the pending index-subgraphs subcommand. Run test. Assert exit 0.

### Ticket 14: Ligar ou apagar os scripts órfãos do ciclo-01 (Refere-se a D8 / DoD 5)
- **Falha 15-D:** `D8. O que o Estágio Processa`
- **Artefato de Handoff:** `tests/test_sem_orfaos_vsa.py`
- **Gate do Ticket:** `python -m pytest -q -p no:cacheprovider tests/test_sem_orfaos_vsa.py`
- **Requisito TDD (Red):** Reprova se algum `scripts/*_vsa.py` ou `docs/padroes/contratos/manifesto_modulos.py` não tiver consumidor fora do próprio teste (7 em 06/10).
- **Implementação Técnica:**
  - Ligados ao `verify`: `manifesto_modulos`, `validador_fractalidade_vsa`.
  - Apagados (já cobertos por `worktree_hermetico.py`, `self_healing.py` e pelo novo gate): `isolamento_vsa`, `resiliencia_vsa`, `observabilidade_vsa`, `rollback_vsa`, `handoff_vsa`, com seus testes.
  - `ERRATA.md` no ciclo-01 corrigindo "Zero Stubs" do `RELATORIO-CONSTRUTOR.md` (o histórico não é reescrito).
- **Verificação (Green):** teste passa.
- **Construtor Prompt (EN):**
  - Write tests/test_sem_orfaos_vsa.py first. For each scripts/*_vsa.py and manifesto_modulos.py assert at least one non test consumer. Run. Assert exit 1.
  - Wire manifesto_modulos and validador_fractalidade_vsa into the verify subcommand. Delete isolamento_vsa, resiliencia_vsa, observabilidade_vsa, rollback_vsa and handoff_vsa with their tests.
  - Add ERRATA.md to docs/auditoria/modularizacao-vsa/ciclo-01 correcting the zero stubs claim. Run test. Assert exit 0.

### Ticket 15: Escopo da convenção de exit codes (Refere-se a D13 / DoD 5)
- **Falha 15-D:** `D13. Quality Gates (Portões)`
- **Artefato de Handoff:** `tests/test_convencao_exit_escopo.py`
- **Gate do Ticket:** `python -m pytest -q -p no:cacheprovider tests/test_convencao_exit_escopo.py`
- **Requisito TDD (Red):** Reprova se `CONVENCAO-EXIT-CODES-DETERMINISTICOS.md` não disser que a escala 0–5 vale só para scripts e CLIs, se algum gate importar `exit_codes` ou se `G_SAIDA_BINARIA` deixar de cobrir os gates nos caminhos novos do mapa.
- **Implementação Técnica:** atualizar a convenção (decisão B); `G_SAIDA_BINARIA` lê o `MAPA-GATES.json`.
- **Verificação (Green):** teste passa; `G_SAIDA_BINARIA` verde.
- **Construtor Prompt (EN):**
  - Write tests/test_convencao_exit_escopo.py first. Assert the convention doc limits the 0 to 5 scale to scripts and CLIs. Assert no gate imports exit_codes. Assert G_SAIDA_BINARIA scans all gate paths from MAPA-GATES.json. Run. Assert exit 1.
  - Update docs/protocolos/CONVENCAO-EXIT-CODES-DETERMINISTICOS.md. Make G_SAIDA_BINARIA read the gate map.
  - Run test. Run G_SAIDA_BINARIA. Assert exit 0.

## Bloco 6 — Micro-gates (Ticket 16) · autônomo

### Ticket 16: Micro-gates verdes por fatia e tempo de commit medido (Refere-se a D12 / DoD 6)
- **Falha 15-D:** `D12. Observabilidade e Frugalidade`
- **Artefato de Handoff:** `tests/test_micro_gates_fatias_verdes.py`
- **Gate do Ticket:** `python -m pytest -q -p no:cacheprovider tests/test_micro_gates_fatias_verdes.py`
- **Requisito TDD (Red):** Os 3 comandos por fatia de `micro_gates.py` saem com exit 1 na coleta (06/10).
- **Implementação Técnica:**
  - Prefixos só em `modulos/`; um comando por fatia e subfatia (pure, open, freedom, master, enterprise, ops, forge, planner) com `--rootdir` e `conftest` próprios.
  - Medir e gravar o tempo de um commit que toca uma fatia × bateria completa.
- **Verificação (Green):** teste passa; tempo registrado no `DOD.md`.
- **Construtor Prompt (EN):**
  - Write tests/test_micro_gates_fatias_verdes.py first. Run every slice command defined in micro_gates.py. Assert each exits 0. Run. Assert exit 1.
  - Keep only modulos prefixes. Split commands per sub slice with own rootdir and conftest.
  - Measure commit time for a one slice change and for the full battery. Write both numbers to docs/auditoria/modularizacao-vsa/ciclo-03/DOD.md. Run test. Assert exit 0.

## Bloco 7 — Contexto enxuto (Tickets 17–19) · com o usuário no 19

### Ticket 17: AGENTS.md local em cada fatia (Refere-se a D14 / DoD 7)
- **Falha 15-D:** `D14. Documentação Viva`
- **Artefato de Handoff:** `tests/test_agents_por_fatia.py`
- **Gate do Ticket:** `python -m pytest -q -p no:cacheprovider tests/test_agents_por_fatia.py`
- **Requisito TDD (Red):** Reprova se alguma das fatias e subfatias não tiver `AGENTS.md` com menos de 400 tokens e `README.md` com menos de 500 (hoje só 1 de 7 tem `AGENTS.md`).
- **Implementação Técnica:** `AGENTS.md` com regras e invariantes da fatia; `AGENTS.md` raiz ganha a tabela de despacho apontando para cada um; validador fractal passa a exigir os dois arquivos.
- **Verificação (Green):** teste passa.
- **Construtor Prompt (EN):**
  - Write tests/test_agents_por_fatia.py first. Assert each slice and sub slice has AGENTS.md under 400 tokens and README.md under 500 tokens. Run. Assert exit 1.
  - Write each AGENTS.md with slice rules and invariants. Add a dispatch table to the root AGENTS.md. Make validador_fractalidade_vsa require both files.
  - Run test. Assert exit 0.

### Ticket 18: Skills com dono único e sync lendo as fatias (Refere-se a D15 / DoD 7)
- **Falha 15-D:** `D15. Fonte Única e Sincronização`
- **Artefato de Handoff:** `tests/test_skills_fatias_sync.py`
- **Gate do Ticket:** `python -m pytest -q -p no:cacheprovider tests/test_skills_fatias_sync.py && python ecossistema.py components verify`
- **Requisito TDD (Red):** Reprova se a mesma skill existir em `componentes/compartilhado/skills` e em `modulos/**/skills` (4 em 06/10) ou se `components sync` ignorar skills que só existem numa fatia.
- **Implementação Técnica:** remover as 4 cópias; `components sync` lê as duas origens; `lazy_skills_scope.py` passa a ser usado pelo sync para gravar só as skills declaradas pela fatia em edição; medir skills carregadas antes/depois.
- **Verificação (Green):** teste passa; `components verify` exit 0; contagem antes/depois registrada.
- **Construtor Prompt (EN):**
  - Write tests/test_skills_fatias_sync.py first. Fail when one skill name exists in both componentes/compartilhado/skills and modulos skills. Fail when components sync skips a skill that only exists in a slice. Run. Assert exit 1.
  - Delete the 4 duplicated skills. Make components sync read both sources and use lazy_skills_scope.py for per slice scoping.
  - Record loaded skill count before and after. Run test and components verify. Assert exit 0.

### Ticket 19: Subgrafos com os nomes do padrão e grafos órfãos removidos (Refere-se a D12 / DoD 7)
- **Falha 15-D:** `D12. Observabilidade e Frugalidade`
- **Artefato de Handoff:** `tests/test_subgrafos_nomes_padrao.py`
- **Gate do Ticket:** `python -m pytest -q -p no:cacheprovider tests/test_subgrafos_nomes_padrao.py`
- **Requisito TDD (Red):** Reprova se `DOMINIOS_VSA` não usar os nomes do padrão §7.5 (`aidd-nucleo`, `modulo-governanca`, `triade-fluxo-pure`, `triade-fluxo-open`, `triade-fluxo-freedom`, `modulo-plataforma-ops`) ou se faltar a regra "consultar primeiro o subgrafo da fatia" no `AGENTS.md` raiz.
- **Implementação Técnica:** ajustar nomes, reindexar; listar ao usuário os ~15 projetos órfãos de worktrees no codebase-memory e apagar só com o OK dele.
- **Verificação (Green):** teste passa; `list_projects` sem órfãos.
- **Construtor Prompt (EN):**
  - Write tests/test_subgrafos_nomes_padrao.py first. Assert DOMINIOS_VSA keys match the six names from the architecture standard section 7.5. Assert root AGENTS.md tells agents to query the slice subgraph first. Run. Assert exit 1.
  - Rename domains and reindex. Show the user the orphan worktree projects in codebase-memory. Delete only after approval.
  - Run test. Assert exit 0.

## Bloco 8 — Fechamento (Tickets 20–22) · autônomo

### Ticket 20: Fiscais em bloqueio e allowlists enxutas (Refere-se a D13 / DoD 8)
- **Falha 15-D:** `D13. Quality Gates (Portões)`
- **Artefato de Handoff:** `tests/test_fiscais_vsa_bloqueio.py`
- **Gate do Ticket:** `python -m pytest -q -p no:cacheprovider tests/test_fiscais_vsa_bloqueio.py`
- **Requisito TDD (Red):** Reprova se `G_COPIA_UNICA_VSA` ou `G_MODULO_FRONTEIRA` não estiverem em `bloqueio` por padrão, ou se `allowlist_fronteira.json` tiver entrada sem motivo atual (100 perdoadas em 06/10; as 60 de `materiais-extras` somem com o Ticket 6).
- **Implementação Técnica:** padrão `bloqueio`; revisar cada entrada restante das allowlists (corrigir ou justificar com data).
- **Verificação (Green):** teste passa; os dois gates verdes em bloqueio.
- **Construtor Prompt (EN):**
  - Write tests/test_fiscais_vsa_bloqueio.py first. Assert both new gates default to bloqueio. Assert every allowlist entry points to an existing file and has a current reason. Run. Assert exit 1.
  - Switch defaults to bloqueio. Fix or justify each remaining allowlist entry.
  - Run test. Run both gates. Assert exit 0.

### Ticket 21: Foto E2E pós-VSA (Refere-se a D12 / DoD 8)
- **Falha 15-D:** `D12. Observabilidade e Frugalidade`
- **Artefato de Handoff:** `docs/auditoria/modularizacao-vsa/ciclo-03/COMPARACAO-E2E.md`
- **Gate do Ticket:** `python scripts/e2e_foto.py comparar --base ciclo-01 --novo ultimo`
- **Requisito TDD (Red):** Sem rodar a foto nova, o arquivo não existe e o gate reprova. A pasta base `TESTES_E2E-ecossistema-aidd` não existe mais (06/10).
- **Implementação Técnica:** restaurar a base ciclo-01 (a partir do histórico ou dos números de `fronteiras-ferramentas/ciclo-01/COMPARACAO-E2E.md`), rodar `e2e_foto.py rodar --ciclo auto` sobre `modulos/` e comparar; nenhuma métrica pode piorar.
- **Verificação (Green):** comparação com exit 0.
- **Construtor Prompt (EN):**
  - Restore the ciclo-01 E2E base folder from history or from the numbers in fronteiras-ferramentas COMPARACAO-E2E.md.
  - Run scripts/e2e_foto.py rodar with --ciclo auto against the modulos layout. Run comparar against ciclo-01.
  - Write the result to docs/auditoria/modularizacao-vsa/ciclo-03/COMPARACAO-E2E.md. Assert exit 0.

### Ticket 22: Laudo revisado, mapas e livros (Refere-se a D15 / DoD 8)
- **Falha 15-D:** `D15. Output Consolidado e Handoff`
- **Artefato de Handoff:** `docs/auditoria/modularizacao-vsa/ciclo-03/LAUDO-REVISADO.md`
- **Gate do Ticket:** `python ecossistema.py audit && python -m pytest -q -p no:cacheprovider tests/test_mapas_e_livros_em_dia.py`
- **Requisito TDD (Red):** `audit` com exit 1 (06/10) e mapas/livros citando `tools/aidd-*`.
- **Implementação Técnica:** laudo item a item do `DIAGNOSTICO.md` com o comando de prova; mapas visuais, livros e `docs/padroes/ARQUITETURA-MODULARIZACAO-VSA-ECOSSISTEMA.md` (status "Implementado", desvios registrados).
- **Verificação (Green):** `audit` exit 0 com tempo registrado; mapas e livros em dia.
- **Construtor Prompt (EN):**
  - Write LAUDO-REVISADO.md. For each finding in DIAGNOSTICO.md give the proof command and its exit code.
  - Regenerate visual maps and books. Update the architecture standard status and record the deviations.
  - Run audit. Run tests/test_mapas_e_livros_em_dia.py. Assert exit 0.
