---
name: aidd-textbook
description: Generates and updates auditable corporate textbooks as PDF (pandoc + typst) with a macro-meso-micro structure, per-chapter traceability and a deterministic audit. Works in any repository. Use when the user wants to write or update a textbook, manual or book in PDF, or types "/aidd-livro-texto", "livro-texto", "gerar livro", "atualizar livro".
---

# aidd-textbook

Produces and maintains PDF textbooks with corporate layout, macro -> micro structure, per-chapter traceability and deterministic audit. Nothing here depends on a specific project.

Slash command: `/aidd-livro-texto <criar|atualizar> <folder>`. Engine: `python <skill>/scripts/livro.py <subcommand>` (in this monorepo `<skill>` is `componentes/compartilhado/skills/aidd-textbook`).

## 1. New work or update?

```bash
python <skill>/scripts/livro.py doctor               # pandoc + typst + fonts
python <skill>/scripts/livro.py status <folder>      # is there a livro.json?
```

- `status` answers -> **update**, go to section 4.
- `status` fails with "manifesto ausente" -> **new work**, go to section 3.

Never create a new work over an existing one: `init` without `--force` refuses, and forcing deletes the manifest and the revision history.

## 2. Six laws of the work

1. **Determinism first.** Concatenating, compiling, auditing, measuring and versioning is `livro.py` work (zero tokens). You write only the Markdown of the parts.
2. **Mandatory traceability.** Every chapter ends with a *Rastreabilidade* section naming the files and sources behind its claims. A claim without a source stays out.
3. **Label honesty.** What is incomplete, red or awaiting a human decision is recorded with date and reason, including an "Estado honesto" appendix.
4. **Evidence before prose.** Read the real material (code, config, data) before writing. Never describe intent as implementation.
5. **Fixed structure.** Macro -> meso -> micro, same template at every level, so two objects compare by reading the same section.
6. **Token economy.** Section 5 applies during the whole run.

## 3. New work

```bash
# 3.1 skeleton (partes/, livro.json, frontmatter with cover metadata)
python <skill>/scripts/livro.py init <folder> \
  --titulo "<Title>" --subtitulo "<Subtitle>" --autor "<Author>" \
  --instituicao "<Footer>" --eyebrow "<COVER LABEL>" --tagline "<one line>"

# 3.2 (optional) own visual identity
python <skill>/scripts/livro.py init <folder> ... --copiar-template

# 3.3 one part per block of the work
python <skill>/scripts/livro.py add-parte <folder> --nome 02-meso --titulo "PARTE II — ..."
```

3.4 **Gather evidence.** Read the real sources and note each path. Query a code graph or project index before text search. Measure numbers, never estimate.

3.5 **Write the parts** in `<folder>/partes/*.md` following `referencias/ESTRUTURA.md` (template) and `referencias/DIAGRAMACAO.md` (layout). Load them only when writing.

3.6 **Audit and compile:**

```bash
python <skill>/scripts/livro.py check <folder> --raiz-evidencia <project-root>
python <skill>/scripts/livro.py build <folder>
python <skill>/scripts/livro.py preview <folder>    # one PNG per page
```

`check` exits 1 on an odd code fence, unbalanced typst block, too-narrow table column, table not filling the body width, missing PT-BR accents or a cited file that does not exist. Fix before compiling.

3.7 **Inspect for real.** Open at least the cover, the table of contents, one wide-table page and one diagram page in the PNGs. `build` exit 0 means it compiled, not that it looks right.

## 4. Update an existing book

```bash
python <skill>/scripts/livro.py status <folder>      # is the PDF current with the source?
# edit only the affected parts in <folder>/partes/
python <skill>/scripts/livro.py update <folder> --nota "what changed in this revision"
```

`update` compares the source hash, runs `check`, recompiles only if something changed and records the revision (date, hash, words, note) in `livro.json`. Scope rules: `referencias/ATUALIZACAO.md`.

Updating is surgery, not rewriting: touch only the parts affected by the new fact; if the structure must change, tell the user first.

## 5. Token economy

- Mechanical work goes to `livro.py`. Never concatenate, count words or validate layout by hand; never rewrite a whole file to change a paragraph.
- Load `referencias/*.md` on demand, one at a time.
- Never dump into context: PDF, build log, generated `.typ`, long directory listings or the consolidated Markdown. Use `| tail -n 20` on verbose commands.
- Write each part once, reviewed.
- In a large work treat each part as an independent unit: read its evidence, write it, release the context, move on.
- Reuse numbers already measured.

## 6. References (open only when needed)

| File | Open when |
|---|---|
| `referencias/ESTRUTURA.md` | defining the index or writing any chapter |
| `referencias/DIAGRAMACAO.md` | building a table, diagram, panel or technical sheet |
| `referencias/ATUALIZACAO.md` | updating an existing work |
| `referencias/INSTALACAO.md` | installing the skill outside this repository |

## 7. Outputs

| Artifact | What it is |
|---|---|
| `<folder>/partes/*.md` | editable source; the content lives here |
| `<folder>/livro.json` | manifest: part order, hash, revision history |
| `<base-name>.md` | consolidated Markdown (generated; do not edit) |
| `<base-name>.pdf` | the book |
| `<folder>/preview/` | one PNG per page for visual inspection (disposable) |
