# Updating an existing textbook

Open this guide when the work already exists. Updating is surgery, not rewriting.

## 1. First, get your bearings

```bash
python <skill>/scripts/livro.py status <folder>
```

The output says how many parts exist, how many words, whether the PDF is current with the text and how many revisions happened. The manifest (`livro.json`) keeps the history: date, text fingerprint, words and the note of each revision.

Three possible results (literal output):

| Result | Meaning | What to do |
| :----------------- | :--------------------------------------------------- | :--------------------------------- |
| `PDF em dia` | nobody touched the text since the last build | go to section 2 |
| `DESATUALIZADO` | someone edited the text and did not rebuild | understand what changed before touching it |
| `PENDENTE` | never built | treat it as a new work |

If the result is `DESATUALIZADO`, **do not rebuild by reflex.** Look at what was edited first: it may be someone else's half-done work.

## 2. Classify the change before touching the text

| Kind of change | Reach |
| :----------------------------------------------- | :--------------------------------------------------------- |
| a fact changed (number, version, status, path) | the sentences citing that fact, in every part |
| a new piece appeared | a new chapter + the inventory table + the glossary |
| a piece left | its chapter goes out + its mentions in other chapters |
| a process changed shape | the process chapter + the affected diagrams |
| something pending was solved | the honest status appendix + the matching chapter |
| the work gained a level or axis | structural: talk to whoever asked before reorganizing |

The last row is the safety rule: **no structural change on your own.** Reorganizing parts breaks cross references, chapter numbers and the index; warn first.

## 3. Find everything that mentions the old fact

The biggest risk of an update is not getting the new text wrong: it is **leaving the old text alive in another chapter**. A book that says two different things about the same subject loses all its authority.

```bash
grep -rn "old term" <folder>/partes/     # every occurrence, in every part
```

Also check indirect mentions: inventory table, glossary, key-files appendix, honest status appendix and the labels inside diagrams.

## 4. Edit only what is needed

Change the affected sentences, not the whole file. Rewriting a whole part to change one number is expensive and tends to add defects where there were none.

To add a new chapter:

```bash
python <skill>/scripts/livro.py add-parte <folder> --nome 07-nova --titulo "Capítulo 7 — ..."
```

To insert in the middle, use `--depois-de <previous-part-name>`; the manifest order is the book order.

## 5. Update the evidence, not only the prose

When the fact changes, that chapter's "Rastreabilidade" section changes too: a file that no longer exists goes out, a new file comes in. A book pointing to a missing source is worse than a book without sources, because it promises an audit and delivers a mistake.

```bash
python <skill>/scripts/livro.py check <folder> --raiz-evidencia <project-root>
```

This command checks that every cited file really exists.

## 6. Rebuild and record

```bash
python <skill>/scripts/livro.py update <folder> --nota "what changed in this revision"
```

`update` compares the text fingerprint, runs the audit, rebuilds **only if something changed** and records the revision in the manifest. The note is not bureaucracy: months later it tells why chapter 12 changed.

If the audit fails, fix the findings. There is an emergency exit (`--pular-check`), but using it means publishing a book with a known defect: only on an explicit decision of whoever asked for the work.

## 7. Check the result

```bash
python <skill>/scripts/livro.py preview <folder>
```

Look at the pages you changed and the two neighbors: new text pushes the old one and may have broken a table or left a title alone at the bottom of a page.

## 8. Never do in an update

- Run `init` over an existing work: it deletes the manifest and the revision history.
- Edit the consolidated file (`<base-name>.md`): it is generated and disappears at the next build. The content lives in `partes/`.
- Delete the honest status appendix because "everything works now": update its rows, recording what was solved and when.
- Change the work title or base name without warning: it renames the delivered file and breaks every external link to it.
