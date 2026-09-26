---
name: aidd-skills
description: Creates, improves and evaluates own agent skills following docs/protocolos/CONVENCAO-AUTORIA-SKILLS.md (aidd-<subject> name, "Use when" description, compact English body, single source in componentes/) and distributes them to every harness. Use when the user wants to create, edit, rename or review a skill, or says "criar skill", "nova skill", "melhorar skill", "skill-creator".
---

# aidd-skills

Thin coordinator. The rules live in one place: `docs/protocolos/CONVENCAO-AUTORIA-SKILLS.md` (sections 5.1 frontmatter, 5.2 body, 5.3 names, 6 step by step). Writing technique: `aidd-agent-writing`. Third-party skills are registered by `aidd-dependencies`, never written here.

## Protocol

1. **Search first** in the catalog (`docs/auditoria/mapa-pecas/catalogo-pecas.json`, list `skills`) by name and description words. If a similar skill exists, improve it instead. Done when the closest existing skill (or "none") is noted.
2. **Find the active harness capabilities.** If it has a native skill authoring tool, use it for frontmatter structure, description clarity and trigger overlap with existing skills.
3. **Otherwise apply the convention:**
   - `name`: `aidd-<subject>`, English, 1 to 3 words, equal to the folder, no `-runner`, no number, no version.
   - `description`: English, third person, what it does + "Use when ..." + the words the user types (PT-BR slash commands and phrases included). Neighbor skills get mutually exclusive descriptions.
   - Body: compact English, target 150 lines, hard cap 450; consultation material in `references/`, one pointer line each; numbered steps ending on a checkable done condition; mechanical work in `scripts/` that the skill tells the agent to run.
   - A human shortcut is a slash command in `componentes/compartilhado/comandos/` that only points to the skill.
   - Never fabricate user approval or decisions inside a skill.
4. **Write the source only in** `componentes/<tool or compartilhado>/skills/<name>/SKILL.md`, never in `.claude/skills/`, `.agents/skills/` etc.
5. **Distribute and confirm:**
   ```bash
   python ecossistema.py components sync --tipo skill --ferramenta <tool or compartilhado>
   python ecossistema.py components verify --tipo skill
   python gates/G_SKILL_ROT.py
   python gates/G_SKILL_FORMATO.py
   ```
   Done when all four exit 0. Never declare a skill ready just because the file was written.
