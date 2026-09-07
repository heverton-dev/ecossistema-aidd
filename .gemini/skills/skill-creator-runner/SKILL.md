---
name: skill-creator-runner
description: Cria, melhora ou avalia skills deste ecossistema (qualquer ferramenta ou compartilhado), garantindo que o resultado seja materializado em componentes/ e sincronizado em todos os harnesses — usa o skill-creator nativo da Anthropic quando disponível, ou o checklist próprio abaixo quando não.
---

# Skill Creator Runner

Coordenador fino. **Não reimplementa** lógica de autoria de skill — delega pro
`skill-creator` nativo (Claude Code) quando disponível, e só garante que o
resultado siga a convenção física deste projeto: fonte única em
`componentes/<ferramenta ou compartilhado>/skills/<nome>/SKILL.md`, nunca
escrito direto numa pasta de harness.

## Protocolo ao ser acionada

1. **Descubra o harness ativo.** Se for Claude Code, o `skill-creator` nativo
   está disponível — invoque-o para toda a parte de autoria/melhoria/avaliação
   (estrutura de frontmatter, clareza de `description` pra triggering correto,
   evitar ambiguidade com outras skills existentes). Não decida essas questões
   sozinho quando o `skill-creator` puder decidir.

2. **Se o harness não tiver `skill-creator` nativo** (OpenCode, MimoCode,
   Gemini CLI, Cursor, Hermes, etc.), siga este checklist condensado, usando
   como referência real as skills já existentes em `componentes/compartilhado/skills/`
   (ex.: `dependencia-runner`, `aidd-ops-runner`) — leia uma antes de escrever:
   - `name`: kebab-case, único no ecossistema (confira `python ecossistema.py components verify --tipo skill` não vai colidir).
   - `description`: 1 frase, específica o bastante pra disparar só quando deveria — nunca genérica ("ajuda com X") a ponto de competir com outra skill.
   - Corpo: seção "Protocolo ao ser acionada" com passos numerados e determinísticos sempre que possível (comando real, não "decida a melhor forma").
   - Nunca fabricar aprovação/decisão do usuário dentro da skill — mesma regra de `planos-auditoria-runner`.

3. **Sempre grave a fonte em `componentes/<ferramenta ou compartilhado>/skills/<nome>/SKILL.md`** — nunca em `.claude/skills/`, `.agents/skills/` etc. diretamente (essas são destinos gerados).

4. **Materialize e confirme:**
   ```bash
   python ecossistema.py components sync --tipo skill --ferramenta <ferramenta ou compartilhado>
   python ecossistema.py components verify --tipo skill
   ```
   Só reporte sucesso depois do `verify` retornar exit 0 — nunca declare a skill pronta só porque o arquivo foi escrito.

## Quando NÃO usar esta skill

- Pra criar skill de terceiro (ex.: instalar mais um `impeccable`-like) — isso é `dependencia-runner`, não esta.
- Pra editar o conteúdo técnico de uma skill já materializada sem passar pelo passo 4 — nunca edite as cópias em `.claude/skills/` etc. diretamente, edite sempre em `componentes/` e resincronize.
