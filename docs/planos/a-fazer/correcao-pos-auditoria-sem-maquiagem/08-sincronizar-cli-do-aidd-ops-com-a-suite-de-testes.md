# Item 8 — Sincronizar CLI do aidd-ops com a suite de testes

> **Escopo:** Entra: `tools/aidd-ops/tests/test_pipeline_ops.py` — atualizar os 8 testes que ainda chamam a interface antiga (texto livre sem subcomando) para usar `plan "<nicho>"` etc., como o CLI real (`scripts/pipeline_ops.py`) já exige. Não entra: mudar a lógica de sizing/intake.
> **Status:** [RASCUNHO — Aguardando Aprovacao Humana]
> **Modelo sugerido:** Claude Sonnet · Antigravity Gemini 3.7 · MiMo mimo-v2.5-pro (atualizar chamadas de teste preservando a intenção de cada caso)

---

## Contexto ja investigado

- Confirmado por fork de auditoria: `pytest -q` em tools/aidd-ops dá 48 passed, 8 failed. Causa: `scripts/pipeline_ops.py` foi refatorado para subcomandos obrigatórios (`plan`/`bootstrap`/`preflight`/`deploy`, `cmd_plan` linha 362), mas os 8 testes (5 de nicho — clínicas, delivery, farmácias, b2b, energia solar — mais 2 de ambiguidade/erro e 1 gate isolado) ainda invocam `pipeline_ops.py "<texto>" --pasta X` sem subcomando, e o argparse rejeita com exit 2 ("invalid choice").
- README/AGENTS.md já descrevem o fluxo real como `/ops plan "<nicho>"` — só os testes ficaram para trás.

## Definicao de Pronto

1. `python -m pytest -q tools/aidd-ops` retorna exit 0, 0 failed.
2. Os 8 testes corrigidos continuam testando o mesmo comportamento de negócio (classificação de nicho, ambiguidade `NICHO_AMBIGUO`, erro `NICHO_NAO_RECONHECIDO`) — não viram skip/xfail para "passar".
3. `python ecossistema.py ops plan "<nicho>"` reproduzido manualmente pelo menos uma vez, confirmando que o fluxo do README funciona de ponta a ponta hoje.

## Criterio de saida

- Arquivos criados ou alterados no local correto.
- Testes reais passando sem stubs falsos.
- Gates de integridade aprovados.

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item 8: Sincronizar CLI do aidd-ops com a suite de testes.
Siga rigorosamente a Definicao de Pronto acima.
Nao invente aprovacoes e mantenha as regras do monorepo.
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 8: Sincronizar CLI do aidd-ops com a suite de testes.
Strictly follow the Definition of Done above.
Do not fabricate approvals and maintain monorepo governance rules.
```
