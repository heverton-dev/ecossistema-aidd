# Item 4 — Eliminar execucao redundante de suite de teste de skills materializadas 7x

> **Escopo:** Entra: parar de rodar a mesma suíte de teste de skill 7 vezes (uma por cópia de harness) quando as 7 cópias já são garantidamente idênticas por outro mecanismo. Não entra: remover as 7 cópias físicas em si (isso é o materializador, fora de escopo — ver item 3); não entra mudar o mecanismo de sync/drift já existente.

> **Status:** [RASCUNHO — Aguardando Aprovação Humana]

---

## Contexto já investigado

- Achado via `code-review-graph` (`get_surprising_connections`) em 2026-09-08: `.agents/skills/planos-auditoria-runner/tests/test_gerenciador_planos.py` (e as cópias idênticas em `.claude/`, `.cursor/`, `.gemini/`, `.mimocode/`, `.opencode/`, `skills/`) chamam de volta o mesmo `scripts/gerenciador_planos.py` — 2.819 conexões desse tipo encontradas no total, a maioria repetição do mesmo padrão para skills diferentes.
- Como as 7 cópias de cada skill já são garantidas idênticas por hash (via `python ecossistema.py components verify`, gate `G_HARNESS_COMPAT`), rodar a suíte de teste 7 vezes não aumenta a cobertura real — testa a mesma lógica repetidamente.
- Precisa de investigação antes de implementar (não assumida aqui): identificar exatamente onde/como a suíte completa de testes é hoje disparada (`python ecossistema.py audit`? `G_TESTES_REAIS.py`? outro comando?) para saber se ela já varre as 7 cópias ou só uma — a solução pode ser tão simples quanto configurar a coleta de teste (`pytest.ini`/`testpaths`) para ignorar as 6 cópias redundantes e rodar só a canônica.

## Definição de Pronto

1. Investigação real (não suposição) de onde a redundância de fato acontece hoje: rodar a suíte completa e medir/contar quantas vezes cada teste de skill executa.
2. Mecanismo ajustado para rodar a suíte de cada skill com teste uma vez só (a partir da cópia canônica), preservando a garantia de que as 7 cópias continuam idênticas (via `G_HARNESS_COMPAT`/`G_COMPONENTE_AGNOSTICO`, que já cobrem isso).
3. Medição real de antes/depois: tempo total de execução da bateria de testes reduzido, sem perda de nenhum teste único (comparar lista de testes coletados antes/depois, não só o tempo).
4. Nenhuma skill sem teste passou a não ser testada por engano.

## Critério de saída

- Redução mensurável e reproduzida do tempo/quantidade de execuções redundantes.
- `python gates/G_TESTES_REAIS.py` (ou equivalente) continua aprovado, mesma cobertura real.
- Nenhum teste único foi perdido (lista de testes coletados comparada antes/depois).

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item 4: Eliminar execucao redundante de suite de teste de skills materializadas 7x.
Siga rigorosamente a Definicao de Pronto acima.
Nao invente aprovacoes e mantenha as regras do monorepo.
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 4: Eliminar execucao redundante de suite de teste de skills materializadas 7x.
Strictly follow the Definition of Done above.
Do not fabricate approvals and maintain monorepo governance rules.
```
