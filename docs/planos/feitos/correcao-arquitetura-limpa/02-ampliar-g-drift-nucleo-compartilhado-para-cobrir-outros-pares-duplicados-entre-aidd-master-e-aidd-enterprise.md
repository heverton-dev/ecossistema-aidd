# Item 2 — Ampliar G_DRIFT_NUCLEO_COMPARTILHADO para cobrir outros pares duplicados entre aidd-master e aidd-enterprise

> **Escopo:** Entra: registrar no baseline (`gates/baseline_nucleo_compartilhado.json`) os pares de arquivo idênticos entre `aidd-master`/`aidd-enterprise` já identificados no grafo, para que `G_DRIFT_NUCLEO_COMPARTILHADO.py` passe a monitorá-los. Não entra: consolidar fisicamente esses arquivos numa fonte só (isso violaria a Regra Fixa #5 do `00-PROCESSO-E-DECISOES.md` — sem acoplamento de runtime entre ferramentas); não entra ampliar o gate para vigiar `templates/core` vs `templates/v2` de uma mesma ferramenta (par diferente, fora deste achado).

> **Status:** ✅ Concluído (auditado por reproducao real em 2026-09-08)

---

## Contexto já investigado

- `gates/G_DRIFT_NUCLEO_COMPARTILHADO.py` hoje só compara `tools/aidd-master/src/core/` vs `tools/aidd-enterprise/src/core/` (ver `DIR_A`/`DIR_B` no próprio script) — arquivos fora dessas duas pastas nunca entram na comparação, mesmo sendo idênticos.
- Achado via `code-review-graph` (`get_hub_nodes`, valores de `total_degree` idênticos entre pares) em 2026-09-08: os seguintes pares são idênticos hoje e **não estão cobertos** pelo gate atual porque vivem fora de `src/core/`:
  - `tools/{aidd-master,aidd-enterprise}/scripts/compose_suite.py`
  - `tools/{aidd-master,aidd-enterprise}/scripts/gates/G_SEGURANCA.py` (`SecurityGate.run_all_checks`)
  - `tools/{aidd-master,aidd-enterprise}/templates/core/openapi.py` e `templates/v2/openapi.py` (além de `src/core/openapi.py`, que já pode estar coberto — confirmar)
  - `tools/{aidd-master,aidd-enterprise}/templates/core/webhooks.py` e `templates/v2/webhooks.py`
  - `tools/{aidd-master,aidd-enterprise}/templates/core/mcp_server.py` (e `src/core/mcp_server.py`, se aplicável)
- Nota de sequenciamento: se o item 1 deste plano (extrair HTML) for executado primeiro, o conteúdo de `openapi.py`/`webhooks.py` muda — rodar `--atualizar-baseline` depois da mudança, não antes, para o baseline refletir o estado final.

## Definição de Pronto

1. Todos os pares confirmados como idênticos na investigação (`diff` real entre os arquivos, não suposição) adicionados a `gates/baseline_nucleo_compartilhado.json` via `python gates/G_DRIFT_NUCLEO_COMPARTILHADO.py --atualizar-baseline`.
2. Cada entrada nova no baseline documentada (`esperado_identico: true`, já é o comportamento do comando).
3. Pares que existem mas **não** são idênticos hoje (se algum for encontrado) registrados com `esperado_identico: false` e motivo real documentado — nunca mascarados como iguais.
4. `python gates/G_DRIFT_NUCLEO_COMPARTILHADO.py` (sem flag) aprovado após a atualização.
5. Escopo do gate (`DIR_A`/`DIR_B` no script) avaliado: se fizer sentido, estender para comparar também `scripts/` e `templates/` das duas ferramentas, não só `src/core/` — decisão técnica de quem implementar, documentada no commit.

## Critério de saída

- `gates/baseline_nucleo_compartilhado.json` atualizado e commitado.
- `python gates/G_DRIFT_NUCLEO_COMPARTILHADO.py` aprovado (100% OK) de verdade, reproduzido.
- Nenhum par foi marcado como idêntico sem checagem real (`diff`/hash comparado, não assumido pelo grafo).

## Execução (2026-09-08)

- **Correção sobre o "Contexto já investigado":** `scripts/compose_suite.py` NÃO é idêntico hoje — o grafo (`total_degree` igual) sugeriu isso, mas o `diff` real mostrou 2 divergências reais (constante `WEBHOOK_DEMO_URL` por projeto + comentário extra em aidd-master sobre dependências incondicionais). Registrado no baseline como `esperado_identico: false` com o motivo real, não mascarado como igual. `scripts/gates/G_SEGURANCA.py`, por outro lado, foi confirmado idêntico por hash real.
- **Decisão de escopo (DoD item 5, delegada):** `DIR_A`/`DIR_B` do gate foram substituídos por uma lista `PARES` de diretórios comparados independentemente: `src/core` (já existia), `scripts`, `scripts/gates`, `templates/core` e `templates/v2`. Cada par é catalogado sob sua própria chave no baseline para não colidir nomes repetidos entre pares (ex.: `openapi.py` existe em 3 pares com veredito diferente em cada um). `templates/core` vs `templates/v2` da mesma ferramenta continua fora de escopo (par diferente, conforme já dito acima).
- **Achados reais na varredura de `scripts/` e `scripts/gates/`** (auto-descobertos ao ampliar o par, não estavam no "Contexto já investigado" original): 5 arquivos adicionais divergentes com motivo real documentado — `add_module.py`, `aidd.py` (divergência grande: pipeline do Injetor Universal integrado na CLI só em aidd-master), `openapi_to_ts.py`, `provision_project.py`, `run_all.py` — e `scripts/gates/G_INJECT.py` (conjunto de checagens diferente por design). `autofix.py`, `scaffold_infra.py` e `test_live.py` em `scripts/`, e as demais 10 gates em `scripts/gates/`, confirmados idênticos por hash.
- **`templates/core` e `templates/v2`:** todos os `.py` comuns (18 e 17 arquivos respectivamente, incluindo `openapi.py`, `webhooks.py` e `mcp_server.py`) confirmados idênticos por hash real — nenhuma divergência encontrada nesses dois pares.
- **Nenhum par foi marcado como idêntico por suposição do grafo** — todo veredito veio de `_hash()` (SHA-256) rodado pelo próprio gate via `--atualizar-baseline`; os textos de `motivo` para os pares divergentes foram escritos após inspeção real do `diff`, substituindo o placeholder `"REVISAR: ..."` que o comando gera automaticamente (o campo `esperado_identico` em si nunca foi editado à mão).
- **Veredito final reproduzido:** `python gates/G_DRIFT_NUCLEO_COMPARTILHADO.py` → 100% OK, exit 0 (84 arquivos catalogados em 5 pares).
- Teste unitário `tools/aidd-master/tests/unit/test_drift_gate_blind_spot.py` adaptado para a nova API (`_checar_par` por par, em vez de monkeypatch de `DIR_A`/`DIR_B` globais) — 5/5 passando.

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item 2: Ampliar G_DRIFT_NUCLEO_COMPARTILHADO para cobrir outros pares duplicados entre aidd-master e aidd-enterprise.
Siga rigorosamente a Definicao de Pronto acima.
Nao invente aprovacoes e mantenha as regras do monorepo.
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 2: Ampliar G_DRIFT_NUCLEO_COMPARTILHADO para cobrir outros pares duplicados entre aidd-master e aidd-enterprise.
Strictly follow the Definition of Done above.
Do not fabricate approvals and maintain monorepo governance rules.
```
