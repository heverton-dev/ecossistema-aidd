# 🔨 AIDD Forge

> **Motor Universal de Governança Agêntica, Descarte de Contexto e Economia Extrema de Tokens**

O **AIDD Forge** (`aidd-forge`) é uma ferramenta autônoma de bootstrap e padronização que injeta em **qualquer projeto** a infraestrutura completa de AI-Driven Development (AIDD): orquestração de subagentes efêmeros, governança granular por fase, 7 Quality Gates determinísticos, auto-descoberta de frota no host e economia extrema de tokens (Tríade Caveman Ultra).

---

## ⚡ Início Rápido (1-Clique)

### Windows
Basta dar duplo clique em:
```text
setup.bat
```

### Linux / macOS
```bash
chmod +x setup.sh && ./setup.sh
```

### Via CLI Python
```bash
pip install -e .
forge init [caminho_do_projeto]
```

---

## 🌐 Agnosticismo Total de Harness

O AIDD Forge **não é amarrado a nenhuma ferramenta específica**. Ele opera em qualquer IDE ou harness:

| Harness / Ambiente | Como o Forge Suporta |
| :--- | :--- |
| **Antigravity (AGY)** | Padrão canônico `.agent/` (skills, regras e comandos). |
| **Claude Code** | Injeção de `CLAUDE.md` e comandos em `.claude/commands/`. |
| **Cursor IDE** | Regras em `.cursor/rules/forge.md` e `.cursor/rules/aidd-init.md`. |
| **Codex / CLI** | Detecção automática via PATH e fallback em worktrees. |
| **Open Code / MimoCode** | Compatibilidade nativa com a pasta `.agent/` e slash router. |
| **Ollama / LLMs Locais** | Suporte de inventário e execução determinística local. |

---

## 🧱 Arquitetura e Componentes Centrais

1. **SubagentPurger (`aidd_forge/core/subagent_purger.py`):** Motor de cognição sob demanda com descarte imediato de contexto (`Context-Purge`). Prompt restrito (<1.000 tokens), validação prévia via `ast.parse` e destruição total da sessão pós-gravação.
2. **Auto-Descoberta de Frota & ORCA Bridge (`aidd_forge/core/detector.py`, `orca_bridge.py`):** Detecta silenciosamente a frota instalada no host e monta o roteamento com fallback em cascata: multi-agente por papel, ou agente único operando em worktrees isoladas sem quebrar.
3. **Phase-Level Agentic Fencing (`aidd_forge/core/phase_fencer.py`):** Provisiona `.aidd/pipeline/` com micro-ambientes isolados (Fases 00 a 04), cada um com `AGENTS.md` cirúrgico (~380 tokens) e MCPs dedicados.
4. **Tríade Caveman Ultra & Context Linter (`aidd_forge/core/token_optimizer.py`, `context_linter.py`):** Economia de até 50% em tokens BPE com entrada em EN, CoT telegráfico interno e saída estrita em PT-BR.
5. **Pacote Canônico de 6 Skills Físicas (`templates/skills/`):** `caveman-ultra`, `orca-orchestration`, `impeccable-ui`, `open-code-review`, `post-mortem` e `cybersecurity-audit` vinculadas em `.agent/skills/`.
6. **7 Quality Gates Determinísticos & Git Hooks (`templates/gates/`, `git_hooks.py`):** Bloqueio de segredos, AST syntax check, contratos Draft 2020-12, suíte real de testes Zero Fail, OWASP Top 10 e performance com bloqueio binário no `pre-commit`.

---

## 🧪 Testes Automatizados

Para rodar a suíte completa de testes (unitários + integração):
```bash
pytest -v
```
*Resultado homologado:* **126 passed, 1 skipped (100% Exit 0)**.

---

## 📄 Licença
Distribuído sob os padrões de engenharia de software industrial do ecossistema AIDD.
