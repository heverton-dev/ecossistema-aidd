# Bateria 5 — AIDD Generator (`tools/aidd-generator`)

> **Escopo:** provar que o pipeline completo de 8 fases (`scripts/pipeline_completo.py`) funciona de ponta a ponta, incluindo o **Protocolo Delegado** (fases 2, 3 e 8), produzindo uma aplicação real, com testes reais passando.
> ⚠️ **Esta é a única bateria com uma restrição real de custo/mecanismo que exige uma decisão explícita antes de rodar** — leia a seção "Modo de execução: Delegado vs. Headless" com atenção antes de rodar qualquer coisa.

---

## Contexto já investigado

- Entrada real: `python scripts/pipeline_completo.py "<ideia>" --pasta <destino> [--interativo] [--implementar-codigo]` (cwd `tools/aidd-generator`, `PYTHONPATH=tools/aidd-generator`) — equivalente via `python ecossistema.py generate "<ideia>" --pasta <destino> ...`.
- **8 fases:** `01_pesquisador` (pesquisa real GitHub/HuggingFace, sem LLM), `02_analisador` (análise via LLM delegado/headless), `03_designer` (5 subagentes em paralelo via LLM), `04_decisor` (config, heurístico ou `--interativo`), `05_criador` (cria projeto real, `git init`+commit, SQLite), `06_documentador` (gera docs), `07_analisador` (auto-crítica determinística, ZERO LLM), `08_implementador` (opcional, só com `--implementar-codigo` — gera código real + roda pytest real por script).
- **Gates:** `scripts/verificar_gates.py <pasta>` roda em sequência: Segredos, `G_VERIFICAR_LLM_PRONTO`, `G_HARNESS_COMPAT`, `G_INTEGRACAO_CROSS_SCRIPT` (I3), `G_CYBERSECURITY_OWASP` — exit 0 só se todos passarem.

### Modo de execução: Delegado vs. Headless — decisão obrigatória antes de rodar

O pipeline precisa de "inteligência" real nas fases 2, 3 e 8. Existem 2 modos reais, mutuamente exclusivos:

1. **Modo Delegado (recomendado, custo zero de API):** as fases 2/3/8 escrevem um pedido em `tools/aidd-generator/scripts/.aidd/cache/_llm_request_{id}.json` e esperam (timeout de 30s por padrão, configurável) uma resposta em `_llm_response_{id}.json` na mesma pasta. **O próprio agente executor desta bateria** (você, rodando esta tarefa) é quem responde de verdade, em tempo real, lendo cada pedido e escrevendo uma resposta genuína — isso não é gambiarra, é o design real do produto ("Zero API Key" quando uma ADE está ativa). Fases identificadas pelo campo `"fase"`: fase 2 é `phase_02` (confirme o valor exato lendo o código), fase 3 tem 5 valores distintos (`phase_03_subagent_especialista_tokens`, `_arquiteto_ferramentas`, `_arquiteto_camadas`, `_engenheiro_scripts`, `_especialista_gates`), fase 8 tem `phase_08` (script principal — grep o campo `"prompt"` por `"SCRIPT: {nome}"` pra saber qual script) mais `phase_08_schema`, `phase_08_integracao`, `phase_08_fix`, `phase_08_autocura`. A resposta mínima válida é `{"conteudo": "...", "tokens_consumidos": <int>}` — mas o `"conteudo"` de cada fase precisa ser um JSON válido com os campos que aquela fase espera (ex.: fase 8 precisa de `{"codigo":..., "teste":..., "caminho_relativo":..., "caminho_teste":...}`) — **uma resposta fake/stub genérica destrava o mecanismo mas quebra o pytest real que a fase 8 roda em seguida**; a resposta precisa ser conteúdo real e funcional, escrito por você de verdade.
2. **Modo Headless (só com aprovação explícita do usuário, custo real):** se `LLM_MODEL` + uma chave de API real (`GROQ_API_KEY`, `OPENAI_API_KEY`, `NVIDIA_NIM_API_KEY`, `OPENROUTER_API_KEY` ou `TOGETHERAI_API_KEY`) estiverem configuradas como variável de ambiente, o pipeline chama `litellm.completion()` de verdade, sem precisar de um agente ativo — mas isso **gasta dinheiro real da conta do usuário a cada chamada**, e há muitas chamadas neste pipeline (fase 2, 5 chamadas paralelas na fase 3, e potencialmente várias na fase 8). **Não use este modo por conta própria** — só se o usuário explicitamente disser que quer usar (e já tiver a chave configurada).

**Default desta bateria: Modo Delegado.** Não gaste chamada real de API sem que o usuário tenha pedido explicitamente.

- Referência de sucesso já alcançada antes (fora do escopo desta bateria, mas prova que o mecanismo funciona de ponta a ponta): uma validação anterior gerou uma API REST de lista de tarefas completa, 8 fases, score de auto-crítica final 91-100, 10/10 testes passando, servidor subindo e respondendo aos 4 verbos REST via curl. Use uma ideia de escopo **igualmente pequeno** (ex.: uma REST API mínima de lista de tarefas, 2-3 endpoints) para manter o volume de respostas delegadas gerenciável.
- Não existe hoje nenhum teste automatizado que exercite o protocolo delegado com arquivos reais em disco (os testes existentes em `tools/aidd-generator/tests/` fazem monkeypatch da função que espera a resposta, pulando o I/O real) — você vai escrever esse harness pela primeira vez.

## Definição de Pronto

5.1. Escrever 2 scripts de apoio (harness, não um teste 100% automatizado sem intervenção — esta bateria é inerentemente ativa, exige você mesmo respondendo em tempo real):
   - Um script "sentinela" que lista pedidos pendentes (`_llm_request_*.json` sem `_llm_response_*.json` correspondente) na pasta de cache, imprimindo `id`, `fase` e `prompt` de cada um — para você chamar repetidamente enquanto o pipeline roda em background.
   - Um script "responder" que recebe um `id` e um conteúdo de resposta (JSON) e escreve `_llm_response_{id}.json` corretamente.
5.2. Rodar o pipeline completo em background com uma ideia pequena e real (ex.: `"REST API de lista de tarefas com criar, listar, concluir e remover"`) `--pasta <tmp>/todo-api --implementar-codigo`.
5.3. Responder, de verdade e com conteúdo genuíno (não fake), a CADA pedido das fases 2, 3 e 8 até o pipeline terminar (exit code real do processo do pipeline).
5.4. Confirmar que as fases 1, 4, 5, 6, 7 completaram sem erro (fase 7 é determinística/zero-LLM — deve sempre funcionar; se falhar, é um bug real a reportar, não um problema de resposta delegada).
5.5. Confirmar projeto real gerado em `<tmp>/todo-api`: estrutura de pastas, `git log` mostrando commit real, `estoque_projeto.db`/`estado_projeto.db` (SQLite) existindo.
5.6. Se `--implementar-codigo` completou: confirmar que os testes gerados por `08_implementador` realmente passam (`pytest` real dentro do projeto gerado, não just conferir que os arquivos existem).
5.7. `python scripts/verificar_gates.py <tmp>/todo-api` → exit 0 (Segredos, `G_VERIFICAR_LLM_PRONTO`, `G_HARNESS_COMPAT`, I3, OWASP).
5.8. Capturar o score de auto-crítica real gerado pela fase 7.
5.9. Suíte `pytest` completa de `tools/aidd-generator` (`python -m pytest tests/ -q`, cwd `tools/aidd-generator`) → exit 0, capturar contagem real.

## Critério de saída

- Pipeline completou as 8 fases com exit code real do processo (não só "os arquivos parecem existir").
- Pelo menos 1 exemplo real e completo de cada tipo de pedido delegado (fase 2, um dos 5 de fase 3, e pelo menos 1 de fase 8) documentado no relatório com o conteúdo REAL da pergunta e da resposta dada.
- Se o modo delegado se mostrar inviável dentro do tempo/orçamento razoável da sessão (ex.: `--implementar-codigo` gera volume grande demais de pedidos), é aceitável reportar **PASSOU COM RESSALVAS**: fases 1-7 completas e provadas (sem `--implementar-codigo`), fase 8 documentada como "não exercitada nesta rodada por volume, mecanismo de fases 2/3 já provado real" — nunca fabricar uma prova de fase 8 que não rodou de verdade.
- Nenhum arquivo de cache (`_llm_request_*`/`_llm_response_*`) órfão deixado em `tools/aidd-generator/scripts/.aidd/cache/` do repositório real ao final — são artefatos internos da própria ferramenta, mas confirme via `git status` que nada disso é rastreado/commitado por engano.

## Prompt de Execução

> Copie o bloco abaixo integralmente para o agente executor. Autocontido. **Antes de rodar, o executor precisa decidir Modo Delegado (default, recomendado) vs. Headless (só se o usuário pedir explicitamente e já tiver uma chave de API configurada) — releia a seção do documento fonte sobre isso.**

```
Você vai provar que o pipeline completo de 8 fases do AIDD Generator
(tools/aidd-generator/scripts/pipeline_completo.py) funciona de ponta a
ponta, no monorepo ecossistema-aidd (raiz em
C:\Users\trcnologia\Desktop\ecossistema-aidd). Esta tarefa é diferente
das outras baterias de teste: ela exige que VOCÊ MESMO atue como o
"LLM delegado" do pipeline em tempo real (Modo Delegado, custo zero de
API) — não é um script que roda sozinho até o fim. Valide tudo de
verdade: exit codes reais, testes gerados rodando de verdade, nunca
simulado ou fabricado.

DECISÃO OBRIGATÓRIA ANTES DE COMEÇAR: use o MODO DELEGADO por padrão.
NÃO configure LLM_MODEL nem nenhuma chave de API real (GROQ_API_KEY,
OPENAI_API_KEY, NVIDIA_NIM_API_KEY, OPENROUTER_API_KEY,
TOGETHERAI_API_KEY) para rodar em modo headless — isso gastaria dinheiro
real da conta do usuário a cada chamada de LLM, e este pipeline faz
muitas chamadas (fase 2, 5 chamadas paralelas na fase 3, várias na fase
8). Só use modo headless se o usuário que te acionou tiver pedido
EXPLICITAMENTE por esse modo E já tiver a chave configurada — nesse
caso, o pipeline roda praticamente sozinho (sem você precisar responder
nada), mas o custo é real.

CONTEXTO JÁ INVESTIGADO (confirme lendo o código antes de agir —
releia especialmente phases/utils_delegacao.py inteiro antes de
escrever qualquer coisa em disco):
- Entrada: `python scripts/pipeline_completo.py "<ideia>" --pasta
  <destino> --implementar-codigo` (cwd tools/aidd-generator, PYTHONPATH
  igual). Rode em BACKGROUND (você precisa continuar interagindo
  enquanto ele espera respostas).
- Pasta de cache do protocolo delegado:
  tools/aidd-generator/scripts/.aidd/cache/ — pedidos chegam como
  `_llm_request_{id}.json` (campos: id, fase, timestamp, modelo_sugerido,
  contexto, prompt), respostas esperadas como `_llm_response_{id}.json`
  (mínimo: {"conteudo": "...", "tokens_consumidos": <int>,
  "modelo_usado": "..."}). Timeout default 30s por pedido — responda
  rápido depois de detectar um pedido novo.
- Campo "fase" identifica de onde veio o pedido: fase 2 é algo como
  "phase_02" (confirme o valor exato no código de 02_analisador.py);
  fase 3 tem 5 valores distintos, um por subagente (grep
  "phase_03_subagent" em phases/03_designer.py); fase 8 usa "phase_08"
  para os pedidos principais de script (leia o campo "prompt" procurando
  "SCRIPT: {nome}" pra saber qual script está sendo pedido) mais
  "phase_08_schema", "phase_08_integracao", "phase_08_fix",
  "phase_08_autocura" para sub-passos.
- O "conteudo" de cada resposta precisa ser JSON válido com os campos
  que aquela fase espera especificamente — leia o parser de cada fase
  (02_analisador.py, 03_designer.py, 08_implementador.py) para saber o
  formato exato esperado ANTES de responder ao primeiro pedido daquela
  fase, e responda com conteúdo real, funcional, pensado por você — uma
  resposta stub/fake destrava o mecanismo mas quebra o pytest real que
  a fase 8 roda depois.
- Use uma ideia pequena e real, ex.: "REST API de lista de tarefas com
  criar, listar, concluir e remover tarefas" — escopo pequeno o
  suficiente para o volume de respostas delegadas ficar gerenciável
  (referência: uma validação anterior, fora do escopo desta bateria,
  completou uma ideia deste tamanho com sucesso, 8 fases, score de
  auto-crítica 91-100, 10/10 testes passando).

PASSO A PASSO:
1. Escreva 2 scripts de apoio e salve em docs/testes/testes/:
   - `05_aidd_generator_sentinela.py`: lista pedidos pendentes
     (_llm_request_*.json sem _llm_response_*.json correspondente) na
     pasta de cache, imprime id/fase/prompt de cada um. Rode-o
     repetidamente (com um intervalo curto) enquanto o pipeline está
     rodando em background.
   - `05_aidd_generator_responder.py <id> <arquivo-json-da-resposta>`:
     escreve _llm_response_{id}.json de forma atômica a partir de um
     arquivo JSON que você mesmo escreve com o conteúdo real da
     resposta.
2. Salve o texto exato da "ideia" usada como prompt de teste em
   `docs/testes/prompts/aidd_generator_ideia_todo_api.txt`.
3. Rode o pipeline em background contra um diretório temporário
   isolado, com --implementar-codigo.
4. Enquanto ele roda, chame o script sentinela repetidamente; para cada
   pedido novo que aparecer, leia o prompt/fase, componha uma resposta
   REAL e funcional (não fake), escreva um arquivo JSON com essa
   resposta e chame o script responder para entregá-la. Repita até o
   processo do pipeline terminar.
5. Confirme o exit code real do processo do pipeline ao terminar.
6. Verifique o projeto gerado: estrutura de pastas, git log com commit
   real, banco SQLite existindo, e se --implementar-codigo completou,
   rode o pytest real do projeto gerado e confirme que os testes
   passam de verdade.
7. Rode `python scripts/verificar_gates.py <pasta-gerada>` e capture o
   exit code real.
8. Capture o score de auto-crítica real da fase 7.
9. Rode a suíte pytest completa de tools/aidd-generator (python -m
   pytest tests/ -q, cwd tools/aidd-generator) e capture exit code e
   contagem real.

Se o volume de pedidos da fase 8 (--implementar-codigo) se mostrar
grande demais para responder tudo dentro de um tempo razoável, é
aceitável interromper --implementar-codigo e reportar as fases 1-7
completas e provadas como suficiente para esta rodada (PASSOU COM
RESSALVAS) — documente isso honestamente, nunca fabrique uma conclusão
de fase 8 que não rodou de verdade.

Escreva o relatório em
`docs/testes/relatorios/05_aidd_generator.md`: para cada fase,
confirme se completou e como; inclua pelo menos 1 exemplo REAL e
completo de pedido+resposta de cada tipo (fase 2, um de fase 3, um de
fase 8 se aplicável) com o conteúdo verdadeiro trocado (não resumido a
ponto de perder a evidência); o score de auto-crítica real; o
resultado real do `verificar_gates.py`; e se --implementar-codigo
rodou, o resultado real do pytest do projeto gerado. Veredito final
(PASSOU / PASSOU COM RESSALVAS / FALHOU, com justificativa). Use as
skills `artifact-design` e `dataviz` se fizer sentido visualizar o
fluxo das 8 fases e o protocolo delegado (ex.: um diagrama de sequência
pedido→resposta por fase), mantendo o Markdown como fonte de verdade.

CRITÉRIO DE SAÍDA:
- Exit code real do processo do pipeline capturado e reportado.
- Pelo menos 1 exemplo real e completo de pedido+resposta por tipo de
  fase documentado no relatório.
- Nenhum arquivo de cache órfão deixado rastreado/commitado por engano
  no repositório real (`git status` limpo além dos arquivos esperados
  em docs/testes/).
- Suíte pytest de tools/aidd-generator sem regressão — reporte o
  número real encontrado.

REGRAS DE ESCOPO — NÃO FAÇA:
- Não use modo headless (chave de API real) sem pedido explícito do
  usuário.
- Não fabrique respostas stub/fake só para destravar o mecanismo mais
  rápido — o objetivo é provar que funciona de verdade, uma resposta
  falsa quebra a prova.
- Não teste aidd-master, aidd-enterprise ou aidd-forge aqui.
- Não faça git commit nem git push no repositório REAL do ecossistema
  (o commit real feito pela fase 5 do pipeline acontece dentro do
  projeto gerado, em diretório temporário isolado — isso é esperado e
  correto).
- Não deixe processos do pipeline órfãos rodando em background ao
  final — confirme que o processo terminou antes de encerrar a tarefa.

ENTREGÁVEL: lista de scripts salvos, prompt salvo, caminho do
relatório, resumo de 8-10 linhas do veredito final incluindo quantas
fases completaram e o score de auto-crítica real.
```

## Prompt de Execução — English version

> Copy the block below in full to the executor agent. Self-contained.
> **Mandatory decision before running: Delegated mode (default,
> recommended) vs. Headless (only if the user explicitly asked for it
> and already has an API key configured) — re-read the source
> document's section about this first.**

```
You are going to prove that the AIDD Generator's complete 8-phase
pipeline (tools/aidd-generator/scripts/pipeline_completo.py) works end
to end, inside the ecossistema-aidd monorepo (root at
C:\Users\trcnologia\Desktop\ecossistema-aidd). This task is different
from the other test batteries: it requires YOU to act as the
pipeline's "delegated LLM" in real time (Delegated mode, zero API
cost) — it is not a script that runs unattended to completion. Validate
everything for real: real exit codes, generated tests actually
running, never simulated or fabricated.

MANDATORY DECISION BEFORE STARTING: use DELEGATED MODE by default. Do
NOT set LLM_MODEL nor any real API key (GROQ_API_KEY, OPENAI_API_KEY,
NVIDIA_NIM_API_KEY, OPENROUTER_API_KEY, TOGETHERAI_API_KEY) to run in
headless mode — that would spend real money from the user's account on
every LLM call, and this pipeline makes many calls (phase 2, 5
parallel calls in phase 3, several in phase 8). Only use headless mode
if the user who triggered you explicitly asked for that mode AND
already has the key configured — in that case the pipeline runs almost
unattended (you won't need to answer anything), but the cost is real.

ALREADY-INVESTIGATED CONTEXT (confirm by reading the code before
acting — re-read phases/utils_delegacao.py in full before writing
anything to disk):
- Entry point: `python scripts/pipeline_completo.py "<idea>" --pasta
  <destination> --implementar-codigo` (cwd tools/aidd-generator, same
  PYTHONPATH). Run it in the BACKGROUND (you need to keep interacting
  while it waits for responses).
- Delegated-protocol cache folder:
  tools/aidd-generator/scripts/.aidd/cache/ — requests arrive as
  `_llm_request_{id}.json` (fields: id, fase, timestamp,
  modelo_sugerido, contexto, prompt), expected responses as
  `_llm_response_{id}.json` (minimum: {"conteudo": "...",
  "tokens_consumidos": <int>, "modelo_usado": "..."}). Default timeout
  30s per request — respond quickly once you detect a new request.
- The "fase" field identifies where the request came from: phase 2 is
  something like "phase_02" (confirm the exact value in
  02_analisador.py's code); phase 3 has 5 distinct values, one per
  subagent (grep "phase_03_subagent" in phases/03_designer.py); phase 8
  uses "phase_08" for the main script requests (read the "prompt" field
  looking for "SCRIPT: {nome}" to know which script is being asked
  for) plus "phase_08_schema", "phase_08_integracao", "phase_08_fix",
  "phase_08_autocura" for sub-steps.
- The "conteudo" of each response needs to be valid JSON with the exact
  fields that phase expects — read each phase's parser (02_analisador.py,
  03_designer.py, 08_implementador.py) to know the exact expected
  format BEFORE answering the first request of that phase, and answer
  with real, functional content that you actually think through — a
  stub/fake response unblocks the mechanism but breaks the real pytest
  run that phase 8 executes afterward.
- Use a small, real idea, e.g. "REST API for a to-do list with create,
  list, complete, and delete tasks" — small enough to keep the volume
  of delegated responses manageable (reference: a prior validation,
  outside the scope of this battery, completed an idea of this size
  successfully — 8 phases, self-critique score 91-100, 10/10 tests
  passing).

STEP BY STEP:
1. Write 2 helper scripts and save them under docs/testes/testes/:
   - `05_aidd_generator_sentinela.py`: lists pending requests
     (_llm_request_*.json with no matching _llm_response_*.json) in the
     cache folder, printing id/fase/prompt for each. Run it repeatedly
     (with a short interval) while the pipeline runs in the
     background.
   - `05_aidd_generator_responder.py <id> <response-json-file>`: writes
     _llm_response_{id}.json atomically from a JSON file you wrote
     yourself with the real response content.
2. Save the exact "idea" text used as the test prompt at
   `docs/testes/prompts/aidd_generator_ideia_todo_api.txt`.
3. Run the pipeline in the background against an isolated temporary
   directory, with --implementar-codigo.
4. While it runs, call the sentinel script repeatedly; for every new
   request that appears, read the prompt/fase, compose a REAL,
   functional response (not fake), write a JSON file with that
   response, and call the responder script to deliver it. Repeat until
   the pipeline's process exits.
5. Confirm the pipeline process's real exit code when it finishes.
6. Verify the generated project: folder structure, git log with a real
   commit, SQLite database existing, and if --implementar-codigo
   completed, run the generated project's real pytest suite and
   confirm the tests actually pass.
7. Run `python scripts/verificar_gates.py <generated-folder>` and
   capture the real exit code.
8. Capture the phase 7 real self-critique score.
9. Run the full pytest suite of tools/aidd-generator (python -m pytest
   tests/ -q, cwd tools/aidd-generator) and capture the real exit code
   and count.

If the volume of phase-8 requests (--implementar-codigo) turns out to
be too large to answer within a reasonable amount of time, it is
acceptable to interrupt --implementar-codigo and report phases 1-7 as
complete and proven as sufficient for this round (PASSED WITH
CAVEATS) — document this honestly, never fabricate a phase-8 conclusion
that did not really run.

Write the report at `docs/testes/relatorios/05_aidd_generator.md`: for
each phase, confirm whether it completed and how; include at least 1
real, complete request+response example of each type (phase 2, one of
phase 3, one of phase 8 if applicable) with the actual content
exchanged (not summarized to the point of losing the evidence); the
real self-critique score; the real result of `verificar_gates.py`; and
if --implementar-codigo ran, the real result of the generated project's
pytest. Final verdict (PASSED / PASSED WITH CAVEATS / FAILED, with
justification). Use the `artifact-design` and `dataviz` skills if it
makes sense to visualize the 8-phase flow and the delegated protocol
(e.g. a sequence diagram of request→response per phase), keeping the
Markdown as the source of truth.

EXIT CRITERIA:
- The pipeline process's real exit code captured and reported.
- At least 1 real, complete request+response example per phase type
  documented in the report.
- No orphaned cache file left tracked/committed by mistake in the real
  repository (`git status` clean beyond the expected files under
  docs/testes/).
- tools/aidd-generator's pytest suite with no regression — report the
  real number found.

SCOPE RULES — DO NOT:
- Do not use headless mode (a real API key) without explicit user
  request.
- Do not fabricate stub/fake responses just to unblock the mechanism
  faster — the goal is to prove it really works, a fake response breaks
  the proof.
- Do not test aidd-master, aidd-enterprise, or aidd-forge here.
- Do not git commit or git push in the REAL ecosystem repository (the
  real commit made by the pipeline's phase 5 happens inside the
  generated project, in an isolated temporary directory — that is
  expected and correct).
- Do not leave orphaned pipeline processes running in the background at
  the end — confirm the process has terminated before ending the task.

DELIVERABLE: list of saved scripts, saved prompt, report path, 8-10
line summary of the final verdict including how many phases completed
and the real self-critique score.
```
