# Layout: what exists and what breaks

Open this guide when building a table, diagram, panel or technical sheet. Every rule here came from a defect seen on a rendered page, not from taste. PT-BR strings inside the examples are literal book content.

## 1. Available visual blocks

The visual template exposes these constructs. Use them inside a raw layout block:

````markdown
```{=typst}
#painel("Título do painel")[
  Texto do painel. Serve para contexto, decisão histórica ou advertência.
]
```
````

| Construct | What it is for |
| :------------- | :-------------------------------------------------------------------- |
| `#painel(t)[…]` | highlight box with a colored stripe on the left |
| `#ficha(…)` | two-column table: the identity card of an object |
| `#esteira(…)` | horizontal sequence of boxes linked by arrows |
| `#no(t, sub:)` | dark box: an automatic step, no intervention |
| `#no-claro(t, sub:)` | light box: a step that uses an AI model |
| `#chip(t)` | small tag to mark a status inside a paragraph |

Ready examples:

````markdown
```{=typst}
#ficha(
  ("Papel", "O que este objeto é, em uma linha"),
  ("Entrada", "O que consome"),
  ("Saída", "O que entrega"),
)
```
````

````markdown
```{=typst}
#esteira(
  no("1. COLETA", sub: "automática"),
  no-claro("2. ANÁLISE", sub: "usa modelo de IA"),
  no("3. ENTREGA", sub: "automática", cor: rgb("#334155")),
)
```
````

Dark/light must mean the same thing in the whole book. Pick the meaning in the opening and never switch it.

## 2. Tables: the two traps

**Trap 1: narrow table.** The converter only makes a table fill the page width when the separator line is longer than 72 characters. Below that the table shrinks to its content and sits misaligned in the middle of the page.

Wrong (the table comes out tiny):

```markdown
| A | B |
|---|---|
| 1 | 2 |
```

Right (long separators, the table fills the page):

```markdown
| Coluna A                        | Coluna B                                          |
| :------------------------------ | :------------------------------------------------- |
| 1                               | 2                                                 |
```

**Trap 2: column too narrow for its content.** Each column's width is proportional to its separator length. If the first column has a short separator and a long name, the text spills into the next column.

Rule of thumb: **each column's separator is proportional to its longest content.** A long technical name needs a long separator.

`check` flags both cases before you build. Always run it.

## 3. Technical names and file paths

Write file names, commands and identifiers between backticks. The template gives them a light background, prevents hyphenation and inserts invisible break points after `/`, `.`, `_` and `-`, so a long path breaks inside the cell instead of spilling over the next column.

In **bold**, hyphenation is off: a tool's proper name must not become "aidd-mas-ter".

## 4. Diagrams: at most four boxes per row

A pipeline with more than four boxes makes each one too narrow and long words start to spill. Break it into two rows:

````markdown
```{=typst}
#esteira(
  no("1. PRIMEIRA", sub: "..."),
  no("2. SEGUNDA", sub: "..."),
  no("3. TERCEIRA", sub: "..."),
  no("4. QUARTA", sub: "..."),
)
#v(-4pt)
#esteira(
  no("5. QUINTA", sub: "..."),
  no("6. SEXTA", sub: "..."),
)
```
````

Box label: at most two short words. The detail goes in `sub:`.

## 5. Headings

`#` opens a chapter and always starts a new page with a dark stripe. Use it for chapters and part opening sheets, never for internal subdivision.

`##` is a section, `###` a subsection, `####` the last useful level. Below that the reader loses the hierarchy and the table of contents becomes unreadable.

Backtick code inside a chapter heading is automatically turned into light text on the dark stripe: it is fine to use.

## 6. Accents

Portuguese text keeps every accent. A word without its accent is a review error, and `check` flags the most common cases. This also applies to labels inside diagrams, which go unnoticed because they sit inside a code block.

## 7. Before declaring it done

```bash
python <skill>/scripts/livro.py check <folder>     # flags the defects above
python <skill>/scripts/livro.py build <folder>
python <skill>/scripts/livro.py preview <folder>   # one image per page
```

Look at least at four pages: the cover, the table of contents, one with a wide table and one with a diagram. Building without error means the file was generated, not that it is readable.
