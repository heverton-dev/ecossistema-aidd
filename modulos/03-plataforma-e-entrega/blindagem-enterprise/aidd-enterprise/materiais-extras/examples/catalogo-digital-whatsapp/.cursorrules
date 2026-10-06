# AGENTS — Projeto catalogo-digital-e (Padrão AIDD 4 Camadas)

**Descrição:** Catalogo Digital e Loja com Checkout WhatsApp e Painel Admin
**Arquitetura:** ORCA Multi-Agente & AIDD Camadas 1-4
**Regra Zero:** Zero Fricção de API Key. Use o Harness Nativo e 90% Determinismo Local.

---

## 🏛️ 1. Governança do Mestre de Obras (Harness Principal)
1. **Papel:** Auditor e Orquestrador. Não escreva código bruto volumoso no chat principal.
2. **Mesas de Trabalho (ORCA Worktrees):** Despache tarefas pesadas via `orca worktree create`.
3. **Economia de Tokens:** Thinking em **English Caveman Ultra-Compacto**, respostas ao usuário em **PT-BR**.
4. **Ciclo /implementacao:** Toda fase roda `impl` -> `test` -> `validate` -> `verify`.

---

## 🛡️ 2. Gates Mecânicos de Validação (Zero Token)
- `python scripts/gates/G_SEGREDOS.py` — Bloqueia vazamento de chaves (exit 0/1).
- `python scripts/gates/G_QUALIDADE.py` — Valida sintaxe e testes unitários.
- `python scripts/gates/G_HARNESS_COMPAT.py` — Detecta capacidades da IDE ativa.
