---
name: aidd-reexplain
description: Re-explains the last message in plain PT-BR using the CONTEXT.md glossary. Use when the user says they did not understand, "não entendi", "explica de novo", or "reexplica".
---

# aidd-reexplain (re-pitch the last message)

The last assistant message did not land. Re-pitch it; add nothing new.

Adapted from `wait-what` in mattpocock/skills (commit c55ee46), MIT license.

## Steps
1. Read `CONTEXT.md` at the repo root. Use its terms with the meaning in "Linguagem". A term listed under "Ambiguidades sinalizadas": name which sense you mean.
2. Re-pitch the last assistant message in plain Portuguese (PT-BR):
   - One sentence of context: where the work is and why it matters.
   - Then the point, in short sentences. Everyday analogy for each technical term; no unexplained jargon.
   - Up to three short paragraphs. Go deeper only if the user asks.
3. Same facts, same numbers, same recommendation as the original message. Done when every claim of the original is present and no new claim was added.

## Negative Guardrails

- NEVER add a new fact, number, option or recommendation; only the original message, re-pitched.
- NEVER drop or soften a warning, a failed test or a pending step of the original message.
- NEVER answer in English or with unexplained jargon; plain PT-BR, one analogy per technical term.
- NEVER use a `CONTEXT.md` term outside its "Linguagem" sense; for a term under "Ambiguidades sinalizadas" (ciclo, fase, plano, sessão, ticket) name the sense you mean.

## Failure Modes & Fallback

- **`CONTEXT.md` missing or term absent:** explain with an everyday analogy and say the term is not in the glossary; never edit `CONTEXT.md` here (that is `/aidd-grill-docs`).
- **Original message is wrong or incomplete:** re-pitch it faithfully, then add one separate line saying what looks wrong; never patch it silently.
- **User still does not understand:** ask which part, by paragraph number, and re-pitch only that part.

## Stopping Checklist

- [ ] Every claim of the original message is present (checked one by one).
- [ ] Zero new claims added.
- [ ] At most three short paragraphs, in PT-BR.
- [ ] Every ambiguous `CONTEXT.md` term carries its chosen sense.
