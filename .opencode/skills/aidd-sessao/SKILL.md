---
name: aidd-sessao
description: Registra deterministicamente o ID e metadados da sessão agêntica atual em secoes/historico_sessoes.json e secoes/INDICE-SESSOES.md para rastreabilidade e recuperação de contexto.
commands:
  - "/sessao"
  - "/session"
  - "/id"
---

# AIDD-Sessao — Gravador Determinístico de ID e Sessão Agêntica

Esta skill é universal e agnóstica a qualquer harness (Antigravity, Claude Code, Cursor, Gemini CLI, OpenCode, MiMoCode).
Garante que o desenvolvedor nunca perca o histórico, transcript ou ID da sessão de trabalho.

## 1. Gatilhos de Ativação

A skill é acionada quando o usuário digitar:
- `/sessao` ou `/session`
- `/id-sessao` ou `/id`
- `/salvar-id` ou `/registrar-sessao`
- Ou linguagem natural: "salve o id desta sessão", "registre o id atual", "qual o id desta conversa".

## 2. Invariantes de Execução (Leis #1, #3, #6)

Ao ser acionada, o agente deve seguir estritamente o protocolo:

1. **Obter o Conversation ID:**
   - Extrair o `Conversation ID` injetado pelo harness nas instruções de sistema (ex: `Conversation ID: <uuid>`).
   - Se o usuário forneceu um ID específico como argumento, usar o ID fornecido.

2. **Identificar Metadados Básicos:**
   - **Harness:** Detectar o ambiente em execução (`antigravity`, `claude`, `cursor`, `gemini`, `opencode`, `mimo`).
   - **Modelo:** Identificar o modelo de linguagem selecionado (ex: `gemini-3.8-flash`, `claude-3-7-sonnet`, `gpt-4o`).
   - **Título / Objetivo:** Sintetizar em 3 a 7 palavras o objetivo central da sessão atual.

3. **Disparar o Script Determinístico via CLI:**
   Executar diretamente via terminal / runner:
   ```bash
   python ecossistema.py sessao registrar --id "<ID>" --harness "<HARNESS>" --modelo "<MODELO>" --titulo "<TITULO_DA_SESSAO>"
   ```

4. **Retorno ao Usuário (Rule 10 & Lei #4):**
   Responder de forma concisa e direta:
   - 1ª linha: Informar que a sessão foi registrada com sucesso.
   - Lista curta com:
     - **ID da Sessão:** Código copiável.
     - **Harness / Modelo:** Ambiente ativo.
     - **Arquivo de Registro:** `secoes/historico_sessoes.json` e `secoes/INDICE-SESSOES.md`.
     - **Transcript Local:** Caminho do arquivo de logs no disco (se detectado).
