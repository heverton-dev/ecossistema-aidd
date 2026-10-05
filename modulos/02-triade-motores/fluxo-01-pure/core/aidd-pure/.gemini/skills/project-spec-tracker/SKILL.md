# Skill: project-spec-tracker v1.0

> Rastreia progresso de projetos com SPEC vivo
> Registra: O QUÊ, QUANDO, QUEM, COMO foi feito

---

## 🎯 O que faz

Cria um documento **SPEC vivo** que:

- ✅ Começa vazio com checklist de todas as tarefas
- ✅ Você marca `[x]` conforme vai progredindo
- ✅ Registra **QUANDO** foi concluído (timestamp)
- ✅ Registra **QUEM** fez (responsável)
- ✅ Registra **COMO** foi feito (hash do commit)
- ✅ Armazena histórico completo em SQLite
- ✅ Auto-gera Markdown (versionável)
- ✅ Auto-gera HTML (visual)
- ✅ Auto-gera PDF (formal)

---

## 📋 Uso

### No Chat (Claude Code)

```
/project-spec-tracker
```

### No Terminal

#### Criar nova SPEC

```bash
python ~/.claude/skills/project-spec-tracker/script.py \
  --init "aidd-project-generator" \
  --versao "2.1"
```

**Resultado:** `docs/PROJECT-SPEC-aidd-project-generator.md` criado automaticamente

#### Atualizar item

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

---

## 📖 Exemplo de SPEC Gerado

```markdown
# PROJECT SPEC: aidd-project-generator

📊 Versão: 2.1
📈 Progresso: 2/6 (33%)

---

## Phase 1: Pesquisador de Referências
- [x] Pesquisador de Referências — 2026-08-29 | Claude | c17469a

## Phase 2: Análise da Ideia
- [ ] Análise da Ideia

## Phase 3: Design AIDD
- [ ] Design AIDD ← PRÓXIMO

## Phase 4: Decisão Global/Local
- [ ] Decisão Global/Local

## Phase 5: Criador de Projeto
- [x] Criador de Projeto — 2026-08-29 | Claude | 648e6d2

## Phase 6: Documentação Tripartite
- [ ] Documentação Tripartite
```

---

## 💾 Estrutura de Dados

### SQLite Tables

**project_specs**
```
id: autoincrement
project_name: string UNIQUE
version: string
descricao: text
data_criacao: ISO8601
data_ultima_atualizacao: ISO8601
progresso_percentual: float
responsavel: string
arquivo_spec: string
```

**spec_items**
```
id: autoincrement
spec_id: foreign key
fase: string
item_nome: string
status: enum (todo/in-progress/done)
data_conclusao: ISO8601 (quando foi completo)
quem: string (responsável)
como: string (descrição de como foi)
commit_hash: string (referência ao commit)
```

---

## 🔄 Fluxo Típico

1. **Criar SPEC inicial**
   ```bash
   python script.py --init "meu-projeto" --versao "1.0"
   ```
   → Cria documento com todas as tarefas em `[ ]`

2. **Conforme implementa, marcar como feito**
   ```bash
   python script.py --update --spec-id 1 --fase "Phase 1" \
     --item "Pesquisador" --status done --commit abc1234
   ```
   → Muda `[ ]` para `[x]` + timestamps + commit

3. **SPEC fica visível no `docs/PROJECT-SPEC-*.md`**
   → Versionável em Git
   → Sempre up-to-date
   → Auditável

---

## 🎁 Features

- ✅ Rastreamento completo (O quê, quando, quem, como)
- ✅ Persistência SQLite (Regra R11 AIDD)
- ✅ Compatível com qualquer harness
- ✅ Zero dependências externas
- ✅ UTF-8 nativo (Windows/Linux/macOS)
- ✅ Integração com Git (commits rastreados)

---

## 📦 Compatibilidade

- Claude Code ✅
- Cursor ✅
- Windsurf ✅
- Vim/Terminal ✅
- Windows 10/11 ✅
- Linux ✅
- macOS ✅

---

**Versão:** 1.0  
**Data:** 29 de Agosto de 2026  
**Status:** 🟢 PRONTO PARA USO
