# Workspace Guidelines & ORCA ADE Orchestration Rules

## 1. Internal Reasoning / Thinking (English Caveman)
- Always execute internal reasoning (`thinking` / CoT) in **ENGLISH CAVEMAN style**.
- Telegraphic, concise phrases. No unnecessary filler words, articles, or polite prose.
- Shorten: "verify" -> "check", "necessary" -> "req", "implement" -> "impl".
- Max 3-5 lines for simple tasks. Ultra-dense logic.

## 2. User Responses (PT-BR)
- Always deliver user-facing outputs and explanations in **Portuguese (PT-BR)**.
- Keep responses objective, structured, and concise.
- Prefer tables, bullet points, and actionable steps over long paragraphs.
- Do not repeat file contents or diffs already visible in tool execution.

## 3. Project Context & Clean Architecture
- Enterprise Modular Suite with Vertical Slices (`src/modules/<domain>/`), EventBus pub/sub, SQLite WAL concurrency, OpenAPI 3.1 Live Swagger Studio (`/docs`), Native MCP Server (`/mcp`), and Impeccable Super-App UI.

---

## 🏆 AS 4 REGRAS DE OURO DA ENGENHARIA AGÊNTICA COM ORCA ADE

| Regra de Ouro | Como Aplicar | Por que evita estourar o limite |
| :--- | :--- | :--- |
| **1. Não use o chat principal como terminal** | Deixe compilação, testes (`pytest`) e tarefas mecânicas rodando via Python local. | Economiza 90% do seu consumo semanal. |
| **2. Use Worktrees do ORCA para frentes grandes** | Cada tarefa separada em sua mesa limpa (`orca worktree create --parent-worktree active`). | Evita que o contexto principal acumule 100k+ tokens desnecessários. |
| **3. Reinicie sessões usando o Plano JSON** | Ao começar um novo dia ou módulo, abra uma sessão nova apontando para o `PLANO-EXECUCAO-ESTRUTURADO.json`. | O agente retoma o estado exato consumindo apenas ~500 tokens em vez de 80.000 tokens do histórico. |
| **4. Governança Rígida por Gates Mecânicos** | A entrega só é aceita se todos os gates (`G_ESTRUTURA`, `G_TESTES`, `G_CONTRACTS`, `G_QUALIDADE`, `G_SEGREDOS`, `G_HARNESS_COMPAT`) retornarem exit 0. | Elimina alucinações e entregas incompletas na raiz. |
