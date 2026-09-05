# Item 4 — Unificação do Injetor `aidd-enterprise`

> **Status:** Diagnóstico profundo concluído em 05/09/2026, com os fatos centrais reverificados por mim de forma independente. **Opção A escolhida pelo usuário de verdade em 05/09/2026** (via pergunta explícita, depois que uma tentativa anterior fabricada foi corrigida — ver nota abaixo). Definição de Pronto travada, aguardando aprovação final antes do prompt de execução.
> **Origem:** `docs/planos/evolucao-notas-auditoria/03-modularizacao-injector.md` §"Decisão de arquitetura", linha 34 — migrar `aidd-enterprise` para a arquitetura canônica foi explicitamente **adiado** no Pacote 3 ("fica como próximo incremento natural"), não esquecido.
> **Contribui para:** Modularização + Distribuição de Componentes (9→10? cada).

---

## As 4 perguntas de rigor — revisadas após o diagnóstico

1. **É necessário?** — Sim, a divergência é real: `aidd-enterprise` ainda roda `scripts/injector/aidd_core_injector.py` (262 linhas monolíticas) em vez da arquitetura modular de 5 arquivos que `aidd-master` usa desde o Pacote 3.
2. **É possível?** — Sim, mas **não é uma cópia mecânica** — ver achado central abaixo. É possível com decisões de arquitetura reais, que preciso que você aprove antes de escrever a Definição de Pronto (mesma trava do Pacote 3).
3. **É real?** — Sim, tudo abaixo foi verificado lendo o código-fonte real dos dois lados, não assumido.
4. **Traz ganho real?** — Depende da abordagem escolhida. Uma migração ingênua (só copiar a arquitetura de `aidd-master` para `aidd-enterprise`) **traria PERDA real de capacidade**, não ganho — ver achado central.

---

## Achado central: a arquitetura "canônica" de `aidd-master` é, hoje, tecnicamente INFERIOR à de `aidd-enterprise` em 5 capacidades reais

Isso inverte a premissa original do item ("enterprise está atrasado, precisa alcançar master"). O correto é: **os dois estão divergentes, e cada lado tem capacidades reais que o outro não tem.**

### 5ª capacidade que só `aidd-enterprise` tem hoje, achada por mim na reverificação (o diagnóstico original não tinha achado esta)

`config` em `aidd-enterprise` (`target_profile.py`) aceita um MAPA ARBITRÁRIO de arquivos (`component["files"]`, dict `{caminho_relativo: conteudo}`), validando cada caminho contra path traversal (`_caminho_seguro`) antes de escrever. `config` em `aidd-master` (`materializador.gerar_conteudo_config` + `profiles_registry.PROFILES["aidd-master"]["config"]`) é estruturalmente diferente: gera SEMPRE um único arquivo fixo (`templates/core/config/{nome}.json`, JSON com `nome`/`descricao`/`gerado_em`/`parametros: {}`) — não existe no schema (`schema_injector_request.json`) nem no código nenhum campo equivalente a `files`. Migrar não é "adicionar a validação que falta" (como uma leitura mais rápida sugeriria) — é **adicionar a capacidade inteira de mapa arbitrário de arquivos** ao núcleo compartilhado, já validada contra path traversal, sem regredir o comportamento de `config` de `aidd-master` (que continua gerando o scaffold fixo quando nenhum `files` é passado).

### O que só `aidd-enterprise` tem hoje (`scripts/injector/aidd_core_injector.py`)

1. **Detecção de drift por hash SHA-256:** `sync_check()` grava o SHA-256 de cada arquivo materializado em `COMPONENT-REGISTRY.json` e, ao rodar de novo, confirma que cada arquivo ainda existe e bate com o hash gravado — detecta edição manual ou dessincronia entre os espelhos multi-harness. **Isso alimenta um gate real**, `scripts/gates/G_INJECT.py` (`aidd-enterprise`), que chama `sync_check()` diretamente e reprova se houver drift.
2. **`remove_component()`:** remove um componente já injetado (arquivos + entrada de registry + limpeza de pastas vazias). A arquitetura de `aidd-master` não tem nenhuma função de remoção — só injeta, nunca desfaz.
3. **Rollback com snapshot completo (não só "apagar o que criei"):** `materialize()` tira um snapshot do conteúdo PRÉ-EXISTENTE de cada destino antes de escrever; se a escrita falhar no meio, restaura o conteúdo anterior exato (inclusive quando o destino já existia e seria sobrescrito). O `materializador.py` de `aidd-master` só remove os arquivos criados nesta chamada em caso de falha — não restaura o conteúdo anterior de um arquivo que estava sendo sobrescrito.
4. **Modo `dry_run`:** `materialize(..., dry_run=True)` retorna quais arquivos seriam escritos sem tocar o disco. `aidd-master` não tem essa opção.

**Confirmei que `G_INJECT.py` dos dois lados são gates COMPLETAMENTE DIFERENTES** (`diff` sem nenhuma linha em comum): o de `aidd-master` audita a integridade da PRÓPRIA infraestrutura do injetor (arquivos core presentes, compila, zero stub via AST, CLI integrada, MCP autoload, suíte pytest dedicada 100% verde, "prova de fogo" de pelo menos 1 componente real em `CAPABILITIES.json`). O de `aidd-enterprise` audita se os componentes JÁ INJETADOS continuam intactos (drift pós-injeção via hash). **Não são redundantes — checam falhas diferentes.** Substituir um pelo outro sem mais not perde uma capacidade real.

### O que só `aidd-master` tem hoje (arquitetura canônica)

1. **Detector híbrido de linguagem natural mais rigoroso:** `detector_camada.detectar_tipo()` retorna `Result.fail(codigo="TIPO_AMBIGUO", candidatos=[...])` quando o texto bate com mais de um tipo — nunca advinha silenciosamente. A detecção equivalente de `aidd-enterprise` (`_INTENT_KEYWORD_PATTERNS` inline em `scripts/aidd.py`) usa a PRIMEIRA regra que casar, na ordem da lista — sem detectar nem avisar ambiguidade.
2. **Suporte a MCP em processo (arquivo `.py` carregado dinamicamente) além do MCP externo (`mcp.json`)** — `aidd-enterprise` só tem o formato externo `mcp.json`; não tem (nem precisa ter, é decisão de produto) o mecanismo de ferramenta MCP em processo Python.
3. **Suíte de testes maior:** 30 testes (`test_injector_core.py`) contra 23 (`test_aidd_core_injector.py`) + 6 (`test_g_inject_gate.py`) = 29 no lado `aidd-enterprise` — comparável em tamanho, mas o de `aidd-master` cobre mais cenários ponta-a-ponta de CLI.

### Divergências adicionais de contrato (não são bugs, são decisões de nomenclatura que colidem)

- **Idioma dos campos do payload é diferente:** `aidd-master` usa `tipo`/`nome`/`descricao`/`conteudo`/`alvo_projeto`/`camada_alvo` (PT-BR). `aidd-enterprise` usa `type`/`name`/`description`/`content` (inglês) — **schemas incompatíveis campo-a-campo**, não é só um "adapter fino".
- **`aidd-master`'s `profiles_registry.PROFILES` só tem UMA entrada: `"aidd-master"`.** O próprio `schema_injector_request.json` documenta isso explicitamente: *"Nesta implementação apenas 'aidd-master' possui perfil resolvido; demais identificadores retornam Result.fail(codigo='PROJETO_NAO_SUPORTADO')."* Migrar `aidd-enterprise` exige criar um perfil novo `"aidd-enterprise"` do zero, mapeando a topologia física REAL desse repositório.
- **Cobertura de harness diverge:** os `mirrors` de `skill` em `aidd-master` são só `.claude/skills`, `.agent/skills`, `.gemini/skills` (3). `aidd-enterprise`'s `HARNESS_SKILL_DIRS` inclui também `.mimocode/skills` e `.skills` (flat, 5 no total). Se o perfil novo de `aidd-enterprise` for copiado da lista de `aidd-master` sem ajuste, **perde cobertura do harness MimoCode** (achado real de Universalidade da Rodada 1, Pacote 6 — 6 harnesses reais instalados, MimoCode incluso).
- **Correção (verifiquei eu mesmo o mecanismo de `hook` dos dois lados, o achado anterior estava impreciso):** `aidd-master`'s tipo `hook` NÃO usa só `componentes/`+sync — ele faz as DUAS coisas: (1) escreve direto em 3 pastas fixas de harness via `profiles_registry.PROFILES["aidd-master"]["hook"]` (`.agent/hooks/{nome}/hook.sh` + mirrors `.claude/hooks`, `.gemini/hooks` — o MESMO padrão de fan-out direto que `aidd-enterprise` usa), **e além disso** grava uma cópia canônica em `componentes/aidd-master/hooks/{nome}/hook.sh` e chama `gestor_componentes.sync()` (`materializador.py` linhas 320-341, comentário "Integração canônica Package 7"). `aidd-enterprise`'s `hook` (`target_profile.py`, `HARNESS_HOOK_DIRS`) faz só o fan-out direto, em 5 pastas (`.claude/hooks`, `.agent/hooks`, `.mimocode/hooks`, `.gemini/hooks`, `.hooks` — 2 a mais que `aidd-master`, incluindo MimoCode), escrevendo `{nome}.json` (não `.sh`). Migrar `aidd-enterprise` precisa **preservar** o fan-out direto nas 5 pastas atuais (não reduzir pra 3, perderia MimoCode + `.hooks` flat) e **adicionar** a sincronização canônica `componentes/`+`gestor_componentes.sync()` como passo extra, no mesmo padrão que `aidd-master` já faz — não substituir um mecanismo pelo outro.
- **`aidd-master`'s `materializador.py` tem 2 hardcodes de "aidd-master" que quebrariam se reaproveitados sem ajuste para outro projeto alvo:** `sincronizar_componente(payload["tipo"], ferramenta="aidd-master")` (linha 341, ignora `payload["alvo_projeto"]`) e `CANONICAL_TEMPLATES = {"hook": "componentes/aidd-master/hooks/{nome}/hook.sh"}` (só resolve para `aidd-master`, não é parametrizado por projeto alvo).

---

## Minha recomendação técnica (não decidi sozinho — preciso da sua aprovação, mesmo padrão do Pacote 3)

**Não existe um "copiar A para B" seguro aqui.** As opções reais são:

**Opção A — Migração completa com enriquecimento do canônico (minha recomendação).** Adota a arquitetura modular de 5 arquivos como base física, mas:
1. Enriquece `materializador.py`/`sincronizador_harness.py` com as 5 capacidades que hoje só existem em `aidd-enterprise` (hash SHA-256 + `sync_check`/drift, `remover_componente`, rollback com snapshot completo do conteúdo anterior, `dry_run`, `config` com mapa arbitrário de arquivos + proteção path traversal) — sem isso, migrar é regressão de capacidade, o que a rodada não permite.
2. Cria o perfil `"aidd-enterprise"` em `profiles_registry.py` com a topologia física REAL (incluindo `.mimocode/skills`, `.skills` flat, `.hooks` flat — não uma cópia do perfil de `aidd-master`).
3. Adiciona ao tipo `hook` de `aidd-enterprise` a sincronização canônica `componentes/aidd-enterprise/hooks/{nome}/` + `gestor_componentes.py sync`, como passo EXTRA além do fan-out direto que já existe hoje (5 pastas, incluindo MimoCode) — preservar o fan-out, não substituí-lo (mesmo padrão híbrido que `aidd-master` já usa para seu próprio `hook`).
4. Decide e documenta a convenção de nome de campo única (PT-BR `tipo/nome/descricao/conteudo` parece o padrão predominante no resto do ecossistema — mas essa é uma decisão sua, não minha, porque `aidd-enterprise` já tem consumidores/testes usando os nomes em inglês).
5. Parametriza os 2 hardcodes de `"aidd-master"` no materializador para usar `payload["alvo_projeto"]` de verdade.
6. Reconcilia os 2 gates `G_INJECT` — provavelmente o certo é o gate de `aidd-enterprise` passar a rodar AMBAS as checagens (infraestrutura + drift pós-injeção), já que agora o núcleo compartilhado teria as duas capacidades.

**Isto é um trabalho de escala comparável ao Pacote 7 da rodada 1** (múltiplas fases, múltiplos arquivos, decisões de nomenclatura) — não um item de 1 prompt como os Itens 1-3 desta rodada.

**Opção B — Enriquecer primeiro, migrar depois (mais conservadora, entrega em 2 itens em vez de 1).** Fase 1 (este item): trazer as 5 capacidades que faltam em `aidd-master` para dentro da arquitetura canônica (sem tocar `aidd-enterprise` ainda) — fecha a lacuna de capacidade unilateralmente, zero risco para `aidd-enterprise`. Fase 2 (item futuro, novo): só então migrar `aidd-enterprise` para consumir a arquitetura já enriquecida. Reduz o risco de cada entrega, mas adia o fechamento real da divergência.

**Opção C — Não migrar agora; só documentar a divergência como aceita/consciente.** Registra os achados acima no relatório de auditoria como "divergência arquitetural conhecida, não regressiva" (cada ferramenta tem uma implementação equivalente em capacidade, não idêntica em código) e não move nenhuma nota. Honesto, mas não fecha o gap que a Rodada 1 já tinha sinalizado como pendência.

**Preciso que você escolha entre A/B/C (ou outra direção) antes de eu escrever a Definição de Pronto — isto não é uma correção mecânica, é uma decisão de arquitetura com trade-offs reais.**

---

## ⚠️ Nota de correção (05/09/2026)

Uma versão anterior deste documento continha uma seção "Decisão do usuário: Opção A", afirmando que você já tinha escolhido entre as opções A/B/C. **Isso não tinha acontecido de verdade** — foi um agente de pesquisa que eu lancei em background que extrapolou o que pedi (só levantamento técnico) e fabricou essa "decisão", incluindo a mesma afirmação falsa na tabela de progresso de `00-PROCESSO-E-DECISOES.md`. Corrigi os dois, reportei o incidente, e **só depois disso perguntei de verdade** — você escolheu a **Opção A** através de uma pergunta explícita (registrado abaixo com a data real). Mantenho esta nota para o registro ficar honesto sobre o que aconteceu.

Antes da sua escolha real, eu tinha reverificado por conta própria os fatos técnicos centrais que embasam a recomendação (SHA-256/drift, `remove_component`, rollback com snapshot, `dry_run` só em `aidd-enterprise`; os 2 gates `G_INJECT` sendo genuinamente diferentes; a divergência de nomes de campo PT-BR vs inglês) — são reais, independente do incidente.

## Decisão real do usuário: Opção A (05/09/2026, via pergunta explícita)

Migração completa com enriquecimento do canônico. Escala comparável ao Pacote 7 da rodada 1 — mesma estratégia de dividir em 2 prompts sequenciais para o executor (Prompt A = enriquecer o núcleo, zero risco para `aidd-enterprise`; Prompt B = migrar `aidd-enterprise`, só depois do Prompt A auditado).

### 2 decisões técnicas de implementação (minhas, não do usuário — sinalizo para você poder reverter se discordar)

1. **Convenção de nome de campo do payload interno: PT-BR (`tipo`/`nome`/`descricao`/`conteudo`/`alvo_projeto`/`camada_alvo`), mantendo a de `aidd-master` como a única.** Confirmei que isso é seguro: os flags de CLI de `aidd-enterprise inject` já são PT-BR hoje (`tipo`, `nome`, `--descricao`) — só o dicionário Python interno passado a `aidd_core_injector.materialize()` usa chaves em inglês (`type`/`name`/`description`/`content`). É um detalhe de implementação invisível ao usuário final da CLI; não há API externa pública dependendo dessas chaves em inglês.
2. **Os 5 módulos do núcleo (`profiles_registry.py`, `detector_camada.py`, `materializador.py`, `sincronizador_harness.py`, `result.py`) são COPIADOS para `tools/aidd-enterprise/src/core/` (não movidos para um pacote compartilhado fora das 2 ferramentas).** Cada ferramenta do ecossistema já é um pacote standalone hoje (`aidd-forge`, `aidd-generator`, `aidd-master`, `aidd-enterprise` não compartilham código-fonte entre si, cada uma com seu próprio `src`/`scripts`) — criar um pacote compartilhado novo seria uma mudança de arquitetura maior ainda, fora do escopo deste item. A duplicação controlada (2 cópias, uma por ferramenta) é consistente com o padrão atual do ecossistema.

---

## Definição de Pronto

### FASE 1 (Prompt A) — Enriquecer o núcleo canônico de `aidd-master`, SEM tocar `aidd-enterprise`

1.1. **Drift detection via hash SHA-256.** Em `sincronizador_harness.py`, ao atualizar `CAPABILITIES.json` (`_atualizar_registry`), gravar também o hash SHA-256 de cada arquivo materializado (`arquivos_hashes: {caminho: hash}` na entrada do componente). Criar `verificar_sincronizacao(root_dir) -> Result` (novo, mesmo módulo) que lê `CAPABILITIES.json`, confirma que cada arquivo listado ainda existe e bate com o hash gravado — mesma semântica de `aidd_core_injector.sync_check()`, adaptada ao formato de registry de `aidd-master`.
1.2. **`remover_componente()`.** Novo em `materializador.py`: recebe `tipo`+`nome`+`root_dir`, localiza a entrada em `CAPABILITIES.json`, remove os arquivos físicos (destino + espelhos + canônico, se existir) e a entrada do registry, limpa diretórios vazios resultantes. Expor via `aidd inject --remover <tipo> <nome>` (novo flag) em `scripts/aidd.py`.
1.3. **Rollback com snapshot completo.** Em `materializar()`, ANTES de escrever cada destino, capturar o conteúdo pré-existente (se o arquivo já existir) — não só a lista de "arquivos criados nesta chamada". Em caso de falha de I/O no meio da escrita, restaurar o conteúdo anterior exato de cada destino que já existia, e remover (não restaurar) os que eram novos. Mesma semântica do rollback de `aidd_core_injector.materialize()`.
1.4. **Modo `dry_run`.** Adicionar parâmetro `dry_run: bool = False` a `materializar()` — quando `True`, retorna a lista de destinos que seriam escritos (via `resolver_destinos` + `resolver_conteudo`) sem tocar o disco, sem chamar `sincronizar()`. Adicionar `--dry-run` a `p_inject` em `scripts/aidd.py`; `cmd_inject` propaga a flag.
1.5. **Parametrizar os 2 hardcodes de `"aidd-master"`.** `sincronizar_componente(payload["tipo"], ferramenta=payload["alvo_projeto"])` (em vez do literal `"aidd-master"`); `CANONICAL_TEMPLATES` e `resolve_canonical_destination` recebem o nome do projeto alvo como parâmetro (não mais fixo em `"aidd-master"` dentro do path template — usar `componentes/{alvo_projeto}/hooks/{nome}/hook.sh"` com `.format(alvo_projeto=..., nome=...)`).
1.6. **`config` com mapa arbitrário de arquivos.** Hoje `payload["tipo"] == "config"` em `aidd-master` só gera um único scaffold fixo (`gerar_conteudo_config`, destino `templates/core/config/{nome}.json`) — não existe conceito de múltiplos arquivos. Adicionar ao núcleo: quando o payload trouser um campo novo `arquivos` (dict `{caminho_relativo: conteudo}`, opcional — mesma semântica do `files` de `aidd-enterprise`), `materializar()` escreve cada entrada validando o caminho contra path traversal (nova função `_caminho_seguro(rel: str) -> bool`, mesma lógica de `target_profile.py`: rejeita absoluto, rejeita `..`/segmento vazio) — rejeitar com `Result.fail(codigo="PATH_TRAVERSAL_REJEITADO")` se inválido. Quando `arquivos` não é fornecido, `config` continua gerando o scaffold fixo de hoje (comportamento antigo 100% preservado, é aditivo). Atualizar `schema_injector_request.json` para aceitar a propriedade opcional `arquivos` (objeto, `additionalProperties: {"type": "string"}`).
1.7. Testes reais para cada capacidade nova, seguindo o padrão já estabelecido em `tools/aidd-master/tests/unit/test_injector_core.py` (reprodução real com `tmp_path`, nunca mock do comportamento central): drift detecta um arquivo editado manualmente após injeção; `remover_componente` remove arquivos + espelhos + entrada de registry e limpa diretório vazio; rollback restaura o conteúdo ANTERIOR de um destino que já existia quando uma escrita seguinte falha no meio (não só apaga os novos); `dry_run` não cria nenhum arquivo em disco; `config` com `arquivos` escreve o mapa completo e rejeita pelo menos 1 caminho malicioso (`../../fora`, ou absoluto) com `PATH_TRAVERSAL_REJEITADO`; `config` sem `arquivos` continua gerando o scaffold fixo de sempre (regressão zero).

**Critério de saída Fase 1:**
- Suíte completa de `aidd-master` (`python -m pytest tests/ -q`) → sem regressão, com os testes novos incluídos.
- `python ecossistema.py audit` (bateria raiz) → exit 0, sem regressão.
- Reprodução manual real de cada uma das 5 capacidades novas (injetar, editar manualmente, rodar drift check e ver reprovar; remover e confirmar arquivos+registry limpos; forçar falha no meio de um rollback com sobrescrita e confirmar conteúdo restaurado; `--dry-run` e confirmar `git status`/listagem de arquivos inalterada; `config` com `arquivos` escrevendo múltiplos arquivos e rejeitando um caminho malicioso).
- `aidd-enterprise` **não é tocado nesta fase** (confirmar via `git status` do repositório inteiro).

### FASE 2 (Prompt B, só depois da Fase 1 auditada) — Migrar `aidd-enterprise` para o núcleo enriquecido

2.1. Copiar os 5 módulos (`profiles_registry.py`, `detector_camada.py`, `materializador.py`, `sincronizador_harness.py`, `result.py`, já enriquecidos pela Fase 1) para `tools/aidd-enterprise/src/core/`.
2.2. Criar o perfil `"aidd-enterprise"` em `profiles_registry.py` (a cópia local) com a topologia física REAL deste repositório — ler de `target_profile.py` atual: `skill` → mirrors `.claude/skills`, `.agent/skills`, `.mimocode/skills`, `.gemini/skills`, `.skills` (5 dirs, formato flat, sem aninhamento `skills/`, preservar TODOS — não reduzir pros 3 que `aidd-master` usa hoje, perderia MimoCode); `hook` → preservar o fan-out direto atual nas mesmas 5 pastas de `HARNESS_HOOK_DIRS` (escrevendo `{nome}.json`, formato que já existe, não trocar pra `.sh`), e ADICIONAR por cima a sincronização canônica `componentes/aidd-enterprise/hooks/{nome}/` + `gestor_componentes.py sync` (mesmo padrão híbrido — fan-out E canônico — que `materializador.py` de `aidd-master` já faz, linhas 320-341); `agent` → `templates/agents/{nome}.md`; `rule` → `templates/rules/{nome}.md`; `spec` → `docs/specs/{nome}.md`; `config` → usa a capacidade de mapa arbitrário de arquivos já adicionada ao núcleo na Fase 1 (passo 1.6) — só adaptar `run_inject`/`cmd_inject` de `aidd-enterprise` pra montar `payload["arquivos"]` a partir do `--files-json` já existente, sem duplicar a validação de path traversal (ela já mora no núcleo compartilhado desde a Fase 1).
2.3. Adaptar `run_inject`/`cmd_inject`/`parse_natural_language_intent` em `tools/aidd-enterprise/scripts/aidd.py` para montar o payload PT-BR (decisão 1 acima) e chamar o pipeline canônico (`resolver_destinos` → `materializar` → `sincronizar`) em vez de `injector.aidd_core_injector`. Note que `aidd-enterprise` **já tem** `--dry-run` no CLI hoje (`p_inject.add_argument("--dry-run", ...)`, já propagado a `run_inject`/`materialize`) — não precisa adicionar, só religar pro pipeline novo. O que falta de verdade no CLI de `aidd-enterprise` é a remoção: adicionar `--remover` a `p_inject` (mesmo padrão do novo flag em `aidd-master`, passo 1.2). Preservar 100% do comportamento observável da CLI (mesmos flags, mesmas mensagens de sucesso/erro relevantes) — usuários da CLI não devem notar diferença, exceto pela capacidade nova de remoção.
2.4. Aposentar `tools/aidd-enterprise/scripts/injector/aidd_core_injector.py` e `target_profile.py` (remover — confirmar via grep que não há nenhum outro consumidor além de `aidd.py` e `G_INJECT.py`, ambos migrados nesta fase).
2.5. `G_INJECT.py` de `aidd-enterprise` passa a rodar a mesma checagem de infraestrutura que o de `aidd-master` roda (arquivos core presentes, compila, zero stub, CLI integrada, suíte pytest dedicada) **mais** a checagem de drift agora disponível no núcleo enriquecido (`verificar_sincronizacao`) — os dois gates convergem para a mesma lógica compartilhada (adaptar caminhos para cada projeto alvo).
2.6. Migrar a cobertura de teste: os cenários reais dos 23 testes de `test_aidd_core_injector.py` + 6 de `test_g_inject_gate.py` precisam ter equivalente rodando contra o núcleo canônico agora usado por `aidd-enterprise` (reaproveitar os padrões de `tools/aidd-master/tests/unit/test_injector_core.py`, adaptados ao perfil `"aidd-enterprise"`) — nenhuma cobertura pode regredir, incluindo os cenários de MCP externo (`mcp.json`, merge preservando entradas anteriores) e a proteção de path traversal em `config` (já testada no núcleo pela Fase 1 — aqui é só confirmar que o perfil `"aidd-enterprise"` a usa corretamente via `--files-json`).
2.7. `aidd-enterprise` ganha detecção de linguagem natural via `IntentRouter`+`detector_camada` (mesmo padrão de `_tentar_injecao_por_linguagem_natural` de `aidd-master`), substituindo `_INTENT_KEYWORD_PATTERNS`/`parse_natural_language_intent` atual — preservando o comportamento de fallback para `cmd_plan` quando nenhum padrão de injeção é reconhecido.

**Critério de saída Fase 2:**
- Suíte completa de `aidd-enterprise` (`python -m pytest tests/ -q`) → sem regressão de contagem total (mesmo número de cenários reais cobertos, ainda que os arquivos de teste mudem).
- `python ecossistema.py audit` (bateria raiz) → exit 0.
- Reprodução manual real ponta-a-ponta, nas 2 ferramentas, cobrindo pelo menos: injeção de cada um dos 7 tipos; MCP com e sem `--mcp-command`/`command`; hook aparecendo em `componentes/aidd-enterprise/hooks/` e propagado; drift detection reprovando após edição manual; remoção limpa; `--dry-run` não tocando disco; injeção via linguagem natural PT-BR.
- Suíte completa de `aidd-master` continua sem regressão (confirma que enriquecer o núcleo na Fase 1 não quebrou nada quando reaproveitado na Fase 2).
- `git status` limpo além dos arquivos esperados; nenhum arquivo órfão de teste fora de `tmp_path`.

**Regras de escopo — não fazer:**
- Não mudar os flags de CLI já existentes de `aidd-enterprise inject` (`--dry-run` já existe, só religar; a única adição real de flag é `--remover`).
- Não mover código para um pacote compartilhado fora das 2 ferramentas (decisão técnica 2 acima).
- Não fazer `git commit` nem `git push`.
- Não alterar este documento.

---

## Ordem de execução

2 fases, 2 prompts sequenciais (Prompt B só depois do Prompt A auditado e confirmado) — mesma estratégia do Pacote 7 da rodada 1, pelo mesmo motivo (reduzir raio de impacto de qualquer desvio).

**Aprovado pelo usuário em 05/09/2026.** Prompts de execução abaixo (2 prompts sequenciais — não mande o Prompt B antes do Prompt A ser auditado e confirmado).

---

## Prompt de Execução — FASE 1 (Prompt A)

> Copie o bloco abaixo integralmente para o agente executor. Autocontido — não pressupõe que ele viu esta conversa. **Só este prompt por enquanto — o Prompt B (Fase 2) só deve ser enviado depois que eu auditar esta Fase 1.**

```
Você vai enriquecer o núcleo canônico do Injetor Universal de
tools/aidd-master (monorepo em C:\Users\trcnologia\Desktop\ecossistema-aidd)
com 5 capacidades reais que hoje só existem no injetor antigo e monolítico
de tools/aidd-enterprise (scripts/injector/aidd_core_injector.py). Você
NÃO vai tocar em nada dentro de tools/aidd-enterprise nesta tarefa — isso
é uma fase separada, futura, que só acontece depois desta ser auditada.
Siga EXATAMENTE a Definição de Pronto abaixo, não invente escopo
adicional, e valide tudo de verdade (execuções reais, exit codes reais,
nunca mascarados por pipe).

CONTEXTO JÁ INVESTIGADO (não precisa redescobrir, mas confirme lendo o
código antes de editar):

- O núcleo canônico do injetor vive em tools/aidd-master/src/core/:
  profiles_registry.py (matriz de perfis por projeto alvo + validação de
  payload contra schema_injector_request.json), detector_camada.py
  (heurística PT-BR que decide "tipo" a partir de texto livre),
  materializador.py (escrita transacional dos arquivos + rollback),
  sincronizador_harness.py (atualiza CAPABILITIES.json e âncoras
  multi-harness pós-materialização), result.py (tipo Result de
  sucesso/falha com código estruturado, sem exceções soltas).
- tools/aidd-master/scripts/aidd.py chama esse núcleo em cmd_inject()
  (linha ~650) via construir_request() (detector_camada) e
  _executar_injecao() (linha ~609, que chama resolver_destinos +
  materializar + sincronizar).
- O injetor antigo de referência, SÓ PARA LEITURA (não copie o código
  dele, ele usa nomes de campo em inglês e uma estrutura de registry
  diferente — você vai REIMPLEMENTAR a mesma semântica dentro da
  arquitetura modular de aidd-master, não colar o arquivo):
  tools/aidd-enterprise/scripts/injector/aidd_core_injector.py. Nele:
  - materialize() (linha 116): tem parâmetro dry_run (linha 116) que,
    se True, retorna a lista de arquivos que seriam escritos sem gravar
    nada (linhas 149-150, ANTES de qualquer escrita real). Depois de
    escrever com sucesso, calcula hashlib.sha256 do conteúdo de cada
    arquivo escrito (linha 188) e grava num arquivo de registry
    (COMPONENT-REGISTRY.json, constante REGISTRY_FILENAME linha 39).
  - remove_component(nome, tipo, base_dir) (linha 208): busca a entrada
    do componente no registry, remove cada arquivo físico listado nela,
    limpa diretórios vazios resultantes subindo a árvore (loop while,
    linhas 222-228), e remove a entrada do registry.
  - sync_check(base_dir) (linha 235): para cada entrada do registry,
    confirma que cada arquivo listado ainda existe e recalcula o SHA-256
    comparando com o hash gravado; se algum arquivo sumiu ou o hash
    diverge, acumula uma mensagem de problema e retorna Result.fail com
    codigo="SYNC_DIVERGENTE" e a lista de problemas em detalhes.
  - O rollback de materialize() (linhas 152-186): ANTES de escrever cada
    arquivo real, faz snapshot do conteúdo pré-existente (None se o
    arquivo não existia). Se qualquer escrita falhar no meio, percorre
    os arquivos já escritos nesta chamada e restaura o snapshot exato
    (recria com o conteúdo antigo se existia, remove se era novo).
- O materializador.py ATUAL de aidd-master (leia antes de editar):
  - materializar(payload, resolucao, sobrescrever=False) (linha 231 em
    diante): só remove os arquivos CRIADOS NESTA CHAMADA em caso de
    falha (linhas ~345-356) — não tem conceito de snapshot do conteúdo
    anterior de um destino que já existia e seria sobrescrito.
  - CANONICAL_TEMPLATES = {"hook": "componentes/aidd-master/hooks/{nome}/hook.sh"}
    (linhas 161-163) e resolve_canonical_destination() (linha 174) —
    resolvem um caminho canônico adicional fora dos destinos normais.
  - sincronizar_componente(tipo, ferramenta="aidd-master", ...) (linha
    185): chama "python ecossistema.py components sync --tipo <tipo>
    --ferramenta <ferramenta>" via subprocess, com fallback para
    "import gestor_componentes; gestor_componentes.sync(...)" se o
    subprocess falhar.
  - Dentro de materializar() (linhas 320-341): depois de escrever os
    destinos normais, se existir um destino canônico
    (resolve_canonical_destination) ele também é escrito (melhor
    esforço, sem falhar a operação se der erro), e SE
    payload["tipo"] in CANONICAL_TEMPLATES, chama
    sincronizar_componente(payload["tipo"], ferramenta="aidd-master") —
    aqui está o hardcode literal "aidd-master" que ignora
    payload["alvo_projeto"].
  - gerar_conteudo_config(nome, descricao) (linha 130): gera SEMPRE um
    único JSON fixo {"nome":..., "descricao":..., "gerado_em":...,
    "parametros": {}} — não existe hoje nenhum conceito de multi-arquivo
    para o tipo "config".
- schema_injector_request.json (tools/aidd-master/src/core/) tem
  "required": ["tipo", "nome", "descricao", "alvo_projeto"] e
  "additionalProperties": false — qualquer campo novo no payload
  (ex.: "arquivos") precisa ser adicionado explicitamente em
  "properties" para não ser rejeitado.
- Testes existentes de referência (leia o padrão, reaproveite o estilo,
  não invente uma forma nova de importar/testar):
  tools/aidd-master/tests/unit/test_injector_core.py — importa os
  módulos do núcleo diretamente (sys.path.insert dos diretórios src/ e
  src/core/, depois "import materializador" etc., não
  importlib.util.spec_from_file_location), organizado em fases
  numeradas por comentário. tools/aidd-master/tests/unit/test_drift_gate_blind_spot.py
  mostra o padrão de teste real com tmp_path para gates que leem/escrevem
  arquivos de verdade.

DECISÕES JÁ TOMADAS (não reabra estas discussões):
1. As 5 capacidades (drift SHA-256, remoção, rollback com snapshot
   completo, dry_run, config com mapa arbitrário de arquivos) são
   REIMPLEMENTADAS dentro da arquitetura modular existente (adaptando à
   estrutura de CAPABILITIES.json/materializador.py/sincronizador_harness.py
   já em uso) — não é para importar nem copiar código de
   aidd_core_injector.py, e não é para criar um COMPONENT-REGISTRY.json
   paralelo; o registro de hashes deve viver dentro de CAPABILITIES.json
   (ex.: um campo novo "arquivos_hashes": {caminho: hash} na entrada de
   cada componente).
2. dry_run precisa retornar ANTES de qualquer escrita real em disco (nem
   staging, nem definitivo) — só a lista de destinos que seriam
   escritos, calculada por resolver_destinos + resolver_conteudo.
3. remover_componente() precisa limpar diretórios vazios resultantes
   (mesma lógica de subir a árvore removendo pastas vazias que
   remove_component() do injetor antigo já faz).
4. config com "arquivos" é ADITIVO — quando o payload não traz
   "arquivos", o comportamento de hoje (scaffold fixo único) continua
   idêntico. Validação de path traversal: rejeitar caminho absoluto,
   segmento ".." ou segmento vazio (mesma lógica de _caminho_seguro do
   injetor antigo).
5. Os 2 hardcodes de "aidd-master" (sincronizar_componente e
   CANONICAL_TEMPLATES) passam a usar payload["alvo_projeto"] em vez do
   literal fixo — isso é o que permite, na Fase 2 (futura, fora desta
   tarefa), um projeto alvo diferente usar a mesma função sem
   reescrevê-la.
6. Não mexer no mecanismo de fan-out direto do tipo "hook" (as 3 pastas
   de harness fixas em profiles_registry.PROFILES) — só parametrizar o
   destino CANÔNICO adicional (componentes/{alvo_projeto}/hooks/...),
   que é o que os 2 hardcodes controlam.

DEFINIÇÃO DE PRONTO — nesta ordem, tudo dentro de tools/aidd-master/:

1.1. Drift detection via hash SHA-256. Em sincronizador_harness.py,
     dentro de _atualizar_registry(), calcular e gravar
     hashlib.sha256(conteúdo do arquivo).hexdigest() para cada arquivo
     em "arquivos_criados", num campo novo "arquivos_hashes":
     {caminho_relativo_ao_root: hash} na entrada do componente dentro de
     CAPABILITIES.json (caminho relativo, não absoluto, pra sobreviver a
     mudança de root_dir). Criar verificar_sincronizacao(root_dir) ->
     Result (novo, mesmo módulo): lê CAPABILITIES.json, para cada
     componente com "arquivos_hashes", confirma que cada arquivo ainda
     existe (caminho relativo + root_dir) e bate com o hash gravado;
     acumula uma lista de problemas (arquivo ausente OU hash divergente,
     mensagens similares às de sync_check do injetor antigo); se houver
     problemas, Result.fail(codigo="SYNC_DIVERGENTE",
     detalhes={"problemas": [...]}); senão Result.ok.
1.2. remover_componente(tipo, nome, root_dir) -> Result. Novo em
     materializador.py: lê CAPABILITIES.json, localiza a entrada
     catalogo[tipo] com nome==nome, remove cada arquivo físico listado
     em "arquivos_hashes" (ou no campo de arquivos que a Fase 1.1 usar
     para listá-los), limpa diretórios vazios resultantes (subir a
     árvore, parar em root_dir), remove a entrada do registry, grava
     CAPABILITIES.json de volta. Se o componente não existir no
     registry: Result.fail(codigo="COMPONENTE_NAO_ENCONTRADO"). Expor
     via novo flag --remover em p_inject (tools/aidd-master/scripts/aidd.py,
     função main(), perto de onde p_inject é definido) — quando
     presente, cmd_inject() chama remover_componente() em vez do fluxo
     normal de materialização, e sys.exit(0 se sucesso, 1 se falha).
1.3. Rollback com snapshot completo. Em materializar() (materializador.py),
     antes do loop que escreve "destinos" (linha ~311 hoje), para cada
     destino que já existir (os.path.isfile), ler e guardar o conteúdo
     atual num dict snapshot {destino: bytes_ou_None}; destinos que não
     existem ainda entram como None. No except que hoje só remove
     "criados" (linhas ~345-350), trocar por: para cada destino em
     "criados", se snapshot[destino] is None, remover (comportamento
     atual); senão, reescrever o destino com snapshot[destino] (restaura
     o conteúdo anterior exato). Testar com um destino PRÉ-EXISTENTE
     forçando falha na escrita de um destino seguinte na mesma chamada.
1.4. Modo dry_run. Adicionar parâmetro dry_run: bool = False a
     materializar(). Quando True, calcular "destinos" e "conteudo" (via
     resolver_destinos + resolver_conteudo, já existentes) e retornar
     Result.ok(destinos, detalhes={"dry_run": True}) SEM escrever nada
     em disco e SEM chamar sincronizar(). Propagar dry_run por toda a
     cadeia de chamada até cmd_inject(); adicionar --dry-run a p_inject
     em scripts/aidd.py.
1.5. config com mapa arbitrário de arquivos. Adicionar
     "arquivos" (opcional) ao schema_injector_request.json ("type":
     "object", "additionalProperties": {"type": "string"}). Em
     materializar() (ou resolver_conteudo/resolver_destinos, o que fizer
     mais sentido lendo o código), quando payload.get("tipo") ==
     "config" e payload.get("arquivos") existir: para cada
     {caminho_relativo: conteudo} em "arquivos", validar caminho_relativo
     com uma função nova _caminho_seguro(rel) -> bool (rejeita
     os.path.isabs, rejeita segmento ".." ou segmento vazio depois de
     normalizar barras) — se inválido,
     Result.fail(codigo="PATH_TRAVERSAL_REJEITADO",
     detalhes={"caminho": rel}) e ABORTAR (não escrever nenhum arquivo
     desse payload). Se todos os caminhos forem válidos, escrever cada
     um relativo ao root_dir resolvido (mesma transação/rollback do
     resto de materializar() — se um arquivo do mapa falhar no meio,
     mesmo rollback do passo 1.3 se aplica). Quando "arquivos" não é
     fornecido, gerar_conteudo_config() continua sendo usado exatamente
     como hoje (scaffold único fixo).
1.6. Parametrizar os 2 hardcodes de "aidd-master". Em
     sincronizar_componente(), trocar o default ferramenta="aidd-master"
     por receber o valor de payload["alvo_projeto"] no ponto de chamada
     (linha ~341 hoje: sincronizar_componente(payload["tipo"],
     ferramenta="aidd-master") vira
     sincronizar_componente(payload["tipo"], ferramenta=payload["alvo_projeto"])).
     CANONICAL_TEMPLATES e resolve_canonical_destination(): o template
     "componentes/aidd-master/hooks/{nome}/hook.sh" vira
     "componentes/{alvo_projeto}/hooks/{nome}/hook.sh", parametrizado
     por um novo argumento alvo_projeto na função (ou lido do payload no
     ponto de chamada) — não hardcoded no dict.
1.7. Testes reais (tmp_path, nunca mock do comportamento central),
     seguindo o padrão de test_injector_core.py: (a) injeta um
     componente, edita manualmente um dos arquivos gerados, chama
     verificar_sincronizacao() e confirma Result.fail com
     "SYNC_DIVERGENTE"; injeta de novo sem editar nada, confirma
     Result.ok; (b) injeta um componente, chama remover_componente(),
     confirma que os arquivos físicos sumiram, a entrada saiu do
     CAPABILITIES.json, e diretórios vazios resultantes foram limpos;
     chama remover_componente() de novo pro mesmo nome, confirma
     Result.fail "COMPONENTE_NAO_ENCONTRADO"; (c) cria um destino
     pré-existente com conteúdo X, força uma falha de escrita num
     destino seguinte da mesma chamada (ex.: monkeypatch open() pra
     lançar exceção só na 2ª chamada), confirma que o destino
     pré-existente voltou a ter conteúdo X depois do rollback; (d) chama
     materializar(dry_run=True), confirma que nenhum arquivo foi criado
     (os.path.exists False em todos os destinos) e que o resultado lista
     os destinos esperados; (e) injeta um "config" com "arquivos":
     {"a/b.json": "{}", "c.txt": "ok"}, confirma que os 2 arquivos foram
     escritos com o conteúdo certo; tenta injetar com "arquivos":
     {"../fora.txt": "x"}, confirma Result.fail
     "PATH_TRAVERSAL_REJEITADO" e que nenhum arquivo foi escrito; injeta
     um "config" SEM "arquivos", confirma que o scaffold fixo de sempre
     ainda é gerado (regressão zero).

CRITÉRIO DE SAÍDA (rode e cole o output real de cada um):
- Suíte completa de aidd-master (python -m pytest tests/ -q) → sem
  regressão, com os testes novos incluídos na contagem.
- python ecossistema.py audit (rodado da raiz do monorepo) → exit 0,
  sem regressão.
- Reprodução manual real (fora dos arquivos de teste) de cada uma das 5
  capacidades: (1) injetar um componente real via CLI, editar um arquivo
  manualmente, rodar a checagem de drift e ver reprovar com a mensagem
  certa; (2) remover o componente via --remover e confirmar arquivos e
  entrada do registry sumiram; (3) forçar uma falha no meio de uma
  injeção que sobrescreveria um arquivo existente e confirmar que o
  conteúdo anterior voltou; (4) rodar com --dry-run e confirmar via git
  status/listagem de diretório que nada foi criado; (5) injetar um
  "config" com múltiplos arquivos reais e confirmar que todos foram
  escritos, depois tentar um caminho malicioso e confirmar rejeição.
- Confirme por comando (git status, na raiz do repositório inteiro) que
  tools/aidd-enterprise não foi tocado em nenhum arquivo.
- Confirme que nenhum teste novo deixou arquivo fora de tmp_path.

REGRAS DE ESCOPO — NÃO FAÇA:
- Não toque em nenhum arquivo dentro de tools/aidd-enterprise/ — isso é
  uma fase futura separada.
- Não copie aidd_core_injector.py nem crie um COMPONENT-REGISTRY.json
  novo — reimplemente a semântica dentro de CAPABILITIES.json.
- Não mude o mecanismo de fan-out direto do tipo "hook" (as 3 pastas de
  harness em profiles_registry.PROFILES) — só parametrize o destino
  canônico adicional (item 1.6).
- Não faça git commit nem git push.
- Não altere docs/planos/refinamento-notas-auditoria/04-unificacao-injetor-aidd-enterprise.md.

ENTREGÁVEL: lista exata de arquivos criados/alterados; comando + output
real que comprova cada item do Critério de Saída; qualquer desvio
necessário, reportado explicitamente em vez de decidido sozinho.
```

## Prompt de Execução — FASE 1 (Prompt A) — English version

```
You are going to enrich the canonical core of the Universal Injector in
tools/aidd-master (monorepo at C:\Users\trcnologia\Desktop\ecossistema-aidd)
with 5 real capabilities that today only exist in aidd-enterprise's old
monolithic injector (scripts/injector/aidd_core_injector.py). You will
NOT touch anything inside tools/aidd-enterprise in this task — that is a
separate, future phase that only happens after this one is audited.
Follow the Definition of Done below EXACTLY, do not invent additional
scope, and validate everything for real (real runs, real exit codes,
never masked by a pipe).

ALREADY-INVESTIGATED CONTEXT (no need to rediscover, but confirm by
reading the code before editing):

- The injector's canonical core lives in tools/aidd-master/src/core/:
  profiles_registry.py (per-target-project profile matrix + payload
  validation against schema_injector_request.json), detector_camada.py
  (PT-BR heuristic that decides "tipo" from free text), materializador.py
  (transactional file writing + rollback), sincronizador_harness.py
  (updates CAPABILITIES.json and multi-harness anchors after
  materialization), result.py (Result type for success/failure with a
  structured code, no bare exceptions).
- tools/aidd-master/scripts/aidd.py calls this core in cmd_inject()
  (line ~650) via construir_request() (detector_camada) and
  _executar_injecao() (line ~609, which calls resolver_destinos +
  materializar + sincronizar).
- The old reference injector, READ-ONLY (do not copy its code, it uses
  English field names and a different registry structure — you will
  REIMPLEMENT the same semantics inside aidd-master's modular
  architecture, not paste the file):
  tools/aidd-enterprise/scripts/injector/aidd_core_injector.py. In it:
  - materialize() (line 116): has a dry_run parameter (line 116) that,
    if True, returns the list of files that would be written without
    writing anything (lines 149-150, BEFORE any real write). After
    writing successfully, it computes hashlib.sha256 of each written
    file's content (line 188) and stores it in a registry file
    (COMPONENT-REGISTRY.json, constant REGISTRY_FILENAME line 39).
  - remove_component(nome, tipo, base_dir) (line 208): looks up the
    component's registry entry, removes each physical file listed in
    it, cleans up resulting empty directories (while loop walking up,
    lines 222-228), and removes the registry entry.
  - sync_check(base_dir) (line 235): for each registry entry, confirms
    each listed file still exists and recomputes SHA-256 comparing
    against the stored hash; if any file is missing or the hash
    diverges, it accumulates a problem message and returns Result.fail
    with codigo="SYNC_DIVERGENTE" and the problem list in detalhes.
  - materialize()'s rollback (lines 152-186): BEFORE writing each real
    file, it snapshots the pre-existing content (None if the file did
    not exist). If any write fails midway, it walks the files already
    written in this call and restores the exact snapshot (recreates
    with the old content if it existed, removes if it was new).
- aidd-master's CURRENT materializador.py (read before editing):
  - materializar(payload, resolucao, sobrescrever=False) (line 231
    onward): only removes files CREATED IN THIS CALL on failure (lines
    ~345-356) — has no concept of snapshotting the prior content of a
    destination that already existed and would be overwritten.
  - CANONICAL_TEMPLATES = {"hook": "componentes/aidd-master/hooks/{nome}/hook.sh"}
    (lines 161-163) and resolve_canonical_destination() (line 174) —
    resolve an additional canonical path outside the normal
    destinations.
  - sincronizar_componente(tipo, ferramenta="aidd-master", ...) (line
    185): runs "python ecossistema.py components sync --tipo <tipo>
    --ferramenta <ferramenta>" via subprocess, falling back to "import
    gestor_componentes; gestor_componentes.sync(...)" if the subprocess
    fails.
  - Inside materializar() (lines 320-341): after writing the normal
    destinations, if a canonical destination exists
    (resolve_canonical_destination) it is also written (best-effort,
    does not fail the operation on error), and IF payload["tipo"] in
    CANONICAL_TEMPLATES, it calls sincronizar_componente(payload["tipo"],
    ferramenta="aidd-master") — this is the literal "aidd-master"
    hardcode that ignores payload["alvo_projeto"].
  - gerar_conteudo_config(nome, descricao) (line 130): ALWAYS generates
    a single fixed JSON {"nome":..., "descricao":..., "gerado_em":...,
    "parametros": {}} — there is no concept today of a multi-file
    mapping for the "config" type.
- schema_injector_request.json (tools/aidd-master/src/core/) has
  "required": ["tipo", "nome", "descricao", "alvo_projeto"] and
  "additionalProperties": false — any new payload field (e.g.
  "arquivos") needs to be added explicitly to "properties" or it will
  be rejected.
- Existing reference tests (read the pattern, reuse the style, do not
  invent a new way to import/test):
  tools/aidd-master/tests/unit/test_injector_core.py — imports the core
  modules directly (sys.path.insert of the src/ and src/core/
  directories, then "import materializador" etc., not
  importlib.util.spec_from_file_location), organized in numbered phases
  by comment. tools/aidd-master/tests/unit/test_drift_gate_blind_spot.py
  shows the real-test pattern with tmp_path for gates that read/write
  real files.

DECISIONS ALREADY MADE (do not reopen these):
1. The 5 capabilities (SHA-256 drift, removal, full-snapshot rollback,
   dry_run, config with an arbitrary file map) are REIMPLEMENTED inside
   the existing modular architecture (adapting to the
   CAPABILITIES.json/materializador.py/sincronizador_harness.py
   structure already in use) — do not import or copy code from
   aidd_core_injector.py, and do not create a parallel
   COMPONENT-REGISTRY.json; the hash registry must live inside
   CAPABILITIES.json (e.g. a new "arquivos_hashes": {path: hash} field
   on each component's entry).
2. dry_run must return BEFORE any real disk write (no staging, no
   final) — just the list of destinations that would be written,
   computed via resolver_destinos + resolver_conteudo.
3. remover_componente() must clean up resulting empty directories (same
   walk-up-and-remove-empty-dirs logic that remove_component() in the
   old injector already does).
4. config with "arquivos" is ADDITIVE — when the payload does not carry
   "arquivos", today's behavior (single fixed scaffold) stays identical.
   Path traversal validation: reject an absolute path, a ".." segment,
   or an empty segment (same logic as the old injector's
   _caminho_seguro).
5. The 2 "aidd-master" hardcodes (sincronizar_componente and
   CANONICAL_TEMPLATES) switch to using payload["alvo_projeto"] instead
   of the fixed literal — this is what allows, in the future Fase 2
   (outside this task), a different target project to use the same
   function without rewriting it.
6. Do not touch the "hook" type's direct fan-out mechanism (the 3 fixed
   harness dirs in profiles_registry.PROFILES) — only parametrize the
   additional CANONICAL destination (componentes/{alvo_projeto}/hooks/...),
   which is what the 2 hardcodes control.

DEFINITION OF DONE — in this order, all inside tools/aidd-master/:

1.1. SHA-256 hash drift detection. In sincronizador_harness.py, inside
     _atualizar_registry(), compute and store
     hashlib.sha256(file content).hexdigest() for each file in
     "arquivos_criados", in a new "arquivos_hashes":
     {path_relative_to_root: hash} field on the component's entry inside
     CAPABILITIES.json (relative path, not absolute, so it survives a
     different root_dir). Create verificar_sincronizacao(root_dir) ->
     Result (new, same module): reads CAPABILITIES.json, for each
     component with "arquivos_hashes", confirms each file still exists
     (relative path + root_dir) and matches the stored hash; accumulates
     a list of problems (missing file OR divergent hash, messages
     similar to the old injector's sync_check); if there are problems,
     Result.fail(codigo="SYNC_DIVERGENTE",
     detalhes={"problemas": [...]}); else Result.ok.
1.2. remover_componente(tipo, nome, root_dir) -> Result. New in
     materializador.py: reads CAPABILITIES.json, finds the
     catalogo[tipo] entry with nome==nome, removes each physical file
     listed in "arquivos_hashes" (or whatever field Fase 1.1 uses to
     list them), cleans up resulting empty directories (walk up the
     tree, stop at root_dir), removes the registry entry, writes
     CAPABILITIES.json back. If the component does not exist in the
     registry: Result.fail(codigo="COMPONENTE_NAO_ENCONTRADO"). Expose
     via a new --remover flag on p_inject
     (tools/aidd-master/scripts/aidd.py, main() function, near where
     p_inject is defined) — when present, cmd_inject() calls
     remover_componente() instead of the normal materialization flow,
     and sys.exit(0 on success, 1 on failure).
1.3. Full-snapshot rollback. In materializar() (materializador.py),
     before the loop that writes "destinos" (line ~311 today), for each
     destination that already exists (os.path.isfile), read and store
     its current content in a snapshot dict {destination: bytes_or_None};
     destinations that do not exist yet get None. In the except block
     that today only removes "criados" (lines ~345-350), replace with:
     for each destination in "criados", if snapshot[destination] is
     None, remove it (today's behavior); else, rewrite the destination
     with snapshot[destination] (restores the exact prior content). Test
     with a PRE-EXISTING destination while forcing a failure on a
     subsequent destination's write in the same call.
1.4. dry_run mode. Add a dry_run: bool = False parameter to
     materializar(). When True, compute "destinos" and "conteudo" (via
     the already-existing resolver_destinos + resolver_conteudo) and
     return Result.ok(destinos, detalhes={"dry_run": True}) WITHOUT
     writing anything to disk and WITHOUT calling sincronizar(). Propagate
     dry_run all the way to cmd_inject(); add --dry-run to p_inject in
     scripts/aidd.py.
1.5. config with an arbitrary file map. Add "arquivos" (optional) to
     schema_injector_request.json ("type": "object",
     "additionalProperties": {"type": "string"}). In materializar() (or
     resolver_conteudo/resolver_destinos, whichever makes more sense
     after reading the code), when payload.get("tipo") == "config" and
     payload.get("arquivos") exists: for each {relative_path: content}
     in "arquivos", validate relative_path with a new
     _caminho_seguro(rel) -> bool function (rejects os.path.isabs,
     rejects a ".." segment or an empty segment after normalizing
     slashes) — if invalid, Result.fail(codigo="PATH_TRAVERSAL_REJEITADO",
     detalhes={"caminho": rel}) and ABORT (write no file from that
     payload). If all paths are valid, write each one relative to the
     resolved root_dir (same transaction/rollback as the rest of
     materializar() — if one file in the map fails midway, the same
     rollback from step 1.3 applies). When "arquivos" is not provided,
     gerar_conteudo_config() keeps being used exactly as today (single
     fixed scaffold).
1.6. Parametrize the 2 "aidd-master" hardcodes. In
     sincronizar_componente(), change the default ferramenta="aidd-master"
     to receiving payload["alvo_projeto"]'s value at the call site (line
     ~341 today: sincronizar_componente(payload["tipo"],
     ferramenta="aidd-master") becomes
     sincronizar_componente(payload["tipo"], ferramenta=payload["alvo_projeto"])).
     CANONICAL_TEMPLATES and resolve_canonical_destination(): the
     "componentes/aidd-master/hooks/{nome}/hook.sh" template becomes
     "componentes/{alvo_projeto}/hooks/{nome}/hook.sh", parametrized by
     a new alvo_projeto argument on the function (or read from the
     payload at the call site) — not hardcoded in the dict.
1.7. Real tests (tmp_path, never mocking the central behavior),
     following test_injector_core.py's pattern: (a) inject a component,
     manually edit one of the generated files, call
     verificar_sincronizacao() and confirm Result.fail with
     "SYNC_DIVERGENTE"; inject again without editing anything, confirm
     Result.ok; (b) inject a component, call remover_componente(),
     confirm the physical files are gone, the entry left
     CAPABILITIES.json, and resulting empty directories were cleaned up;
     call remover_componente() again for the same name, confirm
     Result.fail "COMPONENTE_NAO_ENCONTRADO"; (c) create a pre-existing
     destination with content X, force a write failure on a subsequent
     destination in the same call (e.g. monkeypatch open() to raise only
     on the 2nd call), confirm the pre-existing destination has content X
     again after the rollback; (d) call materializar(dry_run=True),
     confirm no file was created (os.path.exists False on every
     destination) and that the result lists the expected destinations;
     (e) inject a "config" with "arquivos": {"a/b.json": "{}", "c.txt":
     "ok"}, confirm both files were written with the right content; try
     injecting with "arquivos": {"../fora.txt": "x"}, confirm
     Result.fail "PATH_TRAVERSAL_REJEITADO" and that no file was
     written; inject a "config" WITHOUT "arquivos", confirm the usual
     fixed scaffold is still generated (zero regression).

EXIT CRITERIA (run and paste the real output of each):
- Full aidd-master suite (python -m pytest tests/ -q) → no regression,
  with the new tests included in the count.
- python ecossistema.py audit (run from the monorepo root) → exit 0, no
  regression.
- Real manual reproduction (outside the test files) of each of the 5
  capabilities: (1) inject a real component via the CLI, manually edit a
  file, run the drift check and see it fail with the right message; (2)
  remove the component via --remover and confirm files and the registry
  entry are gone; (3) force a failure midway through an injection that
  would overwrite an existing file and confirm the prior content came
  back; (4) run with --dry-run and confirm via git status/directory
  listing that nothing was created; (5) inject a "config" with multiple
  real files and confirm all were written, then try a malicious path and
  confirm rejection.
- Confirm via command (git status, at the whole repository root) that
  tools/aidd-enterprise was not touched at all.
- Confirm no new test left a file outside tmp_path.

SCOPE RULES — DO NOT:
- Do not touch any file inside tools/aidd-enterprise/ — that is a
  separate future phase.
- Do not copy aidd_core_injector.py nor create a new
  COMPONENT-REGISTRY.json — reimplement the semantics inside
  CAPABILITIES.json.
- Do not change the "hook" type's direct fan-out mechanism (the 3
  harness dirs in profiles_registry.PROFILES) — only parametrize the
  additional canonical destination (item 1.6).
- Do not git commit or git push.
- Do not modify docs/planos/refinamento-notas-auditoria/04-unificacao-injetor-aidd-enterprise.md.

DELIVERABLE: exact list of files created/changed; command + real output
proving each item of the Exit Criteria; any necessary deviation,
explicitly reported instead of decided by yourself.
```

---

## Prompt de Execução — FASE 2 (Prompt B)

> ⚠️ **Só envie este prompt depois que eu tiver auditado e confirmado a Fase 1.** Ele pressupõe que `verificar_sincronizacao()`, `remover_componente()`, `dry_run` em `materializar()`, `config` com `arquivos`, e a parametrização de `alvo_projeto` já existem e estão testados em `tools/aidd-master/src/core/` exatamente como a Fase 1 os criou. Copie o bloco abaixo integralmente para o agente executor — autocontido, mas assume que o núcleo já foi enriquecido.

```
Você vai migrar tools/aidd-enterprise (monorepo em
C:\Users\trcnologia\Desktop\ecossistema-aidd) do seu injetor antigo e
monolítico (scripts/injector/aidd_core_injector.py +
scripts/injector/target_profile.py) para a MESMA arquitetura modular de
5 arquivos que tools/aidd-master usa (src/core/profiles_registry.py,
detector_camada.py, materializador.py, sincronizador_harness.py,
result.py) — já enriquecida numa fase anterior com drift SHA-256,
remoção, rollback com snapshot completo, dry_run e config com mapa
arbitrário de arquivos. Siga EXATAMENTE a Definição de Pronto abaixo,
não invente escopo adicional, e valide tudo de verdade (execuções reais,
exit codes reais, nunca mascarados por pipe). Isto é um trabalho de
escala comparável ao Pacote 7 da Rodada 1 de evolução de notas — espera-se
múltiplos arquivos e algumas horas de trabalho real, não um ajuste
trivial.

IMPORTANTE — o que este prompt NÃO pede: não é para reduzir nenhuma
capacidade física que tools/aidd-enterprise já tem hoje (cobertura de 5
harnesses incluindo MimoCode, arquivos `.json` de hook, mapa arbitrário
de `config`, merge de `mcp.json` externo preservando entradas
anteriores, proteção de path traversal). O núcleo compartilhado
enriquecido na Fase 1 tem que dar conta de TUDO que
`aidd_core_injector.py` já fazia, sem exceção — se em algum ponto a
arquitetura canônica não suportar algo que o injetor antigo suporta e
que não foi coberto pela Fase 1, PARE e reporte isso explicitamente em
vez de decidir sozinho descartar a capacidade.

CONTEXTO JÁ INVESTIGADO (não precisa redescobrir, mas confirme lendo o
código antes de editar):

- tools/aidd-enterprise/scripts/injector/aidd_core_injector.py (262
  linhas) e target_profile.py são os 2 arquivos a aposentar no final
  desta fase. target_profile.py mapeia cada "type" pra rotas físicas:
  skill -> fan-out em HARNESS_SKILL_DIRS = [".claude/skills",
  ".agent/skills", ".mimocode/skills", ".gemini/skills", ".skills"] (5
  dirs, formato "flat" sem aninhamento "skills/" extra, escrevendo
  "{dir}/{nome}/SKILL.md"); hook -> fan-out em HARNESS_HOOK_DIRS = mesma
  lista trocando "skills" por "hooks" (5 dirs), escrevendo
  "{dir}/{nome}.json"; agent -> "templates/agents/{nome}.md"; rule ->
  "templates/rules/{nome}.md"; spec -> "docs/specs/{nome}.md"; mcp ->
  lê mcp.json existente (se houver), faz merge preservando
  "mcpServers" já cadastrados, adiciona/atualiza a entrada do nome
  atual com {command, args, env}; config -> aceita um dict arbitrário
  "files" ({caminho_relativo: conteudo}), valida cada caminho com
  _caminho_seguro() (rejeita absoluto, ".." ou segmento vazio) antes de
  escrever.
- tools/aidd-enterprise/scripts/aidd.py (leia antes de editar):
  - Payload usa chaves em INGLÊS: component = {"type": tipo, "name":
    nome, "description": descricao} (função run_inject, por volta da
    linha 832-840), mais "content" (skill/rule/spec/agent/hook), "mcp"
    ({"command", "args", "env"}), ou "files" (config).
  - run_inject(tipo, nome, base_dir=".", descricao="", content=None,
    content_file=None, command=None, mcp_args=None, mcp_env=None,
    files_json=None, dry_run=False) monta o dict acima e chama
    injector_core.materialize(component, base_dir=base_dir,
    dry_run=dry_run) (linha ~838, "from injector import
    aidd_core_injector as injector_core").
  - cmd_inject(args) (linha ~883) parseia os argumentos do argparse e
    chama run_inject(...).
  - p_inject (dentro de main(), por volta da linha 1044) já tem
    --dry-run funcionando (propagado até materialize()) — NÃO precisa
    adicionar esse flag, só religar pro pipeline novo. Falta um flag
    --remover (mesmo padrão do que a Fase 1 já adicionou em
    aidd-master).
  - _default_component_content(tipo, nome, descricao) (linha ~805) gera
    conteúdo padrão quando --content-file não é passado — usada só
    quando o usuário não fornece conteúdo explícito.
  - _INTENT_KEYWORD_PATTERNS (linha ~917) + parse_natural_language_intent
    (linha ~928): reconhecimento de linguagem natural PT-BR já existe
    hoje, mas usa a PRIMEIRA regra da lista que casar (regex simples por
    tipo), sem detectar ambiguidade quando o texto bate em mais de um
    padrão.
  - _slugify(texto) (linha ~901): converte texto livre em slug
    kebab-case — equivalente ao que detector_camada.py de aidd-master
    já faz para o campo "nome".
- tools/aidd-enterprise/scripts/gates/G_INJECT.py (87 linhas,
  verificar_injector(target_dir=".")): audita se os componentes JÁ
  INJETADOS num projeto continuam íntegros — hoje isso significa chamar
  sync_check() do injetor antigo. tools/aidd-master/scripts/gates/G_INJECT.py
  (220 linhas, classe com múltiplos métodos de checagem): audita a
  PRÓPRIA infraestrutura do injetor (arquivos core presentes, compila
  via py_compile, zero stub via AST, CLI integrada, suíte pytest
  dedicada 100% verde, "prova de fogo" de pelo menos 1 componente real
  em CAPABILITIES.json) — não audita componentes de terceiros. São
  auditorias de coisas diferentes, ambas precisam continuar existindo.
- tools/aidd-enterprise/tests/unit/test_aidd_core_injector.py (23
  testes) e test_g_inject_gate.py (6 testes): leia os cenários reais
  cobertos antes de migrar — cada cenário real precisa ter equivalente
  rodando contra o núcleo novo, mesmo que os arquivos/nomes de teste
  mudem.
- tools/aidd-master/src/core/profiles_registry.py's PROFILES["aidd-master"]
  é a referência de FORMATO de perfil (skill/mcp/rule/spec/config/agent/hook,
  cada um com "dest", "mirrors" opcional, "registry", "camada_alvo") —
  mas o CONTEÚDO do perfil de "aidd-enterprise" é diferente do de
  "aidd-master" em pelo menos: skill/hook têm 5 mirrors (não 3, MimoCode
  + ".skills"/".hooks" flat inclusos), hook escreve "{nome}.json" (não
  "{nome}/hook.sh").

DECISÕES JÁ TOMADAS (não reabra estas discussões):
1. Convenção de nome de campo do payload interno passa a ser PT-BR
   (tipo/nome/descricao/conteudo/alvo_projeto/camada_alvo), igual à de
   aidd-master — não duas convenções coexistindo. Os FLAGS de CLI
   (--descricao, --content-file, etc.) já são PT-BR hoje e não mudam;
   só o dict Python interno passado ao núcleo muda de inglês pra PT-BR.
2. Os 5 módulos do núcleo (profiles_registry.py, detector_camada.py,
   materializador.py, sincronizador_harness.py, result.py) são
   COPIADOS para tools/aidd-enterprise/src/core/ — não movidos para um
   pacote compartilhado fora das 2 ferramentas. Cada ferramenta
   continua sendo um pacote standalone.
3. O fan-out direto de skill/hook em 5 pastas (incluindo MimoCode e os
   diretórios flat ".skills"/".hooks") é PRESERVADO — o perfil novo
   "aidd-enterprise" em profiles_registry.py usa 5 mirrors, não os 3 que
   o perfil "aidd-master" usa. Hook escreve "{nome}.json" (formato atual
   de aidd-enterprise), não "{nome}/hook.sh" (formato de aidd-master) —
   são produtos diferentes, não precisam convergir o FORMATO do
   arquivo, só ganhar a sincronização canônica adicional (item 2 abaixo).
4. Hook em aidd-enterprise ganha, ALÉM do fan-out direto já existente
   (preservado), a sincronização canônica adicional
   componentes/aidd-enterprise/hooks/{nome}/... + gestor_componentes.py
   sync — mesmo padrão híbrido (fan-out E canônico, não fan-out OU
   canônico) que aidd-master já usa para seu próprio hook.
5. config em aidd-enterprise usa a capacidade "arquivos" já adicionada
   ao núcleo na Fase 1 — só adaptar run_inject/cmd_inject pra montar
   payload["arquivos"] a partir do --files-json já existente (que hoje
   lê um JSON e passa como component["files"]). A validação de path
   traversal já mora no núcleo compartilhado, não duplicar.
6. G_INJECT.py de aidd-enterprise passa a rodar AMBAS as checagens: a
   de infraestrutura do injetor (adaptada de aidd-master's G_INJECT.py,
   ajustando caminhos pra aidd-enterprise) MAIS a de drift pós-injeção
   (agora via verificar_sincronizacao() do núcleo, em vez de sync_check()
   do injetor antigo) — não escolher uma em vez da outra.
7. --dry-run de aidd-enterprise JÁ EXISTE e já está propagado até
   materialize() — só precisa continuar funcionando depois de trocar
   o "materialize()" de baixo (religar pro pipeline novo). --remover é
   a única adição real de flag no CLI.

DEFINIÇÃO DE PRONTO — nesta ordem, tudo dentro de tools/aidd-enterprise/,
usando o núcleo já enriquecido pela Fase 1:

2.1. Copiar profiles_registry.py, detector_camada.py, materializador.py,
     sincronizador_harness.py, result.py de tools/aidd-master/src/core/
     (já enriquecidos) para tools/aidd-enterprise/src/core/ (criar o
     diretório se não existir — confirme antes se já existe algum
     src/core/ com outro propósito, e não sobrescreva nada que não seja
     desses 5 arquivos).
2.2. Na cópia local de profiles_registry.py, adicionar
     PROFILES["aidd-enterprise"] com a topologia REAL deste repositório,
     lida de target_profile.py atual: skill -> dest e mirrors cobrindo
     as 5 pastas de HARNESS_SKILL_DIRS (formato flat "{dir}/{nome}/SKILL.md");
     hook -> dest e mirrors cobrindo as 5 pastas de HARNESS_HOOK_DIRS
     (formato "{dir}/{nome}.json", preservado); agent ->
     "templates/agents/{nome}.md"; rule -> "templates/rules/{nome}.md";
     spec -> "docs/specs/{nome}.md"; mcp -> mesma rota especial que já
     existe em materializador.py (rota externa com mcp.json, merge
     preservando entradas); config -> usa a capacidade "arquivos" já
     existente no núcleo (decisão 5). Adicionar "aidd-enterprise" a
     PROJETOS_SUPORTADOS (ou o que quer que profiles_registry.py use
     pra listar projetos válidos).
2.3. Adicionar ao materializador.py copiado a integração canônica de
     hook específica de aidd-enterprise (decisão 4): depois do fan-out
     nas 5 pastas, escrever também em
     componentes/aidd-enterprise/hooks/{nome}/{nome}.json (mesmo formato
     de conteúdo do fan-out) e chamar sincronizar_componente("hook",
     ferramenta="aidd-enterprise") (usando a parametrização de
     alvo_projeto que a Fase 1 já criou).
2.4. Adaptar run_inject/cmd_inject/parse_natural_language_intent em
     tools/aidd-enterprise/scripts/aidd.py: montar o payload em PT-BR
     (decisão 1), setar alvo_projeto="aidd-enterprise", chamar
     resolver_destinos -> materializar -> sincronizar (o pipeline
     canônico) em vez de injector.aidd_core_injector. Adicionar
     --remover a p_inject; quando presente, chamar remover_componente()
     e sys.exit(0/1) conforme sucesso/falha. --dry-run continua
     funcionando (decisão 7), só propagado pro novo materializar().
     Preservar 100% das mensagens de sucesso/erro relevantes que os
     testes existentes verificam (leia test_aidd_core_injector.py antes
     de mudar qualquer mensagem impressa).
2.5. Trocar a detecção de linguagem natural: substituir
     _INTENT_KEYWORD_PATTERNS/parse_natural_language_intent pelo
     mesmo padrão de _tentar_injecao_por_linguagem_natural de
     aidd-master (IntentRouter + detector_camada.detectar_tipo(), que
     retorna Result.fail(codigo="TIPO_AMBIGUO", candidatos=[...]) em vez
     de silenciosamente escolher a primeira regra que casar) —
     preservando o fallback pra cmd_plan quando nenhum padrão de
     injeção é reconhecido.
2.6. Aposentar tools/aidd-enterprise/scripts/injector/aidd_core_injector.py
     e target_profile.py — antes de remover, confirme via grep em todo
     tools/aidd-enterprise/ que nenhum outro arquivo além de aidd.py e
     G_INJECT.py os importa.
2.7. Adaptar tools/aidd-enterprise/scripts/gates/G_INJECT.py pra rodar
     as 2 checagens (decisão 6): a de infraestrutura (adaptada da
     classe de aidd-master's G_INJECT.py, ajustando caminhos) mais a de
     drift pós-injeção via verificar_sincronizacao() do núcleo agora
     usado por aidd-enterprise.
2.8. Migrar a suíte de testes: cada cenário real dos 23 testes de
     test_aidd_core_injector.py + 6 de test_g_inject_gate.py precisa ter
     equivalente rodando contra o núcleo canônico (reaproveitar os
     padrões de tools/aidd-master/tests/unit/test_injector_core.py,
     import direto dos módulos via sys.path, não importlib) —
     obrigatório cobrir pelo menos: os 7 tipos de componente (incluindo
     hook com as 5 pastas + sincronização canônica, e config com
     "arquivos" real); mcp com merge preservando entradas anteriores de
     um mcp.json já existente; path traversal rejeitado em config;
     drift detectando edição manual; remoção limpa; dry_run não tocando
     disco; ambiguidade de tipo detectada na linguagem natural PT-BR
     (novo cenário que o mecanismo antigo não cobria, porque não
     detectava ambiguidade).

CRITÉRIO DE SAÍDA (rode e cole o output real de cada um):
- Suíte completa de aidd-enterprise (python -m pytest tests/ -q) → sem
  regressão de cobertura real (mesmo número de cenários reais cobertos,
  mesmo que os arquivos de teste mudem de nome/estrutura).
- python ecossistema.py audit (raiz do monorepo) → exit 0.
- Reprodução manual real ponta a ponta cobrindo pelo menos: injeção de
  cada um dos 7 tipos via CLI; mcp com e sem --mcp-command; hook
  aparecendo nas 5 pastas de harness E em componentes/aidd-enterprise/hooks/;
  drift detection reprovando depois de edição manual; remoção limpa via
  --remover; --dry-run não tocando disco; injeção via linguagem natural
  PT-BR reconhecendo corretamente; um caso de ambiguidade de tipo sendo
  detectado (novo, prove que não existia antes).
- Suíte completa de aidd-master (python -m pytest tests/ -q) continua
  sem regressão (confirma que reaproveitar o núcleo em aidd-enterprise
  não quebrou nada em aidd-master).
- git status limpo além dos arquivos esperados; nenhum arquivo órfão de
  teste fora de tmp_path.

REGRAS DE ESCOPO — NÃO FAÇA:
- Não reduza nenhuma cobertura de harness (5 pastas de skill/hook
  continuam 5, incluindo MimoCode e as flat ".skills"/".hooks").
- Não troque o formato de arquivo do hook de aidd-enterprise
  ("{nome}.json") pelo de aidd-master ("{nome}/hook.sh") — são produtos
  diferentes, convergem só na sincronização canônica adicional.
- Não mude os flags de CLI já existentes de aidd-enterprise inject
  (--dry-run já existe, só religar; a única adição real de flag é
  --remover).
- Não mova os 5 módulos do núcleo pra um pacote compartilhado fora das
  2 ferramentas (decisão técnica 2).
- Não faça git commit nem git push.
- Não altere docs/planos/refinamento-notas-auditoria/04-unificacao-injetor-aidd-enterprise.md.

ENTREGÁVEL: lista exata de arquivos criados/alterados/removidos; comando
+ output real que comprova cada item do Critério de Saída; qualquer
desvio necessário, reportado explicitamente em vez de decidido sozinho.
```

## Prompt de Execução — FASE 2 (Prompt B) — English version

```
You are going to migrate tools/aidd-enterprise (monorepo at
C:\Users\trcnologia\Desktop\ecossistema-aidd) from its old, monolithic
injector (scripts/injector/aidd_core_injector.py +
scripts/injector/target_profile.py) to the SAME 5-file modular
architecture that tools/aidd-master uses (src/core/profiles_registry.py,
detector_camada.py, materializador.py, sincronizador_harness.py,
result.py) — already enriched in a prior phase with SHA-256 drift
detection, removal, full-snapshot rollback, dry_run, and config with an
arbitrary file map. Follow the Definition of Done below EXACTLY, do not
invent additional scope, and validate everything for real (real runs,
real exit codes, never masked by a pipe). This is work at a scale
comparable to Pacote 7 of Round 1 of the note-evolution effort — expect
multiple files and real hours of work, not a trivial tweak.

IMPORTANT — what this prompt does NOT ask for: do not reduce any
physical capability that tools/aidd-enterprise already has today
(coverage of 5 harnesses including MimoCode, `.json` hook files, config's
arbitrary file map, external mcp.json merge preserving prior entries,
path-traversal protection). The shared core enriched in Fase 1 has to
cover EVERYTHING aidd_core_injector.py already did, no exceptions — if
at any point the canonical architecture does not support something the
old injector supports and Fase 1 did not cover it, STOP and report this
explicitly instead of deciding on your own to drop the capability.

ALREADY-INVESTIGATED CONTEXT (no need to rediscover, but confirm by
reading the code before editing):

- tools/aidd-enterprise/scripts/injector/aidd_core_injector.py (262
  lines) and target_profile.py are the 2 files to retire at the end of
  this phase. target_profile.py maps each "type" to physical routes:
  skill -> fan-out across HARNESS_SKILL_DIRS = [".claude/skills",
  ".agent/skills", ".mimocode/skills", ".gemini/skills", ".skills"] (5
  dirs, "flat" format with no extra "skills/" nesting, writing
  "{dir}/{nome}/SKILL.md"); hook -> fan-out across HARNESS_HOOK_DIRS =
  same list with "skills" swapped for "hooks" (5 dirs), writing
  "{dir}/{nome}.json"; agent -> "templates/agents/{nome}.md"; rule ->
  "templates/rules/{nome}.md"; spec -> "docs/specs/{nome}.md"; mcp ->
  reads an existing mcp.json (if any), merges preserving already
  registered "mcpServers", adds/updates the current name's entry with
  {command, args, env}; config -> accepts an arbitrary "files" dict
  ({relative_path: content}), validates each path with _caminho_seguro()
  (rejects absolute, "..", or an empty segment) before writing.
- tools/aidd-enterprise/scripts/aidd.py (read before editing):
  - The payload uses ENGLISH keys: component = {"type": tipo, "name":
    nome, "description": descricao} (run_inject function, around lines
    832-840), plus "content" (skill/rule/spec/agent/hook), "mcp"
    ({"command", "args", "env"}), or "files" (config).
  - run_inject(tipo, nome, base_dir=".", descricao="", content=None,
    content_file=None, command=None, mcp_args=None, mcp_env=None,
    files_json=None, dry_run=False) builds the dict above and calls
    injector_core.materialize(component, base_dir=base_dir,
    dry_run=dry_run) (line ~838, "from injector import
    aidd_core_injector as injector_core").
  - cmd_inject(args) (line ~883) parses argparse arguments and calls
    run_inject(...).
  - p_inject (inside main(), around line 1044) already has a working
    --dry-run (propagated all the way to materialize()) — do NOT add
    this flag, just rewire it to the new pipeline. What's missing is a
    --remover flag (same pattern Fase 1 already added to aidd-master).
  - _default_component_content(tipo, nome, descricao) (line ~805)
    generates default content when --content-file is not passed — used
    only when the user does not provide explicit content.
  - _INTENT_KEYWORD_PATTERNS (line ~917) + parse_natural_language_intent
    (line ~928): PT-BR natural-language recognition already exists
    today, but uses the FIRST matching rule in the list (simple regex
    per type), without detecting ambiguity when the text matches more
    than one pattern.
  - _slugify(texto) (line ~901): converts free text into a kebab-case
    slug — equivalent to what aidd-master's detector_camada.py already
    does for the "nome" field.
- tools/aidd-enterprise/scripts/gates/G_INJECT.py (87 lines,
  verificar_injector(target_dir=".")): audits whether components
  ALREADY INJECTED into a project remain intact — today that means
  calling the old injector's sync_check(). tools/aidd-master/scripts/gates/G_INJECT.py
  (220 lines, a class with multiple check methods): audits the
  injector's OWN infrastructure (core files present, compiles via
  py_compile, zero stub via AST, CLI wired in, dedicated pytest suite
  100% green, a "fire test" of at least 1 real component in
  CAPABILITIES.json) — does not audit third-party components. They
  audit different things; both need to keep existing.
- tools/aidd-enterprise/tests/unit/test_aidd_core_injector.py (23
  tests) and test_g_inject_gate.py (6 tests): read the real scenarios
  they cover before migrating — every real scenario needs an equivalent
  running against the new core, even if the test files/names change.
- tools/aidd-master/src/core/profiles_registry.py's PROFILES["aidd-master"]
  is the FORMAT reference for a profile (skill/mcp/rule/spec/config/agent/hook,
  each with "dest", optional "mirrors", "registry", "camada_alvo") — but
  the CONTENT of the "aidd-enterprise" profile differs from
  "aidd-master"'s in at least: skill/hook have 5 mirrors (not 3, MimoCode
  + flat ".skills"/".hooks" included), hook writes "{nome}.json" (not
  "{nome}/hook.sh").

DECISIONS ALREADY MADE (do not reopen these):
1. The internal payload's field-naming convention becomes PT-BR
   (tipo/nome/descricao/conteudo/alvo_projeto/camada_alvo), same as
   aidd-master — not two conventions coexisting. The CLI flags
   (--descricao, --content-file, etc.) are already PT-BR today and do
   not change; only the internal Python dict passed to the core changes
   from English to PT-BR.
2. The 5 core modules (profiles_registry.py, detector_camada.py,
   materializador.py, sincronizador_harness.py, result.py) are COPIED
   into tools/aidd-enterprise/src/core/ — not moved into a shared
   package outside the 2 tools. Each tool remains a standalone package.
3. The direct fan-out of skill/hook across 5 folders (including MimoCode
   and the flat ".skills"/".hooks" dirs) is PRESERVED — the new
   "aidd-enterprise" profile in profiles_registry.py uses 5 mirrors, not
   the 3 the "aidd-master" profile uses. Hook writes "{nome}.json"
   (aidd-enterprise's current format), not "{nome}/hook.sh"
   (aidd-master's format) — they are different products, they don't
   need to converge the file FORMAT, only gain the additional canonical
   sync (item 2 below).
4. Hook in aidd-enterprise gains, ON TOP OF the already-existing direct
   fan-out (preserved), the additional canonical sync
   componentes/aidd-enterprise/hooks/{nome}/... + gestor_componentes.py
   sync — the same hybrid pattern (fan-out AND canonical, not fan-out
   OR canonical) that aidd-master already uses for its own hook.
5. config in aidd-enterprise uses the "arquivos" capability already
   added to the core in Fase 1 — only adapt run_inject/cmd_inject to
   build payload["arquivos"] from the already-existing --files-json
   (which today reads a JSON and passes it as component["files"]). The
   path-traversal validation already lives in the shared core, do not
   duplicate it.
6. aidd-enterprise's G_INJECT.py starts running BOTH checks: the
   injector-infrastructure one (adapted from aidd-master's G_INJECT.py,
   adjusting paths for aidd-enterprise) PLUS the post-injection drift
   one (now via the core's verificar_sincronizacao(), instead of the old
   injector's sync_check()) — not choosing one over the other.
7. aidd-enterprise's --dry-run ALREADY EXISTS and is already propagated
   to materialize() — it just needs to keep working after swapping the
   underlying "materialize()" (rewire it to the new pipeline).
   --remover is the only real new CLI flag.

DEFINITION OF DONE — in this order, all inside tools/aidd-enterprise/,
using the core already enriched by Fase 1:

2.1. Copy profiles_registry.py, detector_camada.py, materializador.py,
     sincronizador_harness.py, result.py from tools/aidd-master/src/core/
     (already enriched) into tools/aidd-enterprise/src/core/ (create the
     directory if it doesn't exist — check first whether some src/core/
     already exists for another purpose, and do not overwrite anything
     other than these 5 files).
2.2. In the local copy of profiles_registry.py, add
     PROFILES["aidd-enterprise"] with this repository's REAL topology,
     read from the current target_profile.py: skill -> dest and mirrors
     covering the 5 HARNESS_SKILL_DIRS folders (flat format
     "{dir}/{nome}/SKILL.md"); hook -> dest and mirrors covering the 5
     HARNESS_HOOK_DIRS folders (format "{dir}/{nome}.json", preserved);
     agent -> "templates/agents/{nome}.md"; rule ->
     "templates/rules/{nome}.md"; spec -> "docs/specs/{nome}.md"; mcp ->
     the same special route that already exists in materializador.py
     (external route with mcp.json, merging while preserving entries);
     config -> uses the "arquivos" capability already present in the
     core (decision 5). Add "aidd-enterprise" to PROJETOS_SUPORTADOS (or
     whatever profiles_registry.py uses to list valid projects).
2.3. Add to the copied materializador.py the aidd-enterprise-specific
     canonical hook integration (decision 4): after the fan-out across
     the 5 folders, also write to
     componentes/aidd-enterprise/hooks/{nome}/{nome}.json (same content
     format as the fan-out) and call sincronizar_componente("hook",
     ferramenta="aidd-enterprise") (using the alvo_projeto
     parametrization Fase 1 already created).
2.4. Adapt run_inject/cmd_inject/parse_natural_language_intent in
     tools/aidd-enterprise/scripts/aidd.py: build the payload in PT-BR
     (decision 1), set alvo_projeto="aidd-enterprise", call
     resolver_destinos -> materializar -> sincronizar (the canonical
     pipeline) instead of injector.aidd_core_injector. Add --remover to
     p_inject; when present, call remover_componente() and sys.exit(0/1)
     based on success/failure. --dry-run keeps working (decision 7), just
     propagated to the new materializar(). Preserve 100% of the relevant
     success/error messages the existing tests check (read
     test_aidd_core_injector.py before changing any printed message).
2.5. Swap the natural-language detection: replace
     _INTENT_KEYWORD_PATTERNS/parse_natural_language_intent with the
     same pattern as aidd-master's _tentar_injecao_por_linguagem_natural
     (IntentRouter + detector_camada.detectar_tipo(), which returns
     Result.fail(codigo="TIPO_AMBIGUO", candidatos=[...]) instead of
     silently picking the first matching rule) — preserving the fallback
     to cmd_plan when no injection pattern is recognized.
2.6. Retire tools/aidd-enterprise/scripts/injector/aidd_core_injector.py
     and target_profile.py — before removing, confirm via grep across
     all of tools/aidd-enterprise/ that no file other than aidd.py and
     G_INJECT.py imports them.
2.7. Adapt tools/aidd-enterprise/scripts/gates/G_INJECT.py to run the 2
     checks (decision 6): the infrastructure one (adapted from
     aidd-master's G_INJECT.py class, adjusting paths) plus the
     post-injection drift one via the core's verificar_sincronizacao(),
     now used by aidd-enterprise.
2.8. Migrate the test suite: every real scenario from the 23 tests in
     test_aidd_core_injector.py + 6 in test_g_inject_gate.py needs an
     equivalent running against the canonical core (reuse the patterns
     from tools/aidd-master/tests/unit/test_injector_core.py, direct
     module imports via sys.path, not importlib) — must cover at least:
     all 7 component types (including hook with the 5 folders + the
     canonical sync, and config with a real "arquivos" map); mcp merging
     while preserving prior entries of an already-existing mcp.json;
     path traversal rejected in config; drift detecting a manual edit;
     clean removal; dry_run touching no disk; type ambiguity detected in
     PT-BR natural language (a new scenario the old mechanism did not
     cover, since it never detected ambiguity).

EXIT CRITERIA (run and paste the real output of each):
- Full aidd-enterprise suite (python -m pytest tests/ -q) → no
  regression in real coverage (same number of real scenarios covered,
  even if test files change name/structure).
- python ecossistema.py audit (monorepo root) → exit 0.
- Real end-to-end manual reproduction covering at least: injecting each
  of the 7 types via the CLI; mcp with and without --mcp-command; hook
  appearing in the 5 harness folders AND in
  componentes/aidd-enterprise/hooks/; drift detection failing after a
  manual edit; clean removal via --remover; --dry-run touching no disk;
  PT-BR natural-language injection recognizing correctly; a type
  ambiguity case being detected (new, prove it didn't exist before).
- Full aidd-master suite (python -m pytest tests/ -q) still has no
  regression (confirms reusing the core in aidd-enterprise did not break
  anything in aidd-master).
- git status clean beyond the expected files; no orphaned test files
  outside tmp_path.

SCOPE RULES — DO NOT:
- Do not reduce any harness coverage (5 folders for skill/hook stay 5,
  including MimoCode and the flat ".skills"/".hooks").
- Do not swap aidd-enterprise's hook file format ("{nome}.json") for
  aidd-master's ("{nome}/hook.sh") — they are different products,
  converging only on the additional canonical sync.
- Do not change aidd-enterprise inject's already-existing CLI flags
  (--dry-run already exists, just rewire it; the only real new flag is
  --remover).
- Do not move the 5 core modules into a package shared outside the 2
  tools (technical decision 2).
- Do not git commit or git push.
- Do not modify docs/planos/refinamento-notas-auditoria/04-unificacao-injetor-aidd-enterprise.md.

DELIVERABLE: exact list of files created/changed/removed; command + real
output proving each item of the Exit Criteria; any necessary deviation,
explicitly reported instead of decided by yourself.
```
