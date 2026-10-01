# Plano de Evolução (Fase 2) - fronteiras-ferramentas

Plano do ciclo-01 para que cada uma das 8 ferramentas tenha **um único dono por responsabilidade**, nenhuma ferramenta guarde cópia de peça alheia e as etapas sejam trocáveis por contratos fixos.
Origem: `docs/auditoria/meus-prompts/PROMPT-FRONTEIRAS-E-DEDUP-FERRAMENTAS.txt` + visão do usuário (01/10/2026). Diagnóstico: `DIAGNOSTICO.md`. Contratos e gate: `ESPEC-CONTRATOS-E-GATE.md`. Critérios: `DOD.md`.
Foto "antes": [BASELINE-E2E.md](file:///C:/Users/trcnologia/Desktop/TESTES_E2E-ecossistema-aidd/ciclo-01/BASELINE-E2E.md)

## A visão (definida pelo usuário)

| Etapa | Ferramenta | O que entrega |
|---|---|---|
| 1. Terreno pronto | **forge** | Tudo o que a máquina precisa para trabalhar em sincronia: dependências instaladas, configurações finas, leis e guardas (gates), e o **almoxarifado** com todas as peças (moldes, scripts, receitas, contatos). Só entrega o bastão depois de provar a prontidão |
| 2. Planta baixa | **planner** | A planta inteira, seguindo a estrutura do forge: camadas, fases e micro-etapas (tickets), **cada ticket endereçado à ferramenta responsável** — construtor, master, enterprise e ops |
| 3. Construção | **generator \| factory \| bridge** | Só as fatias de domínio, consumindo as peças do almoxarifado |
| 4–6. Acabamento | **master → enterprise → ops** | Integração + Quarteto → blindagem → infraestrutura, consumindo as peças do almoxarifado |

Regras que saem da visão:
1. **Nenhuma ferramenta guarda cópia de peça.** Ela pede a peça ao almoxarifado do forge na hora em que precisa (sob demanda). Quando a peça tem que existir fisicamente no app gerado, ela é copiada **para a pasta do projeto**, nunca para dentro da ferramenta.
2. **Quem guarda não é quem escreve.** O forge guarda e distribui; o conteúdo de cada receita continua com o especialista (ex.: o ops é dono do conteúdo da receita do Dockerfile, que mora no almoxarifado com a etiqueta "ops").
3. **Bastão só com prova.** Cada etapa passa à seguinte um contrato com evidência, gravado por ela mesma.

## Garantia de zero perda (nada do que foi feito certo se perde)

Apagar uma cópia **nunca** apaga a capacidade dela. Antes de qualquer remoção:
1. **Tag de segurança no git** (`pre-fronteiras-ciclo-01`): o estado de hoje fica recuperável para sempre, arquivo por arquivo.
2. **Inventário de capacidades** (Ticket 3): lista cada função, classe, teste, gate, molde e regra de cada cópia, com hash. Cada linha que só existe numa cópia é **juntada** à versão do almoxarifado antes da remoção.
3. **Prova automática:** `inventario_capacidades.py comparar` precisa dar "conteúdo único órfão = 0" — nada que existia em alguma cópia some sem ter ido para o almoxarifado.
4. **Os testes não diminuem:** hoje são 2352 passando. Testes mudam de lugar junto com a peça, mas não somem; o total fica ≥ 2352.
5. **Os 3 fluxos não pioram:** depois de cada ticket, E2E de novo, comparado com o ciclo-01.
6. **Você confirma cada remoção** (Lei #7): o ticket mostra a lista do que vai sair e para onde foi o conteúdo único.

## Estratégia de Execução
- Todo ticket segue TDD estrito: o teste que reprova (exit 1) vem antes da implementação.
- Cada ticket entrega um arquivo **novo** (o orquestrador pula o ticket se o arquivo de entrega já existir).
- **5 blocos, cada um com aprovação do usuário no fim** (`gate_final` verde + `--aprovar`):

| Bloco | Tickets | Como roda |
|---|---|---|
| 1 Fundação | 1–7: gate por ticket, foto E2E, inventário, nomes, mapa, fiscal, validador | Autônomo (o Ticket 1 sozinho primeiro); a tag é criada antes, pelo usuário |
| 2 Almoxarifado | 8–9 | Autônomo |
| 3 Cada ferramenta no seu lugar | 10–18 | Autônomo; o gate de cada ticket inclui o E2E |
| 4 Remoção das cópias | 19 | Com o usuário, peça por peça |
| 5 Fechamento | 20–23: fiscal bloqueando, foto "depois", READMEs, mapas visuais e livros | Autônomo |

- **Cada ticket tem o seu gate** (linha `Gate do Ticket`), rodado pelo orquestrador — nunca só pela palavra do agente.
- **E2E automático no Bloco 3:** `scripts/e2e_foto.py` (Ticket 2) roda os 3 fluxos num worktree isolado, numa pasta nova `TESTES_E2E-ecossistema-aidd\ciclo-NN\`, e compara com o ciclo-01. Nenhuma métrica pode piorar.
- Antes do Bloco 1: o usuário aprova `ESPEC-CONTRATOS-E-GATE.md` e `PLANO-EVOLUCAO.md` (decisões D1–D5 já respondidas).
- **`perfil_app` é sempre dinâmico:** sai do desenho que o planner fez para aquele app (módulos, entidades, integrações, banco, filas, rotas do Quarteto, portas, serviços externos). Os 5 nichos de hoje viram, no máximo, atalhos opcionais — nunca uma lista que limita o que o ops aceita.

## Decisões

| # | Pergunta | Situação |
|---|---|---|
| D1 | `master add-module` cria a fatia de domínio sozinho (trabalho de construtor). | **Decidida pelo usuário (01/10/2026), seguindo a recomendação:** a "fatia mínima" vai para o generator; o master só integra o que recebe |
| D2 | Gates do monorepo × gates entregues ao projeto | **Resolvida pela visão:** todos os gates de projeto moram no almoxarifado do forge; `gates/` da raiz continua sendo a lei do próprio monorepo; o gate interno de cada ferramenta vira teste dela |
| D3 | Injetor em 4 ferramentas | **Resolvida pela visão:** uma peça só no almoxarifado. Conteúdo/lógica: enterprise (blindagem). forge e quem mais precisar consomem a mesma peça |
| D4 | `materiais-extras/examples` (12 projetos) | **Decidida pelo usuário (01/10/2026), seguindo a recomendação:** guardar como arquivo histórico fora do repo (não apagar) |
| D5 | Onde fica o almoxarifado fisicamente | **Decidida pelo usuário (01/10/2026), seguindo a recomendação:** manter em `componentes/compartilhado/` (66 arquivos `.py` já apontam para lá) e fazer do forge o **dono e distribuidor** dela, com catálogo e API de entrega. Mover para dentro de `tools/aidd-forge/` multiplicaria o risco sem ganho |

## Bloco 1 — Fundação (Tickets 1–7) · autônomo
> Passo humano antes: criar a tag `pre-fronteiras-ciclo-01`. O Ticket 1 roda sozinho (`--fase`); depois dele, o compilador gera um JSON por bloco e os Tickets 2–7 rodam em sequência.

### Ticket 1: Gate próprio por ticket e um manifesto por bloco (Refere-se a D13 / DoD 13)
- **Falha 15-D:** `D13. Quality Gates (Portões)`
- **Artefato de Handoff:** `tests/test_compilador_gate_por_ticket.py`
- **Gate do Ticket:** `python -m pytest -q -p no:cacheprovider tests/test_compilador_gate_por_ticket.py`
- **Requisito TDD (Red):** Hoje o compilador grava o mesmo gate (`pytest tests`) em todos os tickets. Medido em 01/10: esse comando coleta 843 testes e **nenhum** de `tools/` ou `gates/`, então 11 dos 22 tickets teriam o próprio teste ignorado. O compilador também não sabe separar blocos.
- **Implementação Técnica:**
  - `scripts/compilador_plano_evolucao.py` lê `- **Gate do Ticket:** \`<comando>\`` de cada ticket e grava em `gate_fase`. Sem a linha, usa o gate atual, e o compilador avisa.
  - Cabeçalhos `## Bloco N — <nome>` no MD geram `PLANO-EVOLUCAO-BLOCO-N.json` (um manifesto por bloco), além do `PLANO-EVOLUCAO.json` completo.
  - Este ticket roda sozinho: `python scripts/orquestrador_4f.py --manifest <json> --fase <nome-do-ticket-1>`.
- **Verificação (Green):** teste passa; recompilar este plano gera 5 JSON de bloco, e o gate de cada ticket é o declarado no MD.
- **Construtor Prompt (EN):**
  - Write tests/test_compilador_gate_por_ticket.py first. Fake plan with two tickets. One declares Gate do Ticket line with custom command. Assert compiled gate_fase equals that command. Assert other ticket falls back to default gate with warning. Fake plan with two Bloco headers. Assert one manifest per block is written. Run. Assert exit 1.
  - Change scripts/compilador_plano_evolucao.py. Parse line starting with Gate do Ticket label inside each ticket. Store command in gate_fase.
  - Parse headers matching Bloco N. Write PLANO-EVOLUCAO-BLOCO-N.json per block plus full PLANO-EVOLUCAO.json.
  - Run test. Run existing compiler tests. Assert exit 0.

### Ticket 2: Foto E2E repetível e comparação automática (Refere-se a D12 / DoD 10)
- **Falha 15-D:** `D12. Observabilidade e Frugalidade`
- **Artefato de Handoff:** `scripts/e2e_foto.py`
- **Gate do Ticket:** `python -m pytest -q -p no:cacheprovider tests/test_e2e_foto.py`
- **Requisito TDD (Red):** Com uma pasta de ciclo falsa que piora uma métrica (fluxo quebra mais cedo, vazamento novo, Quarteto com menos rotas), `comparar` sai com exit 1.
- **Implementação Técnica:**
  - Leva para o repo os scripts do ciclo-01 (`_evidencias/rodar_fluxo.py`, `rodar_continuacao.py`, `checar_quarteto.py`, `consolidar.py`) como um comando só:
    - `rodar --ciclo auto`: cria um worktree isolado, roda os 3 fluxos + continuação + Quarteto em `TESTES_E2E-ecossistema-aidd\ciclo-NN\` e grava `RESULTADO-E2E.json` por fluxo;
    - `comparar --base ciclo-01`: compara exit, etapa onde quebrou, Quarteto, vazamentos, duplicatas, tempo dos gates, tokens e órfãos do inventário; grava `COMPARACAO-E2E.md`; exit 1 se alguma métrica piorar.
  - É o gate que o orquestrador roda depois de cada ticket do Bloco 3, sem depender da palavra do agente.
- **Verificação (Green):** teste passa; `comparar` do ciclo-01 contra ele mesmo dá exit 0.
- **Construtor Prompt (EN):**
  - Write tests/test_e2e_foto.py first. Fake cycle folder where flow breaks earlier. Assert comparar exits 1. Fake cycle with new leak. Assert exit 1. Fake cycle equal to base. Assert exit 0. Run. Assert exit 1.
  - Implement scripts/e2e_foto.py with subcommands rodar and comparar. Port logic from TESTES_E2E-ecossistema-aidd/ciclo-01/_evidencias scripts.
  - rodar creates isolated worktree, runs 3 flows plus continuation plus Quarteto probe, writes RESULTADO-E2E.json per flow into next ciclo folder outside repo.
  - comparar reads base and new cycle. Compare exit, quebrou_em, quarteto, leaks, duplicate count, gate time, tokens, inventory orphans. Write COMPARACAO-E2E.md. Exit 1 if any metric worse.
  - Run test. Assert exit 0.

### Ticket 3: Inventário de capacidades e tag de segurança (Refere-se a D15 / DoD 1)
- **Falha 15-D:** `D15. Fonte Única e Sincronização`
- **Artefato de Handoff:** `scripts/inventario_capacidades.py`
- **Gate do Ticket:** `python -m pytest -q -p no:cacheprovider tests/test_inventario_capacidades.py`
- **Requisito TDD (Red):** Num repo temporário com duas cópias de um arquivo, uma delas com uma função a mais, `comparar` precisa acusar "conteúdo único órfão = 1" quando a cópia maior é removida sem juntar a função.
- **Implementação Técnica:**
  - `foto`: para cada arquivo de `tools/` e `componentes/`, registra hash, funções/classes (AST), testes e linhas únicas por família de cópias; grava `INVENTARIO-ANTES.json` no ciclo.
  - `comparar <antes> <depois>`: lista o que existia antes e não existe mais em lugar nenhum; exit 1 se a lista não estiver vazia.
  - A tag `pre-fronteiras-ciclo-01` é criada **antes** do Bloco 1, com o OK do usuário (passo humano, fora do agente). Este ticket só confere se ela existe.
- **Verificação (Green):** `tests/test_inventario_capacidades.py` passa; a foto real do repo é gravada.
- **Construtor Prompt (EN):**
  - Write tests/test_inventario_capacidades.py first. Build temp repo with two copies of one module. One copy has extra function. Remove that copy without merge. Assert comparar reports one orphan and exits 1. Run. Assert exit 1.
  - Implement scripts/inventario_capacidades.py with subcommands foto and comparar. Record per file: sha256, AST functions and classes, test names, unique lines per copy family.
  - foto writes INVENTARIO-ANTES.json into cycle folder. comparar exits 1 when any capability exists only in old snapshot.
  - Run test. Run foto on real repo. Assert exit 0.

### Ticket 4: Padronizar os nomes dos construtores pelo nome do fluxo (Refere-se a D14 / DoD 12)
- **Falha 15-D:** `D14. Documentação Viva`
- **Artefato de Handoff:** `tests/test_nomes_padronizados.py`
- **Gate do Ticket:** `python -m pytest -q -p no:cacheprovider tests/test_nomes_padronizados.py && python ecossistema.py components verify && python scripts/e2e_foto.py rodar --ciclo auto && python scripts/e2e_foto.py comparar --base ciclo-01 --novo ultimo`
- **Requisito TDD (Red):** O teste reprova enquanto existir referência a `aidd-generator`, `aidd-factory` ou `aidd-bridge` (e às formas `aidd_generator`, `aidd_factory`, `aidd_bridge`) fora da lista de apelidos e dos documentos históricos. Medido em 01/10: ~760 arquivos e ~3900 ocorrências.
- **Implementação Técnica:**
  - `git mv`: `tools/aidd-generator` → `tools/aidd-pure`, `tools/aidd-factory` → `tools/aidd-open`, `tools/aidd-bridge` → `tools/aidd-freedom`; pacotes Python `aidd_*` com o mesmo critério; skills e espelhos de harness juntam os dois nomes em um só (`components sync --tipo todos` + `components verify`).
  - Os comandos antigos (`generate`, `factory`, `bridge`, `aidd-generator`…) continuam funcionando por 1 ciclo como **apelido**, com aviso de "nome antigo".
  - Documentos históricos (`secoes/`, `docs/relatorios/`, relatórios de ciclos fechados) **não** são reescritos — eles registram o passado.
  - Fora deste ticket: renomear os repositórios separados no GitHub (`heverton-dev/aidd-generator` …). Precisa de confirmação própria do usuário.
- **Verificação (Green):** teste passa; `inventario_capacidades.py comparar` com zero órfão; bateria completa verde (≥ 2352 testes); os 3 fluxos E2E rodam de novo, sem piorar contra o ciclo-01.
- **Construtor Prompt (EN):**
  - Write tests/test_nomes_padronizados.py first. Scan git ls-files for aidd-generator, aidd-factory, aidd-bridge, aidd_generator, aidd_factory, aidd_bridge. Allow only alias table and history folders secoes and docs/relatorios. Run. Assert exit 1.
  - git mv tools/aidd-generator to tools/aidd-pure. git mv tools/aidd-factory to tools/aidd-open. git mv tools/aidd-bridge to tools/aidd-freedom. Rename Python packages the same way.
  - Replace references in code, configs, gates, tests, skills and living docs. Keep old CLI names as aliases printing a deprecation warning.
  - Run components sync --tipo todos and components verify. Assert exit 0.
  - Run inventario_capacidades.py comparar. Assert zero orphans. Run full gate battery. Assert at least 2352 passed. Run 3 E2E flows into new ciclo folder. Assert no metric worse than ciclo-01.

### Ticket 5: Mapa de donos e schemas dos 5 contratos (Refere-se a D1 / DoD 2)
- **Falha 15-D:** `D1. Arquitetura e Fronteiras`
- **Artefato de Handoff:** `componentes/compartilhado/specs/MAPA-DONOS-FERRAMENTAS.json`
- **Gate do Ticket:** `python -m pytest -q -p no:cacheprovider tests/test_mapa_donos_ferramentas.py`
- **Requisito TDD (Red):** O teste reprova se faltar uma das 8 ferramentas, se uma responsabilidade tiver dois donos, se alguma ferramenta além do forge tiver `pode_guardar_pecas: true` ou se faltar um dos 5 schemas.
- **Implementação Técnica:**
  - Por ferramenta: `responsabilidades`, `dono_do_conteudo_de` (receitas que ela escreve), `pode_conter`, `nunca_conter`, `zona_escrita_no_projeto`.
  - forge = leis + almoxarifado + prontidão; planner = planta + tickets roteados; demais conforme a visão.
  - Novo `handoff-forge-to-planner.schema.json` (checklist de prontidão) e campos novos nos outros 4 (ver ESPEC).
- **Verificação (Green):** `tests/test_mapa_donos_ferramentas.py` passa.
- **Construtor Prompt (EN):**
  - Write tests/test_mapa_donos_ferramentas.py first. Load componentes/compartilhado/specs/MAPA-DONOS-FERRAMENTAS.json. Assert all 8 tools present. Assert every responsibility has exactly one owner. Assert only aidd-forge has pode_guardar_pecas true. Assert 5 handoff schemas exist. Run. Assert exit 1.
  - Create MAPA-DONOS-FERRAMENTAS.json from ESPEC-CONTRATOS-E-GATE.md. Keys per tool: responsabilidades, dono_do_conteudo_de, pode_conter, nunca_conter, zona_escrita_no_projeto.
  - Create handoff-forge-to-planner.schema.json as readiness checklist. Add evidence fields to the 4 existing handoff schemas as listed in the spec.
  - Run test. Assert exit 0.

### Ticket 6: Gate de fronteira em modo aviso (Refere-se a D1 / DoD 3)
- **Falha 15-D:** `D1. Arquitetura e Fronteiras`
- **Artefato de Handoff:** `gates/G_FRONTEIRA_FERRAMENTAS.py`
- **Gate do Ticket:** `python -m pytest -q -p no:cacheprovider gates/test_g_fronteira_ferramentas.py`
- **Requisito TDD (Red):** Em repo git temporário, um `Dockerfile` plantado em `tools/aidd-open/` gera violação; uma cópia de peça do almoxarifado dentro de qualquer ferramenta gera violação; exit 0 em `aviso`, 1 em `bloqueio`; a allowlist não pode crescer.
- **Implementação Técnica:**
  - Lê o mapa; percorre `git ls-files tools/aidd-*`; compara hashes com o catálogo do almoxarifado para achar cópias; aponta o dono certo.
  - `AIDD_FRONTEIRA_MODO=aviso|bloqueio` (padrão `aviso`); exceções conhecidas em `gates/allowlist_fronteira.json`.
- **Verificação (Green):** `gates/test_g_fronteira_ferramentas.py` passa; no repo real, em modo aviso, lista V1–V11 do `DIAGNOSTICO.md`.
- **Construtor Prompt (EN):**
  - Write gates/test_g_fronteira_ferramentas.py first. Build temp git repo. Plant Dockerfile under tools/aidd-open. Plant copy of catalog piece under tools/aidd-master. Assert both reported. Assert exit 0 when AIDD_FRONTEIRA_MODO=aviso. Assert exit 1 when AIDD_FRONTEIRA_MODO=bloqueio. Assert test fails if gates/allowlist_fronteira.json grows. Run. Assert exit 1.
  - Implement gates/G_FRONTEIRA_FERRAMENTAS.py. Read map. Scan git ls-files under tools. Match hashes against catalog. Print file, current tool, correct owner.
  - Seed gates/allowlist_fronteira.json with current known violations and dates. Register hook in .pre-commit-config.yaml in warn mode.
  - Run test. Assert exit 0.

### Ticket 7: Validador de contratos com evidência, em modo aviso (Refere-se a D2 / DoD 4)
- **Falha 15-D:** `D2. Contratos e Interfaces`
- **Artefato de Handoff:** `scripts/validar_handoff.py`
- **Gate do Ticket:** `python -m pytest -q -p no:cacheprovider tests/test_validar_handoff.py`
- **Requisito TDD (Red):** Reprova contrato com `servidor_sobe: true` sem log, com caminho de fatia inexistente, ou sem `produzido_por` igual à ferramenta dona; `run-fluxo --dry-run` deixa de imprimir "100% DE APROVAÇÃO".
- **Implementação Técnica:**
  - Valida schema + evidência (caminhos existem, sha256 bate, status HTTP medido presente).
  - O orquestrador chama em cada fronteira em modo aviso e grava `RELATORIO-CONTRATOS.json` no projeto.
- **Verificação (Green):** `tests/test_validar_handoff.py` passa.
- **Construtor Prompt (EN):**
  - Write tests/test_validar_handoff.py first. Contract with servidor_sobe true and no log fails. Contract with missing slice path fails. Contract without produzido_por matching tool fails. Dry-run of run-fluxo must not print 100 percent approval. Run. Assert exit 1.
  - Implement scripts/validar_handoff.py. Validate schema plus evidence: paths exist, sha256 matches, measured HTTP status present.
  - Call it from scripts/orquestrador_sincrono.py at every boundary in warn mode. Write RELATORIO-CONTRATOS.json into project folder.
  - Run test. Assert exit 0.

## Bloco 2 — Almoxarifado (Tickets 8–9) · autônomo

### Ticket 8: Almoxarifado único com catálogo (Refere-se a D15 / DoD 5)
- **Falha 15-D:** `D15. Fonte Única e Sincronização`
- **Artefato de Handoff:** `componentes/compartilhado/CATALOGO.json`
- **Gate do Ticket:** `python -m pytest -q -p no:cacheprovider tests/test_catalogo_almoxarifado.py`
- **Requisito TDD (Red):** O teste reprova se uma peça do inventário (gate de projeto, molde do Quarteto, molde de infra, injetor, sincronizador de harness, núcleo `src-core`) não estiver no catálogo, ou se a versão do catálogo tiver perdido uma capacidade de alguma cópia (`inventario_capacidades.py comparar`).
- **Implementação Técnica:**
  - Para cada família de cópias, montar **uma** versão juntando o conteúdo único de todas (base: a versão recomendada na Etapa 4/5 do `DIAGNOSTICO.md`); cada peça com `dono_do_conteudo`, `versao`, `sha256` e `consumidores`.
  - Organização sugerida: `componentes/compartilhado/{gates,src-core,moldes/quarteto,moldes/infra,injetor,specs}/`.
  - Nesta fase, as cópias antigas continuam no lugar; nada é apagado.
- **Verificação (Green):** `tests/test_catalogo_almoxarifado.py` passa e `comparar` dá zero órfão.
- **Construtor Prompt (EN):**
  - Write tests/test_catalogo_almoxarifado.py first. Assert every piece family from inventory exists in componentes/compartilhado/CATALOGO.json. Assert inventario_capacidades.py comparar reports zero orphans between all copies and catalog version. Run. Assert exit 1.
  - For each copy family build one merged version keeping unique content from every copy. Base version per DIAGNOSTICO.md steps 4 and 5.
  - Store under componentes/compartilhado folders gates, src-core, moldes/quarteto, moldes/infra, injetor, specs. Write CATALOGO.json with dono_do_conteudo, versao, sha256, consumidores per piece.
  - Keep old copies in place. Run test. Assert exit 0.

### Ticket 9: Consumo sob demanda — o forge entrega a peça (Refere-se a D15 / DoD 5)
- **Falha 15-D:** `D15. Fonte Única e Sincronização`
- **Artefato de Handoff:** `tools/aidd-forge/aidd_forge/core/almoxarifado.py`
- **Gate do Ticket:** `python -m pytest -q -p no:cacheprovider tools/aidd-forge/tests/test_almoxarifado.py`
- **Requisito TDD (Red):** `obter_peca("moldes/infra/Dockerfile", destino=<projeto>)` copia para a pasta do projeto e confere o sha256; pedir para copiar para dentro de `tools/` reprova; peça inexistente dá erro claro.
- **Implementação Técnica:**
  - API Python `obter_peca(nome, destino)` e `caminho_peca(nome)` (leitura, sem cópia), e CLI `ecossistema.py forge fornecer <peca> --destino <pasta>`.
  - Só lê o `CATALOGO.json`; nunca grava dentro de `tools/`.
- **Verificação (Green):** `tools/aidd-forge/tests/test_almoxarifado.py` passa.
- **Construtor Prompt (EN):**
  - Write tools/aidd-forge/tests/test_almoxarifado.py first. obter_peca copies piece into project folder and checks sha256. Destination inside tools folder raises error. Unknown piece raises clear error. Run. Assert exit 1.
  - Implement tools/aidd-forge/aidd_forge/core/almoxarifado.py with obter_peca and caminho_peca reading componentes/compartilhado/CATALOGO.json.
  - Add CLI ecossistema.py forge fornecer PIECE --destino PATH.
  - Run test. Assert exit 0.

## Bloco 3 — Cada ferramenta no seu lugar (Tickets 10–18) · autônomo, com E2E no gate de cada ticket
> O gate de cada ticket roda o teste dele **e** `e2e_foto.py rodar` + `comparar` contra o ciclo-01. Se qualquer métrica piorar, o bloco para e nada é commitado.

### Ticket 10: Prontidão do forge antes de passar o bastão (Refere-se a D2 / DoD 6)
- **Falha 15-D:** `D2. Contratos e Interfaces`
- **Artefato de Handoff:** `tools/aidd-forge/tests/test_prontidao_forge.py`
- **Gate do Ticket:** `python -m pytest -q -p no:cacheprovider tools/aidd-forge/tests/test_prontidao_forge.py && python scripts/e2e_foto.py rodar --ciclo auto && python scripts/e2e_foto.py comparar --base ciclo-01 --novo ultimo`
- **Requisito TDD (Red):** Reproduz as 3 falhas do baseline: projeto sem commit inicial, dependência faltando (`core.logs`) e nenhuma IA disponível — o forge hoje entrega o bastão mesmo assim.
- **Implementação Técnica:**
  - `forge init` termina com o checklist: dependências da `requirements` instaladas e importáveis, gates na versão do catálogo, harnesses espelhados, commit inicial feito, `capacidade_llm` testada de verdade (pedido → resposta).
  - Grava `.aidd/HANDOFF_FORGE_PLANNER.json` (C1); se algo faltar, para com exit 1 e diz o que fazer.
- **Verificação (Green):** teste passa; o fluxo 01 sem IA para no forge em segundos, com mensagem clara; o fluxo 03 passa do `dispatch`.
- **Construtor Prompt (EN):**
  - Write tools/aidd-forge/tests/test_prontidao_forge.py first. Assert forge init makes initial commit. Assert missing dependency fails readiness. Assert capacidade_llm nenhuma fails readiness with clear message. Assert HANDOFF_FORGE_PLANNER.json written with evidence. Run. Assert exit 1.
  - Add readiness checklist to forge init: dependencies importable, gates match catalog sha256, harness mirrors present, initial commit, real LLM round trip check.
  - Write PROJECT/.aidd/HANDOFF_FORGE_PLANNER.json. Exit 1 with fix hint when any item fails.
  - Run test. Run 3 E2E flows into new ciclo folder. Assert no metric worse than ciclo-01.

### Ticket 11: Planta com tickets roteados para as 6 ferramentas (Refere-se a D2 / DoD 6)
- **Falha 15-D:** `D2. Contratos e Interfaces`
- **Artefato de Handoff:** `tools/aidd-planner/tests/test_planta_tickets_roteados.py`
- **Gate do Ticket:** `python -m pytest -q -p no:cacheprovider tools/aidd-planner/tests/test_planta_tickets_roteados.py && python scripts/e2e_foto.py rodar --ciclo auto && python scripts/e2e_foto.py comparar --base ciclo-01 --novo ultimo`
- **Requisito TDD (Red):** Hoje o planner gera 1 módulo genérico só para o construtor; não há ticket para master, enterprise ou ops, e falta `perfil_app` (o ops reprova com `NICHO_NAO_RECONHECIDO`).
- **Implementação Técnica:**
  - O planner lê o C1 e grava, junto do `PLANNER.json`: camadas, fases e tickets; cada ticket com `ferramenta_destino`, `entrada`, `saida_esperada`, `pecas_do_almoxarifado` e `criterio_de_aceite`.
  - `HANDOFF_PLANNER_ENGINE.json` (C2) passa a carregar a entrada de cada construtor (inclusive a da factory) e o `perfil_app` para o ops, **calculado a partir da própria planta** (cada módulo, banco, fila, integração e rota desenhados geram os itens do perfil; nada vem de lista fixa).
- **Verificação (Green):** teste passa; o fluxo 02 passa do pre-flight da factory.
- **Construtor Prompt (EN):**
  - Write tools/aidd-planner/tests/test_planta_tickets_roteados.py first. Assert planner output has tickets for builder, master, enterprise and ops. Assert each ticket has ferramenta_destino, entrada, saida_esperada, pecas_do_almoxarifado, criterio_de_aceite. Assert perfil_app is derived from planned modules, storage, queues, integrations and routes. Change one planned module and assert perfil_app changes. Assert factory input present for flow 2. Run. Assert exit 1.
  - Make planner read HANDOFF_FORGE_PLANNER.json. Generate layers, phases and routed tickets. Write them into PLANNER.json and HANDOFF_PLANNER_ENGINE.json.
  - Run test. Run 3 E2E flows into new ciclo folder. Assert no metric worse than ciclo-01.

### Ticket 12: Orquestrador só passa o bastão, não escreve contrato (Refere-se a D2 / DoD 6)
- **Falha 15-D:** `D2. Contratos e Interfaces`
- **Artefato de Handoff:** `tests/test_orquestrador_contratos_reais.py`
- **Gate do Ticket:** `python -m pytest -q -p no:cacheprovider tests/test_orquestrador_contratos_reais.py && python scripts/e2e_foto.py rodar --ciclo auto && python scripts/e2e_foto.py comparar --base ciclo-01 --novo ultimo`
- **Requisito TDD (Red):** O orquestrador hoje inventa `PLANO-INFRAESTRUTURA.json` e os 4 contratos, roda o `dispatch` na etapa do construtor e audita o monorepo na etapa 7.
- **Implementação Técnica:**
  - Lê só os contratos gravados pelas ferramentas; entrega a cada ferramenta os tickets dela (da planta).
  - O `dispatch` vai para o começo da etapa do master; a etapa 7 usa `ecossistema.py forge audit <projeto>`.
- **Verificação (Green):** teste passa.
- **Construtor Prompt (EN):**
  - Write tests/test_orquestrador_contratos_reais.py first. Assert orchestrator never writes PLANO-INFRAESTRUTURA.json or handoff files. Assert dispatch runs in master stage. Assert stage 7 runs forge audit on project path. Run. Assert exit 1.
  - Change scripts/orquestrador_sincrono.py. Read handoffs written by tools only. Pass routed tickets to each tool. Move dispatch to master stage. Use ecossistema.py forge audit PROJECT in stage 7.
  - Run test. Run 3 E2E flows into new ciclo folder. Assert no metric worse than ciclo-01.

### Ticket 13: aidd-open consome do almoxarifado e entrega só fatias (Refere-se a D1 / DoD 7)
- **Falha 15-D:** `D1. Arquitetura e Fronteiras`
- **Artefato de Handoff:** `tools/aidd-open/tests/test_fronteira_factory.py`
- **Gate do Ticket:** `python -m pytest -q -p no:cacheprovider tools/aidd-open/tests/test_fronteira_factory.py && python scripts/e2e_foto.py rodar --ciclo auto && python scripts/e2e_foto.py comparar --base ciclo-01 --novo ultimo`
- **Requisito TDD (Red):** O gate acusa V1 e V2 na factory; `vsa_generator.py:25` lê os moldes da própria pasta.
- **Implementação Técnica:**
  - `vsa_generator.py` pede os moldes ao almoxarifado (`caminho_peca`); a factory escreve só `src/modules/<dominio>/` + C3. As cópias de `templates/vsa/` ficam para a fase (d).
- **Verificação (Green):** teste passa; o fluxo 02 passa da etapa 3.
- **Construtor Prompt (EN):**
  - Write tools/aidd-open/tests/test_fronteira_factory.py first. Assert vsa_generator reads templates through aidd_forge almoxarifado caminho_peca. Assert factory writes only src/modules/DOMAIN and HANDOFF_ENGINE_MASTER.json. Run. Assert exit 1.
  - Change tools/aidd-open/src/core/vsa_generator.py to use caminho_peca. Read tickets from HANDOFF_PLANNER_ENGINE.json.
  - Run test. Run 3 E2E flows into new ciclo folder. Assert no metric worse than ciclo-01.

### Ticket 14: aidd-freedom escreve só dentro do projeto (Refere-se a D1 / DoD 7)
- **Falha 15-D:** `D1. Arquitetura e Fronteiras`
- **Artefato de Handoff:** `tools/aidd-freedom/tests/test_fronteira_bridge.py`
- **Gate do Ticket:** `python -m pytest -q -p no:cacheprovider tools/aidd-freedom/tests/test_fronteira_bridge.py && python scripts/e2e_foto.py rodar --ciclo auto && python scripts/e2e_foto.py comparar --base ciclo-01 --novo ultimo`
- **Requisito TDD (Red):** `bridge scan <export>` grava `bridge-manifest.json` dentro do export do usuário (V10).
- **Implementação Técnica:**
  - Manifesto em `<projeto>/.aidd/bridge-manifest.json`; fatia convertida em `src/modules/<dominio>/`; grava o C3.
- **Verificação (Green):** teste passa; no E2E, `vazamentos.origem` fica vazio.
- **Construtor Prompt (EN):**
  - Write tools/aidd-freedom/tests/test_fronteira_bridge.py first. Create temp git repo as export. Run bridge scan. Assert export git status is clean. Assert manifest written inside project folder. Run. Assert exit 1.
  - Change bridge scan to write PROJECT/.aidd/bridge-manifest.json. Write converted slice to src/modules/DOMAIN and HANDOFF_ENGINE_MASTER.json.
  - Run test. Run 3 E2E flows into new ciclo folder. Assert origem leak list is empty.

### Ticket 15: aidd-pure consome do almoxarifado, sem cache dentro da ferramenta (Refere-se a D1 / DoD 7)
- **Falha 15-D:** `D1. Arquitetura e Fronteiras`
- **Artefato de Handoff:** `tools/aidd-pure/tests/test_fronteira_generator.py`
- **Gate do Ticket:** `python -m pytest -q -p no:cacheprovider tools/aidd-pure/tests/test_fronteira_generator.py && python scripts/e2e_foto.py rodar --ciclo auto && python scripts/e2e_foto.py comparar --base ciclo-01 --novo ultimo`
- **Requisito TDD (Red):** O generator usa o próprio injetor (V3) e grava cache em `tools/aidd-pure/scripts/.aidd/cache/` (V11).
- **Implementação Técnica:**
  - Quem precisa de injeção usa a peça única do almoxarifado; ajustar `gates/G_CLI_HELP_CONSISTENCIA.py:59` e `gates/manifesto_harnesses.json`.
  - Cache do protocolo delegado em `<projeto>/.aidd/cache/`.
- **Verificação (Green):** teste passa; nenhum arquivo novo em `tools/aidd-pure/` depois do fluxo 01.
- **Construtor Prompt (EN):**
  - Write tools/aidd-pure/tests/test_fronteira_generator.py first. Assert generator imports injector from catalog piece, not local copy. Assert delegated cache path is inside project folder. Run. Assert exit 1.
  - Switch generator injector usage to catalog piece. Update gates/G_CLI_HELP_CONSISTENCIA.py and gates/manifesto_harnesses.json.
  - Point delegated cache to PROJECT/.aidd/cache.
  - Run test. Run 3 E2E flows into new ciclo folder. Assert worktree tools/aidd-pure unchanged after flow 01.

### Ticket 16: aidd-ops gera infra para qualquer app (Refere-se a D1 / DoD 7)
- **Falha 15-D:** `D1. Arquitetura e Fronteiras`
- **Artefato de Handoff:** `tools/aidd-ops/tests/test_fronteira_ops_infra_generica.py`
- **Gate do Ticket:** `python -m pytest -q -p no:cacheprovider tools/aidd-ops/tests/test_fronteira_ops_infra_generica.py && python scripts/e2e_foto.py rodar --ciclo auto && python scripts/e2e_foto.py comparar --base ciclo-01 --novo ultimo`
- **Requisito TDD (Red):** `ops plan` para "Gestao Tarefas" reprova com `NICHO_NAO_RECONHECIDO`.
- **Implementação Técnica:**
  - O ops vira dono do conteúdo das receitas `moldes/infra/*` (a base é a versão master consertada em 17/09) e as busca no almoxarifado.
  - Entrada pelos tickets de ops da planta + `perfil_app` dinâmico (C5): o ops monta a infra a partir do que o app realmente tem (ex.: se a planta tem fila, sobe o serviço de fila; se tem PostgreSQL, sobe o banco). O nicho vira atalho opcional.
  - Precisa vir **antes** dos tickets 17 e 18, para a infra nunca ficar sem dono.
- **Verificação (Green):** teste passa; na continuação do fluxo 01, `ops plan` dá exit 0 e gera Dockerfile, compose, deploy.sh e nginx.
- **Construtor Prompt (EN):**
  - Write tools/aidd-ops/tests/test_fronteira_ops_infra_generica.py first. Run ops plan with two different perfil_app inputs. Assert exit 0 for both. Assert generated services differ according to profile. Assert Dockerfile, docker-compose.yml, deploy.sh, nginx config generated from catalog pieces. Run. Assert exit 1.
  - Make ops read ops tickets and perfil_app. Fetch moldes/infra pieces through obter_peca. Make niche optional.
  - Run test. Run 3 E2E flows and continuation into new ciclo folder. Assert no metric worse than ciclo-01.

### Ticket 17: aidd-master integra e faz o Quarteto, sem infra (Refere-se a D1 / DoD 7)
- **Falha 15-D:** `D1. Arquitetura e Fronteiras`
- **Artefato de Handoff:** `tools/aidd-master/tests/test_fronteira_master.py`
- **Gate do Ticket:** `python -m pytest -q -p no:cacheprovider tools/aidd-master/tests/test_fronteira_master.py && python scripts/e2e_foto.py rodar --ciclo auto && python scripts/e2e_foto.py comparar --base ciclo-01 --novo ultimo`
- **Requisito TDD (Red):** `master init` grava Dockerfile/compose/deploy.sh/nginx no projeto (V5); `/webhook` dá 404.
- **Implementação Técnica:**
  - O master busca os moldes do Quarteto no almoxarifado; para de gerar infra (agora é do ops); ajustar `attach_vsa_infra.py:27-29`, `bench.py` e `compose_suite._copy_shared_kernel`.
  - Consome o C3, roda o `dispatch`, grava o C4 com status HTTP medido; rota canônica `/webhook` (`/webhooks` vira apelido). Aplicar D1.
- **Verificação (Green):** teste passa; Quarteto 4/4 pelas rotas canônicas.
- **Construtor Prompt (EN):**
  - Write tools/aidd-master/tests/test_fronteira_master.py first. Run master init in temp folder. Assert no Dockerfile, docker-compose.yml, deploy.sh, nginx written. Assert GET /webhook returns 200. Run. Assert exit 1.
  - Fetch Quarteto templates through caminho_peca. Stop infra generation. Fix attach_vsa_infra.py, bench.py, compose_suite.py paths.
  - Consume HANDOFF_ENGINE_MASTER.json. Run dispatch. Write HANDOFF_MASTER_ENTERPRISE.json with measured HTTP status. Add /webhook route, keep /webhooks alias.
  - Run test. Run 3 E2E flows and continuation into new ciclo folder. Assert no metric worse than ciclo-01.

### Ticket 18: aidd-enterprise só blindagem (Refere-se a D1 / DoD 7)
- **Falha 15-D:** `D1. Arquitetura e Fronteiras`
- **Artefato de Handoff:** `tools/aidd-enterprise/tests/test_fronteira_enterprise.py`
- **Gate do Ticket:** `python -m pytest -q -p no:cacheprovider tools/aidd-enterprise/tests/test_fronteira_enterprise.py && python scripts/e2e_foto.py rodar --ciclo auto && python scripts/e2e_foto.py comparar --base ciclo-01 --novo ultimo`
- **Requisito TDD (Red):** O gate acusa V4, V6 e V7 em enterprise.
- **Implementação Técnica:**
  - O enterprise usa só injetor, selo SHA-256, COMPONENT-REGISTRY, auditoria e drift. É dono do conteúdo da peça "injetor" e a consome do almoxarifado.
  - `G_DRIFT_NUCLEO_COMPARTILHADO` compara contra o catálogo, não master × enterprise. Aplicar D4.
- **Verificação (Green):** teste passa; o gate não acusa nada em enterprise (fora as cópias da fase d).
- **Construtor Prompt (EN):**
  - Write tools/aidd-enterprise/tests/test_fronteira_enterprise.py first. Assert enterprise code paths do not use local infra, compose_suite or Quarteto templates. Assert injector loaded from catalog piece. Run. Assert exit 1.
  - Switch enterprise to catalog pieces. Keep injector logic, sha256 seal, COMPONENT-REGISTRY, audit, drift.
  - Change G_DRIFT_NUCLEO_COMPARTILHADO to compare each copy against catalog version. Apply user decision D4.
  - Run test. Run 3 E2E flows and continuation into new ciclo folder. Assert no metric worse than ciclo-01.

## Bloco 4 — Remoção das cópias (Ticket 19) · **com o usuário, peça por peça**
> Não roda pelo orquestrador autônomo: cada remoção mostra a lista e para onde foi o conteúdo único, e espera o OK (Lei #7).

### Ticket 19: Remover as cópias com prova de zero perda (Refere-se a D15 / DoD 8)
- **Falha 15-D:** `D15. Fonte Única e Sincronização`
- **Artefato de Handoff:** `scripts/contar_duplicatas.py`
- **Gate do Ticket:** `python -m pytest -q -p no:cacheprovider tests/test_contar_duplicatas.py && python scripts/inventario_capacidades.py comparar docs/auditoria/fronteiras-ferramentas/ciclo-01/INVENTARIO-ANTES.json`
- **Requisito TDD (Red):** Mede no repo real 249 conteúdos repetidos em 727 arquivos e 126 cópias de gate; o teste exige zero cópia de peça do catálogo dentro de `tools/`.
- **Implementação Técnica:**
  - Para cada ferramenta: listar as cópias, mostrar ao usuário para onde foi o conteúdo único e remover só depois do OK (Lei #7).
  - Depois: `inventario_capacidades.py comparar INVENTARIO-ANTES.json` com zero órfão, e total de testes ≥ 2352.
- **Verificação (Green):** `tests/test_contar_duplicatas.py` passa; `comparar` dá zero órfão; bateria completa verde.
- **Construtor Prompt (EN):**
  - Write tests/test_contar_duplicatas.py first. Assert zero catalog piece copies under tools. Run. Assert exit 1.
  - Implement scripts/contar_duplicatas.py. Use git ls-tree HEAD blob hashes. Skip empty files and harness folders. Print per pair counts and gate copy counts as JSON.
  - List copies per tool and wait for user confirmation before removal.
  - Run inventario_capacidades.py comparar against INVENTARIO-ANTES.json. Assert zero orphans. Assert test count at least 2352. Run full gate battery. Assert exit 0.

## Bloco 5 — Fechamento (Tickets 20–23) · autônomo

### Ticket 20: Fiscal e contratos passam a bloquear (Refere-se a D13 / DoD 9)
- **Falha 15-D:** `D13. Quality Gates (Portões)`
- **Artefato de Handoff:** `gates/test_g_fronteira_bloqueio.py`
- **Gate do Ticket:** `python -m pytest -q -p no:cacheprovider gates/test_g_fronteira_bloqueio.py`
- **Requisito TDD (Red):** Com allowlist vazia e `bloqueio` como padrão, a violação plantada dá exit 1 no commit, e o contrato sem evidência derruba o `run-fluxo`.
- **Implementação Técnica:**
  - `AIDD_FRONTEIRA_MODO` com padrão `bloqueio`; `gates/allowlist_fronteira.json` vazio; `validar_handoff.py` bloqueando.
- **Verificação (Green):** teste passa; bateria completa verde.
- **Construtor Prompt (EN):**
  - Write gates/test_g_fronteira_bloqueio.py first. Plant violation in temp repo. Assert exit 1 with default mode. Plant handoff without evidence. Assert run-fluxo exits 1. Run. Assert exit 1.
  - Set default AIDD_FRONTEIRA_MODO to bloqueio. Empty gates/allowlist_fronteira.json. Make orchestrator stop on validar_handoff failure.
  - Run test and full gate battery. Assert exit 0.

### Ticket 21: Foto "depois" oficial comparada com o baseline (Refere-se a D12 / DoD 10)
- **Falha 15-D:** `D12. Observabilidade e Frugalidade`
- **Artefato de Handoff:** `docs/auditoria/fronteiras-ferramentas/ciclo-01/COMPARACAO-E2E.md`
- **Gate do Ticket:** `python scripts/e2e_foto.py comparar --base ciclo-01 --novo ultimo`
- **Requisito TDD (Red):** Sem rodar a foto "depois", o arquivo de comparação não existe e o gate reprova.
- **Implementação Técnica:**
  - `python scripts/e2e_foto.py rodar --ciclo auto` do zero, num worktree isolado, depois dos blocos 1–4 e do Ticket 20.
  - Copiar o `COMPARACAO-E2E.md` gerado para a pasta deste ciclo; todas as métricas iguais ou melhores que o ciclo-01.
- **Verificação (Green):** o gate sai com exit 0.
- **Construtor Prompt (EN):**
  - Run python scripts/e2e_foto.py rodar --ciclo auto. Assert exit 0.
  - Run python scripts/e2e_foto.py comparar --base ciclo-01 --novo ultimo. Assert exit 0.
  - Copy generated COMPARACAO-E2E.md to docs/auditoria/fronteiras-ferramentas/ciclo-01/COMPARACAO-E2E.md.

### Ticket 22: README de cada ferramenta com a fronteira final (Refere-se a D14 / DoD 11)
- **Falha 15-D:** `D14. Documentação Viva`
- **Artefato de Handoff:** `docs/anatomias/FRONTEIRAS-POR-FERRAMENTA.md`
- **Gate do Ticket:** `python -m pytest -q -p no:cacheprovider tests/test_readme_fronteiras.py`
- **Requisito TDD (Red):** O teste compara a seção "faz / não faz / consome do almoxarifado" de cada `tools/aidd-*/README.md` com o mapa e reprova se divergir.
- **Implementação Técnica:**
  - Gerar o doc a partir do mapa; atualizar os 8 READMEs e o `docs/anatomias/PAPEIS-DAS-8-FERRAMENTAS.md` com a visão (forge = terreno + almoxarifado; planner = planta + tickets roteados).
- **Verificação (Green):** `tests/test_readme_fronteiras.py` passa.
- **Construtor Prompt (EN):**
  - Write tests/test_readme_fronteiras.py first. Parse each tools/aidd-*/README.md boundary section. Compare with MAPA-DONOS-FERRAMENTAS.json. Run. Assert exit 1.
  - Generate docs/anatomias/FRONTEIRAS-POR-FERRAMENTA.md from map. Update 8 README files and docs/anatomias/PAPEIS-DAS-8-FERRAMENTAS.md.
  - Run test. Assert exit 0.

### Ticket 23: Mapas visuais e livros atualizados com o estado final (Refere-se a D14 / DoD 14)
- **Falha 15-D:** `D14. Documentação Viva`
- **Artefato de Handoff:** `tests/test_mapas_e_livros_em_dia.py`
- **Gate do Ticket:** `python scripts/catalogo_pecas.py --check && python -m pytest -q -p no:cacheprovider tests/test_mapa_visual.py tests/test_catalogo_pecas.py tests/test_mapas_e_livros_em_dia.py`
- **Requisito TDD (Red):** O teste roda `scripts/mapa_visual.py <tipo> --check` para os 13 mapas e reprova se algum estiver desatualizado (medido em 01/10: o `indice` já sai com exit 1). Também reprova se o livro mais novo de cada série for anterior à data de fechamento do ciclo, ou se citar `aidd-generator`, `aidd-factory` ou `aidd-bridge` fora da tabela de nomes antigos.
- **Implementação Técnica:**
  - Último ticket: só roda depois dos Tickets 1–22 aprovados.
  - Mapas (`docs/mapas-visuais`): `python scripts/catalogo_pecas.py` → `python scripts/mapa_visual.py <tipo>` para os 13 tipos (comandos, conexoes, encaixes, ferramentas, guardas, harnesses, indice, leis, lente15d, moldes, oficina, scripts, skills); revisar os moldes (`docs/mapas-visuais/moldes/`) com o almoxarifado, os 5 contratos, os nomes novos e a fronteira de cada ferramenta.
  - Livros (`docs/livros`):
    - livro principal: editar `docs/livros/partes/*.md` → `python componentes/compartilhado/skills/aidd-textbook/scripts/livro.py update docs/livros --nota "fronteiras-ferramentas ciclo-01"`;
    - Livro Visual: `python docs/livros/gerar_livro_auditoria.py DD-MM-AAAA`;
    - Mini-livro: recompilar com pandoc + `livro-aidd.typst`.
  - Conferir **todas** as tabelas com números lidos do disco (`git ls-files`), nunca copiados do texto antigo; o `check` do livro não pode ter mais achados do que antes.
- **Verificação (Green):** teste passa; os 13 mapas com `--check` exit 0; os 3 livros com a data do fechamento, em md e pdf.
- **Construtor Prompt (EN):**
  - Write tests/test_mapas_e_livros_em_dia.py first. Run scripts/mapa_visual.py TYPE --check for all 13 types. Assert all exit 0. Assert newest book of each series is dated on or after cycle close date. Assert books do not cite aidd-generator, aidd-factory or aidd-bridge outside old names table. Run. Assert exit 1.
  - Run python scripts/catalogo_pecas.py. Run python scripts/mapa_visual.py TYPE for all 13 types. Update templates in docs/mapas-visuais/moldes with almoxarifado, 5 contracts, new tool names and tool boundaries.
  - Update docs/livros/partes markdown with numbers read from git ls-files. Run livro.py update docs/livros. Run docs/livros/gerar_livro_auditoria.py with current date. Rebuild mini book with pandoc and livro-aidd.typst.
  - Assert book check findings count not higher than before.
  - Run test. Assert exit 0.

## Riscos (Etapa 9)

> Os caminhos abaixo usam os nomes de hoje. A partir do Ticket 4: generator → `aidd-pure`, factory → `aidd-open`, bridge → `aidd-freedom`.

| Risco | Onde | Como o plano trata |
|---|---|---|
| Perder algo feito certo ao apagar cópia | 249 famílias de cópias, 126 cópias de gate | Tag de segurança, inventário (T3), versão juntada no catálogo (T8), `comparar` com zero órfão e testes ≥ 2352 (T19), OK do usuário antes de cada remoção |
| Gates que dependem das cópias | `G_DRIFT_NUCLEO_COMPARTILHADO`, `G_HARNESS_COMPAT`, `G_COMPONENTE_AGNOSTICO`, `G_CLI_HELP_CONSISTENCIA:59` | Ajustados nos tickets 15 e 18 |
| Caminhos fixos | `tests/test_mapa_visual.py`; `G_HONESTIDADE_ROTULO.py` e `termos_proibidos_marketing.json`; `G_ARQUITETURA_DELIVERABLE`, `G_LLM_PROMPT_SHIELD`, `G_QUARTETO_SINE_QUA_NON`, `scripts/catalogo_pecas.py`; `gates/manifesto_harnesses.json`; `vsa_generator.py:25`, `attach_vsa_infra.py:27`, `bench.py:26`, `compose_suite.py:503`; 66 `.py` que apontam para `componentes/compartilhado` | As cópias só saem na fase (d), depois que todos já consomem do almoxarifado; grep refeito antes de cada mudança |
| Os 3 fluxos já quebram na etapa 3 | `run-fluxo` | Os tickets 10, 11 e 12 vêm primeiro na fase (c); até lá, a continuação mede as etapas 4–6 |
| Infra sem dono no meio do caminho | master/enterprise → ops | O ticket 16 (ops) vem antes dos tickets 17 e 18 |
| O forge virar "faz-tudo" | almoxarifado | Regra 2: o forge guarda, o especialista escreve; o mapa registra `dono_do_conteudo_de` |
| Espelhos de harness | `.claude`, `.agents`, `.gemini`, `.opencode`, `.mimocode`, `.cursor` (inclusive dentro de `tools/aidd-master/`) | `components sync --tipo todos` + `components verify` em todo ticket que mexe em skill/command |
| Protocolo delegado do generator | Sem IA respondendo, o fluxo 01 falha | O ticket 10 faz falhar cedo e com mensagem clara; o E2E "depois" roda sozinho e com IA respondendo, separando os dois |
| Agente autônomo em sessão paralela | Orca aberto | `git status` + checagem de escrita concorrente antes de cada ticket |
