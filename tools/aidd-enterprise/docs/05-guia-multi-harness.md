# 05. Guia Multi-Harness: Operação Universal em Qualquer IA

> **Framework:** AIDD Master Enterprise  
> **Compatibilidade:** Claude Code, Antigravity, Cursor, Codex, OpenCode, MimoCode e Gemini CLI.

---

## 1. Princípio da Fonte Canônica

O AIDD Master Enterprise é agnóstico ao ambiente de IA. Para que você não precise duplicar skills e regras a cada nova ferramenta que surge, o projeto adota o padrão de **Fonte Canônica**:

```
.agent/                       # 🌟 FONTE CANÔNICA CENTRAL
└── skills/
    └── resumo-sessao/
            │
            ├────► .claude/skills/resumo-sessao/   (Apontamento Symlink / Junction)
            ├────► .mimocode/skills/resumo-sessao/ (Apontamento Symlink / Junction)
            └────► .skills/resumo-sessao/          (Apontamento Symlink / Junction)
```

Qualquer alteração feita em uma skill dentro de `.agent/` é refletida imediatamente para todas as outras IDEs e agentes.

---

## 2. Como Operar em Cada Harness

### A. Google Antigravity (AGY CLI 2.0 / IDE)
1. Abra a pasta do projeto no Antigravity ou inicie via terminal `agy`.
2. As regras de sistema são lidas automaticamente do arquivo `AGENTS.md` e `.agent/`.
3. Os slash commands como `/compose` ou `/resumo-sessao` funcionam nativamente no chat.
4. Para auditar a esteira via subagente, o Antigravity utiliza os perfis prontos em `templates/agents/`.

### B. Claude Code (CLI Oficial da Anthropic)
1. Execute `claude` dentro da pasta raiz do projeto.
2. O Claude Code lê automaticamente as configurações em `.claude/` e `CLAUDE.md`.
3. Para compor uma nova suíte, digite no terminal do Claude:
   ```bash
   python scripts/aidd.py compose-orca crm erp billing
   ```
4. O Claude Code atuará como arquiteto e o maestro mecânico Python cuidará do isolamento das fatias.

### C. Cursor IDE
1. Abra a pasta no Cursor.
2. O arquivo `.cursorrules` (sincronizado com `AGENTS.md`) garante que o agente do Cursor respeite o Result Monad, a proibição de acoplamento inter-fatias e o modo SQLite WAL.
3. No chat do Cursor (Ctrl+L), solicite: *"Crie o módulo financeiro seguindo as regras do AIDD"*.

### D. OpenAI Codex / OpenCode / MimoCode
1. Cada ferramenta reconhece o manifesto de entrada `AGENTS.md` na raiz.
2. A suíte de auto-descoberta de frota (`FleetDiscovery`) detecta automaticamente qual CLI está no `$PATH` e delega os papéis:
   - Se detectar `codex`, prioriza tarefas de persistência e banco.
   - Se detectar `claude`, prioriza tarefas de arquitetura e Clean Code.
   - Se detectar apenas 1 agente, opera no **Modo Agente Único Isolado**, preservando a pureza de contexto via worktrees efêmeras.

---

## 3. Comandos Universais (Idênticos em Qualquer Harness)

Independentemente de onde você estiver, estes comandos funcionam da mesma forma:

```bash
# Diagnóstico e verificação de frota de IAs
python scripts/aidd.py setup

# Composição com subagentes descartáveis
python scripts/aidd.py compose-orca modulo1 modulo2

# Auditoria completa de 10 Gates
python scripts/run_all.py

# Validação da suíte de testes unitários
python -m pytest tests/
```
