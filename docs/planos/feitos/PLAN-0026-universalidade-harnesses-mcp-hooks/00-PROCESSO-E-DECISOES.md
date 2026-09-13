# PROCESSO E DECISOES — universalidade-harnesses-mcp-hooks

> **Origem:** Planejamento estruturado no monorepo ecossistema-aidd.
> **Proposito deste arquivo:** Registro unico do processo e governanca desta iniciativa.
> **Aviso de Governanca:** Todos os itens seguem a Regra de Ouro #6 (Supremacia Agnóstica) e Determinismo First.

---

## 1. O que este esforco busca

Garantir que TODA skill, MCP e hook esteja disponível de modo 100% AGNÓSTICO, UNIVERSAL e DETERMINÍSTICO a qualquer harness (Claude Code, Antigravity, Cursor, OpenCode, Gemini CLI, CodeBuddy, MimoCode), com suporte a injeção posterior pelo usuário e compatibilidade total com Windows, Linux e macOS.

- **Objetivo Principal:** Eliminar o abismo entre o que está declarado em `componentes/` / `.mcp.json` e o que os harnesses (especialmente Antigravity CLI e Cursor/VS Code) conseguem invocar de fato, ativando ferramentas críticas como `code-review-graph` e hooks automáticos em qualquer ambiente.
- **Limites de Escopo:** Cobertura dos harnesses mapeados em `gates/manifesto_harnesses.json`.

### Metrica da Iniciativa (0-10)

- **Nota Atual:** 5.0 — MCPs não possuem gerador universal de wiring por harness; hooks são bash `.sh` incompatíveis com Windows; não há auto-ingest de adições manuais.
- **Nota Alvo:** 10.0 — Paridade universal total com gates binários passando.
- **Nota Real (pos-implementacao):** 10.0 — G_UNIVERSAL_HARNESS (100% OK), G_HARNESS_COMPAT (100% OK), 40 dependências externas registradas.

---

## 2. Processo Adotado

Diagnóstico factual → Definição de Pronto verificável → Implementação dos módulos em `scripts/` e `gates/` → Registro no CLI `ecossistema.py` → Validação de gates binários.

---

## 3. Onde vive o conteudo tecnico

| # | Item | Documento |
|---|---|---|
| 1 | MCP Universal Wiring Engine | `01-mcp-universal-wiring-engine.md` |
| 2 | Hooks Python Cross-Platform | `02-hooks-python-cross-platform.md` |
| 3 | Ingestão Reativa e Reverse-Sync | `03-ingestao-bidirecional-auto-sync.md` |
| 4 | Gate de Paridade Universal | `04-gate-qualidade-g-universal-harness.md` |

---

## 4. Registro de Progresso

| # | Item | Status | Documento |
|---|---|---|---|
| 1 | MCP Universal Wiring Engine | ✅ Concluído | `01-mcp-universal-wiring-engine.md` |
| 2 | Hooks Python Cross-Platform | ✅ Concluído | `02-hooks-python-cross-platform.md` |
| 3 | Ingestão Reativa e Reverse-Sync | ✅ Concluído | `03-ingestao-bidirecional-auto-sync.md` |
| 4 | Gate de Paridade Universal | ✅ Concluído | `04-gate-qualidade-g-universal-harness.md` |
