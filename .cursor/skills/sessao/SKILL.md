---
name: sessao
description: Registra deterministicamente o ID e metadados da sessão agêntica atual em secoes/historico_sessoes.json e secoes/INDICE-SESSOES.md.
commands:
  - "/sessao"
  - "/session"
  - "/id"
---

# Sessão — Gravador Determinístico de ID da Conversa

Atalho direto da skill canônica `aidd-sessao`.
Quando acionado, o agente executa:
```bash
python ecossistema.py sessao registrar --id "<CONVERSATION_ID>" --harness "<HARNESS>" --modelo "<MODELO>" --titulo "<TITULO>"
```
e retorna o ID da sessão e os caminhos para os logs e índice permanente.
