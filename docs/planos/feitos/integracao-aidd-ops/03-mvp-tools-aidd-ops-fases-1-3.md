# Pacote 3 — MVP `tools/aidd-ops/` (Fases 1-3: Intake, Curadoria, Sizing)

> **Não toca infraestrutura real.** Zero SSH, zero DNS, zero Docker real — produz um **plano de infraestrutura determinístico** (JSON), não executa nada contra um servidor. Reversível via `git revert`.
> **Bloqueado por:** Pacote 2 (governança) já concluído/executado.
> **Decisão que molda este pacote:** `VEREDITO-TECNICO-VIABILIDADE.md` §6 — o MVP deve ser **100% determinístico, zero chamada de LLM**, aproveitando a matriz fixa de nicho→stack que a própria proposta original já define (§6 do plano arquitetural).

---

## Diagnóstico e desenho técnico

### Por que 100% determinístico é possível (e correto) para este MVP

A proposta original (`docs/features/06-09-2026_feature-arquitetura-aidd-ops.md §6`) já define uma matriz fechada de 5 nichos → stack de ferramentas (Clínicas, Delivery, Farmácias, B2B Industrial, Energia Solar). Isso torna as 3 fases do MVP um problema de **lookup + aritmética**, não de síntese criativa — categoria completamente diferente do `aidd-generator` (que sintetiza uma arquitetura nova a partir de uma ideia livre, por isso precisa de LLM em 3 das 8 fases). Mapeamento de decisão:

| Fase | Natureza | Decisão de design |
|---|---|---|
| 1. Intake | Reconhecer qual dos 5 nichos catalogados o texto do usuário descreve (ou nicho passado explicitamente via flag) | **Casamento de palavras-chave contra lista fixa por nicho** — mesmo padrão de `tools/aidd-master/src/core/detector_camada.py`, **SEM LLM**. Se o texto bater com mais de 1 nicho (ou nenhum), retorna erro estruturado com candidatos — nunca adivinha silenciosamente (mesmo princípio de `TIPO_AMBIGUO` já usado em `aidd-master`/`aidd-enterprise`). |
| 2. Curadoria | Dado o nicho reconhecido, listar a stack de ferramentas | **Lookup direto na matriz fixa** (`data/catalogo_nichos.json`) — zero LLM. Curadoria assistida por LLM para nichos fora da matriz fica **fora de escopo deste MVP**, registrada como extensão futura. |
| 3. Sizing | Somar requisitos de recursos (vCPU/RAM/disco) das ferramentas da stack selecionada | **Aritmética pura** sobre uma tabela de requisitos por ferramenta (`data/requisitos_recursos.json`) — zero LLM. |

**Regra não-negociável para o executor:** os números de requisito de recursos (vCPU/RAM/disco) por ferramenta em `requisitos_recursos.json` **precisam vir da documentação oficial real de cada projeto** (Twenty CRM, Chatwoot, Cal.com, Typebot, Evolution API, EspoCRM, Mautic, Documenso, ERPNext, Odoo, Listmonk — cada entrada da matriz de nicho da proposta original) — linkada no próprio arquivo (campo `fonte`). Nunca inventar um número plausível sem citar de onde veio — isso violaria a mesma regra de "reprodução real, nunca simulada" que rege todo o resto deste ecossistema.

### Padrões arquiteturais já homologados que este pacote deve seguir (não reinventar)

- **Result monad:** `tools/aidd-ops/src/core/result.py`, cópia própria (mesmo padrão de duplicação controlada já decidido no Item 4 da Rodada 2 — cada ferramenta é standalone, não compartilha pacote).
- **Contratos JSON Schema Draft 2020-12:** um schema por fase (payload de entrada/saída), validados antes de qualquer processamento — mesmo padrão de `schema_injector_request.json`.
- **Persistência estruturada entre fases:** `PLANO-INFRAESTRUTURA.json` no diretório de saída, acumulando o estado de cada fase (mesmo padrão de `.aidd/cache/` do `aidd-generator` e `PLANO-EXECUCAO-ESTRUTURADO.json` do `aidd-master`) — nunca manter estado só na memória do processo.
- **Gate determinístico próprio:** `tools/aidd-ops/gates/G_OPS_MVP.py` — valida a estrutura do próprio código (compila, zero stub via AST) e, quando rodado com `--dir <saída>`, valida que o `PLANO-INFRAESTRUTURA.json` gerado é conforme os 3 schemas.
- **Testes reais (nunca mock do comportamento central):** cada fase testada com `tmp_path`, casos reais dos 5 nichos + pelo menos 1 caso de ambiguidade + pelo menos 1 caso de nicho não reconhecido.

### O que este pacote NÃO faz (fica para pacotes futuros)

- Não conecta em nenhuma VPS, não cria nenhum registro DNS, não sobe nenhum container — isso são os Pacotes 4, 5, 7 e 9 (com aprovação pontual quando chegar a vez).
- Não cria nenhum MCP (Pacote 5).
- Não cria nenhum componente injetável em `componentes/aidd-ops/` ainda — o MVP não injeta nada em projeto-alvo nenhum, só produz um plano. Se, ao implementar, ficar claro que alguma skill/spec/hook precisa existir como componente formal, registre isso explicitamente no relatório em vez de decidir sozinho a forma exata.

## Definição de Pronto

3.1. `tools/aidd-ops/src/core/result.py` — Result monad (copiar o padrão exato de `tools/aidd-master/src/core/result.py`, adaptado).
3.2. `tools/aidd-ops/schemas/schema_intake_request.json`, `schema_stack_selecionada.json`, `schema_sizing_output.json` — JSON Schema Draft 2020-12, `additionalProperties: false`, campos obrigatórios explícitos.
3.3. `tools/aidd-ops/data/catalogo_nichos.json` — os 5 nichos da proposta original (§6), cada um com: nome de exibição, lista de ferramentas, lista de palavras-chave de reconhecimento (PT-BR, incluindo variações com/sem acento).
3.4. `tools/aidd-ops/data/requisitos_recursos.json` — requisitos de vCPU/RAM/disco por ferramenta, cada entrada com campo `fonte` (URL da documentação oficial real usada).
3.5. `tools/aidd-ops/scripts/phases/01_intake.py`: função `reconhecer_nicho(texto_ou_nicho: str) -> Result` — casamento de palavras-chave contra `catalogo_nichos.json`; se bater com exatamente 1 nicho, `Result.ok(nicho)`; se bater com 0 ou mais de 1, `Result.fail(codigo="NICHO_AMBIGUO"|"NICHO_NAO_RECONHECIDO", detalhes={"candidatos": [...]})`. Aceita também um nicho explícito via flag (bypass do reconhecimento de texto).
3.6. `tools/aidd-ops/scripts/phases/02_curadoria.py`: função `curar_stack(nicho: str) -> Result` — lookup direto em `catalogo_nichos.json`, retorna a lista de ferramentas + validação de schema.
3.7. `tools/aidd-ops/scripts/phases/03_sizing.py`: função `dimensionar(ferramentas: list) -> Result` — soma os requisitos de `requisitos_recursos.json`, retorna spec de VPS sugerida (vCPU/RAM/disco totais, mais os nomes dos bancos lógicos necessários, um por ferramenta que precisar de banco relacional).
3.8. `tools/aidd-ops/scripts/pipeline_ops.py` — orquestrador principal: `python scripts/pipeline_ops.py "<texto ou --nicho>" --pasta <destino>` roda as 3 fases em sequência, grava `PLANO-INFRAESTRUTURA.json` em `<destino>` acumulando o estado de cada fase, imprime resumo legível. Equivalente via `python ecossistema.py ops plan "<texto>" --pasta <destino>` — **esta é a primeira vez que `ops` entra no dispatch de `ecossistema.py`**, agora que existe um `cmd_ops` real por trás.
3.9. `tools/aidd-ops/gates/G_OPS_MVP.py`: valida (a) estrutura do próprio código de `tools/aidd-ops/` (compila via `py_compile`, zero stub via AST — mesmo padrão de `G_INJECT.py` de `aidd-master`); (b) quando rodado com `--dir <saída>`, valida `PLANO-INFRAESTRUTURA.json` contra os 3 schemas.
3.10. `tools/aidd-ops/tests/`: testes reais (tmp_path) cobrindo os 5 nichos reais da matriz + 1 caso de ambiguidade real (um texto que bate com 2 nichos) + 1 caso de nicho não reconhecido + o pipeline completo ponta a ponta via CLI (subprocess real) + o gate `G_OPS_MVP.py` isolado.
3.11. Atualizar `ecossistema.py`: adicionar `"ops"` ao `dispatch` (roteando para `tools/aidd-ops/scripts/pipeline_ops.py`, mesmo padrão de `cmd_master`/`cmd_enterprise`), atualizar `cmd_status()` para refletir que `aidd-ops` agora tem testes reais (via `status --testes`).
3.12. Atualizar `gates/G_CLI_HELP_CONSISTENCIA.py`: adicionar `tools/aidd-ops/scripts/pipeline_ops.py` a `ARQUIVOS_AUDITADOS` — **este é o momento correto para essa mudança**, adiada do Pacote 2 porque o arquivo não existia ainda.
3.13. Se o design revelar necessidade real de algum componente formal (skill/spec) para `aidd-ops`, criar a fonte canônica em `componentes/aidd-ops/{skills,specs}/` (escopo já registrado no Pacote 2) e propagar via `components sync` — nunca criar destino à mão. Se não houver necessidade real, não invente uma só para "preencher" a pasta.

## Critério de saída

- `python tools/aidd-ops/scripts/pipeline_ops.py "<texto de um dos 5 nichos>" --pasta <tmp>` → exit 0, `PLANO-INFRAESTRUTURA.json` real gerado e válido contra os 3 schemas, para cada um dos 5 nichos.
- Caso de ambiguidade real (texto que casa com 2 nichos) → exit 1, `NICHO_AMBIGUO`, candidatos corretos, nenhum arquivo de plano escrito.
- Caso de nicho não reconhecido → exit 1, `NICHO_NAO_RECONHECIDO`.
- `python ecossistema.py ops plan "<texto>" --pasta <tmp>` → mesmo resultado via o dispatcher raiz.
- `python tools/aidd-ops/gates/G_OPS_MVP.py` → exit 0; rodado com `--dir <saída válida>` → exit 0; rodado com `--dir <saída corrompida de propósito>` → exit 1.
- Suíte pytest de `tools/aidd-ops/tests/` → exit 0.
- `python ecossistema.py audit` (raiz) → exit 0, sem regressão, incluindo `G_CLI_HELP_CONSISTENCIA` agora cobrindo o novo arquivo.
- `python ecossistema.py status` → `aidd-ops` continua `[OK] Instalado`; `python ecossistema.py status --testes` → contagem real de testes de `aidd-ops` > 0 pela primeira vez.
- Todo número em `requisitos_recursos.json` tem uma fonte real citada — nenhum "chute plausível".

## Prompt de Execução

> Copie o bloco abaixo integralmente para o agente executor. Autocontido.

```
Você vai construir o MVP de uma 5ª ferramenta, aidd-ops
(tools/aidd-ops/), no monorepo ecossistema-aidd (raiz em
C:\Users\trcnologia\Desktop\ecossistema-aidd). Este MVP cobre só as
Fases 1-3 de um pipeline maior (Intake, Curadoria, Sizing) — NÃO toca
infraestrutura real (zero SSH, zero DNS, zero Docker real). Produz um
plano de infraestrutura determinístico (JSON), não executa nada contra
um servidor. Siga EXATAMENTE a Definição de Pronto abaixo, não invente
escopo adicional, e valide tudo de verdade (execuções reais, exit codes
reais, nunca mascarados por pipe).

DECISÃO DE DESIGN JÁ TOMADA (não reabra): este MVP é 100%
DETERMINÍSTICO — zero chamada de LLM em qualquer fase. Isso é possível
porque a proposta original já define uma matriz fechada de 5 nichos →
stack de ferramentas (docs/features/PLANO ARQUITETURAL NOVA FEATURE
AIDD-OPS.md §6: Clínicas, Delivery, Farmácias, B2B Industrial, Energia
Solar) — as 3 fases do MVP são lookup + aritmética contra essa matriz,
não síntese criativa.

CONTEXTO JÁ INVESTIGADO (confirme lendo o código antes de escrever):
- Padrão de Result monad: tools/aidd-master/src/core/result.py — copie
  a mesma estrutura (Result.ok/Result.fail com codigo/detalhes
  estruturados, sem exceções soltas).
- Padrão de detecção por palavra-chave sem LLM:
  tools/aidd-master/src/core/detector_camada.py — mesma técnica
  (casamento contra lista fixa), incluindo o comportamento de retornar
  erro estruturado com candidatos quando o texto bate com mais de um
  padrão (nunca escolher silenciosamente).
- Padrão de persistência estruturada entre fases:
  tools/aidd-generator/scripts/.aidd/cache/ (estado entre fases do
  pipeline de 8 fases) e PLANO-EXECUCAO-ESTRUTURADO.json (estado do
  aidd-master) — para aidd-ops, o equivalente é PLANO-INFRAESTRUTURA.json
  no diretório de saída, acumulando o resultado de cada fase.
- Padrão de gate determinístico de infraestrutura própria da ferramenta:
  tools/aidd-master/scripts/gates/G_INJECT.py (valida arquivos core
  presentes, compila via py_compile, zero stub via AST, suíte pytest
  dedicada).
- gates/G_CLI_HELP_CONSISTENCIA.py (ARQUIVOS_AUDITADOS, raiz do
  monorepo): este é o momento certo de adicionar
  tools/aidd-ops/scripts/pipeline_ops.py a essa lista — no Pacote
  anterior (governança) isso foi propositalmente adiado porque o
  arquivo ainda não existia (o gate falha se um caminho listado não
  existir em disco).
- ecossistema.py: cmd_forge/cmd_master/cmd_enterprise (linhas ~36-61)
  são o padrão de como rotear um novo comando de ferramenta — replique
  a mesma estrutura para cmd_ops, apontando para
  tools/aidd-ops/scripts/pipeline_ops.py. Adicione "ops" ao dict
  `dispatch` (só agora isso é seguro, porque o módulo real existe).

DEFINIÇÃO DE PRONTO — nesta ordem:
1. tools/aidd-ops/src/core/result.py: Result monad, mesmo padrão de
   tools/aidd-master/src/core/result.py.
2. tools/aidd-ops/schemas/: 3 arquivos JSON Schema Draft 2020-12
   (schema_intake_request.json, schema_stack_selecionada.json,
   schema_sizing_output.json), additionalProperties: false, campos
   obrigatórios explícitos.
3. tools/aidd-ops/data/catalogo_nichos.json: os 5 nichos reais da
   proposta original §6 (Clínicas, Delivery, Farmácias, B2B Industrial,
   Energia Solar), cada um com nome de exibição, lista de ferramentas
   (nomes reais: Typebot, Twenty CRM, Chatwoot, Evolution API, Cal.com,
   Odoo, Listmonk, EspoCRM, Mautic, Documenso, ERPNext — conforme a
   matriz da proposta), e uma lista de palavras-chave de reconhecimento
   em PT-BR (com e sem acento) para cada nicho.
4. tools/aidd-ops/data/requisitos_recursos.json: requisitos de
   vCPU/RAM/disco por ferramenta da matriz. CADA ENTRADA PRECISA DE UM
   CAMPO "fonte" com a URL real da documentação oficial daquela
   ferramenta que embasa o número — nunca invente um número plausível
   sem citar a fonte real. Se não conseguir achar o requisito oficial
   documentado de alguma ferramenta, registre isso explicitamente no
   relatório final em vez de inventar.
5. tools/aidd-ops/scripts/phases/01_intake.py:
   reconhecer_nicho(texto_ou_nicho) -> Result. Casamento de
   palavras-chave contra catalogo_nichos.json. Aceita também um nicho
   explícito (bypass do reconhecimento por texto, ex.: --nicho
   clinicas). Se o texto bater com exatamente 1 nicho:
   Result.ok(nicho). Se bater com 0: Result.fail(codigo=
   "NICHO_NAO_RECONHECIDO"). Se bater com mais de 1: Result.fail(codigo=
   "NICHO_AMBIGUO", detalhes={"candidatos": [...]}) — nunca escolher
   silenciosamente.
6. tools/aidd-ops/scripts/phases/02_curadoria.py: curar_stack(nicho) ->
   Result. Lookup direto em catalogo_nichos.json, valida contra
   schema_stack_selecionada.json.
7. tools/aidd-ops/scripts/phases/03_sizing.py: dimensionar(ferramentas)
   -> Result. Soma os requisitos de requisitos_recursos.json, retorna
   spec de VPS (vCPU/RAM/disco totais) + lista de bancos lógicos
   necessários (uma entrada por ferramenta que precisar de banco
   relacional — confirme quais ferramentas da matriz precisam, não
   assuma que todas precisam).
8. tools/aidd-ops/scripts/pipeline_ops.py: orquestrador principal.
   `python scripts/pipeline_ops.py "<texto>" --pasta <destino>` (ou
   `--nicho <slug>` como alternativa ao texto livre) roda as 3 fases em
   sequência, grava PLANO-INFRAESTRUTURA.json em <destino> acumulando o
   estado de cada fase (payload de entrada + saída de cada fase,
   timestamp), imprime um resumo legível ao usuário. Propague
   corretamente os códigos de erro estruturados das fases 5-7 (não
   masque um Result.fail como sucesso).
9. tools/aidd-ops/gates/G_OPS_MVP.py: (a) sem --dir, valida a própria
   estrutura de tools/aidd-ops/ (compila via py_compile todos os .py,
   zero stub via AST — nenhuma função com só `pass`/`...`/docstring sem
   corpo real); (b) com --dir <saída>, valida que
   <saída>/PLANO-INFRAESTRUTURA.json existe e cada seção bate com o
   schema correspondente.
10. tools/aidd-ops/tests/: testes reais com tmp_path cobrindo: os 5
    nichos reais rodando a pipeline completa ponta a ponta (via
    subprocess real do CLI, não só chamando as funções Python
    diretamente); 1 caso de texto ambíguo real (que casa com 2 nichos)
    confirmando NICHO_AMBIGUO e nenhum arquivo escrito; 1 caso de texto
    não reconhecido confirmando NICHO_NAO_RECONHECIDO; o gate
    G_OPS_MVP.py isolado, nos 2 modos (com e sem --dir).
11. Em ecossistema.py: adicione cmd_ops(args) seguindo o padrão exato
    de cmd_master/cmd_enterprise (linhas ~36-61), apontando para
    tools/aidd-ops/scripts/pipeline_ops.py. Adicione "ops": cmd_ops ao
    dict dispatch. Atualize a docstring do topo do arquivo.
12. Em gates/G_CLI_HELP_CONSISTENCIA.py: adicione
    "tools/aidd-ops/scripts/pipeline_ops.py" a ARQUIVOS_AUDITADOS.
13. Se, ao implementar, você identificar uma necessidade REAL de algum
    componente formal (skill/spec/hook) para aidd-ops, crie a fonte
    canônica em componentes/aidd-ops/{tipo}/ (o escopo "aidd-ops" já
    foi registrado em gates/manifesto_harnesses.json no pacote
    anterior) e propague via `python ecossistema.py components sync
    --tipo <tipo> --ferramenta aidd-ops` — nunca crie o destino
    manualmente. Se não houver necessidade real, não crie nada só para
    preencher a pasta — reporte essa decisão explicitamente.

CRITÉRIO DE SAÍDA (rode e cole o output real de cada um):
- Para cada um dos 5 nichos reais: `python
  tools/aidd-ops/scripts/pipeline_ops.py "<texto do nicho>" --pasta
  <tmp>` → exit 0, PLANO-INFRAESTRUTURA.json real gerado e válido
  contra os 3 schemas.
- 1 caso de ambiguidade real → exit 1, NICHO_AMBIGUO, candidatos
  corretos, nenhum arquivo escrito.
- 1 caso de nicho não reconhecido → exit 1, NICHO_NAO_RECONHECIDO.
- `python ecossistema.py ops plan "<texto>" --pasta <tmp>` → mesmo
  resultado via o dispatcher raiz.
- `python tools/aidd-ops/gates/G_OPS_MVP.py` → exit 0 (modo sem --dir);
  com --dir de uma saída válida → exit 0; com --dir de uma saída
  corrompida de propósito (ex.: PLANO-INFRAESTRUTURA.json com um campo
  obrigatório removido) → exit 1.
- Suíte pytest de tools/aidd-ops/tests/ (python -m pytest tests/ -q,
  cwd tools/aidd-ops) → exit 0.
- python ecossistema.py audit (raiz) → exit 0, sem regressão,
  confirmando que G_CLI_HELP_CONSISTENCIA agora cobre o novo arquivo
  sem reprovar.
- python ecossistema.py status → aidd-ops continua [OK] Instalado;
  python ecossistema.py status --testes → contagem real de testes de
  aidd-ops maior que 0 pela primeira vez.
- git status (raiz) limpo além dos arquivos esperados.

REGRAS DE ESCOPO — NÃO FAÇA:
- Não implemente nada das Fases 4-10 (SSH, DNS, Docker real, etc.) —
  isso são pacotes futuros, com aprovação pontual própria.
- Não use LLM em nenhuma das 3 fases — se você achar que uma decisão
  exige "julgamento" além de lookup/aritmética, PARE e reporte
  explicitamente em vez de decidir sozinho adicionar uma chamada de
  LLM.
- Não invente número de requisito de recursos sem fonte real citada.
- Não crie componente formal em componentes/aidd-ops/ sem necessidade
  real identificada.
- Não faça git commit nem git push.
- Não altere nenhum documento em docs/planos/integracao-aidd-ops/.

ENTREGÁVEL: lista exata de arquivos criados/alterados; comando + output
real que comprova cada item do Critério de Saída; qualquer desvio
necessário (inclusive requisitos de recursos não encontrados), reportado
explicitamente em vez de decidido sozinho.
```

## Prompt de Execução — English version

> Copy the block below in full to the executor agent. Self-contained.

```
You are going to build the MVP of a 5th tool, aidd-ops
(tools/aidd-ops/), inside the ecossistema-aidd monorepo (root at
C:\Users\trcnologia\Desktop\ecossistema-aidd). This MVP covers only
Phases 1-3 of a larger pipeline (Intake, Curation, Sizing) — it does
NOT touch real infrastructure (zero SSH, zero DNS, zero real Docker).
It produces a deterministic infrastructure plan (JSON), it does not run
anything against a server. Follow the Definition of Done below EXACTLY,
do not invent additional scope, and validate everything for real (real
runs, real exit codes, never masked by a pipe).

ALREADY-MADE DESIGN DECISION (do not reopen): this MVP is 100%
DETERMINISTIC — zero LLM calls in any phase. This is possible because
the original proposal already defines a closed matrix of 5 niches →
tool stacks (docs/features/PLANO ARQUITETURAL NOVA FEATURE
AIDD-OPS.md §6: Clinics, Delivery, Pharmacies, B2B Industrial, Solar
Energy) — the MVP's 3 phases are lookup + arithmetic against that
matrix, not creative synthesis.

ALREADY-INVESTIGATED CONTEXT (confirm by reading the code before
writing):
- Result monad pattern: tools/aidd-master/src/core/result.py — copy the
  same structure (Result.ok/Result.fail with a structured
  codigo/detalhes, no bare exceptions).
- Keyword-based, LLM-free detection pattern:
  tools/aidd-master/src/core/detector_camada.py — same technique
  (matching against a fixed list), including the behavior of returning
  a structured error with candidates when the text matches more than
  one pattern (never silently pick one).
- Structured cross-phase persistence pattern:
  tools/aidd-generator/scripts/.aidd/cache/ (state between the 8-phase
  pipeline's phases) and PLANO-EXECUCAO-ESTRUTURADO.json (aidd-master's
  state) — for aidd-ops, the equivalent is PLANO-INFRAESTRUTURA.json in
  the output directory, accumulating each phase's result.
- Deterministic own-infrastructure gate pattern:
  tools/aidd-master/scripts/gates/G_INJECT.py (validates core files
  present, compiles via py_compile, zero stub via AST, dedicated pytest
  suite).
- gates/G_CLI_HELP_CONSISTENCIA.py (ARQUIVOS_AUDITADOS, monorepo root):
  this is the right moment to add
  tools/aidd-ops/scripts/pipeline_ops.py to that list — in the prior
  (governance) package this was deliberately deferred because the file
  did not exist yet (the gate fails if a listed path does not exist on
  disk).
- ecossistema.py: cmd_forge/cmd_master/cmd_enterprise (lines ~36-61)
  are the pattern for routing a new tool command — replicate the same
  structure for cmd_ops, pointing at
  tools/aidd-ops/scripts/pipeline_ops.py. Add "ops" to the `dispatch`
  dict (only now is this safe, because the real module exists).

DEFINITION OF DONE — in this order:
1. tools/aidd-ops/src/core/result.py: Result monad, same pattern as
   tools/aidd-master/src/core/result.py.
2. tools/aidd-ops/schemas/: 3 JSON Schema Draft 2020-12 files
   (schema_intake_request.json, schema_stack_selecionada.json,
   schema_sizing_output.json), additionalProperties: false, explicit
   required fields.
3. tools/aidd-ops/data/catalogo_nichos.json: the 5 real niches from the
   original proposal §6 (Clinics, Delivery, Pharmacies, B2B Industrial,
   Solar Energy), each with a display name, tool list (real names:
   Typebot, Twenty CRM, Chatwoot, Evolution API, Cal.com, Odoo,
   Listmonk, EspoCRM, Mautic, Documenso, ERPNext — per the proposal's
   matrix), and a list of PT-BR recognition keywords (with and without
   accents) per niche.
4. tools/aidd-ops/data/requisitos_recursos.json: vCPU/RAM/disk
   requirements per tool in the matrix. EVERY ENTRY NEEDS A "fonte"
   FIELD with the real URL of that tool's official documentation
   backing the number — never invent a plausible number without citing
   a real source. If you cannot find a tool's officially documented
   requirement, explicitly report that in the final report instead of
   inventing one.
5. tools/aidd-ops/scripts/phases/01_intake.py:
   reconhecer_nicho(texto_ou_nicho) -> Result. Keyword matching against
   catalogo_nichos.json. Also accepts an explicit niche (bypassing
   text recognition, e.g. --nicho clinicas). If the text matches
   exactly 1 niche: Result.ok(niche). If it matches 0:
   Result.fail(codigo="NICHO_NAO_RECONHECIDO"). If it matches more than
   1: Result.fail(codigo="NICHO_AMBIGUO", detalhes={"candidatos": [...]})
   — never silently pick one.
6. tools/aidd-ops/scripts/phases/02_curadoria.py: curar_stack(nicho) ->
   Result. Direct lookup in catalogo_nichos.json, validated against
   schema_stack_selecionada.json.
7. tools/aidd-ops/scripts/phases/03_sizing.py: dimensionar(ferramentas)
   -> Result. Sums the requirements from requisitos_recursos.json,
   returns a suggested VPS spec (total vCPU/RAM/disk) + the list of
   logical databases needed (one entry per tool that needs a
   relational database — confirm which tools in the matrix actually
   need one, do not assume all of them do).
8. tools/aidd-ops/scripts/pipeline_ops.py: main orchestrator.
   `python scripts/pipeline_ops.py "<text>" --pasta <destination>` (or
   `--nicho <slug>` as an alternative to free text) runs the 3 phases
   in sequence, writes PLANO-INFRAESTRUTURA.json to <destination>
   accumulating each phase's state (input payload + output, timestamp),
   prints a readable summary to the user. Correctly propagate the
   structured error codes from phases 5-7 (never mask a Result.fail as
   success).
9. tools/aidd-ops/gates/G_OPS_MVP.py: (a) without --dir, validates
   tools/aidd-ops/'s own structure (compiles every .py via py_compile,
   zero stub via AST — no function with just `pass`/`...`/docstring
   with no real body); (b) with --dir <output>, validates that
   <output>/PLANO-INFRAESTRUTURA.json exists and each section matches
   its corresponding schema.
10. tools/aidd-ops/tests/: real tests with tmp_path covering: the 5
    real niches running the full pipeline end to end (via a real CLI
    subprocess, not just calling the Python functions directly); 1 real
    ambiguous-text case (matching 2 niches) confirming NICHO_AMBIGUO
    and no file written; 1 unrecognized-text case confirming
    NICHO_NAO_RECONHECIDO; the G_OPS_MVP.py gate standalone, in both
    modes (with and without --dir).
11. In ecossistema.py: add cmd_ops(args) following the exact pattern of
    cmd_master/cmd_enterprise (lines ~36-61), pointing at
    tools/aidd-ops/scripts/pipeline_ops.py. Add "ops": cmd_ops to the
    dispatch dict. Update the file's top docstring.
12. In gates/G_CLI_HELP_CONSISTENCIA.py: add
    "tools/aidd-ops/scripts/pipeline_ops.py" to ARQUIVOS_AUDITADOS.
13. If, while implementing, you identify a REAL need for some formal
    component (skill/spec/hook) for aidd-ops, create the canonical
    source under componentes/aidd-ops/{type}/ (the "aidd-ops" scope was
    already registered in gates/manifesto_harnesses.json in the prior
    package) and propagate via `python ecossistema.py components sync
    --tipo <type> --ferramenta aidd-ops` — never create the
    destination by hand. If there is no real need, do not create
    anything just to fill the folder — explicitly report that
    decision.

EXIT CRITERIA (run and paste the real output of each):
- For each of the 5 real niches: `python
  tools/aidd-ops/scripts/pipeline_ops.py "<niche text>" --pasta <tmp>`
  → exit 0, a real PLANO-INFRAESTRUTURA.json generated and valid
  against the 3 schemas.
- 1 real ambiguity case → exit 1, NICHO_AMBIGUO, correct candidates, no
  file written.
- 1 unrecognized-niche case → exit 1, NICHO_NAO_RECONHECIDO.
- `python ecossistema.py ops plan "<text>" --pasta <tmp>` → same result
  via the root dispatcher.
- `python tools/aidd-ops/gates/G_OPS_MVP.py` → exit 0 (mode without
  --dir); with --dir of a valid output → exit 0; with --dir of a
  deliberately corrupted output (e.g. PLANO-INFRAESTRUTURA.json missing
  a required field) → exit 1.
- tools/aidd-ops/tests/'s pytest suite (python -m pytest tests/ -q, cwd
  tools/aidd-ops) → exit 0.
- python ecossistema.py audit (root) → exit 0, no regression,
  confirming G_CLI_HELP_CONSISTENCIA now covers the new file without
  failing.
- python ecossistema.py status → aidd-ops still shows [OK] Instalado;
  python ecossistema.py status --testes → aidd-ops's real test count
  greater than 0 for the first time.
- git status (root) clean beyond the expected files.

SCOPE RULES — DO NOT:
- Do not implement anything from Phases 4-10 (SSH, DNS, real Docker,
  etc.) — those are future packages, each with its own point-in-time
  approval.
- Do not use an LLM in any of the 3 phases — if you think a decision
  needs "judgment" beyond lookup/arithmetic, STOP and explicitly report
  it instead of deciding on your own to add an LLM call.
- Do not invent a resource-requirement number without a real cited
  source.
- Do not create a formal component under componentes/aidd-ops/ without
  an identified real need.
- Do not git commit or git push.
- Do not modify any document under docs/planos/integracao-aidd-ops/.

DELIVERABLE: exact list of files created/changed; command + real
output proving each item of the Exit Criteria; any necessary deviation
(including resource requirements not found), explicitly reported
instead of decided by yourself.
```
