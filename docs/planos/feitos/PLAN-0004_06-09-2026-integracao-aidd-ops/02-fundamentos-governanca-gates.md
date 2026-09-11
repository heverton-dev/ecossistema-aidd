# Pacote 2 — Fundamentos de Governança (reconhecer a 5ª ferramenta)

> **Não toca infraestrutura real.** Só workspace local — reversível via `git revert`.
> **Decisão que autoriza este pacote:** `01-decisao-escopo-e-mvp.md` (5ª ferramenta oficial desde já, implementação real restrita às Fases 1-3 no Pacote 3).

---

## Diagnóstico (verificado no código, não presumido)

Investiguei exatamente quais arquivos hardcodeiam a cardinalidade "4 ferramentas" (o parecer técnico afirmava "no mínimo 3 gates" — confirmei quais são de verdade, e um deles **não precisa mudar agora**, contrariando a suposição inicial):

| Arquivo | Precisa mudar no Pacote 2? | Por quê |
|---|:---:|---|
| `AGENTS.md:11` | ✅ Sim | Afirma textualmente "4 ferramentas complementares". |
| `ecossistema.py` (`cmd_status`, linha ~115 e ~127) | ✅ Sim | Lista hardcoded de 4 tools + 4 skills, usada só para exibição de status — seguro de estender. |
| `scripts/manutencao/gerar_status_testes.py` | ✅ Sim | Usado por `status --testes`; hardcodeia a mesma lista de 4 ferramentas para rodar pytest de cada uma. |
| `gates/G_ECOSSISTEMA_INTEGRIDADE.py` (`TOOLS_REQUIRED`, `SKILLS_REQUIRED`, `COMMANDS_REQUIRED`) | ✅ Sim | **Gate estrito**: se `aidd-ops` for adicionado a essas listas sem os artefatos reais existirem, `python ecossistema.py audit` passa a FALHAR (regressão real, não hipotética — confirmei lendo `audit()`: cada item ausente vira `erros.append(...)` sem tolerância). |
| `gates/test_g_ecossistema_integridade.py` | ✅ Sim | Precisa de cenário real cobrindo a 5ª ferramenta (mesma exigência de qualidade de teste já aplicada em todo o resto do ecossistema). |
| `gates/G_CLI_HELP_CONSISTENCIA.py` (`ARQUIVOS_AUDITADOS`) | ❌ **Não ainda** | Confirmei lendo `_auditar_arquivo()`: se um caminho da lista não existir em disco, o gate **FALHA** ("Arquivo declarado na auditoria não existe"). `tools/aidd-ops` ainda não tem nenhum arquivo `argparse` real (isso é o Pacote 3). Adicionar aqui agora quebraria o gate por um motivo errado. Este arquivo muda no **Pacote 3**, quando o CLI real existir. |
| `gates/G_DRIFT_NUCLEO_COMPARTILHADO.py` (`DIR_A`/`DIR_B`) | ❌ Não | Hardcoded especificamente para comparar `tools/aidd-master/src/core/` vs `tools/aidd-enterprise/src/core/` — não é uma contagem genérica de ferramentas, é uma comparação par-a-par entre essas 2 especificamente. `aidd-ops` só entraria aqui se um dia ganhasse um núcleo compartilhado com outra ferramenta — fora do escopo do MVP (Pacote 3). |

**Consequência prática:** para `G_ECOSSISTEMA_INTEGRIDADE.py` continuar passando depois de adicionar `aidd-ops` às suas 3 listas, este pacote precisa criar, de verdade (não como stub fake — conteúdo real e honesto sobre o status atual da ferramenta), `tools/aidd-ops/README.md`, a skill `aidd-ops-runner` e o comando `ops`.

**⚠️ Correção importante (verificada antes de escrever a versão final deste pacote):** minha primeira leitura presumia que `skills/aidd-ops-runner/SKILL.md` e `.agent/commands/ops.md`/`.claude/commands/ops.md` seriam criados diretamente nesses caminhos. **Isso está errado e violaria o processo já homologado.** Confirmei em `gates/manifesto_harnesses.json` que esses são **destinos gerados por sync**, nunca editados manualmente — a nota do próprio manifesto é explícita: *"A partir desta migração, as pastas físicas por harness (.agent, .claude, .gemini, skills/ bare etc.) são DESTINOS GERADOS por sync - nunca mais editadas manualmente"*. A fonte canônica real das 4 skills `*-runner` e dos 4 slash commands existentes é `componentes/compartilhado/skills/` e `componentes/compartilhado/comandos/` (confirmado: `skills/aidd-forge-runner/SKILL.md` e `.claude/commands/forge.md` são cópias idênticas geradas a partir de `componentes/compartilhado/skills/aidd-forge-runner/SKILL.md` e `componentes/compartilhado/comandos/forge.md`). O caminho correto é:
- Criar a fonte canônica em `componentes/compartilhado/skills/aidd-ops-runner/SKILL.md` e `componentes/compartilhado/comandos/ops.md`.
- Rodar `python ecossistema.py components sync --tipo skill --ferramenta compartilhado` e `python ecossistema.py components sync --tipo command --ferramenta compartilhado` para propagar aos destinos reais (`skills/aidd-ops-runner/`, `.claude/skills/aidd-ops-runner/`, `.agent/skills/aidd-ops-runner/`, `.gemini/skills/aidd-ops-runner/`, `.claude/commands/ops.md`, `.agent/commands/ops.md`) — **nunca criar esses destinos à mão.**
- Adicionalmente, registrar `"aidd-ops"` em `gates/manifesto_harnesses.json["escopos"]` (mesmo formato da entrada `"aidd-forge"`: `root: "tools/aidd-ops"`, os mesmos 8 `tipos_aplicaveis`) — isso não cria nenhum componente novo (o precedente real é `aidd-forge`, que já está registrado como escopo válido mas com `componentes/aidd-forge/` inexistente em disco hoje — `_listar_componentes_fonte()` trata isso graciosamente, retornando lista vazia) — só declara `aidd-ops` como um escopo legítimo para quando, num pacote futuro, ela ganhar componentes próprios injetáveis.

Nenhum dos artefatos novos precisa (nem deve) descrever um CLI funcional que ainda não existe — devem dizer honestamente "governança reconhece esta ferramenta; pipeline funcional (Fases 1-3) chega no Pacote 3 do plano de integração AIDD-Ops".

**Decisão que este pacote NÃO toma sozinho:** não adiciona `ops` ao `dispatch` de `ecossistema.py` nem a `known_cmds` — rotear um comando para um módulo que não existe quebraria em runtime com um erro real na primeira chamada, o que violaria a Regra de Ouro #5 (Zero Stubs). Isso é trabalho do Pacote 3, quando `tools/aidd-ops/` tiver um `cmd_ops` real para receber a chamada.

## Definição de Pronto

2.1. `AGENTS.md §1`: trocar "4 ferramentas complementares" por "5 ferramentas complementares", adicionar `aidd-ops` ao diagrama/lista com descrição honesta do escopo atual (MVP Fases 1-3, ver plano de integração).
2.2. `ecossistema.py`: `cmd_status`'s lista `tools` ganha `("aidd-ops", "<descrição curta e honesta>")`; lista de skills ganha `"aidd-ops-runner"`. Docstring do topo do arquivo atualizada para mencionar as 5 ferramentas (sem adicionar `ops` ao `dispatch`/`known_cmds` — ver Diagnóstico acima).
2.3. `scripts/manutencao/gerar_status_testes.py`: adicionar `aidd-ops` à lista de ferramentas que `status --testes` tenta rodar pytest — confirmar que o script já trata graciosamente uma ferramenta sem `tests/` ainda (ex.: 0 testes encontrados, não erro fatal); se não tratar, ajustar para tratar (ainda dentro do escopo deste pacote, já que sem isso `status --testes` quebraria).
2.4. `gates/G_ECOSSISTEMA_INTEGRIDADE.py`: adicionar `"aidd-ops"` a `TOOLS_REQUIRED`, `"aidd-ops-runner"` a `SKILLS_REQUIRED`, `"ops.md"` a `COMMANDS_REQUIRED`.
2.5. Criar `tools/aidd-ops/README.md` real (conteúdo honesto: propósito da ferramenta, status atual "governança reconhecida, MVP no Pacote 3", link para `docs/features/06-09-2026_feature-arquitetura-aidd-ops.md` e `docs/planos/integracao-aidd-ops/00-PROCESSO-E-DECISOES.md`).
2.6. Registrar `"aidd-ops"` em `gates/manifesto_harnesses.json["escopos"]` (mesmo formato de `"aidd-forge"`: `root: "tools/aidd-ops"`, os mesmos 8 `tipos_aplicaveis`).
2.7. Criar a fonte canônica `componentes/compartilhado/skills/aidd-ops-runner/SKILL.md` (frontmatter YAML válido — `name`/`description` — seguindo o formato exato de `componentes/compartilhado/skills/aidd-forge-runner/SKILL.md`), conteúdo honesto sobre o status atual (não descrever um `/ops` funcional que ainda não existe).
2.8. Criar a fonte canônica `componentes/compartilhado/comandos/ops.md` (mesmo formato de `componentes/compartilhado/comandos/forge.md`), honesto sobre o status atual.
2.9. Rodar `python ecossistema.py components sync --tipo skill --ferramenta compartilhado` e `python ecossistema.py components sync --tipo command --ferramenta compartilhado` para propagar aos destinos reais — **nunca criar os destinos (`skills/aidd-ops-runner/`, `.claude/skills/...`, `.agent/commands/ops.md`, etc.) manualmente.**
2.10. `gates/test_g_ecossistema_integridade.py`: adicionar cenário(s) real(is) cobrindo a 5ª ferramenta (ex.: confirma que o gate reprova se `tools/aidd-ops/README.md` for removido, e que aprova com os artefatos reais no lugar).

## Critério de saída

- `python ecossistema.py audit` → exit 0, sem regressão (todos os 6 gates, incluindo `G_ECOSSISTEMA_INTEGRIDADE`, `G_CLI_HELP_CONSISTENCIA` e `G_DRIFT_NUCLEO_COMPARTILHADO`).
- `python ecossistema.py status` → exit 0, `aidd-ops` aparece listado como `[OK] Instalado` (o diretório e README existem) — **não** confundir com "funcional"; o comando `python ecossistema.py ops ...` continua não existindo até o Pacote 3, e isso é o comportamento correto e esperado, não uma falha.
- `python ecossistema.py status --testes` → exit 0, sem quebrar por causa da ausência de `tests/` em `tools/aidd-ops/`.
- Suíte pytest de `gates/` (`python -m pytest gates/ -q`, se existir essa suíte, ou os testes específicos do gate tocado) → exit 0, incluindo o(s) cenário(s) novo(s) do item 2.10.
- `python ecossistema.py components verify --tipo todos` → exit 0, confirmando que `skills/aidd-ops-runner/` e os destinos de `.claude/commands/ops.md`/`.agent/commands/ops.md` batem byte-a-byte com a fonte canônica em `componentes/compartilhado/`.
- `git status` limpo além dos arquivos esperados (incluindo os destinos GERADOS pelo sync — eles são esperados, não manuais).

## Prompt de Execução

> Copie o bloco abaixo integralmente para o agente executor. Autocontido.

```
Você vai atualizar a camada de governança do monorepo ecossistema-aidd
(raiz em C:\Users\trcnologia\Desktop\ecossistema-aidd) para reconhecer
formalmente uma 5ª ferramenta, aidd-ops, SEM implementar nenhum código
funcional dela ainda (isso é um pacote futuro, separado). Siga
EXATAMENTE a Definição de Pronto abaixo, não invente escopo adicional,
e valide tudo de verdade (execuções reais, exit codes reais, nunca
mascarados por pipe).

CONTEXTO JÁ INVESTIGADO (confirme lendo o código antes de editar):
- `gates/G_ECOSSISTEMA_INTEGRIDADE.py` é ESTRITO: `TOOLS_REQUIRED`
  (linha ~24), `SKILLS_REQUIRED` (linha ~31) e `COMMANDS_REQUIRED`
  (linha ~38) são listas hardcoded; para cada item ausente, o gate
  falha sem tolerância (`audit()`, função principal). Se você adicionar
  "aidd-ops"/"aidd-ops-runner"/"ops.md" a essas listas SEM criar os
  artefatos reais correspondentes primeiro, `python ecossistema.py
  audit` vai começar a falhar — isso seria uma regressão real, não
  aceitável.
- `gates/G_CLI_HELP_CONSISTENCIA.py` também é estrito (`_auditar_arquivo()`,
  linha ~155): se um caminho em `ARQUIVOS_AUDITADOS` não existir em
  disco, o gate falha com "Arquivo declarado na auditoria não existe".
  `tools/aidd-ops` ainda não tem nenhum arquivo argparse real — NÃO
  adicione nada a este gate neste pacote. Isso é trabalho de um pacote
  futuro (quando o CLI real de aidd-ops existir).
- `gates/G_DRIFT_NUCLEO_COMPARTILHADO.py` (`DIR_A`/`DIR_B`, linha ~42)
  é hardcoded especificamente para comparar tools/aidd-master/src/core/
  vs tools/aidd-enterprise/src/core/ — não é uma contagem de
  ferramentas, é uma comparação par-a-par entre essas 2 especificamente.
  NÃO precisa mudar neste pacote.
- `ecossistema.py`: `cmd_status()` tem uma lista `tools` (tuplas
  nome/descrição) e uma lista de skills — só usadas para exibição de
  status, seguras de estender. O `dispatch` dict e `known_cmds`/lógica
  de roteamento de comando NÃO devem ganhar uma entrada "ops" neste
  pacote — não existe nenhum módulo real para rotear ainda, e roteá-lo
  quebraria em runtime na primeira chamada (violaria a Regra de Ouro #5
  do AGENTS.md, Zero Stubs).
- `scripts/manutencao/gerar_status_testes.py` (usado por `python
  ecossistema.py status --testes`) também hardcoda a lista de 4
  ferramentas — precisa reconhecer aidd-ops, e precisa continuar
  funcionando mesmo se `tools/aidd-ops/tests/` ainda não existir
  (verifique como o script já trata isso para as outras ferramentas e
  replique o mesmo tratamento gracioso).
- **CRÍTICO — não crie skills/slash-commands diretamente no destino.**
  `skills/aidd-forge-runner/SKILL.md` e `.claude/commands/forge.md`
  NÃO são editados à mão — são DESTINOS GERADOS por
  `python ecossistema.py components sync`, a partir da fonte canônica
  real em `componentes/compartilhado/skills/aidd-forge-runner/SKILL.md`
  e `componentes/compartilhado/comandos/forge.md` (confirme lendo
  `gates/manifesto_harnesses.json` e comparando o conteúdo dos dois
  lados — são idênticos). Para aidd-ops, você vai criar a fonte
  canônica em `componentes/compartilhado/` e rodar o `sync` — nunca
  criar os arquivos em `skills/`, `.claude/commands/` ou
  `.agent/commands/` diretamente.

DEFINIÇÃO DE PRONTO — nesta ordem:
1. Atualize AGENTS.md §1: "4 ferramentas complementares" vira "5
   ferramentas complementares"; adicione aidd-ops ao diagrama/lista com
   descrição honesta ("Meta-Orquestrador Agêntico de Infraestrutura —
   MVP em construção, ver docs/planos/integracao-aidd-ops/").
2. Em ecossistema.py: adicione ("aidd-ops", "<descrição curta>") à
   lista `tools` de cmd_status(); adicione "aidd-ops-runner" à lista de
   skills verificadas. Atualize a docstring do topo do arquivo para
   mencionar as 5 ferramentas. NÃO adicione "ops" a `dispatch` nem a
   nenhuma lista de comandos conhecidos/roteáveis.
3. Em scripts/manutencao/gerar_status_testes.py: adicione aidd-ops à
   lista de ferramentas; confirme que o script não quebra se
   tools/aidd-ops/tests/ não existir (ajuste se necessário, dentro do
   escopo deste pacote).
4. Crie tools/aidd-ops/README.md (real, honesto): propósito da
   ferramenta (resumo de 1 parágrafo baseado em
   docs/features/06-09-2026_feature-arquitetura-aidd-ops.md §1),
   status atual explícito ("governança reconhecida desde o Pacote 2 da
   integração; implementação funcional do MVP — Fases 1-3 do pipeline —
   chega no Pacote 3"), link para
   docs/planos/integracao-aidd-ops/00-PROCESSO-E-DECISOES.md.
5. Em gates/manifesto_harnesses.json: registre "aidd-ops" em "escopos",
   mesmo formato de "aidd-forge" (root: "tools/aidd-ops", os mesmos 8
   tipos_aplicaveis). Isso não cria nenhum componente novo, só declara
   o escopo como válido (mesmo estado que "aidd-forge" já tem hoje:
   escopo declarado, zero componentes ainda em componentes/aidd-ops/).
6. Crie a FONTE CANÔNICA
   componentes/compartilhado/skills/aidd-ops-runner/SKILL.md com
   frontmatter YAML válido (name: aidd-ops-runner, description real e
   honesta), seguindo o formato de
   componentes/compartilhado/skills/aidd-forge-runner/SKILL.md, mas SEM
   prometer um `/ops <args>` funcional — descreva o status atual
   honestamente.
7. Crie a FONTE CANÔNICA
   componentes/compartilhado/comandos/ops.md, mesmo formato de
   componentes/compartilhado/comandos/forge.md, honesto sobre o status
   atual (não afirme uma ação/CLI funcional que ainda não existe).
8. Rode `python ecossistema.py components sync --tipo skill --ferramenta compartilhado`
   e `python ecossistema.py components sync --tipo command --ferramenta compartilhado`
   para propagar aos destinos reais (skills/aidd-ops-runner/,
   .claude/skills/aidd-ops-runner/, .agent/skills/aidd-ops-runner/,
   .gemini/skills/aidd-ops-runner/, .claude/commands/ops.md,
   .agent/commands/ops.md). Confirme via diff que os destinos batem
   byte-a-byte com a fonte canônica.
9. Em gates/G_ECOSSISTEMA_INTEGRIDADE.py: adicione "aidd-ops" a
   TOOLS_REQUIRED, "aidd-ops-runner" a SKILLS_REQUIRED, "ops.md" a
   COMMANDS_REQUIRED.
10. Em gates/test_g_ecossistema_integridade.py: adicione cenário(s)
    real(is) — ex.: com os artefatos presentes, o gate aprova;
    removendo um deles (num diretório de teste temporário, nunca no
    repo real), o gate reprova com a mensagem certa. Siga o padrão de
    teste real (tmp_path, nunca mock do comportamento central) já usado
    no resto do repositório.

CRITÉRIO DE SAÍDA (rode e cole o output real de cada um):
- python ecossistema.py audit (raiz) → exit 0, sem regressão nos 6
  gates (preste atenção especial a G_ECOSSISTEMA_INTEGRIDADE,
  G_CLI_HELP_CONSISTENCIA — que NÃO deve ter sido tocado — e
  G_DRIFT_NUCLEO_COMPARTILHADO — idem).
- python ecossistema.py status → exit 0, aidd-ops aparece como [OK]
  Instalado.
- python ecossistema.py status --testes → exit 0, sem quebrar por
  causa de tools/aidd-ops/tests/ ausente.
- Suíte de teste do gate tocado (pytest do arquivo/pasta relevante) →
  exit 0, incluindo os cenários novos do item 10.
- python ecossistema.py components verify --tipo todos → exit 0,
  confirmando que os destinos gerados batem byte-a-byte com a fonte
  canônica em componentes/compartilhado/.
- git status (raiz) limpo além dos arquivos esperados: AGENTS.md,
  ecossistema.py, scripts/manutencao/gerar_status_testes.py,
  gates/manifesto_harnesses.json, gates/G_ECOSSISTEMA_INTEGRIDADE.py,
  gates/test_g_ecossistema_integridade.py (modificados);
  tools/aidd-ops/README.md,
  componentes/compartilhado/skills/aidd-ops-runner/SKILL.md,
  componentes/compartilhado/comandos/ops.md, e os destinos GERADOS pelo
  sync (skills/aidd-ops-runner/, .claude/skills/aidd-ops-runner/,
  .agent/skills/aidd-ops-runner/, .gemini/skills/aidd-ops-runner/,
  .claude/commands/ops.md, .agent/commands/ops.md) — todos esperados,
  nenhum criado manualmente.

REGRAS DE ESCOPO — NÃO FAÇA:
- Não implemente nenhum código funcional de tools/aidd-ops/ além do
  README.md (isso é o Pacote 3 — CLI, pipeline de fases, etc.).
- Não adicione "ops" ao dispatch/roteamento de comandos de
  ecossistema.py.
- Não crie skills/aidd-ops-runner/SKILL.md nem .claude/commands/ops.md
  / .agent/commands/ops.md diretamente — sempre via fonte canônica em
  componentes/compartilhado/ + `components sync`.
- Não toque em gates/G_CLI_HELP_CONSISTENCIA.py nem
  gates/G_DRIFT_NUCLEO_COMPARTILHADO.py — confirmado que nenhum dos 2
  precisa mudar neste pacote.
- Não faça git commit nem git push.
- Não altere nenhum documento em docs/planos/integracao-aidd-ops/.

ENTREGÁVEL: lista exata de arquivos criados/alterados; comando + output
real que comprova cada item do Critério de Saída; qualquer desvio
necessário, reportado explicitamente em vez de decidido sozinho.
```

## Prompt de Execução — English version

> Copy the block below in full to the executor agent. Self-contained.

```
You are going to update the governance layer of the ecossistema-aidd
monorepo (root at C:\Users\trcnologia\Desktop\ecossistema-aidd) to
formally recognize a 5th tool, aidd-ops, WITHOUT implementing any of
its functional code yet (that is a separate, future package). Follow
the Definition of Done below EXACTLY, do not invent additional scope,
and validate everything for real (real runs, real exit codes, never
masked by a pipe).

ALREADY-INVESTIGATED CONTEXT (confirm by reading the code before
editing):
- `gates/G_ECOSSISTEMA_INTEGRIDADE.py` is STRICT: `TOOLS_REQUIRED`
  (line ~24), `SKILLS_REQUIRED` (line ~31), and `COMMANDS_REQUIRED`
  (line ~38) are hardcoded lists; for every missing item, the gate
  fails with no tolerance (`audit()`, the main function). If you add
  "aidd-ops"/"aidd-ops-runner"/"ops.md" to these lists WITHOUT first
  creating the corresponding real artifacts, `python ecossistema.py
  audit` will start failing — that would be a real, unacceptable
  regression.
- `gates/G_CLI_HELP_CONSISTENCIA.py` is also strict
  (`_auditar_arquivo()`, line ~155): if a path in `ARQUIVOS_AUDITADOS`
  does not exist on disk, the gate fails with "Arquivo declarado na
  auditoria não existe" (declared audit file does not exist).
  `tools/aidd-ops` has no real argparse file yet — do NOT add anything
  to this gate in this package. That is work for a future package
  (once aidd-ops's real CLI exists).
- `gates/G_DRIFT_NUCLEO_COMPARTILHADO.py` (`DIR_A`/`DIR_B`, line ~42)
  is hardcoded specifically to compare tools/aidd-master/src/core/ vs
  tools/aidd-enterprise/src/core/ — it is not a tool count, it is a
  pairwise comparison between exactly those 2. Does NOT need to change
  in this package.
- `ecossistema.py`: `cmd_status()` has a `tools` list (name/description
  tuples) and a skills list — used only for status display, safe to
  extend. The `dispatch` dict and any known-commands/routing logic must
  NOT gain an "ops" entry in this package — there is no real module to
  route to yet, and routing to one would crash at runtime on the first
  call (violating AGENTS.md's Golden Rule #5, Zero Stubs).
- `scripts/manutencao/gerar_status_testes.py` (used by `python
  ecossistema.py status --testes`) also hardcodes the 4-tool list — it
  needs to recognize aidd-ops, and must keep working even if
  `tools/aidd-ops/tests/` does not exist yet (check how the script
  already handles this for the other tools and replicate the same
  graceful handling).
- **CRITICAL — do not create skills/slash-commands directly at the
  destination.** `skills/aidd-forge-runner/SKILL.md` and
  `.claude/commands/forge.md` are NOT hand-edited — they are DESTINATIONS
  GENERATED by `python ecossistema.py components sync`, from the real
  canonical source at
  `componentes/compartilhado/skills/aidd-forge-runner/SKILL.md` and
  `componentes/compartilhado/comandos/forge.md` (confirm by reading
  `gates/manifesto_harnesses.json` and comparing both sides' content —
  they are identical). For aidd-ops, you will create the canonical
  source under `componentes/compartilhado/` and run `sync` — never
  create the files under `skills/`, `.claude/commands/`, or
  `.agent/commands/` directly.

DEFINITION OF DONE — in this order:
1. Update AGENTS.md §1: "4 ferramentas complementares" becomes "5
   ferramentas complementares"; add aidd-ops to the diagram/list with
   an honest description ("Agentic Infrastructure Meta-Orchestrator —
   MVP under construction, see docs/planos/integracao-aidd-ops/").
2. In ecossistema.py: add ("aidd-ops", "<short description>") to
   cmd_status()'s `tools` list; add "aidd-ops-runner" to the checked
   skills list. Update the file's top docstring to mention the 5
   tools. Do NOT add "ops" to `dispatch` nor to any known/routable
   command list.
3. In scripts/manutencao/gerar_status_testes.py: add aidd-ops to the
   tool list; confirm the script does not break if
   tools/aidd-ops/tests/ does not exist (adjust if needed, within this
   package's scope).
4. Create tools/aidd-ops/README.md (real, honest): the tool's purpose
   (1-paragraph summary based on
   docs/features/06-09-2026_feature-arquitetura-aidd-ops.md §1),
   explicit current status ("governance-recognized since Package 2 of
   the integration; the functional MVP — pipeline Phases 1-3 — arrives
   in Package 3"), a link to
   docs/planos/integracao-aidd-ops/00-PROCESSO-E-DECISOES.md.
5. In gates/manifesto_harnesses.json: register "aidd-ops" under
   "escopos", same format as "aidd-forge" (root: "tools/aidd-ops", the
   same 8 tipos_aplicaveis). This creates no new component, it only
   declares the scope as valid (same state "aidd-forge" already has
   today: declared scope, zero components yet under
   componentes/aidd-ops/).
6. Create the CANONICAL SOURCE
   componentes/compartilhado/skills/aidd-ops-runner/SKILL.md with valid
   YAML frontmatter (name: aidd-ops-runner, real and honest
   description), following the format of
   componentes/compartilhado/skills/aidd-forge-runner/SKILL.md, but
   WITHOUT promising a functional `/ops <args>` — describe the current
   status honestly.
7. Create the CANONICAL SOURCE componentes/compartilhado/comandos/ops.md,
   same format as componentes/compartilhado/comandos/forge.md, honest
   about the current status (do not claim a functional action/CLI that
   does not exist yet).
8. Run `python ecossistema.py components sync --tipo skill --ferramenta compartilhado`
   and `python ecossistema.py components sync --tipo command --ferramenta compartilhado`
   to propagate to the real destinations (skills/aidd-ops-runner/,
   .claude/skills/aidd-ops-runner/, .agent/skills/aidd-ops-runner/,
   .gemini/skills/aidd-ops-runner/, .claude/commands/ops.md,
   .agent/commands/ops.md). Confirm via diff that the destinations
   match the canonical source byte-for-byte.
9. In gates/G_ECOSSISTEMA_INTEGRIDADE.py: add "aidd-ops" to
   TOOLS_REQUIRED, "aidd-ops-runner" to SKILLS_REQUIRED, "ops.md" to
   COMMANDS_REQUIRED.
10. In gates/test_g_ecossistema_integridade.py: add real scenario(s) —
    e.g., with the artifacts present, the gate passes; removing one of
    them (in a temporary test directory, never in the real repo) makes
    the gate fail with the right message. Follow the real-test pattern
    (tmp_path, never mocking the central behavior) already used
    throughout the repository.

EXIT CRITERIA (run and paste the real output of each):
- python ecossistema.py audit (root) → exit 0, no regression across
  the 6 gates (pay special attention to G_ECOSSISTEMA_INTEGRIDADE,
  G_CLI_HELP_CONSISTENCIA — which must NOT have been touched — and
  G_DRIFT_NUCLEO_COMPARTILHADO — same).
- python ecossistema.py status → exit 0, aidd-ops shows as [OK]
  Instalado.
- python ecossistema.py status --testes → exit 0, not breaking because
  of a missing tools/aidd-ops/tests/.
- The touched gate's test suite (pytest of the relevant file/folder) →
  exit 0, including the new scenarios from item 10.
- python ecossistema.py components verify --tipo todos → exit 0,
  confirming the generated destinations match the canonical source
  under componentes/compartilhado/ byte-for-byte.
- git status (root) clean beyond the expected files: AGENTS.md,
  ecossistema.py, scripts/manutencao/gerar_status_testes.py,
  gates/manifesto_harnesses.json, gates/G_ECOSSISTEMA_INTEGRIDADE.py,
  gates/test_g_ecossistema_integridade.py (modified);
  tools/aidd-ops/README.md,
  componentes/compartilhado/skills/aidd-ops-runner/SKILL.md,
  componentes/compartilhado/comandos/ops.md, and the destinations
  GENERATED by sync (skills/aidd-ops-runner/,
  .claude/skills/aidd-ops-runner/, .agent/skills/aidd-ops-runner/,
  .gemini/skills/aidd-ops-runner/, .claude/commands/ops.md,
  .agent/commands/ops.md) — all expected, none created by hand.

SCOPE RULES — DO NOT:
- Do not implement any functional code for tools/aidd-ops/ beyond
  README.md (that is Package 3 — CLI, phase pipeline, etc.).
- Do not add "ops" to ecossistema.py's command dispatch/routing.
- Do not create skills/aidd-ops-runner/SKILL.md nor
  .claude/commands/ops.md / .agent/commands/ops.md directly — always
  via the canonical source under componentes/compartilhado/ +
  `components sync`.
- Do not touch gates/G_CLI_HELP_CONSISTENCIA.py nor
  gates/G_DRIFT_NUCLEO_COMPARTILHADO.py — confirmed neither needs to
  change in this package.
- Do not git commit or git push.
- Do not modify any document under docs/planos/integracao-aidd-ops/.

DELIVERABLE: exact list of files created/changed; command + real
output proving each item of the Exit Criteria; any necessary deviation,
explicitly reported instead of decided by yourself.
```
