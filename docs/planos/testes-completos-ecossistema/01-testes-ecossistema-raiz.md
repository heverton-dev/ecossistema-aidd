# Bateria 1 — Orquestração Raiz (`ecossistema.py` + Meta-Quality Gates)

> **Escopo:** provar que a CLI unificada da raiz (`ecossistema.py`) e os 6 Meta-Quality Gates funcionam de ponta a ponta, incluindo a sincronização/verificação multi-harness de componentes.
> **Não faz parte desta bateria:** testar as 4 ferramentas em profundidade (isso é feito nas baterias 2-5) — aqui só se prova a camada de orquestração/roteamento e os gates de nível raiz.

---

## Contexto já investigado

- `ecossistema.py` (raiz) roteia para 6 comandos: `forge`, `generate`, `master`, `enterprise`, `components sync|verify`, `audit`, `status` (`status --testes` roda a suíte `pytest` real de cada ferramenta e atualiza `PLANO-EXECUCAO-ESTRUTURADO.json`).
- `audit` roda, em sequência, os 6 gates: `G_ECOSSISTEMA_INTEGRIDADE.py`, `G_DRIFT_NUCLEO_COMPARTILHADO.py`, `G_HARNESS_COMPAT.py`, `G_SEGREDOS.py`, `G_CLI_HELP_CONSISTENCIA.py`, `G_COMPONENTE_AGNOSTICO.py` (todos em `gates/`, raiz).
- `components sync|verify --tipo <tipo|todos> [--ferramenta <nome>] [--dry-run]` usa `scripts/gestor_componentes.py`; `"todos"` é um marcador válido (`TODOS_TIPOS_MARCADOR`, `gestor_componentes.py:38`) que expande para todos os tipos reais.
- Este comando já foi rodado dezenas de vezes ao longo das Rodadas 1 e 2 (inclusive nas auditorias dos Itens 4 e 5 desta sessão) e sempre retornou exit 0 no estado atual do repositório — a bateria aqui deve reconfirmar isso do zero, não presumir.

## Definição de Pronto

1.1. `python ecossistema.py status` → exit 0, lista as 4 ferramentas como `[OK] Instalado` e as 4 skills universais como `[OK]`.
1.2. `python ecossistema.py status --testes` → exit 0; capturar a contagem real de testes reportada para cada ferramenta (não estimar) e confirmar que `PLANO-EXECUCAO-ESTRUTURADO.json` foi atualizado com timestamp novo.
1.3. `python ecossistema.py audit` → exit 0; capturar a saída de cada um dos 6 gates individualmente (rodando cada gate isoladamente também, ex.: `python gates/G_SEGREDOS.py`) para confirmar que o exit 0 do `audit` não está mascarando uma falha de um gate específico via pipe.
1.4. `python ecossistema.py components verify --tipo todos` → exit 0.
1.5. `python ecossistema.py components sync --tipo todos --dry-run` → exit 0, confirmar via `git status` (raiz) que nenhum arquivo foi alterado (dry-run real, não escreve nada).
1.6. `python ecossistema.py help` / `--help` / `-h` → todos exit 0, mensagens de ajuda coerentes com os comandos reais disponíveis.
1.7. Comando desconhecido (ex.: `python ecossistema.py comando-que-nao-existe`) → exit 1, mensagem de erro clara (prova que o roteamento rejeita corretamente comandos inválidos, não falha silenciosamente).

## Critério de saída

- Todos os 7 itens acima rodados de verdade, com exit code real colado no relatório (nunca "deveria dar exit 0").
- `git status` da raiz do repositório limpo ao final (nenhum arquivo do ecossistema real alterado por esta bateria — `status --testes` e `audit --report` podem gerar arquivos dentro de `tools/*/` como efeito colateral normal do próprio comando; se isso acontecer, documentar no relatório e reverter com `git checkout --` antes de considerar a bateria concluída, nunca deixar sujeira no repositório real).

## Prompt de Execução

> Copie o bloco abaixo integralmente para o agente executor. Autocontido — não pressupõe que ele viu esta conversa.

```
Você vai escrever e executar uma bateria de testes reais de ponta a ponta
que prova o funcionamento da CLI unificada `ecossistema.py` do monorepo
ecossistema-aidd (raiz em C:\Users\trcnologia\Desktop\ecossistema-aidd) e
dos 6 Meta-Quality Gates que ela orquestra. Valide tudo de verdade
(execuções reais, exit codes reais, nunca mascarados por pipe) — não
escreva um teste que apenas "deveria" passar sem rodá-lo.

CONTEXTO JÁ INVESTIGADO (confirme lendo o código antes de escrever o
script, não invente comportamento):
- `ecossistema.py` (raiz) tem os comandos: forge, generate, master,
  enterprise, components sync|verify, audit, status, status --testes,
  help/--help/-h.
- `audit` roda em sequência: gates/G_ECOSSISTEMA_INTEGRIDADE.py,
  G_DRIFT_NUCLEO_COMPARTILHADO.py, G_HARNESS_COMPAT.py, G_SEGREDOS.py,
  G_CLI_HELP_CONSISTENCIA.py, G_COMPONENTE_AGNOSTICO.py — para de rodar
  no primeiro que falhar (exit code do gate é propagado).
- `components sync|verify --tipo <tipo>` usa scripts/gestor_componentes.py;
  `--tipo todos` é um marcador válido que expande para todos os tipos reais.
- `status --testes` roda pytest real em cada ferramenta (tools/aidd-forge,
  tools/aidd-generator, tools/aidd-master, tools/aidd-enterprise) e
  atualiza PLANO-EXECUCAO-ESTRUTURADO.json com a contagem medida — isto
  pode demorar alguns minutos (a suíte completa das 4 ferramentas juntas).

DEFINIÇÃO DE PRONTO — rode cada item de verdade, nesta ordem:
1. `python ecossistema.py status` — capture a saída completa, confirme
   exit 0 e que as 4 ferramentas + 4 skills aparecem como OK.
2. `python ecossistema.py status --testes` — capture a saída completa
   (contagem real de testes por ferramenta), confirme exit 0, confirme
   que PLANO-EXECUCAO-ESTRUTURADO.json foi atualizado (timestamp novo).
3. `python ecossistema.py audit` — capture a saída completa; depois,
   rode cada um dos 6 gates ISOLADAMENTE (ex.: `python
   gates/G_SEGREDOS.py`) e confirme que cada um também dá exit 0 sozinho
   — isso prova que o exit 0 do `audit` não está escondendo uma falha.
4. `python ecossistema.py components verify --tipo todos` — capture
   saída e exit code.
5. `python ecossistema.py components sync --tipo todos --dry-run` —
   capture saída e exit code; rode `git status` na raiz antes e depois,
   confirme que são idênticos (dry-run não escreveu nada).
6. `python ecossistema.py help`, `--help`, `-h` — confirme exit 0 nos 3.
7. `python ecossistema.py comando-invalido-xyz` — confirme exit 1 e
   mensagem de erro clara.

Escreva um script real (Python ou bash, à sua escolha, o que for mais
robusto para capturar exit codes e saída de cada subcomando
separadamente) que automatiza os 7 passos acima e salve-o em
`docs/testes/testes/01_ecossistema_raiz.{py|sh}`. Não há "prompt em
linguagem natural" usado nesta bateria especificamente (nenhum dos
comandos testados aqui usa entrada em linguagem natural) — pode pular a
pasta `docs/testes/prompts/` para esta bateria específica.

Execute o script de verdade agora. Depois, escreva o relatório da
bateria em Markdown em `docs/testes/relatorios/01_ecossistema_raiz.md`,
contendo: comando rodado, exit code real, um resumo da saída relevante
de cada um dos 7 itens, e um veredito final (bateria PASSOU ou FALHOU,
com justificativa). Se fizer sentido visualmente (ex.: uma tabela
comparando os 6 gates com status/duração), use as skills
`artifact-design` e `dataviz` para produzir uma versão visual do
relatório também (mantendo a versão Markdown como fonte de verdade).

CRITÉRIO DE SAÍDA:
- Os 7 itens da Definição de Pronto rodados de verdade, com evidência
  real (não hipotética) no relatório.
- `git status` da raiz do repositório limpo ao final — se `status
  --testes` ou `audit --report` tiverem gerado algum arquivo novo dentro
  de `tools/*/` como efeito colateral, reverta com `git checkout --`
  antes de finalizar (documente isso no relatório se acontecer).
- Script salvo em `docs/testes/testes/`, relatório salvo em
  `docs/testes/relatorios/`.

REGRAS DE ESCOPO — NÃO FAÇA:
- Não teste as 4 ferramentas em profundidade aqui (isso são as outras 4
  baterias, documentos separados) — só a camada de orquestração raiz.
- Não faça git commit nem git push.
- Não altere nenhum arquivo do ecossistema real fora de `docs/testes/`.

ENTREGÁVEL: caminho do script salvo, caminho do relatório salvo, e um
resumo de 3-5 linhas do veredito final.
```

## Prompt de Execução — English version

> Copy the block below in full to the executor agent. Self-contained.

```
You are going to write and run a battery of real end-to-end tests that
proves the unified CLI (`ecossistema.py`) of the ecossistema-aidd
monorepo (root at C:\Users\trcnologia\Desktop\ecossistema-aidd) and the
6 Meta-Quality Gates it orchestrates actually work. Validate everything
for real (real runs, real exit codes, never masked by a pipe) — do not
write a test that "should" pass without actually running it.

ALREADY-INVESTIGATED CONTEXT (confirm by reading the code before
writing the script, do not invent behavior):
- `ecossistema.py` (root) has these commands: forge, generate, master,
  enterprise, components sync|verify, audit, status, status --testes,
  help/--help/-h.
- `audit` runs, in sequence: gates/G_ECOSSISTEMA_INTEGRIDADE.py,
  G_DRIFT_NUCLEO_COMPARTILHADO.py, G_HARNESS_COMPAT.py, G_SEGREDOS.py,
  G_CLI_HELP_CONSISTENCIA.py, G_COMPONENTE_AGNOSTICO.py — stops at the
  first one that fails (the gate's exit code is propagated).
- `components sync|verify --tipo <tipo>` uses
  scripts/gestor_componentes.py; `--tipo todos` is a valid marker that
  expands to every real type.
- `status --testes` runs the real pytest suite of each tool
  (tools/aidd-forge, tools/aidd-generator, tools/aidd-master,
  tools/aidd-enterprise) and updates PLANO-EXECUCAO-ESTRUTURADO.json
  with the measured count — this can take a few minutes (the combined
  suite of all 4 tools).

DEFINITION OF DONE — run each item for real, in this order:
1. `python ecossistema.py status` — capture full output, confirm exit
   0 and that all 4 tools + 4 skills show as OK.
2. `python ecossistema.py status --testes` — capture full output (real
   test count per tool), confirm exit 0, confirm
   PLANO-EXECUCAO-ESTRUTURADO.json was updated (new timestamp).
3. `python ecossistema.py audit` — capture full output; then run each
   of the 6 gates ISOLATED (e.g. `python gates/G_SEGREDOS.py`) and
   confirm each also exits 0 on its own — this proves the audit's exit
   0 is not hiding a failure.
4. `python ecossistema.py components verify --tipo todos` — capture
   output and exit code.
5. `python ecossistema.py components sync --tipo todos --dry-run` —
   capture output and exit code; run `git status` at the root before
   and after, confirm they are identical (dry-run wrote nothing).
6. `python ecossistema.py help`, `--help`, `-h` — confirm exit 0 on all
   3.
7. `python ecossistema.py invalid-command-xyz` — confirm exit 1 and a
   clear error message.

Write a real script (Python or bash, your choice, whichever captures
exit codes and output of each subcommand most robustly) that automates
the 7 steps above and save it to
`docs/testes/testes/01_ecossistema_raiz.{py|sh}`. There is no "natural
language prompt" used in this specific battery (none of the commands
tested here take natural-language input) — you may skip the
`docs/testes/prompts/` folder for this specific battery.

Run the script for real now. Then write the battery report in Markdown
at `docs/testes/relatorios/01_ecossistema_raiz.md`, containing: command
run, real exit code, a summary of the relevant output for each of the
7 items, and a final verdict (battery PASSED or FAILED, with
justification). If it makes visual sense (e.g. a table comparing the 6
gates by status/duration), use the `artifact-design` and `dataviz`
skills to produce a visual version of the report too (keeping the
Markdown version as the source of truth).

EXIT CRITERIA:
- The 7 items in the Definition of Done run for real, with real (not
  hypothetical) evidence in the report.
- The root repository's `git status` clean at the end — if `status
  --testes` or `audit --report` generated any new file inside
  `tools/*/` as a side effect, revert it with `git checkout --` before
  finishing (document this in the report if it happens).
- Script saved under `docs/testes/testes/`, report saved under
  `docs/testes/relatorios/`.

SCOPE RULES — DO NOT:
- Do not deep-test the 4 tools here (that's the other 4 batteries,
  separate documents) — only the root orchestration layer.
- Do not git commit or git push.
- Do not modify any real ecosystem file outside `docs/testes/`.

DELIVERABLE: path of the saved script, path of the saved report, and a
3-5 line summary of the final verdict.
```
