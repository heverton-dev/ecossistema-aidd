# Plan structure

## Naming convention

Every plan folder is `PLAN-<NNNN>-<3-word-name>` (real example: `PLAN-0016-qualidade-testes-mutacao`).

- `NNNN` is global and permanent: it does not restart per subfolder (`a-fazer/`, `fazendo/`, `feitos/`) and is never reused. Use it to name a plan without ambiguity.
- No date in the name: the number gives the order and git keeps the real date.
- The short name has 3 meaningful words (no articles or prepositions).
- Item files follow the same 3-word limit (`04-eliminar-timesleep-injetar.md`); the item name becomes a file, a table label and a branch. Only exception: the master file `00-PROCESSO-E-DECISOES.md`, fixed in code.
- `python ecossistema.py plan init <name>` generates the number and the short name. Never number by hand.
- The prefix appears in the physical path; `INDEX.md` shows only the clean title.

## Where a plan is born vs where it lives

`plan init` always creates `docs/planos/PLAN-<NNNN>-<name>/` at the root. `scripts/atualizar_index_planos.py` (run by hand or by the pre-commit hook) moves it to `a-fazer/`, `fazendo/` or `feitos/` from the real status of the progress table. Never decide the subfolder yourself.

## Generated files

1. `00-PROCESSO-E-DECISOES.md`: origin, purpose, governance notice; canonical sections (goal with the initiative metric current/target/real grade, adopted process, where the technical content lives, fixed rules, progress log with every item as `⏳ Rascunho gerado, aguardando aprovacao`).
2. `NN-<item>.md` per agreed item: scope, status `[RASCUNHO — Aguardando Aprovacao Humana]`, grade block with evidence, investigated context, checkable definition of done, exit criterion, execution prompt in PT-BR and a self-contained English version.
3. Real grade: filled only when an item or initiative closes, running the SAME real mechanism that measured the current grade, never a "similar" command.

## Canonical examples

- `docs/planos/feitos/PLAN-0001-evolucao-notas-auditoria/00-PROCESSO-E-DECISOES.md`
- `docs/planos/feitos/PLAN-0003-refinamento-notas-auditoria/00-PROCESSO-E-DECISOES.md`
- `docs/planos/feitos/PLAN-0007-testes-completos-ecossistema/00-PROCESSO-E-DECISOES.md`
- `docs/planos/feitos/PLAN-0005-skill-gerador-planos/00-PROCESSO-E-DECISOES.md`
