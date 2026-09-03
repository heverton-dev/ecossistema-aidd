# Padrão de Symlinks — Zero Duplicação

**Aplicável a:** Linux, macOS, Git Bash avançado  
**Status:** Documentação + script de setup

---

## Princípio: Um Arquivo Central, Múltiplos Apontadores

```
AGENTS.md (fonte única)
├── .claude/CLAUDE.md → ../AGENTS.md (symlink)
├── .codex/CODEX.md → ../AGENTS.md (symlink, futuro)
├── .gemini/GEMINI.md → ../AGENTS.md (symlink, futuro)
└── ...

AGENTS-WORKFLOW.md (fonte única)
├── .claude/WORKFLOW-ESTRUTURADO.md → ../AGENTS-WORKFLOW.md (symlink)
├── .codex/WORKFLOW-ESTRUTURADO.md → ../AGENTS-WORKFLOW.md (symlink, futuro)
└── ...
```

**Benefício:**
- ✅ Editar `AGENTS.md` uma vez, todos harness veem a mudança
- ✅ Zero inconsistência (não há 3 cópias desincronizadas)
- ✅ Manutenção centralizada

---

## Como Configurar (em Linux/macOS)

### Opção 1: Script Automático

```bash
cd aidd-generator

# Remover cópias atuais (se existirem)
rm -f .claude/CLAUDE.md .claude/WORKFLOW-ESTRUTURADO.md

# Criar symlinks
ln -s ../AGENTS.md .claude/CLAUDE.md
ln -s ../AGENTS-WORKFLOW.md .claude/WORKFLOW-ESTRUTURADO.md

# Verificar
ls -la .claude/*.md | grep AGENTS
# Output:
# .claude/CLAUDE.md -> ../AGENTS.md
# .claude/WORKFLOW-ESTRUTURADO.md -> ../AGENTS-WORKFLOW.md
```

### Opção 2: Script Fornecido

```bash
bash symlinks-setup.sh
```

(Ver seção "Script Automático" abaixo)

---

## Status Atual (Windows)

No Windows (onde este projeto foi criado), os symlinks não funcionam nativamente sem privilégios administrativos.

**Solução pragmática:**
- ✅ Arquivos estão como **cópias** (conteúdo idêntico)
- ✅ Git rastreia versão única (edita AGENTS.md, commita, pronto)
- ⏳ Quando migrado para Linux/macOS: rodar script symlinks-setup.sh

**Qual é o impacto?**
- Nenhum (conteúdo é o mesmo)
- Manutenção: editar AGENTS.md, depois rodar `git add .claude/CLAUDE.md` (cópia é atualizada)
- **Após symlinks:** automático (editar AGENTS.md é suficiente)

---

## Script Automático: `symlinks-setup.sh`

```bash
#!/bin/bash
# Criar symlinks para AGENTS central

set -e

PROJ_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJ_DIR"

echo "🔗 Criando symlinks para AGENTS central..."

# Remover arquivos antigos
rm -f .claude/CLAUDE.md .claude/WORKFLOW-ESTRUTURADO.md

# Criar symlinks
ln -s ../AGENTS.md .claude/CLAUDE.md
ln -s ../AGENTS-WORKFLOW.md .claude/WORKFLOW-ESTRUTURADO.md

# Criar diretórios de harness futuros (quando suportados)
# mkdir -p .codex .gemini .opencode .mimocode
# ln -s ../AGENTS.md .codex/CODEX.md
# ln -s ../AGENTS-WORKFLOW.md .codex/WORKFLOW-ESTRUTURADO.md
# ... (repetir para outros harness)

echo "✅ Symlinks criados com sucesso:"
ls -la .claude/CLAUDE.md .claude/WORKFLOW-ESTRUTURADO.md

echo "🔍 Git status:"
git status --short .claude/ AGENTS*.md
```

---

## Processo de Manutenção

### Quando Editar `AGENTS.md`

```bash
# 1. Editar arquivo central
vim AGENTS.md

# 2. Commitar
git add AGENTS.md
git commit -m "docs(agents): atualizar padrão universal"

# 3. Em sistemas com symlinks: pronto (automático)
# Em sistemas com cópias: executar
git add .claude/CLAUDE.md
git commit -m "docs(.claude): sincronizar com AGENTS.md"
```

### Quando Criar Novo Harness (ex: Codex)

```bash
# 1. Criar estrutura de diretório
mkdir -p .codex

# 2. Criar symlinks (em Unix) ou cópias (em Windows)
ln -s ../AGENTS.md .codex/CODEX.md
ln -s ../AGENTS-WORKFLOW.md .codex/WORKFLOW-ESTRUTURADO.md

# 3. Commitar
git add .codex/
git commit -m "feat: suporte a Codex harness (symlinks centrais)"
```

---

## Verificação

```bash
# Verificar que são symlinks
file .claude/CLAUDE.md
# Output: symbolic link to ../AGENTS.md

# Verificar conteúdo é o mesmo
diff .claude/CLAUDE.md AGENTS.md
# Output: (vazio = idêntico)

# Verificar git tracking
git ls-files .claude/CLAUDE.md
# Output: .claude/CLAUDE.md
```

---

## Nota para Usuários Windows

Se você estiver no Windows e quiser usar symlinks reais:

```powershell
# Opção 1: Rodar PowerShell como Admin
New-Item -ItemType SymbolicLink -Path '.claude\CLAUDE.md' -Target 'AGENTS.md'

# Opção 2: Usar Git Bash avançado (não suportado por padrão)
# Não recomendado — manter como cópias

# Opção 3: Rodar em WSL2 (Windows Subsystem for Linux)
wsl bash symlinks-setup.sh
```

---

## Impacto em Workflows Futuros

### Quando adicionar Novo Harness

```
1. Criar diretório (ex: .codex/)
2. Copiar estrutura de .claude/
3. Fazer CODEX.md → symlink para ../AGENTS.md
4. Commitar
```

Resultado: **zero duplicação**, uma mudança em AGENTS.md afeta todos automaticamente.

---

## Rastreabilidade Git

```bash
# Ver histórico de mudanças em AGENTS.md
git log --oneline AGENTS.md

# Ver quem editou cada seção
git blame AGENTS.md

# Ver diffs
git diff HEAD~1 AGENTS.md

# Ver que .claude/CLAUDE.md é symlink (em Unix)
git ls-tree HEAD | grep CLAUDE
# Output: 120000 blob ... .claude/CLAUDE.md
#         ^^^^^^ = symlink (120000)
```

---

**Última atualização:** 30/08/2026  
**Próximo passo:** Após migrar para Linux/macOS, executar `bash symlinks-setup.sh`
