---
name: aidd-skills
description: Creates, optimizes, and evaluates agent skills across all ecosystem harnesses.
---

# AIDD Skills — Criador e Otimizador de Skills

Esta skill gerencia a criação, otimização e avaliação de skills agênticas multi-harness no ecossistema AIDD, garantindo conformidade com a convenção canônica: fonte única em `componentes/<ferramenta ou compartilhado>/skills/<nome>/SKILL.md`, nome em `aidd-*` (máximo 3 palavras) e descrição concisa em inglês de 1 linha.

## Protocolo Obrigatório

1. **Estrutura Canônica:**
   - `name`: prefixo obrigatório `aidd-*`, kebab-case, no máximo 3 palavras (ex: `aidd-master`).
   - `description`: exatamente 1 linha em Inglês no frontmatter YAML.
   - Codificação estrita UTF-8 sem BOM.
2. **Materialização na Fonte Única:**
   Grave exclusivamente em `componentes/compartilhado/skills/<nome>/SKILL.md`.
3. **Propagação e Auditoria:**
   ```bash
   python ecossistema.py components sync --tipo skill
   python ecossistema.py components verify --tipo skill
   ```
