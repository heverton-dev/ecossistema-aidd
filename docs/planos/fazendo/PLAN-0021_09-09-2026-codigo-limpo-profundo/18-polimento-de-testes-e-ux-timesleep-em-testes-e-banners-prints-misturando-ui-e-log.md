# Item 18 — Polimento de testes e UX: time.sleep em testes e banners-prints misturando UI e log

> **Escopo:** 2 achados de polimento de baixo risco: pausas fixas (`time.sleep`) em testes que fazem polling de servidor, e banners/prints decorativos misturados com mensagens de log real nas CLIs. Cobre generator, master, enterprise e ops (testes) e ecossistema.py/aidd.py/compose_suite.py/pipeline_ops.py (prints).
> **Status:** [RASCUNHO — Aguardando Aprovacao Humana]

---

## Contexto ja investigado

Fonte: relatório de auditoria, achados #25 e #29.

- **`time.sleep` em 22 pontos** dentro de `tools/*/tests/` (confirmado por `grep -rn time.sleep`), principalmente em funções de polling tipo `_aguardar_servidor` — o relatório classifica isso como I/O real (aceitável, não é mock), mas nota que uma espera condicional (poll com timeout curto, checando a condição real em vez de dormir um tempo fixo) reduziria tempo de execução da suíte e a chance de teste "flaky" (passar/falhar de forma inconsistente por causa de timing).
- **Banner ASCII e `"=" * 80` repetidos** em centenas de `print()` nos fluxos de CLI de `ecossistema.py`, `aidd.py`, `compose_suite.py`, `pipeline_ops.py` — master/enterprise têm **460+ chamadas `print()` cada**. O problema apontado não é estético: misturar UI decorativa com mensagem de log real no mesmo canal (stdout) torna impossível redirecionar/filtrar um sem o outro (ex.: capturar só as mensagens de erro reais para um sistema de log, sem also capturar banners).

## Definicao de Pronto

1. Os 22 pontos de `time.sleep` em testes de polling são substituídos por espera condicional com timeout (poll curto e repetido checando a condição real, com timeout máximo definido) — reduzindo tempo de execução da suíte sem introduzir flakiness nova.
2. Prints de banner/decoração são diferenciados de mensagens de log real (ex.: canal/prefixo diferente, ou uso de um logger estruturado para mensagens reais, mantendo `print()` só para UI decorativa) — não é necessário eliminar os banners, apenas torná-los distinguíveis programaticamente de mensagens de log.
3. Testes reais das 4 ferramentas afetadas continuam passando com exit 0, e o tempo total de execução da suíte de testes é medido antes/depois para confirmar que a mudança de `time.sleep` para poll condicional realmente reduziu o tempo (não é suposição, é medição).

## Criterio de saida

- `time.sleep` fixo substituído por poll condicional nos 22 pontos.
- Log real distinguível de banner decorativo nas CLIs afetadas.
- Testes reais passando, tempo de suíte medido antes/depois.

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item 18: substituir time.sleep fixo por poll condicional em 22 pontos
de teste, e diferenciar banners/prints decorativos de mensagens de log real nas CLIs (ver
docs/relatorios/relatorio-auditoria-codigo-limpo-ecossistema-aidd.html, achados #25 e #29).

Fatos que voce precisa saber antes de comecar:
- 22 ocorrencias de time.sleep em tools/*/tests (grep -rn time.sleep), principalmente em
  funcoes tipo _aguardar_servidor fazendo polling de servidor real (I/O real, aceitavel -
  o problema e o tempo fixo, nao o polling em si).
- master/enterprise tem 460+ chamadas print() cada, misturando banners ASCII decorativos com
  mensagens de log real no mesmo canal (stdout) - dificulta filtrar um do outro.

Regras obrigatorias:
1. Ao trocar time.sleep por poll condicional, meca o tempo total da suite ANTES e DEPOIS da
   mudanca - a Definicao de Pronto exige essa medicao real, nao estimativa.
2. Nao elimine os banners decorativos por completo se isso nao for pedido - o objetivo e
   torna-los distinguiveis de log real, nao remover a UI da CLI.
3. Siga rigorosamente a Definicao de Pronto acima.
4. Nao invente aprovacoes. So marque como concluido apos rodar os testes reais e apresentar
   a medicao de tempo antes/depois.
5. Mantenha as regras de governanca do monorepo (AGENTS.md).
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 18: replace fixed time.sleep with conditional polling in 22
test spots, and differentiate decorative banners/prints from real log messages in the CLIs
(see docs/relatorios/relatorio-auditoria-codigo-limpo-ecossistema-aidd.html, findings #25
and #29).

Facts you need before starting:
- 22 occurrences of time.sleep in tools/*/tests (grep -rn time.sleep), mostly in functions
  like _aguardar_servidor doing real server polling (real I/O, acceptable - the problem is
  the fixed sleep time, not the polling itself).
- master/enterprise each have 460+ print() calls, mixing decorative ASCII banners with real
  log messages on the same channel (stdout) - makes it hard to filter one from the other.

Mandatory rules:
1. When replacing time.sleep with conditional polling, measure the total suite time BEFORE
   and AFTER the change - the Definition of Done requires this real measurement, not an
   estimate.
2. Do not eliminate the decorative banners entirely unless asked - the goal is to make them
   distinguishable from real logs, not to remove the CLI's UI.
3. Strictly follow the Definition of Done above.
4. Do not fabricate approvals. Only mark this done after running the real tests and
   presenting the before/after time measurement.
5. Maintain monorepo governance rules (AGENTS.md).
```
