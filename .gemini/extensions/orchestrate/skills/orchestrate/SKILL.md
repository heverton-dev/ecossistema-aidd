---
name: orchestrate
description: Roteador de ambiente e Plano de Voo para execução de planos ORCA — pergunta ORCA (worktrees) ou Subagentes (Agent tool desta sessão) antes de tudo, compila o Plano de Voo em JSON revisável, e só depois executa.
---

# /orchestrate — Roteador de Ambiente e Plano de Voo

Contrato executável universal do slash command /orchestrate [plano].

## Protocolo Interativo do Agente (/orchestrate)

Quando invocado:

1. **Gate de Ambiente (obrigatório, sempre a primeira pergunta).** Pergunte explicitamente ao usuário, nunca assuma:
   - **1) ORCA** — worktrees efêmeras + terminal separado por frente. Isolamento de arquivo real, execução mecânica monitorada pelo desenvolvedor. Use quando frentes tocam os mesmos arquivos ou exigem revisão humana passo a passo.
   - **2) Subagentes** — Agent tool desta própria sessão, sem worktree, sem terminal separado. Contexto compartilhado, **sem isolamento de arquivo**. Avise o usuário desse risco se o plano tiver frentes que tocam os mesmos arquivos.

2. **Compile o Plano de Voo (zero-LLM, mecânico — nunca decida sozinho harness/modelo/subagent_type sem perguntar).**
   - **Se ORCA:** `python ecossistema.py orchestrate <plano> --ambiente worktree --dry-run` — daqui em diante segue o protocolo já existente de `orca-plan-orchestrator` (pergunta harness por frente, gera branch/worktree/comando).
   - **Se Subagentes:** `python ecossistema.py orchestrate <plano> --ambiente subagent --dry-run [--subagent-type <tipo>] [--model <modelo>]` — compila `subagent_type`/`model`/`prompt` por frente. O CLI nunca executa nada aqui: é só compilador mecânico, sem acesso a modelo/Agent tool.

3. **Apresente o Plano de Voo e o caminho do JSON salvo** (`<pasta-do-plano>/.orca-flight-plan.json`). Convide o usuário a abrir e editar (harness, modelo, subagent_type ou prompt) antes de confirmar. Nunca prossiga sem dar essa chance de revisão.

4. **Peça confirmação explícita** de que o Plano de Voo (editado ou não) está aprovado. Nunca fabrique aprovação.

5. **Execução:**
   - **ORCA:** rode `python ecossistema.py orchestrate <plano> --ambiente worktree --harness ... --yes [--resume]`. ⛔ **Proibição total de subagentes/background tasks continua valendo nesta via** (regra de `orca-plan-orchestrator/SKILL.md`) — o assistente não interfere na execução, só monitora o terminal que o próprio motor abre.
   - **Subagentes:** releia `.orca-flight-plan.json` (possivelmente editado pelo usuário) e, para CADA frente em ordem, chame a tool Agent com `subagent_type`/`model`/`prompt` exatamente como gravado no JSON. Nunca invente aprovação intermediária — se uma frente falhar ou o subagente reportar bloqueio, pare e informe o usuário antes de seguir pra próxima frente. Não há isolamento de arquivo neste modo.

## Quando NÃO usar esta skill

- Execução real do motor de worktrees (branch/merge/gates/circuit breaker) já em andamento → isso é `orca-plan-orchestrator`, não esta.
- Gerar a estrutura do plano em si (`00-PROCESSO-E-DECISOES.md` + `NN-*.md`) → isso é `planos-auditoria-runner`.
