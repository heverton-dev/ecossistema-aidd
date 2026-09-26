# Canonical structure of a textbook

Open this guide when defining the index of the work or writing any chapter. Section and chapter titles quoted in PT-BR below are the literal text that goes into the book.

## 1. The matrix: three levels, fixed axes

The work goes from the general to the particular in three levels, and at each level it asks **the same questions**. That lets the reader compare two objects by reading the same section of each chapter instead of rereading the whole book.

| Level | What it describes | Book part |
| :-------- | :----------------------------------------------------------- | :------------- |
| **Macro** | the whole as a single organism: purpose, laws, topology | Part I |
| **Meso** | the processes: the pipelines from intent to result | Part II |
| **Micro** | the pieces: one chapter per component | Part III |
| Cross-cutting | what crosses every level (patterns, quality) | Part IV |
| Appendices | lookup reference, glossary, honest status | Appendices |

There are three fixed axes (the questions repeated at every level). Adapt the names to the domain, but keep the repetition:

1. **How it was designed and built** (the intent and the engineering behind it).
2. **How it is today** (the real architecture, not the desired one).
3. **The domain's own axis** (cost, performance, security, economy: pick what matters most in that system and keep it at every level).

## 2. Template of each Part III chapter

Every piece chapter has eight sections, in this order (literal PT-BR titles):

```
X.1  O que é
X.2  Papel dentro do processo (nível meso)
X.3  Papel dentro do todo (nível macro)
X.4  Como foi pensada, está estruturada e configurada
X.5  Como funciona individualmente        ─┐
X.6  Como funciona dentro do processo      ├─ the seven items below, in each one
X.7  Como funciona dentro do todo         ─┘
X.8  Rastreabilidade
```

Sections X.5, X.6 and X.7 always answer **the same seven items**:

| Item | Question |
| ---: | :------------------------------------------------------------------------- |
| 1 | Step-by-step execution: what happens, in order |
| 2 | Quality checks: what blocks, and with which criterion |
| 3 | Skills: what is triggered in that layer |
| 4 | Automation: which scripts do the work without intervention |
| 5 | Tools accessed: external programs, services and data |
| 6 | Automatic triggers and rules: what runs by itself and which norms apply |
| 7 | Delivery: what it delivers, how, and to whom |

Opening the chapter with a **technical sheet** (`#ficha(...)`) saves pages: role, position in the process, trigger, input, output, nature.

## 3. The four mandatory sections of the work

**"Como ler este livro"** (opening). Who it is for, the matrix of the work, the visual conventions and what the work deliberately is not.

**"Rastreabilidade"** (end of each chapter). The files or sources that support the chapter's claims. It separates an auditable book from an opinion text: the reader must be able to check alone.

**"Glossário"** (appendix). Every domain term defined in one or two sentences. A term used in the body without explanation must be here.

**"Estado honesto"** (final appendix). Consolidated table of what is incomplete, failing or awaiting a human decision, with date, reason and where it is recorded. A book that only shows what works is a sales brochure, and the lost trust spreads to the rest of the text.

## 4. How to write each chapter

**Evidence first, prose after.** Read the real material before writing. Numbers come from measurement, never estimation; when something is an estimate, say so.

**One claim, one source.** If you cannot point to where something is, the claim goes out or goes in marked as a hypothesis.

**Explain why, not only what.** The interesting technical decision is the one with a documented reason, especially when it came from a real problem. Record the problem.

**Contradiction is content.** When the documentation says one thing and the code does another, the book records both and says which one holds.

**Length follows complexity.** A simple piece chapter may have three pages; do not inflate it to match its neighbor.

## 5. Recommended writing order

1. Gather evidence and build the index (chapter names and what each covers).
2. Write Part III (the pieces): the most concrete evidence is there.
3. Write Part II (the processes), already knowing how the pieces work.
4. Write Part I (the whole), which synthesizes what the two previous parts showed.
5. Write Part IV and the appendices, which consolidate what repeated.
6. Write the opening last: only then do you know what the book really became.

Writing the macro first leads to promising at the start what the micro later contradicts.
