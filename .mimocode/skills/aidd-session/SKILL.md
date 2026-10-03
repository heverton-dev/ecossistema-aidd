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

## Negative Guardrails

- NEVER invent or guess a session ID: use the harness-injected ID or the user's argument; `registrar_sessao` rejects an empty ID with exit 1.
- NEVER hand-edit `secoes/historico_sessoes.json` or `secoes/INDICE-SESSOES.md`; `salvar_historico` rewrites the JSON atomically and regenerates the Markdown mirror.
- NEVER delete or reset `secoes/historico_sessoes.json` to fix a load error without the user's OK; it is the only session history.
- NEVER report "recorded" before the `sessao registrar` exit code is read from a file.

## Failure Modes & Fallback

- **No ID visible in the system instructions:** ask the user once for the ID (or the transcript path); never register a placeholder.
- **`Falha ao carregar arquivo de sessões` (corrupt JSON or missing `sessoes` key):** stop, show the error, and ask before restoring the file from git (`git show HEAD:secoes/historico_sessoes.json`).
- **Same ID registered twice:** expected; the script updates the entry and sets `atualizado_em`. Report "updated", not a duplicate.

## Stopping Checklist

- [ ] `python ecossistema.py sessao registrar --id "<ID>" ... > sess.txt 2>&1; echo $? > sess.rc` holds `0`.
- [ ] `python ecossistema.py sessao buscar "<ID>" > busca.txt 2>&1; echo $? > busca.rc` holds `0` and shows the harness and model given.
- [ ] `grep -c "<ID>" secoes/INDICE-SESSOES.md` returns at least 1.
