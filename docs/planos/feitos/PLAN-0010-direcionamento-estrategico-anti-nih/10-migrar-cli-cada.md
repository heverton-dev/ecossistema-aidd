# Item 10 — Migrar CLI de cada ferramenta de argparse para o padrão do ecossistema.py (Onda 4 remanescente)

**STATUS: ✅ CONCLUÍDO em 2026-09-09 — correção e fechamento real por Claude, após auditoria ter encontrado que o fechamento anterior (Buffy) estava incompleto e continha uma afirmação falsa.**

## Definição de Feito

Zero `argparse` nos pontos de entrada de CLI das ferramentas; padrão único = click (mesmo padrão do `ecossistema.py`).

## O que a auditoria encontrou (fechamento anterior, revertido)

O registro anterior deste item afirmava "CONCLUÍDO" e alegava que `aidd.py` (master/enterprise),
`aidd_inject.py` e `pipeline_completo.py` (generator) "já estavam em click antes deste item". Essa
afirmação era **falsa**: os 4 arquivos importavam `argparse` e usavam `ArgumentParser` de verdade,
inclusive `aidd.py`, que é o ponto de entrada chamado diretamente pelo `ecossistema.py` (`cmd_master`/
`cmd_enterprise`). Só 3 scripts secundários (`add_module.py`, `run_all.py`, `autofix.py`) haviam sido
migrados de fato. A CLI do forge (`aidd_forge/cli.py`) também seguia em argparse e não era mencionada.

## O que foi corrigido nesta sessão

Migração real, preservando comportamento externo (mesmos flags, mesmos textos de ajuda, mesmos
códigos de saída):

| Ponto de entrada | Ferramenta | Linhas | Status |
| :--- | :--- | :--- | :--- |
| `aidd_forge/cli.py` | forge | 145 | ✅ migrado (init/inject) |
| `scripts/aidd_inject.py` | generator | 141 | ✅ migrado (subcomando `inject`; fallback de linguagem natural preservado fora do click) |
| `scripts/pipeline_completo.py` | generator | 393 | ✅ migrado (comando único, sem subcomandos) |
| `scripts/pipeline_ops_deploy.py` | ops | 308 | `import argparse` removido — era um import morto, o arquivo nunca teve parser/CLI própria (é uma classe `DeployOrchestrator` chamada por `pipeline_ops.py`, que já estava em click) |
| `scripts/aidd.py` | master | 1160 | ✅ migrado (19 subcomandos: plan, apply, bench, heal, prompt, setup, init, compose, compose-orca, add-module, test, audit, deploy, status, export-frontend, refine-module, scaffold-infra, inject, verificar-drift) |
| `scripts/aidd.py` | enterprise | 1146 | ✅ migrado (18 subcomandos — mesma lista do master, sem `verificar-drift`) |

Padrão adotado para os `cmd_*(args)` pré-existentes (que leem atributos via `getattr(args, ...)`):
os comandos click constroem um `types.SimpleNamespace(...)` equivalente e chamam a função original
sem alterar sua lógica interna — zero reescrita de regra de negócio, só a camada de parsing.

Ajustes finos feitos durante a migração:
- 2 textos de ajuda (`plan`, `prompt`) tinham a "disclosure" de SEM LLM presa ao `help=` do argumento
  posicional — argparse mostra isso em `--help`, click não. Movido para o `help=` do comando.
- 1 escape `100%%` (necessário no argparse por causa do `%`-substitution interno) virou `100%` (não é
  necessário no click).
- 2 gates (`G_INJECT.py` de master e enterprise) faziam grep textual por `'"inject": cmd_inject'`
  (o dict de dispatch do argparse antigo) — atualizados para também reconhecer o padrão de wiring via
  `@cli.command("inject", ...)` + `cmd_inject(types.SimpleNamespace(...))`.

## Prova

- `python -m pytest` real em cada ferramenta, tudo verde: forge 196 passed; generator 929 passed;
  aidd-ops 150 passed; aidd-master 285 passed (4 skipped, mesma baseline); aidd-enterprise 262 passed
  (4 skipped, mesma baseline).
- `gates/G_CLI_HELP_CONSISTENCIA.py`: APROVADO (100% OK) após a migração completa.
- `gates/G_DRIFT_NUCLEO_COMPARTILHADO.py`: APROVADO (100% OK) — inalterado pela migração.
- `tools/aidd-master/scripts/gates/G_INJECT.py` e `tools/aidd-enterprise/scripts/gates/G_INJECT.py`:
  APROVADOS após o ajuste do grep textual.
- `python ecossistema.py audit`: todos os 9 gates determinísticos do ecossistema (incluindo
  `G_TESTES_REAIS`, que roda o pytest real de cada ferramenta) aprovados.
- Varredura real (`grep -rn "^import argparse" tools/**/scripts/**/*.py`): as únicas ocorrências
  restantes são dentro de `gates/*.py` (parser interno de 1 flag `--dir`, uso interno documentado
  como fora de escopo desde a versão original deste item) — zero em pontos de entrada de CLI de
  ferramenta.
- Smoke test real via subprocess/`ecossistema.py` para `forge --help`, `aidd_inject.py --help`,
  `pipeline_completo.py --help`, `ecossistema.py master --help`, `ecossistema.py enterprise --help`
  e diversos subcomandos individuais.
