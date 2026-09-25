---
name: aidd-reexplica
description: Re-explain the last message in plain PT-BR using the CONTEXT.md glossary. Use when the user says they did not understand, "não entendi", "explica de novo", or "reexplica".
---

# AIDD-Reexplica — Re-pitch the Last Message

The last assistant message did not land. Re-pitch it; add nothing new.

Adapted from `wait-what` in mattpocock/skills (commit c55ee46), MIT license.

## Steps
1. Read `CONTEXT.md` at the repo root. Use its terms with the meaning in "Linguagem". A term listed under "Ambiguidades sinalizadas": name which sense you mean.
2. Re-pitch the last assistant message in plain Portuguese (PT-BR):
   - One sentence of context: where the work is and why it matters.
   - Then the point, in short sentences. Everyday analogy for each technical term; no unexplained jargon.
   - Up to three short paragraphs. Go deeper only if the user asks.
3. Same facts, same numbers, same recommendation as the original message. Done when every claim of the original is present and no new claim was added.
