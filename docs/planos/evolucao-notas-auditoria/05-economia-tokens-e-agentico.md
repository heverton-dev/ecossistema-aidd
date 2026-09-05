# Pacote 5 — Economia de Tokens + Engenharia Agêntica

> **Status:** ✅ CONCLUÍDO em 05/09/2026 — nota final 9.5/10 (ver Veredito ao final do documento).
> **Origem:** `docs/planos/PLANO-EVOLUCAO-NOTAS-AUDITORIA.md` §6 (Fase 5) — rotulagem `medido` vs `autodeclarado` no protocolo delegado.
> **Contribui para:** dimensões Economia de Tokens (7→8/10) e Engenharia Agêntica Aplicada (8→8.5/10).
> **Teto estrutural já reconhecido (`00-PROCESSO-E-DECISOES.md` §5):** o número de tokens no modo delegado é autodeclarado por quem responde — não há como verificar de forma independente. "Pronto" aqui significa que essa limitação fica **rotulada e documentada honestamente**, nunca que ela deixa de existir.

---

## Verificação independente que já fiz (o diagnóstico original subestimou o problema)

1. **Confirmado, ainda válido:** em `tools/aidd-generator/scripts/phases/utils_delegacao.py`, o Modo Delegado (`solicitar_llm_modo_delegado()`, linha ~216) só valida `"conteudo" in dados and "tokens_consumidos" in dados` e retorna o dict como veio — `tokens_consumidos` é o que a ADE que respondeu escreveu no arquivo JSON, nunca medido pelo código local. O Modo Headless (`solicitar_llm_modo_headless()`, linha ~369) mede de verdade via `resposta.usage.total_tokens` da chamada `litellm.completion()`. Hoje **não existe nenhum campo no dicionário de retorno que diga qual dos dois caminhos gerou aquele número** — os dois saem com a mesma forma (`conteudo`, `tokens_consumidos`, `modelo_usado`, `timestamp_resposta`).
2. **Achado novo, mais grave que o diagnóstico original previa:** o problema não é só "os dois números são indistinguíveis" — em pelo menos 3 fases que consomem `solicitar_llm()`, o código **rotula ativamente como "medição real" um número que, na prática (Modo Delegado, que é o modo padrão), nunca passou por `litellm`:**
   - `scripts/phases/02_analisador.py:363`: `'medicao': 'real (litellm resposta.usage.total_tokens)' if tokens_reais is not None else 'nao disponivel (...)'`
   - `scripts/phases/03_designer.py:499`: `'medicao': 'real (litellm, soma das 5 chamadas)' if self._tokens_reais_totais is not None else 'nao disponivel'`
   - `scripts/phases/08_implementador.py:1321`: `'medicao': 'real (soma de todas as chamadas LLM, incluindo correções)'` — **sem condicional nenhuma, sempre afirma "real".**
   
   Ou seja: toda vez que uma ADE responde no Modo Delegado (o modo padrão, universal, o que a maioria das sessões reais usa) e escreve qualquer valor em `tokens_consumidos` — mesmo um valor inventado — essas 3 fases gravam no `_phase_NN_index.json` a frase **"medição real via litellm"**, o que é falso. Isso é uma violação direta da Lei Fundamental de Transparência Total do próprio `AGENTS.md` ("conhecimento é poder" / zero alucinação em métricas), não apenas uma lacuna de precisão.
3. **Confirmado, ainda válido:** nenhum schema/contrato formal define o dicionário de resposta do protocolo delegado — é só a forma implícita usada em `utils_delegacao.py` e reproduzida por convenção nas fases consumidoras. Não há um lugar único para travar o campo novo.
4. **`scripts/phases/05_criador.py`:** não usa o padrão `medicao` das outras 3 — reporta `tokens.consumidos: 0` na sua fase (parece não fazer chamada LLM direta neste ponto do fluxo, ou já é tratado em outro lugar). Fica como item a confirmar durante a implementação (não decidir agora, sem evidência suficiente).
5. **`07_analisador.py`** (auto-crítica) e **`web/status_parser.py`** (dashboard) apenas somam/exibem `tokens.consumidos` de cada fase sem qualquer distinção de origem — herdam o problema de cima sem adicionar um novo.
6. **`docs/PRINCIPIO-UNIVERSALIDADE.md`** já documenta o protocolo delegado com um estilo honesto (FAQ explícito sobre limitações de timeout, tamanho de payload, etc.) mas **não menciona em nenhum lugar** que o número de tokens não é verificável — a lacuna documental do diagnóstico original também se confirma.

---

## Definição de Pronto

**Regra geral:** o objetivo NÃO é fingir que dá para medir tokens de verdade no Modo Delegado (é estruturalmente impossível — a ADE que responde pode escrever qualquer número). O objetivo é que **nenhum lugar do sistema minta sobre a origem de um número** — cada valor de tokens deve carregar consigo, de forma rastreável, se foi medido via API real ou autodeclarado por quem respondeu.

**Fase 1 — Origem da medição na fonte (`utils_delegacao.py`)**
1.1. Em `solicitar_llm_modo_delegado()`: ao retornar a resposta, garantir que o dict sempre contenha `"origem_medicao": "autodeclarado"` — inserido pelo código local (não confiar que a ADE externa vá escrever esse campo; se ela escrever algo diferente por engano, o código local sobrescreve com `"autodeclarado"`, já que por definição este modo nunca é medido de forma independente).
1.2. Em `solicitar_llm_modo_headless()`: ao retornar a resposta, incluir `"origem_medicao": "medido_api"` quando `tokens` (de `resposta.usage.total_tokens`) não for `None`; `"origem_medicao": "indisponivel"` quando o provedor não retornar `usage` (`tokens is None`).
1.3. Teste real: chamar `solicitar_llm_modo_delegado()` com um arquivo de resposta simulado (sem o campo novo, como uma ADE real hoje escreveria) e confirmar que o retorno inclui `origem_medicao: "autodeclarado"` de qualquer forma. Chamar `solicitar_llm_modo_headless()` com `litellm.completion` mockado (resposta com e sem `usage`) e confirmar os dois rótulos corretos.

**Fase 2 — Corrigir a legenda falsa nas fases consumidoras**
2.1. Em `02_analisador.py`, `03_designer.py` e `08_implementador.py`: substituir a lógica atual de `'medicao': 'real (litellm...)' if ... else '...'` por uma que leia `origem_medicao` de verdade da(s) resposta(s) de `solicitar_llm()` — nunca inferir "real" a partir de "o número não é `None`".
2.2. Onde uma fase soma tokens de múltiplas chamadas LLM (ex.: `03_designer.py` soma 5 chamadas, `08_implementador.py` soma todas as correções): se QUALQUER uma das chamadas for `autodeclarado`, o total agregado também deve ser rotulado `autodeclarado` (a incerteza da pior parte contamina a soma) — nunca `medido_api` a menos que TODAS as parcelas sejam `medido_api`.
2.3. Confirmar (ler o código, não assumir) o que `05_criador.py` realmente faz antes de decidir se precisa do mesmo tratamento — reportar o que for encontrado.
2.4. Teste real: simular uma fase recebendo 2 respostas, uma `medido_api` e outra `autodeclarado`, confirmar que o rótulo final é `autodeclarado`; simular todas `medido_api`, confirmar rótulo final `medido_api`.

**Fase 3 — Propagar a distinção para os agregadores/relatórios**
3.1. `07_analisador.py`: ao consolidar tokens de todas as fases no relatório de auto-crítica, reportar os totais separados por origem (ex.: "X tokens medidos via API + Y tokens autodeclarados pela ADE") em vez de somar tudo como se tivesse a mesma confiabilidade.
3.2. `web/status_parser.py`: propagar o campo `origem_medicao`/`medicao` de cada fase para a estrutura que o dashboard consome (não precisa redesenhar a UI nesta fase — só garantir que o dado exista para quem for exibir depois).

**Fase 4 — Documentar honestamente a limitação estrutural**
4.1. Atualizar `docs/PRINCIPIO-UNIVERSALIDADE.md`: adicionar uma entrada de FAQ (mesmo estilo já usado no documento) explicando que, no Modo Delegado, o número de tokens é autodeclarado pela ADE que responde e não é verificável de forma independente pelo código local — e que essa é uma limitação estrutural do próprio design (arquivo JSON como protocolo, sem acesso à conta/billing real de quem respondeu), não um bug a corrigir depois.

**Critério de saída (rodar e colar o output real de cada um):**
- Suíte completa de `aidd-generator` (`python -m pytest tests/ -q`) → sem regressão, com os testes novos das Fases 1 e 2 incluídos.
- Teste real de ponta a ponta: rodar uma fase (ex.: `02_analisador.py`) com uma resposta delegada simulada e confirmar que o `_phase_02_index.json` gerado tem o rótulo `autodeclarado` (nunca "real"/"litellm") quando a resposta veio do modo delegado.
- Teste real: rodar a mesma fase em Modo Headless com `litellm` mockado e confirmar rótulo `medido_api`.
- `07_analisador.py` reporta os totais separados por origem — confirmar com um índice de fases misto (algumas medidas, outras autodeclaradas).
- Nenhuma fase, em nenhum caminho de código, gera a string "medição real" ou equivalente para um valor que veio do Modo Delegado — grep de confirmação em todo `scripts/phases/` ao final.

---

## Ordem de execução recomendada

1. Fase 1 (fonte) — sem isso, nada mais tem de onde ler a origem real.
2. Fase 2 (corrigir a legenda falsa) — é o achado mais grave, a prioridade real deste pacote.
3. Fase 3 (propagação para relatórios) — depende das Fases 1-2 já existirem.
4. Fase 4 (documentação) — pode ser feita em paralelo com qualquer uma das anteriores, mas fica por último para documentar o estado final real, não uma promessa.

Escopo cabe em **1 prompt único** (1 ferramenta, `aidd-generator`; nenhuma decisão de arquitetura pendente).

**Aprovado pelo usuário em 05/09/2026.** Prompt de execução abaixo.

---

## Prompt de Execução

> Copie o bloco abaixo integralmente para o agente executor. Autocontido — não pressupõe que ele viu esta conversa.

```
Você vai corrigir um problema real de transparência no protocolo delegado
do aidd-generator (monorepo em C:\Users\trcnologia\Desktop\ecossistema-aidd,
ferramenta em tools/aidd-generator) — hoje o sistema afirma ativamente
"medição real via litellm" para números de tokens que, no Modo Delegado
(o modo padrão), nunca passaram por litellm; são só o que a ADE que
respondeu escreveu no arquivo JSON, sem nenhuma verificação independente
possível. Isto é uma violação da Lei Fundamental de Transparência do
AGENTS.md (zero alucinação em métricas). Siga EXATAMENTE a Definição de
Pronto abaixo, não invente escopo adicional, e valide tudo de verdade
(execuções reais, exit codes reais, nunca mascarados por pipe).

IMPORTANTE — o que este prompt NÃO pede: não é possível, nem é o
objetivo, fazer o Modo Delegado medir tokens de verdade (a ADE externa que
responde pode escrever qualquer número, é uma limitação estrutural do
protocolo baseado em arquivo JSON). O objetivo é parar de MENTIR sobre a
origem do número — rotular honestamente cada valor como medido ou
autodeclarado, nunca afirmar "real" quando não é.

CONTEXTO JÁ INVESTIGADO (não precisa redescobrir, mas confirme lendo o
código antes de cada fase — os números de linha abaixo podem ter mudado
levemente):
- `tools/aidd-generator/scripts/phases/utils_delegacao.py`:
  `solicitar_llm_modo_delegado()` (por volta da linha 233) retorna o dict
  de resposta como veio do arquivo JSON escrito pela ADE — `tokens_consumidos`
  nunca é medido localmente. `solicitar_llm_modo_headless()` (por volta da
  linha 295) mede de verdade via `resposta.usage.total_tokens` da chamada
  real a `litellm.completion()`. Os dois retornam a MESMA forma de dict
  hoje (`conteudo`, `tokens_consumidos`, `modelo_usado`,
  `timestamp_resposta`) — nada distingue a origem.
- **Achado confirmado, o motivo real deste pacote:** em
  `tools/aidd-generator/scripts/phases/02_analisador.py` (por volta da
  linha 363), a linha
  `'medicao': 'real (litellm resposta.usage.total_tokens)' if tokens_reais is not None else 'nao disponivel (...)'`
  rotula como "real" qualquer valor não-nulo, MESMO quando ele veio do
  Modo Delegado (nunca passou por litellm). O mesmo padrão existe em
  `03_designer.py` (por volta da linha 499,
  `'medicao': 'real (litellm, soma das 5 chamadas)' if ... else '...'`) e
  em `08_implementador.py` (por volta da linha 1321,
  `'medicao': 'real (soma de todas as chamadas LLM, incluindo correções)'`
  — este último nem tem condicional, sempre afirma "real").
- `tools/aidd-generator/scripts/phases/05_criador.py` reporta
  `tokens.consumidos: 0` — padrão diferente das outras 3 fases. Confirme
  você mesmo lendo o código o que essa fase realmente faz antes de decidir
  se ela precisa do mesmo tratamento; relate o que encontrar, não decida
  sozinho se for ambíguo.
- `tools/aidd-generator/scripts/phases/07_analisador.py` (auto-crítica)
  soma `tokens.consumidos` de todas as fases sem nenhuma distinção de
  origem — herda o problema, não o cria.
- `tools/aidd-generator/web/status_parser.py` (por volta da linha 182) lê
  `tokens.consumidos` de cada índice de fase para exibir num dashboard —
  mesma ausência de distinção.
- `tools/aidd-generator/docs/PRINCIPIO-UNIVERSALIDADE.md` já documenta o
  protocolo delegado com um estilo honesto (seção FAQ existente, por volta
  da linha 225, com perguntas sobre timeout e tamanho de payload) — segue
  o mesmo estilo ao adicionar a entrada nova.
- Existem arquivos de cache reais em
  `tools/aidd-generator/scripts/.aidd/cache/_llm_response_*.json` — são
  respostas históricas reais do protocolo delegado (úteis como exemplo do
  formato real, mas NÃO são fixtures de teste — não os edite nem os use
  como entrada de teste, são artefatos de uso real do produto).

DECISÕES JÁ TOMADAS (não reabra estas discussões):
1. Não tente fazer o Modo Delegado medir tokens de verdade — é
   estruturalmente impossível. O objetivo é rotular honestamente a
   origem, não eliminar a limitação.
2. O campo novo se chama `origem_medicao`, com 3 valores possíveis:
   `"autodeclarado"` (Modo Delegado, sempre), `"medido_api"` (Modo
   Headless, quando o provedor retornou `usage`), `"indisponivel"` (Modo
   Headless, quando o provedor não retornou `usage`).
3. Quando uma fase soma tokens de múltiplas chamadas LLM: se QUALQUER
   parcela for `autodeclarado`, o total agregado também é `autodeclarado`
   — a incerteza da pior parte contamina a soma. Só é `medido_api` se
   TODAS as parcelas forem `medido_api`.

DEFINIÇÃO DE PRONTO — nesta ordem:

FASE 1 — Origem da medição na fonte (`utils_delegacao.py`)
1.1. Em `solicitar_llm_modo_delegado()`: garanta que o dict retornado
     sempre contenha `"origem_medicao": "autodeclarado"` — inserido pelo
     código local, sobrescrevendo qualquer valor que a ADE externa tenha
     escrito nesse campo (se ela escrever algo), já que por definição
     este modo nunca é medido de forma independente.
1.2. Em `solicitar_llm_modo_headless()`: inclua `"origem_medicao":
     "medido_api"` quando `tokens` (de `resposta.usage.total_tokens`) não
     for `None`; `"origem_medicao": "indisponivel"` quando for `None`.
1.3. Teste real: chame `solicitar_llm_modo_delegado()` com um arquivo de
     resposta simulado SEM o campo novo (como uma ADE real hoje
     escreveria, sem conhecer esse campo) e confirme que o retorno inclui
     `origem_medicao: "autodeclarado"` mesmo assim. Chame
     `solicitar_llm_modo_headless()` com `litellm.completion` mockado (um
     teste com resposta incluindo `usage`, outro sem `usage`) e confirme
     os dois rótulos corretos.

FASE 2 — Corrigir a legenda falsa nas fases consumidoras
2.1. Em `02_analisador.py`, `03_designer.py` e `08_implementador.py`:
     substitua a lógica atual de `'medicao': 'real (litellm...)' if ...
     else '...'` por uma que leia `origem_medicao` de verdade da(s)
     resposta(s) de `solicitar_llm()` — nunca infira "real" a partir de
     "o número não é `None`".
2.2. Aplique a regra de contaminação da Decisão 3 onde uma fase soma
     tokens de múltiplas chamadas (`03_designer.py` soma 5 chamadas,
     `08_implementador.py` soma todas as correções).
2.3. Leia `05_criador.py` e confirme o que ele realmente faz com tokens
     antes de decidir se precisa do mesmo tratamento — relate o achado
     explicitamente no seu entregável, não decida sozinho se a evidência
     for ambígua.
2.4. Teste real: simule uma fase recebendo 2 respostas de
     `solicitar_llm()`, uma `medido_api` e outra `autodeclarado`, confirme
     que o rótulo final agregado é `autodeclarado`; simule todas
     `medido_api`, confirme rótulo final `medido_api`.

FASE 3 — Propagar a distinção para os agregadores/relatórios
3.1. Em `07_analisador.py`: ao consolidar tokens de todas as fases no
     relatório de auto-crítica, reporte os totais separados por origem
     (ex.: "X tokens medidos via API + Y tokens autodeclarados pela
     ADE") em vez de somar tudo como se tivesse a mesma confiabilidade.
3.2. Em `web/status_parser.py`: propague o campo `origem_medicao`/rótulo
     de cada fase para a estrutura que o dashboard consome (não precisa
     redesenhar a UI nesta fase — só garanta que o dado exista para quem
     for exibir depois).

FASE 4 — Documentar honestamente a limitação estrutural
4.1. Atualize `docs/PRINCIPIO-UNIVERSALIDADE.md`: adicione uma entrada de
     FAQ (mesmo estilo do documento) explicando que, no Modo Delegado, o
     número de tokens é autodeclarado pela ADE que responde e não é
     verificável de forma independente pelo código local — e que essa é
     uma limitação estrutural do próprio design (arquivo JSON como
     protocolo, sem acesso à conta/billing real de quem respondeu), não
     um bug a corrigir depois.

CRITÉRIO DE SAÍDA (rode e cole o output real de cada um):
- Suíte completa de `aidd-generator` (`python -m pytest tests/ -q`) →
  sem regressão, com os testes novos das Fases 1 e 2 incluídos.
- Teste real de ponta a ponta: rode uma fase (ex.: `02_analisador.py`)
  com uma resposta delegada simulada e confirme que o
  `_phase_02_index.json` gerado tem o rótulo `autodeclarado` (nunca
  "real"/"litellm") quando a resposta veio do modo delegado.
- Teste real: rode a mesma fase em Modo Headless com `litellm` mockado e
  confirme rótulo `medido_api`.
- `07_analisador.py` reporta os totais separados por origem — confirme
  com um índice de fases misto (algumas medidas, outras autodeclaradas).
- Rode `grep -rn "medicao.*real\|real.*litellm" tools/aidd-generator/scripts/phases/`
  ao final e confirme que nenhuma ocorrência remanescente afirma "real"
  incondicionalmente ou a partir só de "não é None" — cole o output real
  do grep.

REGRAS DE ESCOPO — NÃO FAÇA:
- Não tente fazer o Modo Delegado medir tokens de verdade — isso é
  estruturalmente impossível e não é o que este pacote pede.
- Não edite nem use como fixture de teste os arquivos reais em
  `scripts/.aidd/cache/_llm_response_*.json` — são artefatos de uso real
  do produto, não dados de teste.
- Não toque em `aidd-master`, `aidd-enterprise` nem `aidd-forge` — este
  pacote é só `aidd-generator`.
- Não faça `git commit` nem `git push`.
- Não altere
  `docs/planos/evolucao-notas-auditoria/05-economia-tokens-e-agentico.md`.

ENTREGÁVEL: lista exata de arquivos criados/alterados; para cada fase,
comando + output real que comprova; o que você encontrou em
`05_criador.py` (item 2.3) e a decisão tomada, reportada explicitamente;
qualquer desvio necessário, reportado explicitamente em vez de decidido
sozinho.
```

## Prompt de Execução — English version

```
You are going to fix a real transparency problem in aidd-generator's
delegated LLM protocol (monorepo at
C:\Users\trcnologia\Desktop\ecossistema-aidd, tool at
tools/aidd-generator) — today the system actively claims "real
measurement via litellm" for token numbers that, in Delegated Mode (the
default mode), never went through litellm at all; they are just whatever
the ADE that responded wrote into the JSON file, with no independent
verification possible. This is a violation of AGENTS.md's Fundamental
Law of Transparency (zero hallucination in metrics). Follow the
Definition of Done below EXACTLY, do not invent additional scope, and
validate everything for real (real runs, real exit codes, never masked
by a pipe).

IMPORTANT — what this prompt does NOT ask for: it is not possible, nor
is it the goal, to make Delegated Mode actually measure tokens for real
(the external ADE that responds can write any number it wants — it's a
structural limitation of the JSON-file-based protocol). The goal is to
stop LYING about the number's origin — honestly label every value as
measured or self-declared, never claim "real" when it isn't.

ALREADY-INVESTIGATED CONTEXT (no need to rediscover, but confirm by
reading the code before each phase — the line numbers below may have
shifted slightly):
- `tools/aidd-generator/scripts/phases/utils_delegacao.py`:
  `solicitar_llm_modo_delegado()` (around line 233) returns the response
  dict exactly as it came from the JSON file written by the ADE —
  `tokens_consumidos` is never measured locally. `solicitar_llm_modo_headless()`
  (around line 295) measures it for real via `resposta.usage.total_tokens`
  from the actual `litellm.completion()` call. Both return the SAME dict
  shape today (`conteudo`, `tokens_consumidos`, `modelo_usado`,
  `timestamp_resposta`) — nothing distinguishes the origin.
- **Confirmed finding, the real reason for this package:** in
  `tools/aidd-generator/scripts/phases/02_analisador.py` (around line
  363), the line
  `'medicao': 'real (litellm resposta.usage.total_tokens)' if tokens_reais is not None else 'nao disponivel (...)'`
  labels any non-null value as "real", EVEN when it came from Delegated
  Mode (never went through litellm). The same pattern exists in
  `03_designer.py` (around line 499,
  `'medicao': 'real (litellm, soma das 5 chamadas)' if ... else '...'`)
  and in `08_implementador.py` (around line 1321,
  `'medicao': 'real (soma de todas as chamadas LLM, incluindo correções)'`
  — this last one has no conditional at all, it always claims "real").
- `tools/aidd-generator/scripts/phases/05_criador.py` reports
  `tokens.consumidos: 0` — a different pattern from the other 3 phases.
  Confirm yourself by reading the code what this phase actually does
  before deciding whether it needs the same treatment; report what you
  find, do not decide alone if the evidence is ambiguous.
- `tools/aidd-generator/scripts/phases/07_analisador.py`
  (auto-critique) sums `tokens.consumidos` across all phases with no
  origin distinction at all — it inherits the problem, doesn't create it.
- `tools/aidd-generator/web/status_parser.py` (around line 182) reads
  `tokens.consumidos` from each phase index to display on a dashboard —
  same lack of distinction.
- `tools/aidd-generator/docs/PRINCIPIO-UNIVERSALIDADE.md` already
  documents the delegated protocol with an honest style (existing FAQ
  section, around line 225, with questions about timeout and payload
  size) — follow the same style when adding the new entry.
- Real cache files exist at
  `tools/aidd-generator/scripts/.aidd/cache/_llm_response_*.json` — these
  are real historical responses from the delegated protocol (useful as a
  reference for the real format, but NOT test fixtures — do not edit them
  or use them as test input, they are real product-usage artifacts).

DECISIONS ALREADY MADE (do not reopen these):
1. Do not try to make Delegated Mode measure tokens for real — it is
   structurally impossible. The goal is to honestly label the origin,
   not eliminate the limitation.
2. The new field is called `origem_medicao`, with 3 possible values:
   `"autodeclarado"` (Delegated Mode, always), `"medido_api"` (Headless
   Mode, when the provider returned `usage`), `"indisponivel"` (Headless
   Mode, when the provider did not return `usage`).
3. When a phase sums tokens across multiple LLM calls: if ANY part is
   `autodeclarado`, the aggregated total is also `autodeclarado` — the
   worst part's uncertainty contaminates the sum. It's only `medido_api`
   if ALL parts are `medido_api`.

DEFINITION OF DONE — in this order:

PHASE 1 — Measurement origin at the source (`utils_delegacao.py`)
1.1. In `solicitar_llm_modo_delegado()`: ensure the returned dict always
     contains `"origem_medicao": "autodeclarado"` — inserted by local
     code, overwriting any value the external ADE may have written in
     that field (if it writes one), since by definition this mode is
     never independently measured.
1.2. In `solicitar_llm_modo_headless()`: include `"origem_medicao":
     "medido_api"` when `tokens` (from `resposta.usage.total_tokens`) is
     not `None`; `"origem_medicao": "indisponivel"` when it is `None`.
1.3. Real test: call `solicitar_llm_modo_delegado()` with a simulated
     response file WITHOUT the new field (as a real ADE would write
     today, unaware of this field) and confirm the return includes
     `origem_medicao: "autodeclarado"` regardless. Call
     `solicitar_llm_modo_headless()` with `litellm.completion` mocked
     (one test with a response including `usage`, another without
     `usage`) and confirm both correct labels.

PHASE 2 — Fix the false label in the consuming phases
2.1. In `02_analisador.py`, `03_designer.py`, and `08_implementador.py`:
     replace the current `'medicao': 'real (litellm...)' if ... else
     '...'` logic with one that reads the real `origem_medicao` from
     `solicitar_llm()`'s response(s) — never infer "real" from "the
     number is not `None`".
2.2. Apply the Decision 3 contamination rule wherever a phase sums
     tokens across multiple calls (`03_designer.py` sums 5 calls,
     `08_implementador.py` sums all corrections).
2.3. Read `05_criador.py` and confirm what it actually does with tokens
     before deciding whether it needs the same treatment — explicitly
     report the finding in your deliverable, do not decide alone if the
     evidence is ambiguous.
2.4. Real test: simulate a phase receiving 2 responses from
     `solicitar_llm()`, one `medido_api` and one `autodeclarado`, confirm
     the final aggregated label is `autodeclarado`; simulate all
     `medido_api`, confirm the final label is `medido_api`.

PHASE 3 — Propagate the distinction to aggregators/reports
3.1. In `07_analisador.py`: when consolidating tokens across all phases
     in the auto-critique report, report the totals split by origin
     (e.g. "X tokens measured via API + Y tokens self-declared by the
     ADE") instead of summing everything as if it had the same
     reliability.
3.2. In `web/status_parser.py`: propagate the `origem_medicao`/label
     field from each phase into the structure the dashboard consumes (no
     need to redesign the UI in this phase — just ensure the data exists
     for whoever displays it later).

PHASE 4 — Honestly document the structural limitation
4.1. Update `docs/PRINCIPIO-UNIVERSALIDADE.md`: add a FAQ entry (same
     style as the document) explaining that, in Delegated Mode, the
     token number is self-declared by the responding ADE and cannot be
     independently verified by local code — and that this is a
     structural limitation of the design itself (a JSON file as the
     protocol, with no access to the real account/billing of whoever
     responded), not a bug to fix later.

EXIT CRITERIA (run and paste the real output of each):
- Full `aidd-generator` suite (`python -m pytest tests/ -q`) → no
  regression, with the new Phase 1 and 2 tests included.
- Real end-to-end test: run a phase (e.g. `02_analisador.py`) with a
  simulated delegated response and confirm the generated
  `_phase_02_index.json` has the `autodeclarado` label (never
  "real"/"litellm") when the response came from delegated mode.
- Real test: run the same phase in Headless Mode with `litellm` mocked
  and confirm the `medido_api` label.
- `07_analisador.py` reports totals split by origin — confirm with a
  mixed phase index (some measured, some self-declared).
- Run `grep -rn "medicao.*real\|real.*litellm" tools/aidd-generator/scripts/phases/`
  at the end and confirm no remaining occurrence unconditionally claims
  "real" or infers it just from "not None" — paste the real grep output.

SCOPE RULES — DO NOT:
- Do not try to make Delegated Mode measure tokens for real — that is
  structurally impossible and not what this package asks for.
- Do not edit or use as test fixtures the real files at
  `scripts/.aidd/cache/_llm_response_*.json` — they are real
  product-usage artifacts, not test data.
- Do not touch `aidd-master`, `aidd-enterprise`, or `aidd-forge` — this
  package is `aidd-generator` only.
- Do not `git commit` or `git push`.
- Do not modify
  `docs/planos/evolucao-notas-auditoria/05-economia-tokens-e-agentico.md`.

DELIVERABLE: exact list of files created/changed; for each phase, the
command + real output that proves it; what you found in `05_criador.py`
(item 2.3) and the decision made, explicitly reported; any necessary
deviation, explicitly reported instead of decided by yourself.
```

---

## Veredito — Auditoria do Prompt de Execução

**Auditoria independente realizada — não me baseei no relatório do agente executor.**

**Confirmado correto, por reprodução ao vivo, fora dos arquivos de teste do executor:**
- **Fase 1:** os testes cobrem os 2 modos corretamente, incluindo um teste extra não pedido mas bem-vindo — confirma que o código sobrescreve mesmo se a ADE alegar (por erro ou má-fé) `origem_medicao: "medido_api"` no modo delegado.
- **Fase 2:** reproduzi eu mesmo, chamando `02_analisador.py` diretamente com uma resposta simulada de modo delegado (`origem_medicao: "autodeclarado"`) — o `index['tokens']` gerado veio com `origem_medicao: "autodeclarado"` e `medicao` sem nenhuma menção a "real"/"litellm". Repeti com uma resposta estilo headless (`"medido_api"`) — rótulo `medido_api` correto, com "litellm" na descrição. A regra de contaminação (`03_designer.py`/`08_implementador.py`) está corretamente implementada e testada (mistura de origens → `autodeclarado`; todas `medido_api` → `medido_api`).
- **`05_criador.py`:** confirmei via grep independente que este arquivo NUNCA chama `solicitar_llm` — a única ocorrência de `tokens_consumidos` é uma coluna SQL sem relação. A decisão do executor de não tocar nele está correta.
- **Fase 3:** `07_analisador.py` agora separa os totais por origem, tanto no relatório markdown quanto no índice JSON, com fallback sensato para dados de fases antigas sem o campo novo. `status_parser.py` propaga o campo para a estrutura que o dashboard consome.
- **Fase 4:** `PRINCIPIO-UNIVERSALIDADE.md` documenta a limitação honestamente, no mesmo estilo de FAQ já usado no documento.
- **Critério de saída do grep:** reproduzi eu mesmo — `grep -rn "medicao.*real\|real.*litellm" tools/aidd-generator/scripts/phases/` → zero ocorrências.
- Sem regressão: suíte de `aidd-generator` 757→765 (+8 testes: 4 em `test_utils_delegacao.py`, 4 em `test_transparencia_tokens.py` novo). `ecossistema.py audit` (bateria raiz) exit 0, 6/6 gates.
- Sem poluição do repositório. Regras de escopo respeitadas: nenhuma outra ferramenta tocada (`aidd-master`, `aidd-enterprise`, `aidd-forge` intocados); arquivos de cache reais (`_llm_response_*.json`) intocados; nenhum commit feito; documento do pacote intocado.

**Notável:** quarto pacote consecutivo (depois do 3 e do 4) a fechar de primeira, sem nenhuma correção necessária — e desta vez corrigindo um achado que na minha própria reverificação se revelou mais grave do que o diagnóstico original previa (legenda ativamente falsa, não só ausência de distinção).

### Nota Final — Pacote 5 (Economia de Tokens + Engenharia Agêntica): 9.5/10

**Por que 9.5, não 10:**
- As 4 fases foram implementadas corretamente na primeira tentativa, incluindo o tratamento correto da regra de contaminação (parte mais fácil de fazer sutilmente errado) e a decisão correta de não tocar em `05_criador.py`.
- A violação mais grave (afirmação incondicional de "real" em `08_implementador.py`) foi corrigida e comprovada por teste dedicado, não só pela remoção da frase.
- **0.5 de desconto:** não reproduzi manualmente 100% dos 8 cenários de teste novos (verifiquei uma amostra representativa de alto risco — os dois fluxos de ponta a ponta mais importantes — e rodei a suíte completa + o grep de confirmação final); e a limitação estrutural em si (tokens autodeclarados no modo delegado nunca são verificáveis) continua existindo por design — não é uma falha deste pacote, é o teto já reconhecido antes de começar.
- **Efeito nas dimensões:** Economia de Tokens 7→**8/10** (alvo do plano original atingido — a limitação agora é honestamente rotulada, não escondida). Engenharia Agêntica Aplicada 8→**8.5/10** (alvo atingido — o protocolo delegado em si já funcionava bem, a correção fecha a lacuna de transparência que o cercava).
