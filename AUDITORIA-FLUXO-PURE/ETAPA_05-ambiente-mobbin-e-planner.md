# Auditoria de Etapa: Ambiente, Mobbin e abertura do planner (investigação e decisões)

Esta etapa é de **investigação**: nada foi implementado no planner. Ela nasceu quando se foi apresentar a ETAPA de planejamento e o usuário perguntou como a entrevista (grill, spec) e o Mobbin entram no `/pure`. Tudo abaixo foi lido no código executado ou medido de verdade; o que não foi verificado está marcado.

### [RECURSO]: Leitura do estágio planner (código executado de fato)
- **Ordem de Execução:** após a ETAPA_04 (forge). O `ecossistema.py planner` executa `aidd_planner.cli` (fachada de 16 linhas) que chama `src/cli.py`; as 3 cópias em `aidd_planner/core/` são re-exportações.
- **Ação Executada:** leitura de `src/cli.py` (`cmd_init`), `ui_reference_resolver.py`, `mobbin_client.py`, `design_system.py`, do orquestrador síncrono e das skills `aidd-planner`, `aidd-grill`, `aidd-spec`.
- **Entrega / Artefato Gerado:** mapa do que o `planner init` faz.
  - *Caminho Exato (100% concluído):* `modulos/01-governanca-e-qualidade/core/aidd-planner/src/` e `aidd_planner/`.
- **Status & Diagnóstico:**
  - *Sucesso:* Sim.
  - *Falhas / Anomalias:*
    - *Ocorrência:* (a) o `planner init` gera `PLANNER.json` por **template** a partir de nome, slug e domínio; **não há entrevista**: em todo o diretório do planner a busca por "grill", "spec" e "entrevista" não achou nada, e o orquestrador também não chama grill nem spec. A cadeia documentada `/aidd-grill → /aidd-spec → /aidd-planner` não é acionada pelo `/pure`. (b) O Mobbin entra no `init`, mas só busca **1 tela** com o **domínio como termo** e usa `screen_type: "dashboard"` fixo; muda só o rótulo `fonte` e o `arquetipo_topologico` do `DESIGN-SYSTEM.json`; a paleta vem do catálogo por palavras-chave e **não** da tela. Sem chave ou sem resultado, cai no determinístico **em silêncio**.
    - *Localização Exata do Erro:* `src/cli.py` `cmd_init` (linhas ~64-135); `src/core_planner/ui_reference_resolver.py` (`buscar_referencias_mobbin`, `resolver_referencia_ui`); `src/core_planner/design_system.py:49-89`.
  - *Ação Corretiva Cirúrgica:* nenhuma ainda; ver Tickets.
  - *Erros meus nesta investigação (registrados):* li primeiro o `src/cli.py` sem confirmar que era o executado (conferi depois: a fachada o chama, conclusões mantidas); afirmei que o PURE não lia variável do `.env` na ETAPA_03 sem varrer o planner (ver Ticket 7).

### [RECURSO]: Testes da API REST do Mobbin (3 sondas, ~120 chamadas, fora do projeto)
- **Ordem de Execução:** após a leitura do planner; autorizado pelo usuário a "fazer quantos testes precisar".
- **Ação Executada:** scripts em `C:\Users\trcnologia\aidd-tmp\mobbin_probe\` (`probe1.py`, `probe2.py`, `probe3.py`) lendo a chave do `.env` sem imprimi-la: modos, plataformas, limites, qualidade de imagem, paginação, erros, endpoints não documentados, português x inglês, determinismo, rajada de 75 chamadas; extração de tokens do ecossistema sobre 6 telas reais.
- **Entrega / Artefato Gerado:** fatos medidos (também em `memory/reference_mobbin_api_comportamento_testado.md`).
  - *Caminho Exato (100% concluído):* `C:\Users\trcnologia\aidd-tmp\mobbin_probe\probe*.out` e `r1\*.json`. As imagens baixadas foram apagadas (conteúdo protegido).
- **Status & Diagnóstico:**
  - *Sucesso:* Sim.
  - *Resultados:* um único endpoint REST, `POST /v1/screens/search`; `flows`, `sections`, `apps`, `me` dão 404. Parâmetros: `query` 1-500 (descrever **uma** tela; citar o app restringe ao app), `platform` obrigatório (`ios|web`), `mode` padrão **deep** (12-30 s; `standard` 1,5-4 s; `fast` é alias idêntico e deprecado), `limit` 1-100 (100 em ~2 s), `image_quality` `optimized` 768 px ou `high` 1920 px, `exclude_screen_ids` (paginação funciona). Resposta: só `id`, `app_name`, `platform`, `mobbin_url` e `image{url,url_expires_at,width,height}`; `image_url` é deprecado; URL vale ~30 dias e baixa sem chave. Determinística (3 execuções, mesmos ids e ordem). Português ≈ inglês (3/5 iguais). Negação e adjetivos vagos são ignorados. Erros estruturados `{"error":{"code","message"}}` (`bad_request`, `unauthorized`). 75 chamadas em 124 s não geraram 429. Toda imagem traz uma barra escura de ~48 px no rodapé ("curated by Mobbin").
  - *Falhas / Anomalias:*
    - *Ocorrência:* **extrator de tokens do ecossistema tem 4 defeitos**, medidos sobre 6 telas reais: (1) o laço da cor primária dá `break` ao juntar 6 cores e só vê tons quase brancos (`primary` saiu `#fefefe`, `#f7f7f7`, `#fdfdfd`); (2) tipografia é tabela por nome do app e espaçamentos e raios são constantes iguais nas 6 telas; (3) `classificar_arquetipo` usa tags/nome e a API não devolve tags, então tudo caiu em `analytics_canvas`; (4) o cliente usa `image_url` (deprecado), aceita `fast`, e `executar_busca` faz `sys.exit(1)` dentro de biblioteca.
    - *Localização Exata do Erro:* `componentes/compartilhado/mcps/mobbin_mcp/token_extractor.py` (`extrair_paleta_imagem`, `_derivar_stack_tipografico`, `extrair_tokens_mobbin`); `archetype_engine.py` (`classificar_arquetipo`); `modulos/01-governanca-e-qualidade/core/aidd-planner/src/core_planner/mobbin_client.py` (`executar_busca`).
  - *Não testado:* o 429 de verdade (limite 60/min não foi atingido) e os direitos de uso das imagens (a documentação não os cita).

### [RECURSO]: Documentação oficial e MCP oficial do Mobbin
- **Ordem de Execução:** após as sondas REST.
- **Ação Executada:** leitura de `docs.mobbin.com/openapi.json`, da referência do endpoint, de `llms.txt` e dos guias de 6 clientes; autenticação OAuth do MCP oficial (`https://api.mobbin.com/mcp`) pelo usuário nesta sessão; 3 buscas (`search_flows`, `search_screens`, `search_sections`).
- **Entrega / Artefato Gerado:** tabela de configuração por harness e prova de que fluxos existem.
  - *Caminho Exato (100% concluído):* sem arquivos no projeto (resultado em `memory/reference_mobbin_api_comportamento_testado.md`).
- **Status & Diagnóstico:**
  - *Sucesso:* Sim.
  - *Resultados:* `search_flows` (limite 10, página até 20) devolve fluxos ordenados (`id`, `name`, `actions[]`, app, plataforma, `screen_count`, telas com `position`); a consulta "criar pedido" trouxe Shopify (14 e 10 telas) e Deel (11 telas, assistente em 4 passos). `search_sections` (limite 30) devolve seções de sites. O MCP usa OAuth no navegador, planos Pro+, 60 req/min por usuário, e **só o harness o usa** (não scripts/CLI). Autorização é **por cliente**: a deste Claude Code não vale para Antigravity, OpenCode ou MiMoCode. O MCP oficial **não está registrado em nenhum arquivo do projeto** (só o `mobbin-mcp` local, REST + chave).
  - *Falhas / Anomalias:*
    - *Ocorrência:* OpenCode, MiMoCode e Gemini CLI não constam da lista de clientes do Mobbin; pela documentação deles (não testado aqui) aceitam MCP remoto com OAuth (`opencode mcp auth`, `mimo mcp auth`, `/mcp auth`). A documentação do Gemini CLI informa que ele foi substituído pelo Antigravity CLI em 18/06/2026 para o plano gratuito. OAuth exige navegador (documentado como limitação do Gemini).
    - *Localização Exata do Erro:* N/A.
  - *Ação Corretiva Cirúrgica:* N/A.

### [RECURSO]: Decisões de desenho tomadas com o usuário
- **Ordem de Execução:** ao longo da etapa, uma pergunta por vez.
- **Ação Executada:** registro das decisões.
- **Status & Diagnóstico:**
  - *Sucesso:* Sim.
  - *Decisões:* (1) a jornada real do planner é **Ambiente → entrevista (grill) → spec → Mobbin → planner**; (2) o bloco **Ambiente** apresenta 3 caminhos para o Mobbin (A: chave no `.env`; B: MCP oficial pelo harness, com passo a passo do harness detectado; C: nenhum), registra a escolha em arquivo do projeto sem segredos, **nunca bloqueia**, e nunca pede segredo no chat; (3) o planner **bloqueia** se faltarem variáveis exigidas por deploy; (4) **sem Mobbin, o fallback é a spec/entrevista**, não o catálogo por palavras-chave; (5) o grill precisa **perguntar o visual** (tom, cores, referências, público); (6) fluxos e estrutura visual entram pelo harness, em JSON validado com origem registrada; guardar só tokens derivados e links, não as imagens; (7) tudo é feito **nesta sessão**, com tickets resolvidos no ato; (8) o passo a passo por harness vem da documentação oficial e marca "não verificado" onde não foi testado.

## TICKETS
Todos **ABERTOS, NÃO EXECUTADOS**: a correção do planner só começa depois da troca do Next.js (ETAPA_06), porque o `DESIGN-SYSTEM.json` e os tokens alimentam o gerador de frontend.

### Ticket 1: Planner não abre com o bloco Ambiente (Refere-se a pré-requisitos do fluxo)
- **Falha:** o planner não pergunta nem verifica o `.env`, nem pede a escolha do Mobbin; faltar chave cai no determinístico sem aviso.
- **Artefato de Handoff:** `modulos/01-governanca-e-qualidade/core/aidd-planner/src/cli.py`
- **Requisito TDD (Red):** `planner init` sem escolha de Mobbin registrada reprova com exit 1 e mensagem que lista os 3 caminhos; com variáveis de deploy exigidas ausentes, bloqueia com exit 1.
- **Implementação Técnica:**
  - Detectar harness (`CLAUDECODE`, `OPENCODE*`, `MIMO*`, `ANTIGRAVITY*`, `GEMINI_*`) e mostrar o passo a passo oficial só dele.
  - Verificar a chave com uma chamada real mínima; gravar `.aidd/ambiente.json` sem segredos.
- **Verificação (Green):** pytest do planner com exit 0; `planner init` real com a escolha registrada passa.
- **Construtor Prompt (EN):**
  - Add an Environment step to `planner init` that detects the harness, offers the three Mobbin paths, validates the chosen one with a real minimal call, and writes `.aidd/ambiente.json` without secrets.
  - Make it block only on deploy-required variables; run the planner tests and assert exit 0.

### Ticket 2: Estágio planner não aciona grill nem spec (Refere-se à cadeia documentada)
- **Falha:** `/aidd-grill → /aidd-spec → /aidd-planner` existe como skills soltas; o `/pure` gera plano de template.
- **Artefato de Handoff:** `scripts/orquestrador_sincrono.py` (`etapa_02_planner`) e a skill `aidd-pure`.
- **Requisito TDD (Red):** teste que roda a etapa 2 e afirma que existe `spec.md` validado (`spec validar` exit 0) antes do `planner init`; hoje falha.
- **Implementação Técnica:**
  - Acionar o grill (com perguntas visuais) e a spec via protocolo delegado; passar a spec ao planner.
- **Verificação (Green):** teste acima com exit 0; `pure --dry-run` continua exit 0.
- **Construtor Prompt (EN):**
  - Make stage 2 run the grill interview and the spec before `planner init`, include visual questions, and pass the validated spec to the planner; add the failing test first and finish with exit 0.

### Ticket 3: Mobbin pouco aproveitado no `planner init` (Refere-se a "extrair o máximo da API")
- **Falha:** 1 tela, termo = domínio, sem tokens, sem cache, fallback silencioso.
- **Artefato de Handoff:** `src/core_planner/ui_reference_resolver.py`, `design_system.py`, `mobbin_client.py`.
- **Requisito TDD (Red):** com API simulada, o `init` consulta uma busca por tela da spec (`standard`, `limit` alto), grava `referencias-ui.json` com origem e `mobbin_url`, gera `DESIGN-SYSTEM.json` a partir dos tokens, e reusa o cache numa segunda execução sem nova chamada.
- **Implementação Técnica:**
  - Consulta descritiva por tela, âncora de app de referência, `standard` explícito, cache por hash em `.aidd/cache/`, fluxos via harness quando houver MCP, guardar só tokens e links.
- **Verificação (Green):** pytest com exit 0; execução real contra a API com exit 0.
- **Construtor Prompt (EN):**
  - Rework the Mobbin step: descriptive per-screen queries from the spec, explicit `standard` mode, hash-keyed cache, store only derived tokens and links, record provenance, and fall back to the spec (never silently to the catalog).

### Ticket 4: Quatro defeitos do extrator de tokens (Refere-se a correção de cor, tipografia, arquétipo e cliente)
- **Falha:** ver "Falhas" da seção das sondas.
- **Artefato de Handoff:** `componentes/compartilhado/mcps/mobbin_mcp/token_extractor.py`, `archetype_engine.py`, `mobbin_client.py`.
- **Requisito TDD (Red):** sobre uma imagem de teste com fundo branco e botão colorido, o `primary` extraído deve ser a cor do botão (hoje sai quase branco); o rodapé de 48 px é cortado antes; o cliente levanta exceção em vez de `sys.exit`.
- **Implementação Técnica:**
  - Cortar o rodapé, tirar o `break` das 6 cores, agregar as 3 telas, usar `image.url`, aceitar só `standard|deep`, levantar exceções.
- **Verificação (Green):** `pytest tests/test_mobbin_mcp.py` com exit 0.
- **Construtor Prompt (EN):**
  - Write a failing test with a synthetic image (white background, colored button) asserting the extracted primary is the button color, then crop the footer, remove the six-color break, and replace `sys.exit` with exceptions.

### Ticket 5: `forge mobbin` duplicado e relatórios contraditórios (Refere-se à Inconsistência 30)
- **Falha:** o relatório E2E (05/10) manda remover o Mobbin do forge e o marca RESOLVIDO; o `aidd-forge.md` §9 (03/10) diz que foi adicionado; o `forge mobbin` ainda existe.
- **Artefato de Handoff:** `componentes/compartilhado/skills/aidd-forge/scripts/cli.py`, `docs/teste-end-to-end/`.
- **Requisito TDD (Red):** `forge mobbin --help` não deve existir (ou deve delegar ao planner).
- **Implementação Técnica:** remover ou delegar; reconciliar os dois registros.
- **Verificação (Green):** pytest do forge com exit 0.
- **Construtor Prompt (EN):**
  - Remove the duplicated `mobbin` subcommand from the forge CLI (or make it delegate to the planner) and reconcile the two contradictory reports.

### Ticket 6: Documentação do planner e chave parcialmente impressa (Refere-se a documentação e segredos)
- **Falha:** a skill do planner não cita Mobbin nem `--ui-ref`; `planner mobbin status` imprime os 4 primeiros e 4 últimos caracteres da chave.
- **Artefato de Handoff:** `.agents/skills/aidd-planner/SKILL.md` (fonte em `componentes/`) e `mobbin_client.py` (`cmd_status`).
- **Requisito TDD (Red):** `cmd_status` não pode imprimir nenhum caractere da chave.
- **Implementação Técnica:** mostrar só "configurada: sim/não"; documentar Mobbin, `--ui-ref` e o bloco Ambiente.
- **Verificação (Green):** pytest com exit 0.
- **Construtor Prompt (EN):**
  - Make `cmd_status` print only whether the key is set, never any character of it, and document Mobbin, `--ui-ref` and the Environment step in the planner skill.

### Ticket 7: Correção do diagnóstico do Ticket 2 da ETAPA_03 (Refere-se à veracidade do relatório)
- **Falha:** a ETAPA_03 (v2 a v4) afirma que o PURE não lê variável do `.env`; o planner lê `MOBBIN_API_KEY` e `MOBBIN_API_URL`.
- **Artefato de Handoff:** `AUDITORIA-FLUXO-PURE/ETAPA_03-configuracao-de-ambiente_v4.md`.
- **Requisito TDD (Red):** não aplicável (correção de registro).
- **Implementação Técnica:** acrescentar emenda ao relatório; a varredura de `os.environ` deve incluir o planner.
- **Verificação (Green):** relatório emendado e conferido por leitura.
- **Construtor Prompt (EN):**
  - Amend the ETAPA_03 report: the planner reads `MOBBIN_API_KEY` and `MOBBIN_API_URL`; extend the env-variable scan to cover the planner.

### Ticket 8: Lista de harnesses desatualizada (Refere-se a cobertura de harnesses)
- **Falha:** o Gemini CLI foi substituído pelo Antigravity CLI em 18/06/2026 para o plano gratuito (documentação do Gemini); o ecossistema ainda lista `gemini-cli`.
- **Artefato de Handoff:** `modulos/04-nucleo-compartilhado/contracts/manifesto_harnesses.json` e `dependencias_externas.json`.
- **Requisito TDD (Red):** a definir após confirmar o que o usuário mantém.
- **Implementação Técnica:** decidir com o usuário se `gemini-cli` permanece.
- **Verificação (Green):** gates de harness com exit 0.
- **Construtor Prompt (EN):**
  - Ask the user whether `gemini-cli` stays; then update the harness manifest accordingly and run the harness gates asserting exit 0.
