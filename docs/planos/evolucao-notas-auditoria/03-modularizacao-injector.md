# Pacote 3 — Modularização (Divergência do Injector)

> **Status:** ✅ CONCLUÍDO em 05/09/2026 — nota final 9.5/10 (ver Veredito ao final do documento).
> **Origem:** `docs/planos/PLANO-EVOLUCAO-NOTAS-AUDITORIA.md` §4 (Fase 3) — divergência de capacidade entre os injectors de `aidd-master` e `aidd-enterprise`.
> **Contribui para:** dimensão Modularização (7→9/10).

---

## Verificação independente que já fiz (o diagnóstico original não é mais suficiente sozinho)

Reconfirmei a divergência original e encontrei uma camada extra que muda a resposta técnica certa:

1. **Confirmado, ainda válido:** `tools/aidd-enterprise/scripts/injector/aidd_core_injector.py` (262 linhas) suporta `VALID_TYPES = ("skill", "mcp", "rule", "spec", "config", "hook", "agent")` — 7 tipos — e tem `--mcp-command` real no CLI (`scripts/aidd.py:1047`). `tools/aidd-master/src/core/profiles_registry.py` só suporta `TIPOS_VALIDOS = ("skill", "mcp", "rule", "spec", "config", "agent")` — 6 tipos, sem `hook` — e `aidd-master/scripts/aidd.py` não tem `--mcp-command` em nenhum lugar.
2. **Achado novo (não estava no diagnóstico original):** desde esse diagnóstico, `aidd-master` ganhou uma arquitetura de injector **mais nova e mais limpa** que o próprio `aidd_core_injector.py` monolítico de `aidd-enterprise` — `profiles_registry.py` (matriz de perfis) + `detector_camada.py` (construção/validação do payload) + `materializador.py` (escrita transacional com rollback) + `sincronizador_harness.py` (sync multi-harness) + `result.py` (tipo `Result` compartilhado). Confirmei que `tools/aidd-master/implementacao/PLANO-ORQUESTRACAO-ORCA3-UNIVERSAL-INJECTOR.md` e o equivalente em `aidd-enterprise` são **byte-idênticos** (`diff` sem saída) — ou seja, existe UM plano canônico de arquitetura para os dois, e só `aidd-master` o implementou; `aidd-enterprise` ainda roda o injector antigo, pré-plano.
3. **Achado ainda mais importante — os dois tipos `mcp` não significam a mesma coisa:**
   - Em `aidd-master`, o tipo `mcp` gera um arquivo Python (`src/core/mcp/{nome}.py`) carregado **dinamicamente em processo** por `MCPServer.register_injected_tools()` — mecanismo proprietário, específico da implementação própria de servidor MCP do `aidd-master`.
   - Em `aidd-enterprise`, o tipo `mcp` (com `--mcp-command`) grava/mescla uma entrada em `mcp.json` na raiz do projeto, no formato **padrão** `{"mcpServers": {"<nome>": {"command", "args", "env"}}}` — o mesmo formato que harnesses reais (Claude Code, etc.) usam para descobrir servidores MCP externos. Este é o mecanismo mais alinhado com a Regra de Ouro #6 (Supremacia Agnóstica) — registro portável, não proprietário.
   - **Não são a mesma funcionalidade com nomes diferentes — são duas funcionalidades diferentes que hoje colidem no mesmo nome de tipo.** Precisam coexistir, não uma substituir a outra (`aidd-master` já tem usuários/testes dependendo do comportamento atual de `mcp` como ferramenta em processo).
4. **Confirmado, ainda válido:** o tipo `hook` de `aidd-enterprise` (`target_profile.py`) grava `{harness_dir}/{nome}.json` em múltiplas pastas de harness fixas (`HARNESS_HOOK_DIRS`) — exatamente o padrão de distribuição multi-harness que o **Pacote 7 já resolveu de forma canônica e testada** via `componentes/<ferramenta>/<tipo>/` + `gestor_componentes.py sync/verify`. Copiar o mecanismo antigo de `aidd-enterprise` (escrita direta em múltiplas pastas fixas) reintroduziria exatamente o padrão que o Pacote 7 existe para eliminar. `aidd-master`'s próprio injector, hoje, **não chama** `gestor_componentes`/`components sync` para nenhum tipo — isso já era uma limitação residual documentada e aceita no Pacote 7 (fora de escopo lá).
5. **Confirmado, ainda válido:** `gates/G_DRIFT_NUCLEO_COMPARTILHADO.py`'s `_arquivos_comuns()` retorna só a interseção de nomes de arquivo `.py` presentes nos dois lados (`nomes_a & nomes_b`) — um arquivo removido de um lado nunca é comparado, então a divergência de subsistema inteiro (como a deste próprio pacote) não teria sido detectada automaticamente por esse gate.

---

## Decisão de arquitetura (meu parecer técnico, registrado para sua aprovação — não decidi sozinho, é isto que você está aprovando)

**Não é mais um "A ou B ou C" simples como no diagnóstico original.** Minha recomendação, dada a descoberta acima:

- **NÃO copiar `aidd_core_injector.py` (262 linhas monolíticas) para dentro de `aidd-master`** — isso reintroduziria duplicação de código E traria de volta o padrão de distribuição multi-harness que o Pacote 7 já eliminou.
- **Estender a arquitetura já-canônica de `aidd-master`** (`profiles_registry.py`/`detector_camada.py`/`materializador.py`/`sincronizador_harness.py`) para fechar a lacuna de capacidade real, usando a infraestrutura que já existe:
  - **Tipo `hook` (novo em `aidd-master`):** fonte canônica `componentes/aidd-master/hooks/{nome}/...`, propagado via `gestor_componentes.py sync` (mesma mecânica que `aidd-forge`/`aidd-generator` já usam desde o Pacote 7) — não escrita direta em pastas fixas de harness.
  - **Tipo `mcp` (comportamento existente preservado, capacidade nova adicionada):** se o payload não incluir `command`, comportamento idêntico ao atual (arquivo Python em processo, sem mudança — zero regressão para quem já usa `mcp` hoje). Se o payload incluir `command` (novo, opcional, equivalente ao `--mcp-command` de `aidd-enterprise`), grava/mescla uma entrada em `mcp.json` na raiz, **no mesmo formato exato** que `aidd-enterprise` já usa (`{"mcpServers": {nome: {command, args, env}}}`) — consistência entre ferramentas, não reinvenção de formato.
  - **CLI (`scripts/aidd.py`):** adicionar `"hook"` à lista `choices` de `p_inject`; adicionar `--mcp-command`, `--mcp-args` (JSON list, opcional) e `--mcp-env` (JSON dict, opcional) aos argumentos de `inject`.
- **Independente da decisão acima:** corrigir o ponto cego do gate de drift (`G_DRIFT_NUCLEO_COMPARTILHADO.py`) — se um arquivo do baseline com `esperado_identico: true` desaparecer de um dos lados, o gate reprova, em vez de simplesmente não ter nada para comparar.
- **Fora de escopo deste pacote, registrado para o futuro:** migrar `aidd-enterprise` para a mesma arquitetura canônica (aposentando `aidd_core_injector.py` de vez) — não faço isso agora para não inflar o escopo; fica como próximo incremento natural, na mesma nota já registrada como limitação residual do Pacote 7.

**Preciso que você confirme esta abordagem (em vez das opções A/B/C originais) antes de eu escrever o prompt de execução.**

---

## Definição de Pronto

**Fase 1 — Tipo `hook` em `aidd-master`, via mecanismo canônico do Pacote 7**
1.1. Adicionar `"hook"` a `TIPOS_VALIDOS` em `detector_camada.py`/`profiles_registry.py`, com perfil de destino `componentes/aidd-master/hooks/{nome}/...` (mesma convenção de pasta-por-componente já usada por `skill`).
1.2. Em `materializador.py`, ao materializar um componente `hook`, gravar na fonte canônica (`componentes/aidd-master/hooks/{nome}/...`) e então chamar `gestor_componentes.py sync --tipo hook --ferramenta aidd-master` (mesmo padrão de integração que `aidd-forge`/`aidd-generator` usam desde a Fase 4 do Pacote 7 — reaproveitar o código já existente lá, não reinventar).
1.3. Adicionar `"hook"` aos `choices` de `p_inject` em `scripts/aidd.py`.
1.4. Teste real: injetar um hook via `aidd inject hook <nome>`, confirmar que aparece em `componentes/aidd-master/hooks/<nome>/...` E propagado para as pastas de harness declaradas no manifesto (`python ecossistema.py components verify --tipo hook --ferramenta aidd-master` exit 0). Limpar o componente de teste ao final.

**Fase 2 — Capacidade `mcp` com `command` (registro externo via `mcp.json`)**
2.1. Estender o payload de `construir_request`/`materializador.py` para aceitar campos opcionais `command`, `args` (lista), `env` (dict) no tipo `mcp`.
2.2. Quando `command` está presente: gravar/mesclar uma entrada em `mcp.json` na raiz do projeto alvo, no formato `{"mcpServers": {nome: {"command": ..., "args": [...], "env": {...}}}}` — ler o arquivo existente primeiro se houver, preservando outras entradas (mesma lógica de merge que `aidd-enterprise/scripts/injector/target_profile.py` já usa — reaproveitar a lógica, adaptada ao módulo de `aidd-master`).
2.3. Quando `command` está ausente: comportamento idêntico ao atual (arquivo Python em `src/core/mcp/{nome}.py`, carregado por `register_injected_tools()`) — **zero mudança** neste caminho, para não quebrar nada que já depende dele.
2.4. Adicionar `--mcp-command`, `--mcp-args`, `--mcp-env` aos argumentos de `p_inject` em `scripts/aidd.py`; `cmd_inject` só passa esses campos ao payload quando `--mcp-command` for fornecido.
2.5. Teste real: (a) injetar um `mcp` SEM `--mcp-command` e confirmar que o comportamento é idêntico ao pré-existente (arquivo `.py` gerado, nada em `mcp.json`); (b) injetar um `mcp` COM `--mcp-command` e confirmar que `mcp.json` é criado/mesclado corretamente, inclusive testando merge com uma entrada pré-existente de outro servidor (não pode apagar a entrada anterior). Limpar os componentes de teste ao final.

**Fase 3 — Corrigir o ponto cego do gate de drift**
3.1. Em `gates/G_DRIFT_NUCLEO_COMPARTILHADO.py`, adicionar checagem: para cada entrada do baseline com `esperado_identico: true`, se o arquivo não existir mais em um dos dois lados (`DIR_A`/`DIR_B`), o gate reprova (exit 1) reportando qual arquivo desapareceu e de qual lado — em vez de simplesmente não ter nada para comparar (comportamento atual).
3.2. Teste real: remova temporariamente (num teste, não no repositório real) um arquivo de um dos dois lados que hoje está marcado `esperado_identico: true` no baseline, confirme que o gate reprova apontando o arquivo certo, restaure e confirme que volta a passar.

**Critério de saída (rodar e colar o output real de cada um):**
- `python ecossistema.py components verify --tipo hook --ferramenta aidd-master` → exit 0 (após a Fase 1).
- Suíte completa de `aidd-master` (`python -m pytest tests/ -q`) → sem regressão, com os testes novos das Fases 1 e 2 incluídos.
- `python gates/G_DRIFT_NUCLEO_COMPARTILHADO.py` → continua exit 0 no estado real do repositório, e o teste de reprodução da Fase 3.2 confirma que ele genuinamente reprova quando deveria.
- `python ecossistema.py audit` (bateria raiz) → exit 0, sem regressão nos outros 5 gates.
- Nenhum teste novo deixa arquivo fora de `tmp_path`/diretório de teste temporário no repositório real (confirmar via `git status`).

---

## Ordem de execução recomendada

1. Fase 3 (gate de drift) — independente das outras, mais simples, e detecta qualquer divergência futura enquanto as Fases 1/2 ainda estão em andamento.
2. Fase 1 (`hook`) — reaproveita infraestrutura já pronta do Pacote 7, menor risco.
3. Fase 2 (`mcp` com `command`) — maior superfície (merge de JSON existente, dois caminhos de comportamento a preservar).

Dado o tamanho moderado (3 fases, 1 ferramenta só — diferente dos Pacotes 4 e 7, que cobriam as 2 ferramentas), recomendo **1 prompt único** para o agente executor, não dividir em rodadas sequenciais.

**Aprovado pelo usuário em 05/09/2026.** Prompt de execução abaixo.

---

## Prompt de Execução

> Copie o bloco abaixo integralmente para o agente executor. Autocontido — não pressupõe que ele viu esta conversa.

```
Você vai fechar a divergência de capacidade do Injetor Universal entre
`aidd-master` e `aidd-enterprise` no ecossistema-aidd (monorepo em
C:\Users\trcnologia\Desktop\ecossistema-aidd) — hoje `aidd-enterprise`
suporta 7 tipos de componente injetável (incluindo `hook` e registro real
de servidor MCP externo via `--mcp-command`), enquanto `aidd-master` só
suporta 6 tipos, sem `hook` e sem `--mcp-command`. Siga EXATAMENTE a
Definição de Pronto abaixo, não invente escopo adicional, e valide tudo
de verdade (execuções reais, exit codes reais, nunca mascarados por pipe).

CONTEXTO JÁ INVESTIGADO (não precisa redescobrir, mas DEVE confirmar você
mesmo lendo o código antes de cada fase):
- `tools/aidd-master/src/core/profiles_registry.py` define
  `TIPOS_VALIDOS = ("skill", "mcp", "rule", "spec", "config", "agent")` —
  precisa ganhar `"hook"`.
- O Injetor Universal de `aidd-master` é composto por
  `src/core/profiles_registry.py` (matriz de perfis),
  `src/core/detector_camada.py` (`construir_request()`, valida e monta o
  payload), `src/core/materializador.py` (`materializar()`, escrita
  transacional com rollback), `src/core/sincronizador_harness.py`
  (`sincronizar()`) e `src/core/result.py` (tipo `Result` compartilhado).
  `scripts/aidd.py`'s `cmd_inject` (por volta da linha 650) orquestra os
  quatro via `_executar_injecao()`.
- **NÃO CONFUNDIR** este Injetor Universal (o deste pacote) com o
  mecanismo de `componentes/` + `python ecossistema.py components
  sync/verify` criado no Pacote 7 (Agnosticismo de Distribuição de
  Componentes) — são coisas diferentes que agora precisam se conectar
  (ver Fase 1 abaixo), mas não são o mesmo código.
- `gates/manifesto_harnesses.json` (raiz do monorepo, criado no Pacote 7)
  JÁ declara `"hook"` como tipo aplicável ao escopo `aidd-master`
  (`escopos.aidd-master.tipos_aplicaveis` já inclui `"hook"`), com
  `pasta_fonte: "hooks"`, `unidade: "diretorio"`,
  `dest_harness_template: "{prefixo_pasta}/hooks/{nome}"`,
  `harnesses_aplicaveis: ["claude-code", "antigravity", "opencode",
  "mimocode", "gemini-cli"]`. Você NÃO precisa alterar o manifesto — a
  declaração já existe, só falta o Injetor Universal de `aidd-master`
  usá-la.
- O padrão de integração canônica entre um Injetor Universal e o
  mecanismo de `components sync` já existe e funciona em
  `tools/aidd-forge/aidd_forge/core/injector_profiles.py`
  (`resolve_canonical_destination()`, `sincronizar_componente()`,
  `_default_ecossistema_root()`) e é chamado de
  `tools/aidd-forge/aidd_forge/core/materializador.py` (dentro de
  `materializar()`, depois da escrita transacional principal, antes do
  retorno). LEIA esses dois arquivos primeiro — é o padrão de referência
  a replicar para `aidd-master`, adaptado à sua própria estrutura de
  módulos (não copie literalmente, adapte).
- `tools/aidd-enterprise/scripts/injector/target_profile.py` (função
  `build_file_map`, ramo `if tipo == "mcp":`) já implementa a lógica de
  merge de `mcp.json` que você vai replicar na Fase 2 — leia como
  referência de formato, não copie o arquivo inteiro (a estrutura de
  módulos de `aidd-master` é diferente).
- `gates/G_DRIFT_NUCLEO_COMPARTILHADO.py`'s `_arquivos_comuns()` (raiz do
  monorepo) retorna `nomes_a & nomes_b` — só a interseção. Um arquivo
  marcado `esperado_identico: true` no baseline
  (`gates/baseline_nucleo_compartilhado.json`) que suma de um dos lados
  não é detectado hoje.

DECISÕES JÁ TOMADAS (não reabra estas discussões):
1. NÃO copiar `tools/aidd-enterprise/scripts/injector/aidd_core_injector.py`
   (262 linhas monolíticas) para dentro de `aidd-master` — isso
   reintroduziria duplicação de código e o padrão antigo de escrita
   direta multi-pasta que o Pacote 7 já eliminou. Em vez disso, ESTENDER
   a arquitetura já-canônica de `aidd-master` (profiles_registry.py/
   detector_camada.py/materializador.py/sincronizador_harness.py).
2. O tipo `hook` novo em `aidd-master` usa o mecanismo de `componentes/` +
   `gestor_componentes.py sync` (Pacote 7) — NÃO escrita direta em pastas
   fixas de harness como `aidd-enterprise` faz hoje.
3. O tipo `mcp` de `aidd-master` MANTÉM 100% do comportamento atual
   (arquivo Python em processo, carregado por
   `MCPServer.register_injected_tools()`) quando nenhum `command` é
   fornecido — zero regressão. Só GANHA a capacidade nova (registro em
   `mcp.json`) quando `command` é explicitamente fornecido. As duas
   coisas coexistem, uma não substitui a outra.
4. `mcp.json` gerado/mesclado deve usar exatamente o mesmo formato que
   `aidd-enterprise` já usa: `{"mcpServers": {"<nome>": {"command": ...,
   "args": [...], "env": {...}}}}`.

DEFINIÇÃO DE PRONTO — nesta ordem:

FASE 1 — Tipo `hook` via mecanismo canônico do Pacote 7
1.1. Adicione `"hook"` a `TIPOS_VALIDOS` em `profiles_registry.py` (e
     onde mais for necessário para `detector_camada.py` validar/aceitar
     o tipo). Adicione um perfil de destino "local" (o `dest` que a
     ferramenta grava dentro do próprio projeto-alvo) para `hook` — siga
     a convenção já usada por `skill` (pasta dedicada por componente); um
     exemplo razoável seria `.agent/hooks/{nome}/hook.sh`, mas confirme
     você mesmo qual convenção já existe no projeto antes de decidir
     (grep por `hooks/` no repositório de `aidd-master`).
1.2. Em `materializador.py`, depois da escrita transacional principal
     (mesmo ponto onde `aidd-forge`'s `materializador.py` chama
     `resolve_canonical_destination()`/`sincronizar_componente()`),
     adicione o mesmo padrão para `aidd-master`: grave o conteúdo também
     em `componentes/aidd-master/hooks/{nome}/hook.sh` (fonte canônica,
     raiz do monorepo — cuidado com o cálculo do caminho, use o mesmo
     padrão de função isolada e monkeypatchável (`_default_ecossistema_root()`)
     que `aidd-forge` usa, para não repetir o bug de path que já foi
     encontrado e corrigido lá) e então chame
     `python ecossistema.py components sync --tipo hook --ferramenta aidd-master`
     (via subprocess, com fallback de import direto de
     `scripts/gestor_componentes.py`, mesmo padrão de `aidd-forge`).
1.3. Adicione `"hook"` aos `choices` do argumento `tipo` de `p_inject` em
     `scripts/aidd.py`.
1.4. Teste real: rode `python scripts/aidd.py inject hook <nome-teste>
     --descricao "..."` a partir de um diretório de projeto de teste
     (não a raiz do monorepo), confirme que o conteúdo aparece em
     `componentes/aidd-master/hooks/<nome-teste>/hook.sh` (fonte canônica
     REAL do monorepo, não uma cópia errada) e que
     `python ecossistema.py components verify --tipo hook --ferramenta aidd-master`
     retorna exit 0. LIMPE o componente de teste da fonte canônica e de
     toda pasta de harness para onde foi propagado ao final — não deixe
     lixo no repositório (ver achado do Pacote 7 sobre isso, não repita).

FASE 2 — Capacidade `mcp` com `command` (registro em `mcp.json`)
2.1. Estenda `construir_request()` (`detector_camada.py`) para aceitar
     campos opcionais `command` (string), `args` (lista de strings,
     default vazia) e `env` (dict de string→string, default vazio) no
     payload quando `tipo == "mcp"`.
2.2. Em `materializador.py`, quando o payload de tipo `mcp` inclui
     `command`: leia `mcp.json` na raiz do projeto-alvo se existir
     (parseie como JSON; se inválido, retorne erro claro em vez de
     sobrescrever silenciosamente), mescle/adicione a entrada
     `mcpServers[nome] = {"command": ..., "args": [...], "env": {...}}`
     preservando QUALQUER entrada pré-existente de outros servidores, e
     grave de volta. Quando `command` NÃO está presente no payload,
     comportamento idêntico ao atual (arquivo Python em
     `src/core/mcp/{nome}.py`) — não toque nesse caminho.
2.3. Adicione `--mcp-command`, `--mcp-args` (aceite uma string JSON de
     lista, ex.: `--mcp-args '["--flag", "valor"]'`) e `--mcp-env`
     (aceite uma string JSON de objeto) aos argumentos de `p_inject` em
     `scripts/aidd.py`. `cmd_inject` só inclui esses campos no payload
     quando `--mcp-command` for explicitamente fornecido.
2.4. Teste real, 3 casos:
     a) Injete um `mcp` SEM `--mcp-command` — confirme que o
        comportamento é idêntico ao pré-existente (arquivo `.py` gerado
        em `src/core/mcp/{nome}.py`, `mcp.json` NÃO foi criado nem
        tocado).
     b) Injete um `mcp` COM `--mcp-command` num projeto-teste onde
        `mcp.json` ainda não existe — confirme que é criado com a
        entrada certa.
     c) Injete um SEGUNDO `mcp` COM `--mcp-command` no MESMO
        projeto-teste — confirme que a entrada do primeiro servidor
        continua em `mcp.json` (merge, não sobrescrita).
     LIMPE os artefatos de teste ao final.

FASE 3 — Corrigir o ponto cego do gate de drift
3.1. Em `gates/G_DRIFT_NUCLEO_COMPARTILHADO.py`, modifique a lógica de
     checagem (`checar_drift()` ou equivalente): para cada entrada do
     baseline (`gates/baseline_nucleo_compartilhado.json`) com
     `esperado_identico: true`, verifique que o arquivo correspondente
     ainda existe em AMBOS `DIR_A` e `DIR_B` — se estiver ausente de
     qualquer um dos dois lados, reprove (exit 1), reportando
     explicitamente qual arquivo desapareceu e de qual lado (`DIR_A` ou
     `DIR_B`), distinto de uma divergência de conteúdo comum.
3.2. Teste real: escreva um teste que renomeie/remova temporariamente
     (dentro do próprio teste, usando arquivos de fixture ou um
     monkeypatch de `DIR_A`/`DIR_B` apontando para diretórios de teste —
     NUNCA mexa nos arquivos reais de `src/core/` das ferramentas de
     verdade) um arquivo hoje marcado `esperado_identico: true`, confirme
     que o gate reprova apontando o arquivo certo, e confirme que o
     comportamento atual (divergência de conteúdo entre arquivos que
     existem nos dois lados) continua funcionando sem regressão.

CRITÉRIO DE SAÍDA (rode e cole o output real de cada um):
- `python ecossistema.py components verify --tipo hook --ferramenta aidd-master` → exit 0.
- Suíte completa de `aidd-master` (`python -m pytest tests/ -q`) → sem
  regressão, com os testes novos das Fases 1 e 2 incluídos na contagem.
- `python gates/G_DRIFT_NUCLEO_COMPARTILHADO.py` → continua exit 0 no
  estado real do repositório (sem regressão do comportamento existente).
- O teste de reprodução da Fase 3.2 (gate reprova quando deveria,
  usando fixtures/monkeypatch, nunca tocando nos arquivos reais).
- `python ecossistema.py audit` (bateria raiz, 6 gates) → exit 0.
- Os 4 cenários de teste da Fase 2.4 (sem `command`, com `command` em
  `mcp.json` novo, merge preservando entrada anterior).
- Confirme por comando (`git status`) que nenhum teste novo deixou
  arquivo fora de `tmp_path`/diretório de teste temporário, e que nenhum
  componente de teste ficou na fonte canônica `componentes/` nem em
  pastas de harness reais.

REGRAS DE ESCOPO — NÃO FAÇA:
- Não copie `aidd_core_injector.py` (ou qualquer parte dele) para dentro
  de `aidd-master` — a decisão já tomada é estender a arquitetura
  existente, não portar a antiga.
- Não migre `aidd-enterprise` para a arquitetura canônica nem aposente
  `aidd_core_injector.py` — isso é um próximo incremento, fora de escopo
  deste pacote.
- Não altere o comportamento de `mcp` quando `command` não é fornecido.
- Não altere `gates/manifesto_harnesses.json` — a declaração de `hook`
  para o escopo `aidd-master` já existe.
- Não faça `git commit` nem `git push`.
- Não altere
  `docs/planos/evolucao-notas-auditoria/03-modularizacao-injector.md`.

ENTREGÁVEL: lista exata de arquivos criados/alterados; para cada fase,
comando + output real que comprova; qualquer desvio necessário,
reportado explicitamente em vez de decidido sozinho; a convenção de
`dest` local que você escolheu para `hook` (item 1.1) e por que.
```

## Prompt de Execução — English version

```
You are going to close the Universal Injector capability gap between
`aidd-master` and `aidd-enterprise` in the ecossistema-aidd monorepo
(C:\Users\trcnologia\Desktop\ecossistema-aidd) — today `aidd-enterprise`
supports 7 injectable component types (including `hook` and real external
MCP server registration via `--mcp-command`), while `aidd-master` only
supports 6 types, with no `hook` and no `--mcp-command`. Follow the
Definition of Done below EXACTLY, do not invent additional scope, and
validate everything for real (real runs, real exit codes, never masked
by a pipe).

ALREADY-INVESTIGATED CONTEXT (no need to rediscover, but you MUST confirm
it yourself by reading the code before each phase):
- `tools/aidd-master/src/core/profiles_registry.py` defines
  `TIPOS_VALIDOS = ("skill", "mcp", "rule", "spec", "config", "agent")` —
  it needs to gain `"hook"`.
- `aidd-master`'s Universal Injector is composed of
  `src/core/profiles_registry.py` (profile matrix),
  `src/core/detector_camada.py` (`construir_request()`, validates and
  builds the payload), `src/core/materializador.py` (`materializar()`,
  transactional write with rollback), `src/core/sincronizador_harness.py`
  (`sincronizar()`), and `src/core/result.py` (shared `Result` type).
  `scripts/aidd.py`'s `cmd_inject` (around line 650) orchestrates all
  four via `_executar_injecao()`.
- **DO NOT CONFUSE** this Universal Injector (this package's subject)
  with the `componentes/` + `python ecossistema.py components sync/verify`
  mechanism created in Package 7 (Component Distribution Agnosticism) —
  these are different things that now need to connect (see Phase 1
  below), but are not the same code.
- `gates/manifesto_harnesses.json` (monorepo root, created in Package 7)
  ALREADY declares `"hook"` as an applicable type for the `aidd-master`
  scope (`escopos.aidd-master.tipos_aplicaveis` already includes
  `"hook"`), with `pasta_fonte: "hooks"`, `unidade: "diretorio"`,
  `dest_harness_template: "{prefixo_pasta}/hooks/{nome}"`,
  `harnesses_aplicaveis: ["claude-code", "antigravity", "opencode",
  "mimocode", "gemini-cli"]`. You do NOT need to change the manifest —
  the declaration already exists, only `aidd-master`'s Universal
  Injector needs to use it.
- The canonical integration pattern between a Universal Injector and the
  `components sync` mechanism already exists and works in
  `tools/aidd-forge/aidd_forge/core/injector_profiles.py`
  (`resolve_canonical_destination()`, `sincronizar_componente()`,
  `_default_ecossistema_root()`) and is called from
  `tools/aidd-forge/aidd_forge/core/materializador.py` (inside
  `materializar()`, after the main transactional write, before
  returning). READ both files first — it's the reference pattern to
  replicate for `aidd-master`, adapted to its own module structure (do
  not copy literally, adapt).
- `tools/aidd-enterprise/scripts/injector/target_profile.py` (function
  `build_file_map`, `if tipo == "mcp":` branch) already implements the
  `mcp.json` merge logic you will replicate in Phase 2 — read it as a
  format reference, do not copy the whole file (aidd-master's module
  structure is different).
- `gates/G_DRIFT_NUCLEO_COMPARTILHADO.py`'s `_arquivos_comuns()`
  (monorepo root) returns `nomes_a & nomes_b` — only the intersection. A
  file marked `esperado_identico: true` in the baseline
  (`gates/baseline_nucleo_compartilhado.json`) that disappears from one
  side is not detected today.

DECISIONS ALREADY MADE (do not reopen these):
1. Do NOT copy
   `tools/aidd-enterprise/scripts/injector/aidd_core_injector.py` (262
   monolithic lines) into `aidd-master` — this would reintroduce code
   duplication and the old direct multi-folder-write pattern that
   Package 7 already eliminated. Instead, EXTEND `aidd-master`'s
   already-canonical architecture (profiles_registry.py/
   detector_camada.py/materializador.py/sincronizador_harness.py).
2. The new `hook` type in `aidd-master` uses the `componentes/` +
   `gestor_componentes.py sync` mechanism (Package 7) — NOT direct
   writes to fixed harness folders like `aidd-enterprise` does today.
3. `aidd-master`'s `mcp` type KEEPS 100% of its current behavior
   (in-process Python tool file, loaded by
   `MCPServer.register_injected_tools()`) when no `command` is provided
   — zero regression. It only GAINS the new capability (registering in
   `mcp.json`) when `command` is explicitly provided. The two coexist,
   neither replaces the other.
4. The generated/merged `mcp.json` must use the exact same format
   `aidd-enterprise` already uses: `{"mcpServers": {"<name>": {"command":
   ..., "args": [...], "env": {...}}}}`.

DEFINITION OF DONE — in this order:

PHASE 1 — `hook` type via Package 7's canonical mechanism
1.1. Add `"hook"` to `TIPOS_VALIDOS` in `profiles_registry.py` (and
     wherever else needed for `detector_camada.py` to validate/accept the
     type). Add a "local" destination profile (the `dest` the tool
     writes inside the target project itself) for `hook` — follow the
     convention already used by `skill` (a dedicated folder per
     component); a reasonable example would be
     `.agent/hooks/{nome}/hook.sh`, but confirm yourself which convention
     already exists in the project before deciding (grep for `hooks/` in
     the `aidd-master` repo).
1.2. In `materializador.py`, after the main transactional write (the
     same point where aidd-forge's `materializador.py` calls
     `resolve_canonical_destination()`/`sincronizar_componente()`), add
     the same pattern for `aidd-master`: also write the content to
     `componentes/aidd-master/hooks/{nome}/hook.sh` (canonical source, at
     the monorepo root — be careful with the path computation, use the
     same isolated, monkeypatchable function pattern
     (`_default_ecossistema_root()`) that `aidd-forge` uses, to avoid
     repeating the path bug already found and fixed there), then call
     `python ecossistema.py components sync --tipo hook --ferramenta aidd-master`
     (via subprocess, with a direct-import fallback of
     `scripts/gestor_componentes.py`, same pattern as `aidd-forge`).
1.3. Add `"hook"` to the `choices` of `p_inject`'s `tipo` argument in
     `scripts/aidd.py`.
1.4. Real test: run `python scripts/aidd.py inject hook <test-name>
     --descricao "..."` from a test project directory (not the monorepo
     root), confirm the content appears at
     `componentes/aidd-master/hooks/<test-name>/hook.sh` (the REAL
     canonical source of the monorepo, not a wrong copy) and that
     `python ecossistema.py components verify --tipo hook --ferramenta aidd-master`
     returns exit 0. CLEAN UP the test component from the canonical
     source and every harness folder it propagated to at the end — leave
     no garbage in the repository (see the Package 7 finding about this,
     do not repeat it).

PHASE 2 — `mcp` capability with `command` (registering in `mcp.json`)
2.1. Extend `construir_request()` (`detector_camada.py`) to accept
     optional fields `command` (string), `args` (list of strings,
     default empty), and `env` (dict of string→string, default empty) in
     the payload when `tipo == "mcp"`.
2.2. In `materializador.py`, when the `mcp`-type payload includes
     `command`: read `mcp.json` at the target project's root if it
     exists (parse as JSON; if invalid, return a clear error instead of
     silently overwriting), merge/add the entry
     `mcpServers[name] = {"command": ..., "args": [...], "env": {...}}`
     preserving ANY pre-existing entry for other servers, and write it
     back. When `command` is NOT present in the payload, behavior is
     identical to today (Python file at `src/core/mcp/{nome}.py`) — do
     not touch that path.
2.3. Add `--mcp-command`, `--mcp-args` (accept a JSON list string, e.g.
     `--mcp-args '["--flag", "value"]'`), and `--mcp-env` (accept a JSON
     object string) to `p_inject`'s arguments in `scripts/aidd.py`.
     `cmd_inject` only includes these fields in the payload when
     `--mcp-command` is explicitly provided.
2.4. Real test, 3 cases:
     a) Inject an `mcp` WITHOUT `--mcp-command` — confirm behavior is
        identical to the pre-existing one (`.py` file generated at
        `src/core/mcp/{nome}.py`, `mcp.json` NOT created or touched).
     b) Inject an `mcp` WITH `--mcp-command` in a test project where
        `mcp.json` doesn't exist yet — confirm it's created with the
        right entry.
     c) Inject a SECOND `mcp` WITH `--mcp-command` in the SAME test
        project — confirm the first server's entry is still in
        `mcp.json` (merge, not overwrite).
     CLEAN UP the test artifacts at the end.

PHASE 3 — Fix the drift gate's blind spot
3.1. In `gates/G_DRIFT_NUCLEO_COMPARTILHADO.py`, modify the checking
     logic (`checar_drift()` or equivalent): for every baseline entry
     (`gates/baseline_nucleo_compartilhado.json`) with
     `esperado_identico: true`, verify the corresponding file still
     exists on BOTH `DIR_A` and `DIR_B` — if it's missing from either
     side, fail (exit 1), explicitly reporting which file disappeared
     and from which side (`DIR_A` or `DIR_B`), distinct from a common
     content-divergence failure.
3.2. Real test: write a test that temporarily renames/removes (inside
     the test itself, using fixture files or a monkeypatch of
     `DIR_A`/`DIR_B` pointing to test directories — NEVER touch the real
     tools' actual `src/core/` files) a file currently marked
     `esperado_identico: true`, confirm the gate fails pointing at the
     right file, and confirm the existing behavior (content divergence
     between files present on both sides) still works with no
     regression.

EXIT CRITERIA (run and paste the real output of each):
- `python ecossistema.py components verify --tipo hook --ferramenta aidd-master` → exit 0.
- Full `aidd-master` suite (`python -m pytest tests/ -q`) → no
  regression, with the new Phase 1 and 2 tests included in the count.
- `python gates/G_DRIFT_NUCLEO_COMPARTILHADO.py` → still exits 0 against
  the repository's real current state (no regression of existing
  behavior).
- The Phase 3.2 reproduction test (gate fails when it should, using
  fixtures/monkeypatching, never touching real files).
- `python ecossistema.py audit` (root battery, 6 gates) → exit 0.
- The 4 Phase 2.4 test scenarios (no `command`, `command` into new
  `mcp.json`, merge preserving the earlier entry).
- Confirm via command (`git status`) that no new test left a file
  outside `tmp_path`/a temporary test directory, and that no test
  component remained in the canonical `componentes/` source or in real
  harness folders.

SCOPE RULES — DO NOT:
- Do not copy `aidd_core_injector.py` (or any part of it) into
  `aidd-master` — the decision already made is to extend the existing
  architecture, not port the old one.
- Do not migrate `aidd-enterprise` to the canonical architecture or
  retire `aidd_core_injector.py` — that's a future increment, out of
  scope for this package.
- Do not change `mcp`'s behavior when `command` is not provided.
- Do not modify `gates/manifesto_harnesses.json` — the `hook` declaration
  for the `aidd-master` scope already exists.
- Do not `git commit` or `git push`.
- Do not modify
  `docs/planos/evolucao-notas-auditoria/03-modularizacao-injector.md`.

DELIVERABLE: exact list of files created/changed; for each phase, the
command + real output that proves it; any necessary deviation, explicitly
reported instead of decided by yourself; the local `dest` convention you
chose for `hook` (item 1.1) and why.
```

---

## Veredito — Auditoria do Prompt de Execução

**Auditoria independente realizada — não me baseei no relatório do agente executor.**

**Confirmado correto, por reprodução ao vivo, fora dos arquivos de teste do executor:**
- **Fase 1 (`hook`):** injetei um hook real via `python scripts/aidd.py inject hook ... --dir <projeto-teste>` — confirmei escrita no destino local (`.agent`/`.claude`/`.gemini/hooks/`), na fonte canônica (`componentes/aidd-master/hooks/{nome}/hook.sh`, raiz REAL do monorepo, não uma cópia errada) e propagação via `python ecossistema.py components sync` — os dois arquivos (canônico e propagado) são byte-idênticos. `components verify --tipo hook --ferramenta aidd-master` exit 0.
- **Fase 2 (`mcp` com `command`):** reproduzi 3 cenários independentes — dois servidores injetados em sequência no mesmo projeto, confirmei que `mcp.json` faz merge preservando a entrada anterior (não sobrescreve); confirmei que `mcp` sem `--mcp-command` continua 100% no comportamento legado (arquivo `.py` em processo, `mcp.json` nunca tocado).
- **Fase 3 (gate de drift):** os 4 testes novos usam `monkeypatch`/`tmp_path` corretamente para `DIR_A`/`DIR_B`/`BASELINE_PATH`, nunca tocando os arquivos reais de `src/core/`. O gate real contra o estado atual do repositório continua exit 0 (sem regressão).
- **Boa prática notável:** o executor atualizou proativamente `schema_injector_request.json` para aceitar os campos novos (`command`/`args`/`env`) e o tipo `hook` — evitando exatamente o bug de "schema desatualizado bloqueando tipo novo" encontrado durante o Pacote 7 (Correção 2, achado 2).
- Sem regressão: suíte de `aidd-master` 215→228 (+13 testes: 4 do gate de drift, 9 do injetor). `aidd-enterprise` não foi tocado (confirmado via `git status`), suíte segue 219 passed, igual.
- Sem poluição do repositório (`git status` limpo após rodar a suíte). `python ecossistema.py audit` (bateria raiz) exit 0, 6/6 gates.
- Regras de escopo respeitadas: `aidd_core_injector.py` não foi copiado; `aidd-enterprise` não foi migrado nem tocado; comportamento de `mcp` sem `command` inalterado; `gates/manifesto_harnesses.json` não foi alterado (a declaração de `hook` já existia); nenhum commit feito; documento do pacote intocado.

**Achado menor, não bloqueante (já verificado e confirmado correto por mim):** nenhum teste prova que `_default_ecossistema_root()` (`parents[4]`, em `materializador.py`) resolve para a raiz real do monorepo — todos os testes isolam essa função via a fixture `conftest.py` (corretamente replicada do padrão estabelecido no Pacote 7), o que é o comportamento certo para não poluir o repositório durante `pytest`, mas nenhum teste com marker `raiz_real` (como o padrão estabelecido no Pacote 7 Corretivo 2) prova que o cálculo do índice está correto de forma independente. Verifiquei manualmente e confirmei que `parents[4]` está correto para a localização atual de `materializador.py` — não é um defeito hoje, mas um refactor futuro que mova o arquivo poderia quebrar isso silenciosamente sem nenhum teste detectar.

### Nota Final — Pacote 3 (Modularização): 9.5/10

**Por que 9.5, não 10:**
- As 3 fases foram implementadas corretamente na primeira tentativa, sem nenhuma rodada corretiva necessária — terceiro pacote consecutivo (depois do 4) a fechar de primeira.
- A decisão de arquitetura mais delicada (não copiar o injector antigo, preservar 100% o comportamento legado de `mcp`, usar o mecanismo canônico do Pacote 7 para `hook`) foi seguida com precisão, incluindo o detalhe mais fácil de errar (isolar `_default_ecossistema_root()` via fixture, replicando corretamente uma lição aprendida em outro pacote).
- **0.5 de desconto:** falta o teste `raiz_real` que prova a resolução de path de forma independente (mesmo padrão que o Pacote 7 passou a exigir depois de um bug real ter escapado justamente por faltar esse tipo de prova) — risco baixo mas real para regressão futura silenciosa; e não reproduzi manualmente 100% dos 13 cenários de teste novos (verifiquei uma amostra representativa de alto risco + rodei a suíte completa).
- **Efeito na dimensão Modularização:** 7/10 → **9/10** (alvo do plano original atingido). A divergência de capacidade entre os dois injectors está fechada sem reintroduzir duplicação de código nem o padrão antigo de distribuição multi-harness; o ponto cego do gate de drift que permitiu a divergência silenciosa original também está corrigido. Fica registrado, fora de escopo deste pacote: migrar `aidd-enterprise` para a mesma arquitetura canônica e aposentar `aidd_core_injector.py` — próximo incremento natural, não item quebrado desta entrega.
