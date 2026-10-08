# Plano de Evolução (Fase 2) - aidd-visual-maps

Este plano foi gerado pelo Arquiteto (Fase 2) do Pipeline Linear de Auditoria 4F, com o objetivo de readequar a ferramenta `aidd-visual-maps` em conformidade com o Laudo 15-D (`LAUDO-15D-INICIAL.md`, média 3,8) e a Definição de Pronto (`DOD.md`).

## Estratégia de Execução
Todos os tickets abaixo requerem ciclo TDD estrito (Red-Green-Refactor). Para cada requisito funcional, testes automatizados (exit 0 / exit 1) devem ser criados antes da implementação real, rodados e vistos falhando com exit 1 antes de qualquer correção.

Regras que valem para todos os tickets:
- **Isolamento:** cada ticket roda numa Git Worktree efêmera própria (`git worktree add` a partir da branch do ciclo), removida ao fim. Nada é gerado direto no checkout principal.
- **Exit code real:** redirecionar a saída para arquivo e capturar `$?` na mesma linha; nunca confiar em `cmd | tail`. Rodar com `TEMP=TMP=C:\Users\trcnologia\aidd-tmp`.
- **Fonte única:** nenhum número, nome ou lista é digitado à mão nos mapas (Lei #8). Todo ticket que muda um coletor ou um molde termina regenerando, nesta ordem: `catalogo_pecas.py` → os mapas (`mapa_visual.py <tipo>`) → índice → `livro_mapas.py`.
- **Proibido:** editar `docs/auditoria/CONFIG-EXECUCAO-USUARIO.json`; gravar artefato desta auditoria em `docs/planos/`.
- **Local do portão:** o DoD 6 cita `gates/G_aidd_visual_maps.py`. Depois da migração VSA não existe `gates/` na raiz; os portões de ferramenta moram em `modulos/<área>/gates/` (precedente: `modulos/01-governanca-e-qualidade/gates/G_aidd_diagnose.py`). O portão novo fica em `modulos/04-nucleo-compartilhado/gates/`, ao lado do `G_mapa_pecas.py`.
- **Catálogo só de fontes versionadas:** `.claude/settings.local.json` não é versionado e não existe nas worktrees. Se o catálogo o lesse, o `--check` de frescor daria resultados diferentes em cada máquina. Por isso o Ticket 4 cobre os hooks pelos scripts de `.claude/hooks/`, e não pelo arquivo local.

## Rastreabilidade (achado do laudo → ticket)

| Achado / Dimensão | Gravidade | Ticket |
|---|---|---|
| F1 catálogo velho aprovado + N4 livro idem | Grave / Alta | 1 |
| F2 portão `G_mapa_pecas` aprova lixo (M5 sobrevive) | Grave | 2 |
| F3 pasta órfã `docs/mapas-visuais/tecnicos/` | Grave | 3 |
| F5 coletores de hooks/MCPs incompletos + N9 hooks fora | Grave / Baixa | 4 |
| F4 sem mapa de pipelines, `modulos/` e agentes | Grave | 5 |
| F6 inglês no mapa não técnico + N6 DRY | Grave / Média | 6 |
| N2 "13 leis" + N7 contagens fixas | Alta / Média | 7 |
| N1 manual sem link do mapa-10 | Alta | 8 |
| D14 / DoD 7 FAILED + N3 escrita parcial | Alta | 9 |
| D3 / DoD 2 FAILED | — | 10 |
| D11 / DoD 4 FAILED: Not implemented | — | 11 |
| D12 / DoD 5 FAILED: Not implemented | — | 12 |
| D2 + D10 / DoD 1 parcial (sem `ecossistema.py visual-maps`) | — | 13 |
| D15 + D1 / DoD 8 parcial (sem manifesto, contrato com 3 afirmações falsas) | — | 14 |
| D13 / DoD 6 FAILED: Not implemented + N5 sem automação + N8 fora do AGENTS.md | Média | 15 |

### Ticket 1: Catálogo Conferido Contra o Repositório (Refere-se a D7 / D10 / DoD 6)
- **Falha 15-D:** `D10. Orquestração e Topologia`
- **Artefato de Handoff:** `tests/test_visual_maps_catalogo_fresco.py`
- **Requisito TDD (Red):** Num repositório de teste (`tmp_path`) com um catálogo commitado que cita um script já apagado, `mapa_visual.py <tipo> --check`, `livro_mapas.py --check` e `status_mapa` têm de reprovar. Hoje os 13 `--check` dão exit 0 e o índice mostra "concluído" → o teste falha (exit 1).
- **Implementação Técnica:**
  - Expor em `scripts/catalogo_pecas.py` uma função `catalogo_em_dia(raiz) -> tuple[bool, list[str]]` que gera o catálogo em memória e compara com o JSON em disco, devolvendo as chaves divergentes.
  - Fazer o `--check` de `mapa_visual.py` e de `livro_mapas.py` chamar essa função primeiro: catálogo velho → `[DESATUALIZADO] catálogo` e exit 1, antes de comparar o mapa.
  - `status_mapa` passa a marcar "desatualizado" quando o catálogo em disco não bate com o repositório.
  - Regenerar no repositório o catálogo, os 13 mapas (técnico e não técnico), o índice e as partes do livro, para a suíte ficar verde com o estado real (`handoff_vsa`, `rollback_vsa`, `G_AST_BOUNDED_CONTEXT`, `G_modularizacao_vsa` e o achado `arquivos_identicos_entre_donas` somem).
- **Verificação (Green):** O teste novo passa (exit 0). `python scripts/catalogo_pecas.py --check`, os 13 `mapa_visual.py <tipo> --check` e `livro_mapas.py --check` dão exit 0 juntos. Com um script apagado de propósito na worktree, todos dão exit 1.
- **Construtor Prompt (EN):**
  - Write test first: tests/test_visual_maps_catalogo_fresco.py. Build fixture repo in tmp_path. Commit catalog citing deleted script. Assert mapa_visual.py --check, livro_mapas.py --check and status_mapa all report stale. Run. Assert exit 1.
  - Add catalogo_em_dia(raiz) to scripts/catalogo_pecas.py. Build catalog in memory. Compare with JSON on disk. Return divergent keys.
  - Call catalogo_em_dia first inside --check of scripts/mapa_visual.py and scripts/livro_mapas.py. Stale catalog: print stale message, exit 1.
  - Make status_mapa return desatualizado when disk catalog differs from repo scan.
  - Regenerate in order: catalogo_pecas.py, all 13 map types, index, livro_mapas.py.
  - Run tests/test_visual_maps_catalogo_fresco.py, tests/test_mapa_visual.py, tests/test_catalogo_pecas.py, tests/test_livro_mapas.py, tests/test_mapas_e_livros_em_dia.py. Assert exit 0.

### Ticket 2: Portão G_mapa_pecas Confere Conteúdo, Não Só Existência (Refere-se a D13 / DoD 6)
- **Falha 15-D:** `D13. Quality Gates (Portões)`
- **Artefato de Handoff:** `modulos/04-nucleo-compartilhado/gates/G_mapa_pecas.py`
- **Requisito TDD (Red):** `G_mapa_pecas.py --mapas-dir <pasta com 14 HTML de 330 bytes "<html>LIXO">` tem de dar exit 1, e `--catalogo <JSON com ferramentas/skills/leis/encaixes vazios>` também. Hoje ambos dão exit 0 "APROVADO (100% OK)" → teste falha.
- **Implementação Técnica:**
  - `auditar_mapas_visuais`: cada mapa oficial tem de ser idêntico ao que `mapa_visual.montar(tipo, catalogo, ...)` produz (mesma regra do `--check`), e não apenas conter `<html` e ter mais de 100 caracteres.
  - `auditar_catalogo`: exigir listas não vazias em `ferramentas`, `skills`, `leis`, `encaixes`, `gates` e cada `totais.<chave>` igual a `len(<lista>)`.
  - Corrigir a docstring "13 mapas" para não citar número (a lista vem de `MAPAS_PREVISTOS`).
  - Repetir a mutação M5 do laudo (gate sem checar conteúdo): o mutante tem de morrer.
- **Verificação (Green):** HTML-lixo → exit 1; catálogo de listas vazias → exit 1; repositório real → exit 0; mutante M5 morto pelo teste novo.
- **Construtor Prompt (EN):**
  - Write test first: tests/test_g_mapa_pecas_conteudo.py. Feed 14 junk HTML files of 330 bytes via --mapas-dir. Feed catalog with empty lists via --catalogo. Run. Assert both exit 1 fails today.
  - Edit auditar_mapas_visuais in modulos/04-nucleo-compartilhado/gates/G_mapa_pecas.py. Compare each official map byte by byte with mapa_visual.montar output.
  - Edit auditar_catalogo. Require non-empty ferramentas, skills, leis, encaixes, gates. Require totais value equal to list length.
  - Remove hardcoded map count from module docstring.
  - Re-run mutant M5 (skip content check). Assert new test kills it.
  - Run tests/test_g_mapa_pecas_conteudo.py and tests/test_g_mapa_pecas.py. Assert exit 0. Run gate on real repo. Assert exit 0.

### Ticket 3: Remover a Pasta Órfã tecnicos/ e Barrar Órfãos Novos (Refere-se a D3 / D9 / DoD 7)
- **Falha 15-D:** `D3. Raio de Impacto e Isolamento`
- **Artefato de Handoff:** `tests/test_visual_maps_sem_orfaos.py`
- **Requisito TDD (Red):** Teste que lista todo `.html` versionado sob `docs/mapas-visuais/` e reprova qualquer arquivo que não seja: mapa oficial (`arquivo_mapa` de `MAPAS_PREVISTOS` + índice), seu par em `nao-tecnicos/`, o manual, ou molde em `moldes/` / `moldes-nao-tecnicos/`. Hoje os 14 arquivos de `docs/mapas-visuais/tecnicos/` reprovam → exit 1.
- **Implementação Técnica:**
  - Antes de apagar, conferir por busca que nada (scripts, manual, livro, mapas) aponta para `tecnicos/`; o único uso conhecido é um `tmp_path` em `tests/test_mapa_visual.py:427`, que não depende da pasta real.
  - `git rm -r docs/mapas-visuais/tecnicos/`.
  - Expor em `scripts/mapa_visual.py` uma função `arquivos_esperados() -> set[str]`, derivada de `MAPAS_PREVISTOS`, usada pelo teste (e depois pelo portão do Ticket 15).
- **Verificação (Green):** `git ls-files docs/mapas-visuais/tecnicos | wc -l` → 0; teste novo exit 0; criar um `.html` solto em `docs/mapas-visuais/` na worktree faz o teste voltar a exit 1.
- **Construtor Prompt (EN):**
  - Write test first: tests/test_visual_maps_sem_orfaos.py. List tracked HTML under docs/mapas-visuais/. Fail on any file outside expected set. Run. Assert exit 1 on 14 orphans in docs/mapas-visuais/tecnicos/.
  - Grep repo for references to docs/mapas-visuais/tecnicos/. Confirm none outside tmp_path tests.
  - Run git rm -r docs/mapas-visuais/tecnicos/.
  - Add arquivos_esperados() to scripts/mapa_visual.py. Derive set from MAPAS_PREVISTOS, index, manual, non-technical twins, mold folders.
  - Run tests/test_visual_maps_sem_orfaos.py and tests/test_mapa_visual.py. Assert exit 0. Drop stray HTML file. Assert exit 1. Remove it.

### Ticket 4: Coletores de Hooks e MCPs Completos (Refere-se a D4 / DoD 1)
- **Falha 15-D:** `D4. Componentes e Fractalidade`
- **Artefato de Handoff:** `tests/test_visual_maps_coletores.py`
- **Requisito TDD (Red):** Com repositório de teste contendo `.mcp.json` que registra `mobbin_mcp`, `componentes/compartilhado/mcps/mobbin_mcp/server.py` e 5 scripts em `.claude/hooks/` (3 ligados no `settings.json`), o catálogo tem de listar `mobbin_mcp` em `internos_das_ferramentas` e os 5 hooks. Hoje lista 3 MCPs internos e 3 hooks → exit 1.
- **Implementação Técnica:**
  - `coletar_mcps`: unir `mcps_proprios` das ferramentas, servidores registrados no `.mcp.json` e pastas `componentes/compartilhado/mcps/*/server.py`, sem duplicar por nome.
  - `coletar_hooks`: manter os gatilhos de `.claude/settings.json` e acrescentar cada `.claude/hooks/*.py` sem gatilho versionado com o status "sem gatilho no settings.json" (cobre `regra10_check.py` e `aidd_session_auto_hook.py`).
  - Não ler `.claude/settings.local.json` (não versionado; quebraria o `--check` de frescor do Ticket 1 entre máquinas). Registrar essa decisão no docstring.
  - Regenerar catálogo, mapas, índice e livro.
- **Verificação (Green):** Teste novo exit 0; catálogo real mostra `mobbin_mcp` e os 5 hooks; `mapa-07-conexoes.html` regenerado cita os dois.
- **Construtor Prompt (EN):**
  - Write test first: tests/test_visual_maps_coletores.py. Fixture repo with .mcp.json registering mobbin_mcp, componentes/compartilhado/mcps/mobbin_mcp/server.py, five scripts in .claude/hooks/, three wired in .claude/settings.json. Assert catalog lists mobbin_mcp and five hooks. Run. Assert exit 1.
  - Edit coletar_mcps in scripts/catalogo_pecas.py. Merge mcps_proprios, .mcp.json servers, componentes/compartilhado/mcps/*/server.py. Dedupe by name.
  - Edit coletar_hooks. Keep .claude/settings.json triggers. Add every .claude/hooks/*.py without tracked trigger, status "no trigger in settings.json".
  - Never read .claude/settings.local.json. Explain why in docstring: untracked, breaks catalog freshness check across machines.
  - Regenerate catalog, maps, index, book.
  - Run tests/test_visual_maps_coletores.py and tests/test_catalogo_pecas.py. Assert exit 0.

### Ticket 5: Mapas de Pipelines, Módulos VSA e Agentes (Refere-se a D5 / D9)
- **Falha 15-D:** `D5. Visão e Escopo`
- **Artefato de Handoff:** `tests/test_visual_maps_cobertura.py`
- **Requisito TDD (Red):** Teste que exige em `MAPAS_PREVISTOS` e em `GERADORES` os tipos `pipelines`, `modulos` e `agentes`, e no catálogo as chaves `pipelines` (Tríade 01/02/03 e fluxos melhoria→plan→orchestrate, aidd-ingest, aidd-audit-4f, aidd-evolution), `modulos` (as 4 áreas de `modulos/` e suas fatias) e `agentes` (templates de `modulos/03-plataforma-e-entrega/*/templates/agents/`, com os idênticos agrupados por hash). Hoje nenhum existe → exit 1.
- **Implementação Técnica:**
  - Coletores novos em `scripts/catalogo_pecas.py`: `coletar_pipelines` (a partir de `receita_triade` e das etapas declaradas nas skills de fluxo, sem lista digitada), `coletar_modulos` (varredura de `modulos/*/`), `coletar_agentes` (hash de conteúdo para marcar cópias idênticas entre enterprise e master).
  - Geradores `valores_pipelines`, `valores_modulos`, `valores_agentes` em `scripts/mapa_visual.py`, moldes técnicos em `docs/mapas-visuais/moldes/` e não técnicos em `docs/mapas-visuais/moldes-nao-tecnicos/`, com títulos em `TITULOS`.
  - Acrescentar os 3 tipos ao fim de `MAPAS_PREVISTOS` (sem renumerar os mapas existentes: viram `mapa-13`, `mapa-14`, `mapa-15`).
  - Regenerar catálogo, os 16 mapas, índice e livro (capítulos novos em `docs/livros/mapas-aidd/`).
- **Verificação (Green):** Teste novo exit 0; `grep -c agent_architect docs/mapas-visuais/mapa-15-agentes.html` ≥ 1; índice mostra 15 previstos e 0 "a criar"; `--check` dos 16 tipos exit 0.
- **Construtor Prompt (EN):**
  - Write test first: tests/test_visual_maps_cobertura.py. Require map types pipelines, modulos, agentes in MAPAS_PREVISTOS and GERADORES. Require catalog keys pipelines, modulos, agentes. Run. Assert exit 1.
  - Add coletar_pipelines, coletar_modulos, coletar_agentes to scripts/catalogo_pecas.py. Derive pipelines from receita_triade and flow skill steps. Scan modulos/*/ for areas and slices. Hash agent templates under modulos/03-plataforma-e-entrega/*/templates/agents/. Group identical copies.
  - Add valores_pipelines, valores_modulos, valores_agentes to scripts/mapa_visual.py. Add molds in docs/mapas-visuais/moldes/ and docs/mapas-visuais/moldes-nao-tecnicos/. Add TITULOS entries.
  - Append three types to end of MAPAS_PREVISTOS. Keep existing numbers.
  - Regenerate catalog, all maps, index, book chapters in docs/livros/mapas-aidd/.
  - Run tests/test_visual_maps_cobertura.py, tests/test_mapa_visual.py, tests/test_livro_mapas.py. Assert exit 0. Run --check for every type. Assert exit 0.

### Ticket 6: Mapa Não Técnico em PT-BR e Montagem Sem Cópia (Refere-se a D8 / DoD 3)
- **Falha 15-D:** `D8. O que o Estágio Processa`
- **Artefato de Handoff:** `scripts/compilar_mapas_nao_tecnicos.py`
- **Requisito TDD (Red):** Teste que varre `docs/mapas-visuais/nao-tecnicos/*.html` e conta frases-padrão em inglês (`Use when`, `Builds`, `Runs`, `Records`, `Use this`); hoje `mapa-05-skills.html` tem 124 → exit 1. Segundo teste: `compilar_nao_tecnico` não pode ter conferência de marcadores própria (tem de chamar a função compartilhada de `mapa_visual`) → hoje falha.
- **Implementação Técnica:**
  - Fonte PT-BR determinística por skill, nesta ordem: `description` do comando slash correspondente (já em PT-BR); senão, entrada em `docs/mapas-visuais/moldes-nao-tecnicos/descricoes-pt.json`. Skill sem nenhuma das duas → `ValueError` com a lista das que faltam e exit 1 (nunca cai para o inglês, nunca inventa texto).
  - Valores não técnicos próprios por tipo (`valores_nao_tecnicos_<tipo>`), que reaproveitam os técnicos e só trocam os campos de descrição; acabar com o uso direto de `mv.GERADORES` na versão não técnica.
  - DRY: extrair de `montar` uma `aplicar_molde(molde, valores, titulo, fragmento)` usada pelas duas versões; o caminho do catálogo passa a ser declarado só em `catalogo_pecas.SAIDA_PADRAO` e importado por `mapa_visual.py`, `livro_mapas.py` e `G_mapa_pecas.py`.
- **Verificação (Green):** 0 frases-padrão em inglês nos `nao-tecnicos/`; o caminho `catalogo-pecas.json` aparece declarado 1 vez (`grep -n "catalogo-pecas.json" scripts/*.py modulos/04-nucleo-compartilhado/gates/G_mapa_pecas.py`); testes exit 0.
- **Construtor Prompt (EN):**
  - Write test first: tests/test_visual_maps_nao_tecnico_ptbr.py. Count English boilerplate (Use when, Builds, Runs, Records, Use this) in docs/mapas-visuais/nao-tecnicos/*.html. Assert zero. Assert compilar_nao_tecnico calls shared mold helper. Run. Assert exit 1.
  - Resolve Portuguese text per skill: slash command description first, then docs/mapas-visuais/moldes-nao-tecnicos/descricoes-pt.json. Missing both: raise ValueError listing skills, exit 1. Never fall back to English.
  - Add per-type non-technical value builders. Reuse technical values. Swap only description fields. Stop calling mv.GERADORES directly from scripts/compilar_mapas_nao_tecnicos.py.
  - Extract aplicar_molde(molde, valores, titulo, fragmento) from montar in scripts/mapa_visual.py. Use it in both versions.
  - Declare catalog path once in catalogo_pecas.SAIDA_PADRAO. Import it in scripts/mapa_visual.py, scripts/livro_mapas.py, modulos/04-nucleo-compartilhado/gates/G_mapa_pecas.py.
  - Regenerate maps and book. Run tests/test_visual_maps_nao_tecnico_ptbr.py and tests/test_mapa_visual.py. Assert exit 0.

### Ticket 7: Nenhuma Contagem Digitada nos Moldes (Refere-se a D8 / D1)
- **Falha 15-D:** `D8. O que o Estágio Processa`
- **Artefato de Handoff:** `tests/test_visual_maps_sem_contagem_fixa.py`
- **Requisito TDD (Red):** Teste que varre `docs/mapas-visuais/moldes/*.html`, `docs/mapas-visuais/moldes-nao-tecnicos/*.html` e as strings de `MAPAS_PREVISTOS` atrás de número seguido de substantivo contável (`\b\d+\s+(leis|ferramentas|mapas|skills|guardas|scripts|hooks|comandos)\b`). Hoje acha "13 leis" (`moldes-nao-tecnicos/leis.html:18`), "8 ferramentas" (`moldes-nao-tecnicos/ferramentas.html:8`, `mapa_visual.py:55`) → exit 1.
- **Implementação Técnica:**
  - Trocar cada contagem por marcador (`{{TOTAL_LEIS}}`, `{{TOTAL_FERRAMENTAS}}`…) preenchido pelos geradores a partir de `totais` do catálogo.
  - Em `MAPAS_PREVISTOS`, reescrever a descrição sem número ("as ferramentas, seus comandos…").
  - Regenerar mapas e livro: o mapa de leis passa a dizer 14.
- **Verificação (Green):** Teste novo exit 0; `nao-tecnicos/mapa-01-leis.html` mostra o total igual a `totais.leis` do catálogo.
- **Construtor Prompt (EN):**
  - Write test first: tests/test_visual_maps_sem_contagem_fixa.py. Scan mold HTML and MAPAS_PREVISTOS strings with regex number plus countable noun (leis, ferramentas, mapas, skills, guardas, scripts, hooks, comandos). Run. Assert exit 1.
  - Replace each typed count with marker like {{TOTAL_LEIS}} or {{TOTAL_FERRAMENTAS}}. Fill markers from catalog totais in value builders.
  - Rewrite MAPAS_PREVISTOS descriptions without numbers in scripts/mapa_visual.py.
  - Regenerate maps and book. Assert law count in docs/mapas-visuais/nao-tecnicos/mapa-01-leis.html equals totais.leis.
  - Run tests/test_visual_maps_sem_contagem_fixa.py and tests/test_mapa_visual.py. Assert exit 0.

### Ticket 8: Manual Liga Todos os Mapas (Refere-se a D9 / D1)
- **Falha 15-D:** `D9. O que o Estágio Entrega`
- **Artefato de Handoff:** `docs/mapas-visuais/manual-montagem-aidd.html`
- **Requisito TDD (Red):** Teste que exige, no manual, um `href` para cada `arquivo_mapa(tipo)` de `MAPAS_PREVISTOS` e para o índice. Hoje falta `mapa-10-scripts.html` (e os 3 mapas do Ticket 5) → exit 1.
- **Implementação Técnica:**
  - Expor `links_faltando_no_manual(texto_manual) -> list[str]` em `scripts/mapa_visual.py`, derivada de `MAPAS_PREVISTOS`.
  - Acrescentar no manual os links que faltam (mapa-10 e os novos), no mesmo padrão `mapa-link` dos existentes.
  - Esta função será chamada pelo portão do Ticket 15, tornando verdadeira a frase da SKILL "The assembly manual links every map".
- **Verificação (Green):** `grep -c mapa-10-scripts docs/mapas-visuais/manual-montagem-aidd.html` ≥ 1; teste exit 0; apagar um link na worktree faz o teste voltar a exit 1.
- **Construtor Prompt (EN):**
  - Write test first: tests/test_visual_maps_manual_links.py. Require href in docs/mapas-visuais/manual-montagem-aidd.html for every arquivo_mapa of MAPAS_PREVISTOS plus index. Run. Assert exit 1 on missing mapa-10-scripts.html.
  - Add links_faltando_no_manual(texto_manual) to scripts/mapa_visual.py. Derive expected files from MAPAS_PREVISTOS.
  - Add missing links to manual using existing mapa-link pattern. Include new maps from ticket 5.
  - Run tests/test_visual_maps_manual_links.py. Assert exit 0. Delete one link. Assert exit 1. Restore.

### Ticket 9: Gravação Atômica do Par Técnico/Não Técnico e Rollback (Refere-se a D14 / DoD 7)
- **Falha 15-D:** `D14. Critério de Rejeição (Rollback)`
- **Artefato de Handoff:** `scripts/gravacao_atomica_mapas.py`
- **Requisito TDD (Red):** Num repositório de teste, apagar `moldes-nao-tecnicos/guardas.html` e rodar `mapa_visual.py guardas`: o teste exige exit 1 com mensagem `[ERRO]` (sem traceback) e o mapa técnico com o mesmo hash de antes. Hoje sai `FileNotFoundError` cru e o técnico já foi regravado → exit 1.
- **Implementação Técnica:**
  - Montar as duas versões (técnica e não técnica) em memória antes de gravar qualquer arquivo.
  - `gravar_lote(pares: dict[Path, str])`: grava cada texto em arquivo temporário na mesma pasta e só então faz `os.replace` de todos; se algo falhar, apaga os temporários e restaura o que já tinha sido trocado (cópia de segurança em memória).
  - Usar `gravar_lote` em `mapa_visual.main`, `compilar_mapas_nao_tecnicos.main` (todos os tipos num lote só) e `livro_mapas.py`.
  - `FileNotFoundError`/`OSError` de molde viram `[ERRO] <arquivo>` e exit 1.
- **Verificação (Green):** O cenário do laudo (N3) termina com exit 1, mensagem `[ERRO]`, técnico intacto (`md5sum -c` OK) e nenhum `*.tmp` sobrando em `docs/mapas-visuais/`.
- **Construtor Prompt (EN):**
  - Write test first: tests/test_visual_maps_rollback.py. Fixture repo. Delete moldes-nao-tecnicos/guardas.html. Run mapa_visual.py guardas. Assert exit 1, [ERRO] message, no traceback, technical map hash unchanged, no temp files left. Run. Assert test fails today.
  - Implement scripts/gravacao_atomica_mapas.py with gravar_lote(pares). Write temp file per target in same folder. Swap all via os.replace. On error remove temps and restore swapped files from memory backup.
  - Build technical and non-technical text in memory before any write in scripts/mapa_visual.py.
  - Use gravar_lote in scripts/mapa_visual.py, scripts/compilar_mapas_nao_tecnicos.py, scripts/livro_mapas.py.
  - Turn FileNotFoundError and OSError from molds into [ERRO] line and exit 1.
  - Run tests/test_visual_maps_rollback.py and tests/test_mapa_visual.py. Assert exit 0.

### Ticket 10: Escopo de Escrita Permitido (Refere-se a D3 / DoD 2)
- **Falha 15-D:** `D3. Raio de Impacto e Isolamento`
- **Artefato de Handoff:** `scripts/escopo_escrita_mapas.py`
- **Requisito TDD (Red):** `mapa_visual.py leis --saida <raiz>/AGENTS.md` (e qualquer `--saida` fora das pastas permitidas e fora do diretório temporário) tem de dar exit 1 sem tocar no arquivo. Hoje grava → exit 1 do teste.
- **Implementação Técnica:**
  - `garantir_escopo(caminho: Path) -> Path`: aceita só `docs/mapas-visuais/`, `docs/auditoria/mapa-pecas/`, `docs/livros/mapas-aidd/` ou um caminho dentro de `tempfile.gettempdir()`/worktree efêmera; o resto vira `[ERRO] escrita fora do escopo` e exit 1.
  - Chamar `garantir_escopo` dentro de `gravar_lote` (Ticket 9) e no `--saida` de `catalogo_pecas.py`, `mapa_visual.py` e `livro_mapas.py`.
  - Documentar no `SKILL.md` que regeneração completa roda em worktree efêmera (o CLI do Ticket 13 faz isso).
- **Verificação (Green):** `--saida AGENTS.md` → exit 1 e `git diff --quiet AGENTS.md` exit 0; `--saida <tmp>/x.html` → exit 0.
- **Construtor Prompt (EN):**
  - Write test first: tests/test_visual_maps_escopo.py. Run mapa_visual.py leis --saida pointing to AGENTS.md in fixture repo. Assert exit 1 and file untouched. Run. Assert test fails today.
  - Implement scripts/escopo_escrita_mapas.py with garantir_escopo(caminho). Allow docs/mapas-visuais/, docs/auditoria/mapa-pecas/, docs/livros/mapas-aidd/, temp dir, ephemeral worktree. Reject rest with [ERRO] and exit 1.
  - Call garantir_escopo inside gravar_lote and on --saida of scripts/catalogo_pecas.py, scripts/mapa_visual.py, scripts/livro_mapas.py.
  - Run tests/test_visual_maps_escopo.py. Assert exit 0. Assert --saida inside temp dir still exit 0.

### Ticket 11: Falha Estruturada e Retry com Backoff de I/O (Refere-se a D11 / DoD 4)
- **Falha 15-D:** `D11. Tratamento de Exceções e Fallback`
- **Artefato de Handoff:** `scripts/resiliencia_mapas.py`
- **Requisito TDD (Red):** Simular `PermissionError` nas 2 primeiras tentativas de `os.replace` (arquivo preso pelo navegador ou antivírus no Windows): o teste exige sucesso na 3ª tentativa com esperas crescentes; simular falha permanente exige exit 1 com uma linha JSON `{"estagio","tipo","arquivo","tentativas","erro"}`. Hoje não existe retry → exit 1.
- **Implementação Técnica:**
  - `com_retry(funcao, tentativas=3, espera_base=0.2, erros=(PermissionError, OSError))`: espera `espera_base * 2**n`; não repete `FileNotFoundError` nem `ValueError` (erro de dado não é transitório).
  - `FalhaMapa(estagio, tipo, arquivo, erro)` com `para_json()`; os `main()` de `catalogo_pecas.py`, `mapa_visual.py`, `compilar_mapas_nao_tecnicos.py` e `livro_mapas.py` capturam, imprimem a linha JSON e devolvem exit 1.
  - Envolver leituras de catálogo/molde e o `os.replace` de `gravar_lote` com `com_retry`.
- **Verificação (Green):** Teste de falha transitória passa na 3ª tentativa (espera medida ≥ 0,2 + 0,4 s com relógio injetado); falha permanente → exit 1 e JSON válido; nenhum traceback cru.
- **Construtor Prompt (EN):**
  - Write test first: tests/test_visual_maps_resiliencia.py. Patch os.replace to raise PermissionError twice then succeed. Assert success on third try with growing waits via injected sleep. Patch permanent failure. Assert exit 1 and one JSON line with keys estagio/tipo/arquivo/tentativas/erro. Run. Assert exit 1.
  - Implement scripts/resiliencia_mapas.py with com_retry(funcao, tentativas, espera_base, erros). Wait espera_base * 2**n. Never retry FileNotFoundError or ValueError.
  - Add FalhaMapa(estagio,tipo,arquivo,erro) with para_json().
  - Catch FalhaMapa in main of scripts/catalogo_pecas.py, scripts/mapa_visual.py, scripts/compilar_mapas_nao_tecnicos.py, scripts/livro_mapas.py. Print JSON line. Return exit 1.
  - Wrap catalog and mold reads plus os.replace in gravar_lote with com_retry.
  - Run tests/test_visual_maps_resiliencia.py and tests/test_mapa_visual.py. Assert exit 0.

### Ticket 12: Telemetria de Execução Persistida (Refere-se a D12 / DoD 5)
- **Falha 15-D:** `D12. Observabilidade e Frugalidade`
- **Artefato de Handoff:** `scripts/telemetria_mapas.py`
- **Requisito TDD (Red):** Rodar `mapa_visual.py leis --saida <tmp>` e `catalogo_pecas.py --saida <tmp>` com `AIDD_MEDICOES_DIR=<tmp>` e exigir uma linha nova em `<tmp>/aidd-visual-maps.jsonl` com `estagio`, `tipo`, `duracao_ms`, `arquivos_gravados`, `hash_catalogo`, `exit_code`, `llm_tokens`. Hoje nada é gravado (`grep -n "secoes\|logging\|perf_counter"` → 0) → exit 1.
- **Implementação Técnica:**
  - Context manager `medir(estagio, tipo)` com `time.perf_counter`, que acrescenta uma linha JSON em `secoes/medicoes/aidd-visual-maps.jsonl` (pasta já ignorada no `.gitignore`, então não suja a árvore nem o `--check`), com destino trocável por `AIDD_MEDICOES_DIR`.
  - `llm_tokens: 0` explícito (motor sem LLM: frugalidade registrada, não presumida).
  - Usar `medir` nos 4 `main()`, inclusive no `--check` (com `arquivos_gravados: 0`).
- **Verificação (Green):** Teste exit 0; depois de uma regeneração real, `secoes/medicoes/aidd-visual-maps.jsonl` tem uma linha por estágio e `git status --porcelain secoes/` continua vazio.
- **Construtor Prompt (EN):**
  - Write test first: tests/test_visual_maps_telemetria.py. Set AIDD_MEDICOES_DIR to tmp_path. Run mapa_visual.py leis --saida and catalogo_pecas.py --saida into tmp_path. Assert new line in aidd-visual-maps.jsonl with estagio, tipo, duracao_ms, arquivos_gravados, hash_catalogo, exit_code, llm_tokens. Run. Assert exit 1.
  - Implement scripts/telemetria_mapas.py with context manager medir(estagio, tipo). Use time.perf_counter. Append JSON line to secoes/medicoes/aidd-visual-maps.jsonl. Honor AIDD_MEDICOES_DIR override.
  - Record llm_tokens 0 explicitly.
  - Wrap main of scripts/catalogo_pecas.py, scripts/mapa_visual.py, scripts/compilar_mapas_nao_tecnicos.py, scripts/livro_mapas.py with medir, including --check runs.
  - Run tests/test_visual_maps_telemetria.py. Assert exit 0. Assert git status --porcelain secoes/ stays empty.

### Ticket 13: CLI Unificada e Ordem do Pipeline Garantida (Refere-se a D2 / D10 / DoD 1)
- **Falha 15-D:** `D2. Input e Gatilhos`
- **Artefato de Handoff:** `componentes/compartilhado/skills/aidd-visual-maps/scripts/cli.py`
- **Requisito TDD (Red):** `python ecossistema.py visual-maps check` tem de existir e dar exit 0 no repositório real; hoje dá exit 1 "comando desconhecido 'visual-maps'". Segundo teste: `visual-maps gerar` num repositório de teste com catálogo velho tem de regenerar o catálogo antes dos mapas (ordem catálogo → mapas → índice → livro) → hoje não existe.
- **Implementação Técnica:**
  - `cli.py` com subcomandos `catalogo`, `mapa <tipo>`, `gerar` (pipeline completo na ordem obrigatória, rodando numa worktree efêmera e promovendo só os arquivos do escopo do Ticket 10 via `gravar_lote`) e `check` (frescor do catálogo + `--check` de todos os mapas + livro, exit 1 no primeiro desvio).
  - `cmd_visual_maps` em `ecossistema.py`, no mesmo padrão de `cmd_diagnose`, registrado como `visual-maps` e `aidd-visual-maps`.
  - Fonte canônica em `componentes/compartilhado/skills/aidd-visual-maps/`; rodar o sync de componentes para as cópias por harness.
- **Verificação (Green):** `python ecossistema.py visual-maps check` → exit 0; `gerar` com catálogo velho deixa catálogo, mapas e livro em dia (o `check` seguinte dá exit 0); cópias por harness com o mesmo hash.
- **Construtor Prompt (EN):**
  - Write test first: tests/test_visual_maps_cli.py. Run python ecossistema.py visual-maps check. Assert exit 0 required; fails today with unknown command. Assert gerar on stale fixture catalog refreshes catalog before maps. Run. Assert exit 1.
  - Implement componentes/compartilhado/skills/aidd-visual-maps/scripts/cli.py. Subcommands: catalogo, mapa <tipo>, gerar, check.
  - Make gerar run catalog, maps, index, book in fixed order inside ephemeral worktree. Promote only allowed paths via gravar_lote.
  - Make check run catalog freshness, every map --check, book --check. Exit 1 on first drift.
  - Add cmd_visual_maps to ecossistema.py like cmd_diagnose. Register visual-maps and aidd-visual-maps.
  - Run components sync. Assert harness copies match canonical hash.
  - Run tests/test_visual_maps_cli.py. Assert exit 0.

### Ticket 14: Manifesto dos Mapas, Handoff ao Livro e Contrato da SKILL (Refere-se a D15 / D1 / DoD 8)
- **Falha 15-D:** `D15. Output Consolidado e Handoff`
- **Artefato de Handoff:** `componentes/compartilhado/skills/aidd-visual-maps/scripts/handoff.py`
- **Requisito TDD (Red):** Depois de `visual-maps gerar`, o teste exige `docs/mapas-visuais/MANIFESTO-MAPAS.json` com `hash_catalogo` (sha256 do catálogo), e por mapa `arquivo`, `versao` (técnica/não técnica), `sha256` e `status`; e um `handoff-livro` com a lista de partes de `docs/livros/mapas-aidd/` para o `aidd-textbook`. Hoje nenhum existe → exit 1.
- **Implementação Técnica:**
  - `emitir_manifesto(catalogo, mapas)` determinístico (sem data/hora, para o `check` não oscilar; tempos ficam na telemetria do Ticket 12), gravado por `gravar_lote` no fim do `gerar`.
  - `conferir_manifesto()` usado pelo `check`: hash de cada arquivo e do catálogo têm de bater.
  - Handoff ao livro: o `gerar` termina chamando o build do `aidd-textbook` para `docs/livros/mapas-aidd/` (hoje é passo manual na docstring de `livro_mapas.py`) e registra o resultado no manifesto.
  - Atualizar o `SKILL.md` canônico: Stopping Checklist com `python ecossistema.py visual-maps check`; afirmações (a), (b), (c) do laudo passam a ser verdadeiras e citam o portão do Ticket 15; sincronizar as 6 cópias por harness.
- **Verificação (Green):** Teste exit 0; alterar 1 byte de um mapa na worktree faz `visual-maps check` dar exit 1 citando o manifesto; as 7 cópias do `SKILL.md` com o mesmo hash.
- **Construtor Prompt (EN):**
  - Write test first: tests/test_visual_maps_manifesto.py. After visual-maps gerar require docs/mapas-visuais/MANIFESTO-MAPAS.json with hash_catalogo and per-map keys arquivo/versao/sha256/status. Require book handoff list for aidd-textbook. Run. Assert exit 1.
  - Implement componentes/compartilhado/skills/aidd-visual-maps/scripts/handoff.py with emitir_manifesto and conferir_manifesto. No timestamps in manifest. Write via gravar_lote.
  - Call conferir_manifesto from cli.py check.
  - Make gerar call aidd-textbook build for docs/livros/mapas-aidd/. Record result in manifest.
  - Update canonical SKILL.md. Add visual-maps check to Stopping Checklist. Make manual, gate and index claims true. Run components sync.
  - Run tests/test_visual_maps_manifesto.py. Assert exit 0. Flip one byte in a map. Assert check exit 1.

### Ticket 15: Portão G_aidd_visual_maps no Pre-commit e Registro no AGENTS.md (Refere-se a D13 / DoD 6)
- **Falha 15-D:** `D13. Quality Gates (Portões)`
- **Artefato de Handoff:** `modulos/04-nucleo-compartilhado/gates/G_aidd_visual_maps.py`
- **Requisito TDD (Red):** Testes que apontam o portão para fixtures de saída ilusória e exigem exit 1 em cada uma: catálogo velho (F1), HTML-lixo (F2), arquivo órfão (F3), frase-padrão em inglês no não técnico (F6), contagem digitada no molde (N2), link faltando no manual (N1), manifesto com hash divergente (Ticket 14). Hoje o portão não existe (`ls` → "No such file") → exit 1.
- **Implementação Técnica:**
  - O portão reaproveita as funções dos tickets anteriores (`catalogo_em_dia`, `arquivos_esperados`, `links_faltando_no_manual`, `conferir_manifesto`, detector de inglês e de contagem fixa), sem reimplementar regra; saída no padrão dos outros portões (`APROVADO`/`REPROVADO` + motivo por linha) e exit 0/1 (Lei #8 e Lei #13).
  - Registrar `g-aidd-visual-maps` no `.pre-commit-config.yaml` (mesmo formato do `g-aidd-diagnose`) e atualizar qualquer registro/contagem de portões que os testes conferem (procurar `G_aidd_diagnose` em `tests/`).
  - Medir o tempo do portão no pre-commit e registrar no relatório do Construtor (o ciclo agilidade-gates baixou o commit para 2-3 min; o portão não pode desfazer isso).
  - Citar a skill `aidd-visual-maps` e o portão no `AGENTS.md` (N8), conferindo antes se outra sessão está editando o arquivo.
- **Verificação (Green):** As 7 fixtures ilusórias → exit 1 cada; repositório real → exit 0; `pre-commit run g-aidd-visual-maps --all-files` → exit 0; `grep -c aidd-visual-maps AGENTS.md` ≥ 1.
- **Construtor Prompt (EN):**
  - Write test first: tests/test_g_aidd_visual_maps.py. Point gate at fixtures: stale catalog, junk HTML, orphan file, English boilerplate in non-technical map, typed count in mold, missing manual link, manifest hash mismatch. Assert exit 1 each. Run. Assert exit 1 because gate file missing.
  - Implement modulos/04-nucleo-compartilhado/gates/G_aidd_visual_maps.py. Reuse catalogo_em_dia, arquivos_esperados, links_faltando_no_manual, conferir_manifesto, English and typed-count detectors. Print APROVADO or REPROVADO with one reason per line. Exit 0 or 1.
  - Register g-aidd-visual-maps in .pre-commit-config.yaml like g-aidd-diagnose. Update gate registry or count tests found by grep G_aidd_diagnose in tests/.
  - Time gate inside pre-commit. Report duration in builder report.
  - Check AGENTS.md for concurrent edits. Add aidd-visual-maps skill and gate entry.
  - Run tests/test_g_aidd_visual_maps.py. Assert exit 0. Run gate on real repo. Assert exit 0. Run pre-commit run g-aidd-visual-maps --all-files. Assert exit 0.
