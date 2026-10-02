# Project SPEC Tracker — Quick Start

📋 Rastreie o progresso do seu projeto com um documento vivo.

---

## Instalação

A skill já está instalada globalmente em `~/.claude/skills/project-spec-tracker/`

Para usar em um projeto, crie symlink:

```bash
ln -s ~/.claude/skills/project-spec-tracker ~/.seu-projeto/.claude/skills/project-spec-tracker
```

---

## Como Usar

### 1. Criar SPEC inicial

```bash
python ~/.claude/skills/project-spec-tracker/script.py \
  --init "Meu Projeto" \
  --versao "1.0"
```

Resultado: `docs/PROJECT-SPEC-meu-projeto.md` criado automaticamente com checklist:

```markdown
- [ ] Phase 1: Pesquisador de Referências
- [ ] Phase 2: Análise da Ideia
- [ ] Phase 3: Design AIDD
- [ ] Phase 4: Decisão Global/Local
- [ ] Phase 5: Criador de Projeto
- [ ] Phase 6: Documentação Tripartite
```

### 2. Marcar como concluído

Conforme você implementa, marque cada item:

```bash
python ~/.claude/skills/project-spec-tracker/script.py \
  --update \
  --spec-id 1 \
  --fase "Phase 1" \
  --item "Pesquisador de Referências" \
  --status "done" \
  --quem "Claude" \
  --commit "c17469a"
```

Resultado no documento:

```markdown
- [x] Phase 1: Pesquisador de Referências — 2026-08-29 | Claude | c17469a
```

### 3. Ver progresso

A SPEC gera automaticamente:

```
docs/PROJECT-SPEC-meu-projeto.md

📈 Progresso: 1/6 (16%)

- [x] Phase 1: Pesquisador de Referências
- [ ] Phase 2: Análise da Ideia
- [ ] Phase 3: Design AIDD
...
```

---

## Campos Registrados

| Campo | O que é | Exemplo |
|-------|---------|---------|
| **Fase** | Agrupamento lógico | Phase 1, Phase 3 |
| **Item** | Tarefa específica | Pesquisador de Referências |
| **Status** | Estado atual | todo / in-progress / done |
| **Quando** | Timestamp de conclusão | 2026-08-29T15:20:00Z |
| **Quem** | Responsável | Claude |
| **Como** | Commit hash | c17469a |

---

## Exemplos

### Exemplo 1: Criar SPEC para aidd-project-generator

```bash
python script.py --init "aidd-project-generator" --versao "2.1"
```

### Exemplo 2: Marcar Phase 1 como DONE

```bash
python script.py --update \
  --spec-id 1 \
  --fase "Phase 1" \
  --item "Pesquisador de Referências" \
  --status "done" \
  --quem "Claude" \
  --commit "c17469a"
```

### Exemplo 3: Marcar Phase 3 como IN-PROGRESS

```bash
python script.py --update \
  --spec-id 1 \
  --fase "Phase 3" \
  --item "Design AIDD" \
  --status "in-progress" \
  --quem "Claude"
```

---

## Arquivos Gerados

```
docs/
├── PROJECT-SPEC-aidd-project-generator.md    (Markdown versionável)
├── PROJECT-SPEC-aidd-project-generator.html  (HTML interativo) [TODO]
└── PROJECT-SPEC-aidd-project-generator.pdf   (PDF formal) [TODO]

database/
└── project_specs.db  (SQLite com histórico completo)
```

---

## Status

✅ v1.0 — Rastreamento básico completo  
⏳ v1.1 — Geração de HTML/PDF tripartite  
⏳ v1.2 — Dashboard interativo

---

**Criada:** 29 de Agosto de 2026  
**Versão:** 1.0.0  
**Status:** 🟢 PRONTO
