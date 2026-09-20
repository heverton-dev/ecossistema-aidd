# Item 2 — Enforcement real em G_ZERO_HEADLESS

> **Escopo:** Entra: escolher e implementar UMA das duas rotas abaixo para a Regra de Ouro #7 (Zero Subagentes Headless). Não entra: reescrever `orchestrator_engine.py` inteiro ou mexer no protocolo ORCA ADE em geral.
> **Status:** [CONCLUIDO — Executado e Comprovado em Runtime]
> **Rota Executada:** Rota A (Enforcement Real via Hook de Harness + Teste de Reprodução Ativa + Prova de Mordida Lei #13)
> **Evidência de Execução:** `pytest -v gates/test_g_zero_headless.py` (6 passed), `python gates/G_ZERO_HEADLESS.py` (exit 0), `python gates/G_PORTAO_PROVA_QUE_MORDE.py` (27/27 gates aprovados).

---

## Contexto ja investigado

- `gates/G_ZERO_HEADLESS.py` era uma fachada que apenas conferia presença literal de duas strings e imprimia alegação indevida de "zero risco".
- Hook canônico de interceptação criado em `componentes/compartilhado/hooks/anti_headless_subagent_hook.py`, sincronizado universalmente e registrado no assistente (`.claude/settings.json` via `PreToolUse`).
- O gate `G_ZERO_HEADLESS.py` foi reescrito para exercitar o hook em runtime: bloqueia 2 agentes paralelos sem confirmação, bloqueia concorrência com subagente ativo, permite com confirmação explícita e expõe limite conhecido per Lei #8.

## Definicao de Pronto — Resultado

**Rota A — enforcement real (IMPLEMENTADA):**
1. Hook implementado em `componentes/compartilhado/hooks/anti_headless_subagent_hook.py` e configurado no assistente (`.claude/settings.json`).
2. Reprodução real comprovada:
   - Tentativa de disparar 2 subagentes paralelos sem confirmação é barrada com código != 0 e saída `[BLOQUEIO G_ZERO_HEADLESS]`.
   - Tentativa de concorrência ativa com outro subagente em execução é barrada.
   - Caminho legítimo com confirmação explícita (`user_confirmed: true` / `--confirmed`) é aprovado com código 0 e `[PERMITIDO]`.
3. Limite de cobertura explicitamente declarado per Lei #8: processos externos que operam fora das chamadas de ferramentas do repositório/harness não são contidos por hooks locais.
4. Gate `G_ZERO_HEADLESS.py` exercita o hook em tempo de execução e o teste `gates/test_g_zero_headless.py` cumpre estritamente a Lei #13 (provando reprovação exit 1 se o hook falhar ou for desconfigurado).

## Criterio de saida

- Arquivos criados ou alterados no local correto.
- Testes reais passando sem stubs falsos.
- Gates de integridade aprovados.

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item 2: Enforcement real em G_ZERO_HEADLESS.
Siga rigorosamente a Definicao de Pronto acima.
Nao invente aprovacoes e mantenha as regras do monorepo.
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 2: Enforcement real em G_ZERO_HEADLESS.
Strictly follow the Definition of Done above.
Do not fabricate approvals and maintain monorepo governance rules.
```
