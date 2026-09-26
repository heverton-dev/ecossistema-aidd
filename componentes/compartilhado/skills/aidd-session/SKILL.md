---
name: aidd-session
description: Records the current agent session ID and metadata deterministically in secoes/historico_sessoes.json and secoes/INDICE-SESSOES.md for traceability and context recovery. Use when the user wants to save or see the session ID, or types "/sessao", "/session", "/id", "/id-sessao", "/salvar-id", "salve o id desta sessão", "qual o id desta conversa".
---

# aidd-session

Universal across harnesses (Antigravity, Claude Code, Cursor, Gemini CLI, OpenCode, MiMoCode): the developer never loses the history, transcript or ID of a work session.

## Protocol

1. **Get the conversation ID** injected by the harness in the system instructions (e.g. `Conversation ID: <uuid>`). If the user passed an ID as argument, use it.
2. **Identify basic metadata:**
   - harness: `antigravity`, `claude`, `cursor`, `gemini`, `opencode` or `mimo`;
   - model: the selected language model;
   - title: the session goal in 3 to 7 words.
3. **Run the deterministic script:**
   ```bash
   python ecossistema.py sessao registrar --id "<ID>" --harness "<HARNESS>" --modelo "<MODEL>" --titulo "<SESSION_TITLE>"
   ```
   Done when the command exits 0.
4. **Answer concisely (Rule 10, Law #4):**
   - first line: the session was recorded;
   - short list: session ID (copyable), harness / model, record files `secoes/historico_sessoes.json` and `secoes/INDICE-SESSOES.md`, local transcript path if detected.
