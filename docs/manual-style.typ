// Estilo visual do Manual Completo do Ecossistema AIDD.
// Paleta e tipografia consistentes com docs/reports/analise-stack-por-camada.typ
// (Inter para texto, Consolas para código, slate/emerald/amber/red para status).
//
// Para regerar o PDF (pandoc + typst):
//   pandoc docs/MANUAL-COMPLETO.md --pdf-engine=typst --toc \
//     --include-in-header=docs/manual-style.typ \
//     --metadata title="Manual Completo do Ecossistema AIDD" \
//     -o docs/MANUAL-COMPLETO-ECOSSISTEMA-AIDD-v2.pdf

#set text(font: "Inter", size: 10.5pt, fill: luma(30))
#set page(numbering: "1", number-align: center)

#show heading.where(level: 1): it => {
  pagebreak(weak: true)
  block(above: 0pt, below: 14pt)[
    #text(size: 19pt, weight: "black", fill: rgb("#0f172a"))[#it.body]
    #v(4pt)
    #line(length: 100%, stroke: 1.5pt + rgb("#0f172a"))
  ]
}
#show heading.where(level: 2): it => block(above: 16pt, below: 8pt)[
  #text(size: 13pt, weight: "bold", fill: rgb("#1e293b"))[#it.body]
]
#show heading.where(level: 3): it => block(above: 12pt, below: 6pt)[
  #text(size: 11pt, weight: "bold", fill: rgb("#334155"))[#it.body]
]

#show raw.where(block: false): it => box(fill: luma(240), outset: (y: 2pt), inset: (x: 3pt), radius: 2pt)[#text(font: "Consolas", size: 9pt, fill: rgb("#0369a1"))[#it.text]]
#show raw.where(block: true): it => block(fill: luma(246), inset: 8pt, radius: 4pt, width: 100%, stroke: 0.5pt + luma(220))[#text(font: "Consolas", size: 8.5pt, fill: luma(30))[#it]]

#set table(
  stroke: 0.5pt + luma(210),
  inset: 6pt,
  fill: (_, y) => if y == 0 { rgb("#0f172a") } else if calc.odd(y) { luma(250) } else { white },
)
#show table.cell.where(y: 0): set text(fill: white, weight: "bold", size: 8.5pt)

// Pandoc envolve toda tabela em #figure(), cujo bloco interno é
// breakable:false por padrão no Typst — isso sobrepunha texto em
// tabelas longas (ex.: Glossário) em vez de quebrar de página.
#show figure.where(kind: table): set block(breakable: true)

#let corDoStatus(t) = {
  if t in ("CRÍTICA", "ALTA") { rgb("#dc2626") }
  else if t in ("MÉDIA", "PARCIAL") { rgb("#d97706") }
  else if t in ("BAIXA", "NENHUMA", "CONCLUÍDO", "IMPLEMENTADO") { rgb("#059669") }
  else { none }
}

#show strong: it => {
  let s = it.body
  let plano = if type(s) == str { s } else if s.has("text") { s.text } else { none }
  let cor = if plano != none { corDoStatus(plano) } else { none }
  if cor != none { text(fill: cor, weight: "bold")[#it.body] } else { it }
}
