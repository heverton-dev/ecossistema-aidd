# Relatório do Construtor (Fase 3) — skills-pocock ciclo-01

> Branch `audit/evolucao-skills-pocock-ciclo-01`. Tabela por ticket preenchida no Ticket 12; execução real do gate de prova no Ticket 13 (manual).

## Tabela por ticket

Método: o teste de cada ticket (versão final, do HEAD) roda numa worktree temporária sobre a árvore do commit anterior ao ticket ("antes") e sobre a do próprio commit ("depois"). Exit capturado com `> arquivo 2>&1; echo $?`, sem pipe. Reproduzido em 25/09/2026.

| Ticket | Commit | Arquivo entregue | Comando de teste | Exit antes | Exit depois |
|---|---|---|---|---|---|
| 1 | `27bc7de` | `componentes/compartilhado/skills/aidd-diagnose/SKILL.md` | `python -m pytest tests/test_skills_pocock_diagnose.py` | 1 | 0 |
| 2 | `66e72dc` | `componentes/compartilhado/skills/aidd-tickets/SKILL.md` | `python -m pytest tests/test_skills_pocock_tickets.py` | 1 | 0 |
| 3 | `785efdf` | `componentes/compartilhado/skills/aidd-grill/SKILL.md (+ aidd-grill-docs)` | `python -m pytest tests/test_skills_pocock_grill.py` | 1 | 0 |
| 4 | `083cb97` | `componentes/compartilhado/skills/aidd-tdd/SKILL.md` | `python -m pytest tests/test_skills_pocock_tdd.py` | 1 | 0 |
| 5 | `19796cf` | `componentes/compartilhado/skills/aidd-escrita-agentes/SKILL.md` | `python -m pytest tests/test_skills_pocock_escrita.py` | 1 | 0 |
| 6 | `4097a89` | `componentes/compartilhado/skills/aidd-retro/SKILL.md` | `python -m pytest tests/test_skills_pocock_retro.py` | 1 | 0 |
| 7 | `49fff00` | `CONTEXT.md, docs/adr/README.md, componentes/compartilhado/skills/aidd-reexplica/SKILL.md` | `python -m pytest tests/test_skills_pocock_contexto.py` | 1 | 0 |
| 8 | `9567aa9` | `componentes/compartilhado/skills/aidd-entrega/SKILL.md` | `python -m pytest tests/test_skills_pocock_entrega.py` | 1 | 0 |
| 9 | `440a941` | `componentes/compartilhado/skills/aidd-wizard/template.sh (+ SKILL.md)` | `python -m pytest tests/test_skills_pocock_wizard.py` | 1 | 0 |
| 10 | `afe8b4a` | `scripts/gerenciador_planos.py (+ aidd-planos/SKILL.md)` | `python -m pytest tests/test_skills_pocock_planos.py` | 1 | 0 |
| 11 | `c83c693` | `scripts/relatorio_skills_duplicadas.py` | `python -m pytest tests/test_relatorio_skills_duplicadas.py` | 1 | 0 |
| 12 | (este commit) | cópias do forge (4), `docs/protocolos/AGENTS-REFERENCIA-COMPLETA.md`, `AGENTS.md` | `python -m pytest tests/test_skills_pocock_distribuicao.py` | 1 | 0 |

Os testes dos Tickets 1 a 8 e 10 são testes de contrato do texto: provam que a regra está escrita, não que o agente a segue. A prova de comportamento é o Ticket 13 (manual).

## Ticket 12 — distribuição

- Passo vermelho trocado com aprovação do usuário (25/09/2026): `python ecossistema.py components verify` já dava exit 0 antes do sync (o hook de commit sincroniza os harnesses a cada commit). A divergência real estava nas cópias do forge (`aidd-grill`, `aidd-spec`, `aidd-tdd`, `aidd-tickets`), que nenhum gate compara por conteúdo; o novo teste compara.
- `aidd-spec` não foi alterada neste ciclo: a cópia do forge já estava defasada antes e foi alinhada junto.
- `components verify` depois: exit 0 (coberto pelo teste).
- `python ecossistema.py audit` (exit real em arquivo, sem pipe):
  - Rodada 1 → exit 1. G_DISCIPLINA_TESTE_FERRAMENTA (Lei #9): `tools/aidd-forge/` mudou sem atualizar o relatório de teste. Corrigido com execução real (`forge init` + `forge audit` em pasta temporária, exit 0) registrada na seção 14 de `docs/teste-end-to-end/relatorio-teste-end-to-end.md`. G_SEGREDOS marcou "files were modified by this hook" porque este relatório foi editado durante a varredura (a varredura em si aprovou); sem edição concorrente, passou.
  - Rodada 2 → exit 1. 39 gates Passed; G_TESTES_REAIS com as 8 ferramentas verdes (aidd-forge 294 passed). Falhou só G_PORTAO_PROVA_QUE_MORDE por `gates/test_g_aidd_diagnose.py::test_aprova_relatorio_valido_markdown` (gate do ciclo aidd-diagnose, já na `main`). Não reproduziu em 14 execuções seguidas (3 isoladas, 3 pelo hook do pre-commit, 8 do meta-gate direto). Hipótese de a pasta temporária do pytest ser apagada por sessões concorrentes foi testada e refutada. Causa ainda desconhecida; o teste passou a imprimir a saída do gate ao falhar, para a próxima ocorrência trazer a causa.
  - Rodada 3 (reprodução com os hooks do pre-commit em sequência, RAM livre 4,1 GB) → exit 0. A falha intermitente não apareceu; ela coincidiu com pouca memória livre (1,7 GB de 15,7 GB), sem prova direta da relação.
  - Incidente na 1ª tentativa de commit deste ticket: o passo de telemetria do hook (`status --testes --write`) rodou o pytest das ferramentas herdando `GIT_DIR`/`GIT_INDEX_FILE`. Testes que fazem `git commit`/`git config` em pasta temporária gravaram 9 commits de lixo nesta branch e, no `.git/config` compartilhado, `user.name = t` e `core.bare = true` (a pasta principal na `main` parou de aceitar `git status`). Reparo: commit interrompido; branch voltou para `c83c693` com `git reset --mixed` (lixo no reflog); `core.bare` voltou para `false` e a seção `[user]` falsa foi removida (cópia do arquivo poluído guardada fora do repositório). Correção da causa no commit `5f0e582` (teste de regressão exit 1 → 0).
  - Commit deste ticket: gates do hook + telemetria rodando com a correção; conferido depois que nenhum commit de lixo nem alteração no `.git/config` apareceu.

## Achados fora do escopo

- `componentes/compartilhado/skills/planos-auditoria-runner/tests/test_gerenciador_planos.py`: 8 testes já reprovavam no HEAD antes deste ciclo (esperam nome de pasta sem o prefixo `PLAN-NNNN`).
- `gates/allowlist_skipped_testes.json`: a chave `raiz-tests` (skips do wizard) é só registro; o G_TESTES_REAIS lê apenas as ferramentas de `tools/`.
- `gates/test_g_layout_entrega.py`: passa sozinho; falhou uma vez quando rodou junto com outros testes. Mesma natureza da falha intermitente do `test_g_aidd_diagnose.py` acima: sem causa comprovada.
- Testes dentro de `componentes/compartilhado/skills/*/tests/` não são rodados por nenhum gate (as 8 falhas do `test_gerenciador_planos.py` passaram despercebidas por isso).

## Ticket 11 — execução real contra as skills globais

Comando: `python scripts/relatorio_skills_duplicadas.py > saida.txt 2>&1; echo $?` → exit 0 (25/09/2026).

| Skill global | Par AIDD | Sugestão |
|---|---|---|
| `~/.agents/skills/code-review` | `review-changes` | remover |
| `~/.agents/skills/diagnosing-bugs` | `aidd-diagnose` | remover |
| `~/.agents/skills/grill-me` | `aidd-grill` | remover |
| `~/.agents/skills/grill-with-docs` | `aidd-grill-docs` | remover |
| `~/.agents/skills/grilling` | `aidd-grill` | remover |
| `~/.agents/skills/handoff` | `aidd-handoff` | remover |
| `~/.agents/skills/tdd` | `aidd-tdd` | remover |
| `~/.agents/skills/to-spec` | `aidd-spec` | remover |
| `~/.agents/skills/to-tickets` | `aidd-tickets` | remover |

Remoção só à mão pelo usuário; este script nunca apaga nada.
