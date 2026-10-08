# Laudo 15-D Inicial — `aidd-visual-maps`

> Auditoria de 2026-10-08 (Fase 1 — Inspetor, branch `audit/auditoria-aidd-visual-maps-ciclo-01`, HEAD `d132b337`).
> Todo achado tem reprodução real nesta sessão (comando + exit code capturado por redirecionamento para arquivo, `$?` na mesma linha). Nada foi regenerado no repositório: catálogo fresco em `C:\Users\trcnologia\aidd-tmp\vm\cat_novo.json` (`catalogo_pecas.py --saida`), mutações e escrita parcial numa cópia `git archive HEAD` + `tests/` em `aidd-tmp\vm\sb`.
> Mapeamento graph-first (Lei #14): `search_graph`, `get_code_snippet` e `trace_path` (codebase-memory-mcp, projeto `ecossistema-aidd`) antes de qualquer grep.

## 1. Identificação da Ferramenta
- **Nome da Ferramenta:** `aidd-visual-maps`
- **Descrição Breve:** Gera mapas HTML (técnico e não técnico) de cada tipo de peça do ecossistema a partir de um molde PT-BR com `{{MARCADORES}}` mais o catálogo `docs/auditoria/mapa-pecas/catalogo-pecas.json`, com índice de status, manual de montagem e livro.
- **Comando de Gatilho:** `/aidd-visual-maps` (só slash command) + `python scripts/mapa_visual.py <tipo> [--check|--saida|--fragmento]`. `python ecossistema.py visual-maps` → **exit 1** ("comando desconhecido 'visual-maps'").

### Resumo dos achados conhecidos (F1–F6)

| ID | Veredito | Prova (comando → exit) |
|---|---|---|
| F1 | **CONFIRMADO (grave)** | `catalogo_pecas.py --check` → 1; os 13 `mapa_visual.py <tipo> --check` → 0; `G_mapa_pecas.py` → 0; com catálogo fresco, 8/13 mapas mudariam |
| F2 | **CONFIRMADO (grave), pior que o descrito** | 14 arquivos de 330 bytes `<html>LIXO…` → gate exit 0; catálogo falso de listas vazias → gate exit 0; mutante M5 sobrevive aos 7 testes do gate |
| F3 | **CONFIRMADO (grave)** | `docs/mapas-visuais/tecnicos/` tem 14 arquivos versionados, 14/14 diferem de `docs/mapas-visuais/`; nenhum script grava ali |
| F4 | **CONFIRMADO (grave)** | `MAPAS_PREVISTOS` (`scripts/mapa_visual.py:53`) tem 12 tipos, nenhum de pipelines, `modulos/` ou subagentes |
| F5 | **CONFIRMADO (grave)** | `coletar_hooks` lê só `.claude/settings.json` (`scripts/catalogo_pecas.py:260-275`); `mobbin_mcp` fica fora de `internos_das_ferramentas` |
| F6 | **CONFIRMADO (grave)** | `nao-tecnicos/mapa-05-skills.html`: 124 frases-padrão em inglês ("Use when", "Builds"…); o compilador reusa `mv.GERADORES` (`scripts/compilar_mapas_nao_tecnicos.py:27`) |

### Achados novos (N1–N9)

| ID | Gravidade | Achado | Prova |
|---|---|---|---|
| N1 | Alta | O manual não tem link para `mapa-10-scripts.html`, e mesmo assim o gate passa (a SKILL diz que o gate barra link faltante) | `grep -c mapa-10-scripts manual-montagem-aidd.html` → 0; varredura: 12 `mapa-link` no manual; gate exit 0 |
| N2 | Alta | Contagem fixa errada no molde não técnico: "As 13 leis", mas o catálogo tem 14 (fere o Guardrail "NEVER type a count") | `moldes-nao-tecnicos/leis.html:18`, `nao-tecnicos/mapa-01-leis.html:129`; `totais.leis = 14` |
| N3 | Alta | Escrita parcial: se o molde não técnico falta, o mapa técnico já foi regravado, a dupla fica desencontrada e sai traceback cru | sandbox: `mapa_visual.py guardas` → exit 1 `FileNotFoundError`; `md5sum -c` do técnico → "did NOT match" |
| N4 | Alta | `livro_mapas.py --check` também dá exit 0 com catálogo desatualizado (mesma causa de F1) | `livro_mapas.py --check` → 0 "[OK] Partes do livro em dia." enquanto `catalogo_pecas.py --check` → 1 |
| N5 | Média | Nenhuma automação roda `catalogo_pecas.py --check`, `mapa_visual.py --check` ou `livro_mapas.py --check` | `grep catalogo_pecas\|mapa_visual .pre-commit-config.yaml` → exit 1; varredura de `*.py/*.yaml/*.json/*.toml` só acha os próprios scripts |
| N6 | Média | DRY: `compilar_nao_tecnico` (`compilar_mapas_nao_tecnicos.py:22-49`) copia `montar` (`mapa_visual.py:649-665`): conferência de marcadores, `re.sub` e cabeçalho. O caminho do catálogo é declarado 4 vezes | `mapa_visual.py:37`, `livro_mapas.py:26`, `G_mapa_pecas.py:133`, `catalogo_pecas.py:40` (`SAIDA_PADRAO`) |
| N7 | Média | Texto fixo que vai envelhecer: "as 8 ferramentas" (`mapa_visual.py:55`) e "8 ferramentas" (`moldes-nao-tecnicos/ferramentas.html:8`); docstring do gate diz "13 mapas", mas a lista tem 14 arquivos (`G_mapa_pecas.py:11` vs `:31-46`) | grep → linhas citadas |
| N8 | Média | A skill não aparece no `AGENTS.md`; o portão `gates/G_aidd_visual_maps.py` exigido pelo DoD 6 não existe | `grep -c aidd-visual-maps AGENTS.md` → 0; `ls gates/G_aidd_visual_maps.py modulos/*/gates/G_aidd_visual_maps.py` → "No such file" |
| N9 | Baixa | `.claude/hooks/` tem 5 scripts .py, mas o catálogo/mapa conhece 3 (`regra10_check.py` e `aidd_session_auto_hook.py` ficam fora) | `ls .claude/hooks/`; `cat_novo.json` `hooks` = 3 itens |

## 2. A Matriz Anatômica (Lens 15-D)

### Fase 1: Governança e Blindagem
- **D1. Contratos e Regras:** — **Nota 5/10.** `.agents/skills/aidd-visual-maps/SKILL.md` (71 linhas) mais 6 cópias por harness, todas com o mesmo hash `148db4ac` (md5 das 7 cópias). O contrato tem três afirmações falsas, cada uma provada por comando:
  - (a) "The assembly manual links every map" (`SKILL.md:13`) — falso: `mapa-10-scripts` não tem link (N1).
  - (b) Failure Modes: "`G_mapa_pecas` fails at pre-commit: a required map or manual link is missing" — falso: com 14 HTMLs-lixo sem nenhum link, o gate dá exit 0 (F2).
  - (c) "Done when the index shows every map as concluded" — o índice mostra 13 "concluído", mas com o catálogo fresco `status_mapa` dá 7/12 `desatualizado` (F1).
  - O Stopping Checklist não pede `catalogo_pecas.py --check`.
  - A skill não está citada no `AGENTS.md` (N8).
- **D2. Input e Gatilhos:** — **Nota 5/10.** Entrada formal via argparse: `tipo` ∈ 13 `GERADORES` (`scripts/mapa_visual.py:638-646`), `--saida`, `--fragmento`, `--link-manual`, `--check` (`:668-675`). Requisito de estado: o catálogo em disco (`:677-679`). Esse catálogo é aceito sem conferir se ainda bate com o repositório (F1). Não há CLI unificada: `python ecossistema.py visual-maps` → exit 1 (DoD 1 parcial: só scripts locais).
- **D3. Raio de Impacto e Isolamento:** — **Nota 4/10.** Por padrão grava direto em `docs/mapas-visuais/` e `docs/mapas-visuais/nao-tecnicos/` (`scripts/mapa_visual.py:701-705`), sem worktree e sem gravação atômica. `--saida` isola só a versão técnica. A escrita parcial está provada (N3: técnico regravado, não técnico falhou, exit 1). Contaminação do repositório: a pasta órfã `docs/mapas-visuais/tecnicos/` (14 arquivos, 14/14 diferentes dos oficiais, sem gerador) — F3 confirmado (`git ls-files docs/mapas-visuais/tecnicos | wc -l` → 14). O único "uso" de `tecnicos` no código é um `tmp_path` de teste (`tests/test_mapa_visual.py:427`). **DoD 2: FAILED.**
- **D4. Componentes e Fractalidade:** — **Nota 4/10.** Não usa MCP nem subagente: é um motor Python puro, com `pastas_ferramentas` (`mapa_visual.py:32`) e `compilar_mapas_nao_tecnicos` (import tardio, `:691`). O coletor que alimenta os mapas é incompleto (F5):
  - `coletar_hooks` só lê `.claude/settings.json`. No checkout principal, `.claude/settings.local.json` tem 2 hooks (`PostToolUse`, `Stop`, impeccable) que nunca entram. Esse arquivo não é versionado (`git ls-files` → 0).
  - `coletar_mcps` só enxerga `f["mcps_proprios"]` das ferramentas em `modulos/` (`catalogo_pecas.py:251`). `componentes/compartilhado/mcps/mobbin_mcp/server.py` existe e está registrado no `.mcp.json:69-72`, mas `internos_das_ferramentas` tem só 3 itens (cloudflare, docker, verificador-cve).
  - Hooks fora do catálogo: N9.

### Fase 2: O Chão de Fábrica (Workflow Agêntico)
- **D5. Visão e Escopo:** — **Nota 5/10.** Visão correta: nada digitado à mão, tudo sai do catálogo. A cobertura tem buracos (F4):
  - **Pipelines:** os fluxos de várias etapas (melhoria→plan→orchestrate, aidd-ingest, aidd-audit-4f, aidd-evolution) só aparecem como item de lista em `mapa-05/06`. A Tríade 01/02/03 só aparece como etapas da receita no `mapa-03-encaixes`, sem um mapa de pipeline.
  - **`modulos/`:** as 4 áreas e suas fatias VSA não têm mapa; aparecem só como caminho citado em `mapa-03/07/09`.
  - **Subagentes:** `.claude/agents/` não existe no repositório (`ls` → "No such file"). Os 18 templates de agente em `modulos/03-plataforma-e-entrega/*/templates/agents/` (9 idênticos entre enterprise e master, `cmp` → 9 iguais) não aparecem em mapa nenhum (`grep agent_architect mapa-*.html` → 0).
  - **Fidelidade:** 8/13 mapas descrevem um ecossistema antigo (F1), e "13 leis" está errado (N2).
- **[Estágio 1 — Coleta] D6. O que o Estágio Faz:** — **Nota 6/10.** `scripts/catalogo_pecas.py` varre o repositório e grava o catálogo (20 chaves: `achados`, `gates`, `skills`, `hooks`, `mcps`, `receita_triade`…).
- **[Estágio 2 — Montagem] D6. O que o Estágio Faz:** — `montar()` (`mapa_visual.py:649-665`) junta o molde com `valores_<tipo>(cat)` e recusa marcadores sem par (`ValueError`).
- **[Estágio 3 — Não técnico] D6. O que o Estágio Faz:** — `gravar_ou_conferir()` (`compilar_mapas_nao_tecnicos.py:52-67`) gera a versão "conceitual". **[Estágio 4 — Livro]** `scripts/livro_mapas.py` gera as partes de `docs/livros/mapas-aidd/`.
- **[Estágio 1→4] D7. O que o Estágio Recebe:** — **Nota 4/10.**
  - Estágio 1 recebe a árvore do repositório.
  - Estágios 2, 3 e 4 recebem **o JSON em disco**, não o repositório. Esse é o defeito estrutural de F1: o catálogo commitado tem `handoff_vsa`, `rollback_vsa` (scripts apagados; `ls scripts | grep vsa` → só 3 outros), `G_AST_BOUNDED_CONTEXT` (5×) e `G_modularizacao_vsa` (4×). O catálogo fresco tem 0 de cada.
  - O achado resolvido `arquivos_identicos_entre_donas: gates + modulos: 69` continua impresso em `mapa-02-ferramentas.html`. No catálogo fresco essa lista é `[]`.
  - Totais velhos: `scripts` 52→48, `gates_arquivos` 203→132.
- **[Estágio 1→4] D8. O que o Estágio Processa:** — **Nota 6/10.** É 100% determinístico, sem LLM (DoD 3 OK): só regex e `html.escape` (`mapa_visual.py:79-80`). Falhas de processamento:
  - A versão não técnica reaproveita os mesmos valores técnicos (`compilar_mapas_nao_tecnicos.py:27` → `mv.GERADORES[tipo](catalogo)`). Resultado: a descrição em inglês do `SKILL.md` sai literal em `nao-tecnicos/mapa-05-skills.html`, com 124 frases-padrão em inglês contadas por script (F6 confirmado).
  - Contagens fixas no molde (N2, N7).
- **[Estágio 1→4] D9. O que o Estágio Entrega:** — **Nota 4/10.** 13 mapas técnicos + 13 não técnicos + manual + livro, com 0 links locais quebrados (varredura de todos os `href` relativos → 0). Mas:
  - o manual não liga o mapa-10 (N1);
  - 8 mapas e o índice estão obsoletos em relação ao repositório (F1);
  - há uma terceira cópia órfã em `tecnicos/` (F3).
- **D10. Orquestração e Topologia:** — **Nota 3/10.** A topologia é linear e passa por arquivo: catálogo.json → mapas → índice (o índice lê os outros do disco, `status_mapa` `:601-608`) → livro. Nenhum elo reconfere o elo anterior contra a fonte real. O `--check` compara mapa × JSON (`:693`), e não JSON × repositório. Prova: com o catálogo fresco, 8 tipos mudariam (`guardas, skills, indice, encaixes, ferramentas, leis, oficina, scripts`), mas os 13 `--check` dão exit 0. Ninguém orquestra a ordem obrigatória (catálogo → mapas → índice): ela está só na prosa da SKILL.

### Fase 3: Resiliência e Economia (Engenharia Operacional)
- **D11. Tratamento de Exceções e Fallback:** — **Nota 3/10.**
  - `ValueError` de molde/gerador vira mensagem e exit 1 (`:682-684`); catálogo ausente dá exit 1 com instrução (`:677-679`).
  - `FileNotFoundError` do molde não técnico escapa como traceback cru, depois de já ter gravado a versão técnica (N3).
  - `compilar_mapas_nao_tecnicos.main()` grava tipo por tipo sem tratar erro (`:75-77`).
  - Retry/backoff: **FAILED: Not implemented** (DoD 4). Para um motor determinístico o retry não é essencial, mas o tratamento estruturado de falha também falta.
- **D12. Observabilidade e Frugalidade:** — **Nota 1/10.** **FAILED: Not implemented.** `grep -n "secoes\|logging\|perf_counter"` nos 3 scripts → exit 1 (0 ocorrências). Não há métrica, tempo nem registro em `secoes/` (DoD 5). Frugalidade de tokens: OK por construção, porque não chama LLM.

### Fase 4: O Inspetor e a Expedição (Validação)
- **D13. Quality Gates (Portões):** — **Nota 2/10.**
  - O DoD 6 exige `gates/G_aidd_visual_maps.py`: **FAILED: Not implemented** (N8).
  - O único portão no pre-commit é `G_mapa_pecas` (`.pre-commit-config.yaml:419-425`). Ele é raso (F2 confirmado e ampliado):
    - `auditar_mapas_visuais` (`G_mapa_pecas.py:107-125`) só confere se o arquivo existe, tem mais de 100 caracteres e contém `<html`. 14 arquivos `<html>LIXO…` de 330 bytes → exit 0 "APROVADO (100% OK)".
    - `auditar_catalogo` (`:49-77`) só exige chaves e totais > 0. Um catálogo com `ferramentas/skills/leis/encaixes` vazios → exit 0.
  - Testes que mordem (mutação na cópia sandbox, script `aidd-tmp\vm\mut.py`):
    - mutantes M1 (`status_mapa` sempre concluído), M2 (`--check` técnico nunca falha), M3 (check não técnico nunca falha), M4 (`e()` sem escape) e M6 (gate ignora encaixes quebrados): **mortos**;
    - M5 (gate sem checar conteúdo): **sobreviveu** (7/7 verdes).
  - Suítes reais: `pytest tests/test_mapa_visual.py tests/test_catalogo_pecas.py` → exit 0 (62 passed); `test_g_mapa_pecas.py` + `test_livro_mapas.py` → exit 0 (12 passed). Tudo verde com o catálogo velho: nenhum teste prova que o catálogo bate com o repositório.
  - `catalogo_pecas.py --check`, `mapa_visual.py --check` e `livro_mapas.py --check` não estão em nenhum hook (N5).
- **D14. Critério de Rejeição (Rollback):** — **Nota 2/10.** Os `exit 1` existem (`--check` divergente, marcador órfão, catálogo ausente), mas o critério de rejeição principal não dispara diante do estado real (F1/N4). Não há rollback: na falha do estágio 3, o arquivo técnico regravado fica no repositório (N3). Os 14 arquivos de `tecnicos/` sobrevivem sem dono (F3). **DoD 7: FAILED.**
- **D15. Output Consolidado e Handoff:** — **Nota 3/10.** A entrega são HTMLs e o livro. Não há manifesto estruturado do que foi gerado, com qual hash de catálogo e com qual status. O índice faz esse papel, mas mente quando o catálogo está velho (F1). Não há handoff formal para o `aidd-textbook`: a docstring do `livro_mapas.py` manda rodar `livro.py build` à mão. **DoD 8: parcial**, porque este laudo sai com EXIT 0, mas falta o manifesto da ferramenta.

### Notas por dimensão

| D1 | D2 | D3 | D4 | D5 | D6 | D7 | D8 | D9 | D10 | D11 | D12 | D13 | D14 | D15 | Média |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 5 | 5 | 4 | 4 | 5 | 6 | 4 | 6 | 4 | 3 | 3 | 1 | 2 | 2 | 3 | **3,8** |

---

## 3. Matriz de Avaliação da Execução
- [ ] A ferramenta isolou seu raio de impacto corretamente? — **Não.** Grava direto em `docs/` sem worktree nem gravação atômica, deixa escrita parcial (N3) e tem a pasta órfã `tecnicos/` (F3).
- [x] O workflow seguiu as fases sem alucinações de LLM em tarefas mecânicas? — **Sim.** O motor é 100% determinístico, sem LLM. Os erros são de fonte de dados velha e de molde com texto fixo, não de inferência.
- [ ] O output final passou em todos os Quality Gates e emitiu o Handoff? — **Não de verdade.** `G_mapa_pecas` e os 13 `--check` passam (exit 0) enquanto `catalogo_pecas.py --check` reprova (exit 1). O portão aprova lixo (F2), `G_aidd_visual_maps.py` não existe e não há manifesto de handoff.

### Comandos de reprodução (todos com `TEMP=TMP=C:\Users\trcnologia\aidd-tmp`)
```text
python scripts/catalogo_pecas.py --check                                  -> exit 1 [DESATUALIZADO]
python scripts/mapa_visual.py <cada um dos 13 tipos> --check              -> exit 0 (13/13)
python modulos/04-nucleo-compartilhado/gates/G_mapa_pecas.py              -> exit 0
python scripts/livro_mapas.py --check                                     -> exit 0
python scripts/catalogo_pecas.py --saida aidd-tmp\vm\cat_novo.json        -> exit 0
python aidd-tmp\vm\stale_vs_fresh.py aidd-tmp\vm\cat_novo.json            -> 8 mapas mudariam; 7/12 'desatualizado'
python G_mapa_pecas.py --mapas-dir aidd-tmp\vm\lixo                       -> exit 0 (14 HTML-lixo de 330 B)
python G_mapa_pecas.py --catalogo aidd-tmp\vm\cat_falso.json              -> exit 0 (listas vazias)
python aidd-tmp\vm\mut.py <sandbox>                                       -> M1-M4,M6 mortos; M5 sobreviveu
python -m pytest tests/test_mapa_visual.py tests/test_catalogo_pecas.py   -> exit 0 (62 passed)
python ecossistema.py visual-maps                                         -> exit 1 (comando desconhecido)
sandbox: rm moldes-nao-tecnicos/guardas.html; mapa_visual.py guardas      -> exit 1 FileNotFoundError; técnico já regravado
```
