# Especificação — Contratos de Passagem e Gate de Fronteira (ciclo-01)

> Só especificação. Nenhum código neste ciclo de diagnóstico.
> Analogia: cada ferramenta é uma estação de uma linha de montagem. O contrato é a **etiqueta da caixa** que passa de uma estação para a outra. Hoje quem escreve a etiqueta é o supervisor (o orquestrador), não a estação que fez o trabalho — por isso a etiqueta diz "tudo certo" até quando a caixa está vazia.

## Visão (definida pelo usuário)
forge prepara o terreno completo e guarda o **almoxarifado** de peças → planner desenha a planta com tickets endereçados a cada ferramenta → construtor e acabamento **consomem as peças sob demanda**. Nenhuma ferramenta guarda cópia de peça; quem guarda é o forge, quem escreve o conteúdo de cada receita é o especialista dono dela.

## Regras que valem para todos os contratos

1. **Quem produz escreve.** O JSON de saída é gravado pela própria ferramenta, nunca montado pelo orquestrador.
2. **Quem recebe valida.** A ferramenta seguinte valida o JSON (schema + evidência) antes de começar; o orquestrador só confere se o arquivo existe e passou.
3. **Evidência, não promessa.** Campo booleano do tipo "ok" é proibido sem a prova junto (caminho existente, hash, status HTTP medido, resumo do pytest).
4. **Tudo dentro da pasta do projeto.** Todo caminho do contrato é relativo à pasta do projeto e precisa existir nela.
5. **Schemas em** `componentes/compartilhado/specs/` (fonte única). Os 4 que já existem ganham os campos novos; falta criar o `handoff-forge-to-planner`.

## Os 5 contratos

### C1 — forge → planner · `.aidd/HANDOFF_FORGE_PLANNER.json` (novo) — **checklist de prontidão do terreno**
O forge só passa o bastão quando tudo abaixo foi **testado de verdade**. Se qualquer item falhar, o forge para ali (exit 1) e diz o que fazer.

| Campo obrigatório | Tipo | Prova exigida |
|---|---|---|
| `versao_schema` | string | — |
| `projeto_dir` | string | pasta existe |
| `git.inicializado` / `git.commit_inicial` | bool / SHA | `git rev-parse HEAD` responde |
| `dependencias[]` | {pacote, versao} | `import` real de cada uma dá certo |
| `leis_e_guardas[]` | {gate, sha256} | instalado no projeto com o hash do catálogo do almoxarifado |
| `harnesses[]` | string[] | espelhos presentes e conferidos (`components verify`) |
| `almoxarifado` | {catalogo_sha256, pecas_disponiveis} | o `CATALOGO.json` existe, e cada peça listada abre |
| `capacidade_llm` | `delegado_com_resposta` \| `headless_com_chave` \| `nenhuma` | teste real de ida e volta (pedido → resposta) |
| `estrutura_projeto` | árvore de pastas esperada | pastas criadas (é nela que o planner desenha) |

Valida: planner, na entrada.

### C2 — planner → construtor e acabamento · `HANDOFF_PLANNER_ENGINE.json` (já existe; quem grava passa a ser só o planner) — **a planta baixa com tickets roteados**
| Campo obrigatório | Prova exigida |
|---|---|
| `camadas[]` e `fases[]` | seguem a `estrutura_projeto` do C1 |
| `tickets[]`: {id, ferramenta_destino, entrada, saida_esperada, pecas_do_almoxarifado[], criterio_de_aceite} | toda `ferramenta_destino` está no mapa; toda peça citada existe no catálogo |
| tickets para **as 6 ferramentas seguintes** | pelo menos 1 para o construtor do fluxo, master, enterprise e ops |
| `entrada_construtor` | factory: plano de motores; bridge: `origem_export` com caminho e hash; generator: ideia + `capacidade_llm` exigida |
| `perfil_app` (**dinâmico**) | calculado da própria planta: cada módulo, entidade, banco, fila, integração externa, rota do Quarteto e porta desenhados gera um item do perfil; mudar a planta muda o perfil. Nada vem de lista fixa de nichos — é o que o ops usa para montar a infra |

Valida: cada ferramenta valida os **próprios** tickets antes de começar (o construtor no pre-flight; master, enterprise e ops na entrada de cada etapa).

### C3 — construtor → master · `HANDOFF_ENGINE_MASTER.json` (já existe; quem grava passa a ser o construtor)
| Campo obrigatório | Prova exigida |
|---|---|
| `origem_engine` | igual ao fluxo do C2 |
| `slices_geradas[].caminho_src` | existe e fica em `src/modules/<dominio>/` |
| `slices_geradas[].sha256_arvore` | hash da pasta bate |
| `testes_executados` | vem de relatório real do pytest (junit/json), não de conta fixa |
| `arquivos_fora_da_zona` | precisa ser lista vazia |

Valida: master, na entrada.

### C4 — master → enterprise · `HANDOFF_MASTER_ENTERPRISE.json` (já existe)
| Campo obrigatório | Prova exigida |
|---|---|
| `quarteto[]` | {rota, status_http_medido}, com as 4 rotas: `/api/...`, `/webhook`, `/mcp`, `/docs` |
| `servidor_sobe` | log da subida + porta |
| `componentes_para_blindagem[]` | {caminho_relativo, sha256} |

Valida: enterprise, na entrada.

### C5 — enterprise → ops · `HANDOFF_ENTERPRISE_OPS.json` (já existe)
| Campo obrigatório | Prova exigida |
|---|---|
| `registry` | caminho do `COMPONENT-REGISTRY.json` + sha256 |
| `selo_sha256` | hash do conjunto blindado |
| `drift` | resultado do `verificar-drift` (exit code real) |
| `perfil_app` | runtime, portas, banco — **dado pelo app, não por "nicho"** |

Sai do contrato: `dockerfile_presente` e `compose_presente` (isso é **saída** do ops, não entrada).
Valida: ops, na entrada.

## Cada quebra do E2E e o contrato que teria pegado

| Quebra medida (BASELINE-E2E) | Contrato | Como teria pegado |
|---|---|---|
| Fluxo 01: generator espera 45 s por uma IA que não existe, e cai sem chave headless (59 s, exit 1) | C1 `capacidade_llm` | O forge pararia na prontidão, em segundos, com a mensagem "nenhuma IA disponível: abra numa ADE ou configure LLM_MODEL" |
| Fluxo 01: `No module named 'core.logs'` | C1 `dependencias[]` | O `import` real reprovaria no forge |
| Fluxo 02: `FACTORY_INPUT_INVALID` — o orquestrador inventa um `PLANO-INFRAESTRUTURA.json` de 4 campos, e a factory exige outros 5 | C2 `tickets[]` + `entrada_construtor` | O planner é obrigado a produzir os tickets e a entrada da factory; o orquestrador perde o poder de inventar o arquivo |
| Fluxo 03: `dispatch` falha com `invalid reference: main` (o forge fez `git init` mas nenhum commit) | C1 `git.commit_inicial` | O forge não fecha a etapa sem commit inicial |
| Fluxo 03: o `dispatch` (código do master) roda dentro da etapa do construtor | C3 + gate de fronteira | Despachar fatias vira trabalho do master, depois de receber o C3 |
| Fluxo 03: a bridge grava `bridge-manifest.json` dentro do export do usuário | Regra 4 + gate de fronteira (modo execução) | Escrita fora da pasta do projeto reprova |
| `--dry-run` aprova os 4 contratos com "100%" sem rodar nada | Regras 1 e 3 | Sem arquivo da ferramenta e sem prova, o contrato não passa |
| Continuação: `ops plan` reprova app genérico (`NICHO_NAO_RECONHECIDO`) | C2 `perfil_app` + tickets de ops, repassados no C5 | O ops recebe da planta o perfil do app e os tickets dele, em vez de adivinhar um nicho pelo texto |
| 249 conteúdos repetidos entre ferramentas | Gate de fronteira (cópia de peça do catálogo dentro de `tools/`) | Cada cópia é acusada com o nome da peça do almoxarifado que deveria ser consumida |
| Continuação: `/webhook` dá 404 (o real é `/webhooks`) | C4 `quarteto[]` | A rota canônica é medida e precisa responder 2xx/3xx |

## Gate de fronteira — `gates/G_FRONTEIRA_FERRAMENTAS.py` (especificação)

**Fonte de dados:** `componentes/compartilhado/specs/MAPA-DONOS-FERRAMENTAS.json` (gerado na fase a), com uma entrada por ferramenta:

```json
{
  "aidd-factory": {
    "pode_conter": ["src/**", "scripts/**", "schemas/**", "tests/**", "templates/dominio/**"],
    "nunca_conter": ["**/Dockerfile*", "**/docker-compose*", "**/deploy.sh", "**/nginx/**",
                     "**/mcp_server*", "**/webhook*", "**/openapi*", "**/swagger*", "**/G_*.py", "**/*inject*"],
    "zona_escrita_no_projeto": ["src/modules/*/**", "HANDOFF_ENGINE_MASTER.json"]
  }
}
```

**Modo estático (no commit):** percorre `git ls-files tools/aidd-*`. Arquivo que bate em `nunca_conter` da ferramenta onde está → violação, com o nome do dono certo.

**Modo execução (no E2E):** antes e depois de cada etapa, tira uma foto (mtime + sha256) da pasta do projeto, do clone da ferramenta e da origem do export. Escrita fora de `zona_escrita_no_projeto` da etapa, ou fora da pasta do projeto → violação.

Zonas de escrita no projeto, por etapa:

| Etapa | Pode escrever |
|---|---|
| forge | `.git/hooks/`, pastas de harness, `gates/`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.aidd/HANDOFF_FORGE_PLANNER.json` |
| planner | `PLANNER.json`, `HANDOFF_PLANNER_ENGINE.json`, `VSA_DISPATCH.json`, `DESIGN-SYSTEM.json` |
| generator / factory / bridge | `src/modules/<dominio>/**`, `frontend/app/<dominio>/**`, `HANDOFF_ENGINE_MASTER.json`, `.aidd/cache/**` |
| master | `src/core/**`, `src/server.py`, `src/shared/**`, `frontend/` (casca), `docs/`, `HANDOFF_MASTER_ENTERPRISE.json` |
| enterprise | `COMPONENT-REGISTRY.json`, `RELATORIO-AUDITORIA.json`, `templates/rules/**`, `.aidd/selo/**`, `HANDOFF_ENTERPRISE_OPS.json` |
| ops | `Dockerfile`, `docker-compose.yml`, `deploy.sh`, `nginx/**`, `.sops.yaml`, `secrets/*.enc.*`, `monitoramento/**` |

**Níveis:** `AIDD_FRONTEIRA_MODO=aviso` (padrão nas fases a–d: imprime relatório e sai com exit 0) e `bloqueio` (fase e: exit 1). As violações conhecidas hoje entram numa lista de exceções com data (`gates/allowlist_fronteira.json`), que só pode diminuir — um teste reprova se ela crescer.

**Teste que prova que o gate funciona:** planta um `Dockerfile` em `tools/aidd-factory/` de um repo temporário e espera exit 1 em `bloqueio`; planta uma escrita do construtor fora de `src/modules/` e espera violação no modo execução.
