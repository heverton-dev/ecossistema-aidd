# Auditoria de Etapa: Abertos da ETAPA 09 — tokens da spec (9-A), passo a passo por harness (9-B) e `.codebuddy` (9-C)

> **EXECUTADO EM MODO AUTÔNOMO (`/goal`, 14/10/2026).** O usuário pediu "quero resolver os abertos" e, durante a execução, ajustou o escopo do 9-B: "mapeie: mimo, agy, opencode, claude, omp" e "preciso que o passo a passo do claude code esteja mapeado e testado tambem". As demais decisões técnicas foram minhas, uma a uma, e estão marcadas como "Decisão autônoma".

Fecha os Tickets 9-A, 9-B e 9-C da ETAPA_09. Correção feita no motor original (branch `fix/pure-etapa-12-abertos-da-09`, commit `8ec1c08e`, no GitHub) e espelhada neste clone por patch.

### [RECURSO]: 9-A — tipografia, raios e espaçamentos vêm da spec
- **Ordem de Execução:** primeiro o teste (Red), depois o código.
- **Ação Executada:** a Visual Direction da spec aceita `fonte` (nome da família), `raio` (`reto|suave|arredondado`) e `densidade` (`compacta|confortavel|ampla`), todos opcionais. `design_system.tokens_da_direcao` converte em `tipografia.font_sans`, `raios_borda` e `espacamentos`; `intake.erros_do_bloco_visual` reprova valor fora do conjunto (e fonte com caracteres fora de letras, números, espaço e hífen, contra injeção); o `DESIGN-SYSTEM.json` ganha `tokens_da_direcao` com `declarado_na_spec` e `convencao` (o que a spec não declarou).
- **Entrega / Artefato Gerado:** `tests/test_direcao_visual_tokens.py` (14 testes).
  - *Caminho Exato (100% concluído):* `modulos/01-governanca-e-qualidade/core/aidd-planner/src/core_planner/{design_system,intake}.py`.
- **Status & Diagnóstico:**
  - *Sucesso:* Sim. Red: erro de coleta (`tokens_da_direcao` inexistente). Green: 14 passed.
  - *Decisão autônoma:* campos opcionais (a spec antiga continua válida) e nada inventado quando faltam: ficam declarados como "convenção".
  - *Limite:* a cor continua vindo da imagem; o que a imagem não informa agora vem da spec, mas só se a spec disser.

### [RECURSO]: 9-B — passo a passo do Mobbin por harness, mapeado e testado
- **Ação Executada:** verificação feita nesta máquina, harness por harness, e o `ambiente.py` agora marca cada passo a passo com o nível de verificação (`executado`, `help`, `binario`, `documentacao`):
  - **claude (executado):** `claude mcp add --transport http <nome> https://api.mobbin.com/mcp` → "Added HTTP MCP server"; `claude mcp get` → status `Needs authentication` (o OAuth é o passo seguinte); `claude mcp remove` → some. O servidor `mobbin` já registrado estava `Connected` e uma busca real pelo MCP (`search_screens`) devolveu 2 telas.
  - **agy (executado):** `agy mcp add <nome> <url>` → "(http)" detectado pela URL; `list` mostra; `remove` desfaz.
  - **mimo (help):** `mimo mcp add` (interativo), `auth [name]`, `list`, `logout`, `debug` existem; `mimo mcp list` mostra o `mobbin` como "needs authentication". A ajuda sai no stderr fora de um terminal.
  - **opencode (documentação):** **não existe `opencode mcp add`**; o servidor entra no `opencode.json` (`type: remote`) e `opencode mcp auth <nome>` autoriza. A instalação local está quebrada ("postinstall script was not run"), então nada foi executado. Não corrigi a instalação do usuário.
  - **omp (binário):** **não tem subcomando `mcp`** (`omp mcp` cai no `launch`); os comandos são de barra dentro do omp: `/mcp add <nome> [--scope project|user] [--url <url> --transport http|sse] [--token <token>] [-- <comando>]`, `/mcp reauth <nome>`, `/mcp list`, `/mcp enable`. Lidos do binário; interativos, não executados.
  - **gemini-cli (documentação):** `gemini mcp add --transport http …` e `/mcp auth <nome>`; não está instalado; a documentação diz que foi substituído pelo Antigravity CLI em 18/06/2026.
- **Entrega / Artefato Gerado:** `tests/test_ambiente_harnesses.py` (17 testes: 14 de mapa e detecção; 3 reais — claude add/get/remove, agy add/list/remove, mimo help — atrás de `AIDD_TESTE_HARNESS_REAL=1`, com nome descartável e `finally` desfazendo); `AIDD_TESTE_HARNESS_REAL` documentada no `.env.example`; skill `aidd-planner` e 6 espelhos documentam os passos.
- **Status & Diagnóstico:**
  - *Sucesso:* Sim, com limites declarados. Planner no clone: **138 passed** (com os 3 reais ligados); sem a variável: 135 passed, 3 skipped.
  - *Decisão autônoma:* detectar o omp só por variáveis exatas (`OMP_PLUGIN_ROOT`, `OMP_PROFILE`, `OMP_AUTH_BROKER_URL`, `OMP_MCP_TIMEOUT_MS`), porque `OMP_NUM_THREADS` é do OpenMP; dentro do Claude Code vale o Claude Code. As variáveis do omp foram lidas do binário, **não** observadas numa sessão real dele.
  - *Falhas / Anomalias:* o primeiro teste real do mimo falhou porque o yargs escreve a ajuda no stderr fora de um terminal; corrigido juntando stdout e stderr.

### [RECURSO]: 9-C — `.codebuddy/` local
- **Ação Executada:** `.codebuddy/skills/aidd-planner/SKILL.md` copiado da fonte da branch e `.codebuddy/commands/planner.md` de `git show HEAD:.claude/commands/planner.md` (não versionado; `G_HARNESS_COMPAT` exige).
- **Status & Diagnóstico:** Sim.

## TICKETS
- **Resolvidos neste relatório:** 9-A, 9-B (nos limites abaixo), 9-C.
- **Ticket 12-A: a autorização OAuth não foi exercitada em nenhum harness — ABERTO:** só o registro do servidor foi provado; autorizar exige o navegador do usuário. *Red:* após `claude mcp add`, `claude mcp get` sai com `Connected`. *Prompt (EN):* Run the Mobbin OAuth flow once per supported harness with the user present, then record the post-auth status next to each step-by-step.
- **Ticket 12-B: opencode e omp não executados — ABERTO:** o opencode local tem o postinstall quebrado e o omp só tem comandos de barra interativos. *Prompt (EN):* Reinstall opencode without --ignore-scripts and run `opencode mcp auth` against a throwaway server; drive omp's `/mcp add` through its print mode in a test.
