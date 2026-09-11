---
name: orchestrate
description: Roteador de ambiente e Plano de Voo para execução de planos ORCA — pergunta ORCA (app real), Subagentes (Agent tool desta sessão) ou Git Worktree nativo antes de tudo; cada ambiente compila um JSON no formato certo pra ele, e só depois executa.
---

# /orchestrate — Roteador de Ambiente e Plano de Voo

Contrato executável universal do slash command `/orchestrate [plano]`.

## Posicao no Fluxo (leia antes de agir)

O ecossistema tem **um unico fluxo de trabalho de 3 etapas**, e cada etapa
termina com uma **parada obrigatoria** onde quem decide e o usuario:

| Etapa | Comando | Entra | Sai | Parada obrigatoria no fim |
|---|---|---|---|---|
| 1 | `/melhoria <pedido em linguagem natural>` | pedido do usuario, ou um plano existente pra reanalisar | relatorio em `docs/melhorias/` com Nota Atual e evidencia | "quer que eu gere o plano a partir disto?" |
| 2 | `/plan <nome>` | o relatorio da etapa 1 (ou o pedido direto) | pasta em `docs/planos/<nome>/` com todos os itens em rascunho | "aprova este plano?" |
| 3 | `/orchestrate <plano>` | plano aprovado | execucao real das frentes | escolha de ambiente + aprovacao do Plano de Voo |

**Nenhuma etapa dispara a seguinte sozinha** (Regra de Ouro #7 do `AGENTS.md`).
Cada comando tem **um dono unico**: `melhoria`, `plan` e `orchestrate`. As
skills-motor (`planos-auditoria-runner`, `orca-plan-orchestrator`) nao tem
slash command proprio e sao acionadas por elas.

> **Nome das iniciativas:** toda pasta de plano segue `PLAN-<NNNN>-<nome-curto>` (ex.: `PLAN-0016-qualidade-testes-mutacao`). O `NNNN` e um identificador global unico — use ele pra falar do plano sem ambiguidade, em vez de "plano 03", que existia em tres subpastas ao mesmo tempo. Quem gera o nome e o `plan init`; nunca monte a mao.

## Regra Fixa: Cada Ambiente Tem Seu Proprio Formato de Plano de Voo

Nunca existiu (e nunca deve existir) um unico formato de `.orca-flight-plan.json`
servindo os tres ambientes. Sao motores de execucao diferentes, com formatos
diferentes — misturar os formatos e exatamente o bug que gerava planos
inexecutaveis no app ORCA real:

| Ambiente | O que executa de fato | Formato do Plano de Voo |
|---|---|---|
| **ORCA** | O aplicativo ORCA real, via `orca-cli` (worktree/terminal de verdade) | `orca_real_plan.compilar_plano_orca` — separa comando de lancamento (sem prompt) do texto da tarefa (enviado depois) |
| **Subagentes** | Agent tool desta sessao (contexto compartilhado, sem worktree) | `subagent_plan.compilar_plano_subagentes` — `subagent_type`/`model`/`prompt` por frente |
| **Git Worktree nativo** | Motor deste projeto (`orchestrator_engine.py`) — git worktree puro + harness spawnado direto, sem precisar do app ORCA | `flight_plan.gerar_plano_de_voo` — comando completo (harness + prompt embutido) pronto pra `subprocess.run` |

## Nome da Mesa: `PLAN-<NNNN>-fase-<NN>-<nome-curto>`

Cada frente vira uma mesa (worktree) com este nome, **nos tres ambientes**:

```
PLAN-0016-fase-04-eliminar-timesleep-injetar
```

- `PLAN-0016` e o identificador global do plano (o mesmo da pasta em
  `docs/planos/`), e `fase-04` e o item `04-*.md` daquele plano.
- **A fase leva dois digitos sempre.** Com um so, `fase-10` apareceria antes
  de `fase-2` em qualquer lista ordenada por nome — e o painel de mesas e
  ordenado por nome.
- O branch e `orca/<mesma-coisa>`.
- O nome curto do item entra cortado em 3 palavras: sem o corte o rotulo passa
  de 70 caracteres, e ele vira caminho de pasta e nome de branch.

**Por que isso importa:** varios planos podem estar rodando ao mesmo tempo.
Sem o identificador no nome, uma mesa chamada `orca-portas-efemeras` nao diz de
qual plano ela e, e o painel vira uma gaveta de chaves sem etiqueta — da pra
ver quantas tem, nao da pra saber qual abre o que. Com o rotulo, olhar a lista
ja responde o que esta rodando, o que ja rodou e o que falta.

**Nunca invente o nome da mesa.** Ele vem pronto no campo `rotulo` de cada
frente do `.orca-flight-plan.json`, gerado por `plan_parser.rotulo_da_frente`.
Use o valor exato — inclusive no `--name` do `worktree create`.

## Protocolo Interativo do Agente (/orchestrate)

Quando invocado:

### Passo 1: Gate de Ambiente (obrigatorio, sempre a primeira pergunta)
Pergunte explicitamente ao usuario, nunca assuma:

- **1) ORCA (aplicativo real, via orca-cli)** — worktree e terminal de verdade
  dentro do app ORCA instalado. Use quando o app esta instalado e voce quer
  acompanhar cada frente pela interface do ORCA. Cada frente nasce em uma mesa
  **independente (`--no-parent`, sem `--base-branch`)** — que e o padrao do
  manual oficial do `orca-cli` pra trabalho paralelo. **So crie mesa filha
  (`--parent-worktree`) quando o usuario pedir trabalho empilhado explicito**
  ("parte do branch atual", "em cima da frente anterior"). Encadear mesa filha
  por padrao foi o que gerou arvore de mesa dentro de mesa, cada nivel abrindo
  outro harness.
- **2) Subagentes** — Agent tool desta propria sessao, sem worktree, sem
  terminal separado. Contexto compartilhado, **sem isolamento de arquivo**.
  Avise o usuario desse risco se o plano tiver frentes que tocam os mesmos
  arquivos.
- **3) Git Worktree nativo** — motor deste projeto, isolamento de arquivo
  real via `git worktree` puro, sem precisar do app ORCA instalado. Use
  quando o app ORCA nao esta disponivel e Subagentes gastaria tokens
  demais/contexto compartilhado nao serve.

### Passo 2: Compile o Plano de Voo (zero-LLM, mecânico — nunca decida sozinho harness/modelo/subagent_type sem perguntar)
- **Se ORCA:** `python ecossistema.py orchestrate <plano> --ambiente orca --dry-run [--repo-path <caminho>] [--parent-worktree <selector>]` — gera o plano com nome/branch/comando-de-lancamento (sem prompt) + prompt separado por frente.
- **Se Subagentes:** `python ecossistema.py orchestrate <plano> --ambiente subagent --dry-run [--subagent-type <tipo>] [--model <modelo>]` — compila `subagent_type`/`model`/`prompt` por frente.
- **Se Git Worktree nativo:** `python ecossistema.py orchestrate <plano> --ambiente gitworktree --dry-run` — segue o protocolo ja existente de `orca-plan-orchestrator` (pergunta harness por frente, gera branch/worktree/comando completo).

O CLI nunca executa nada nesta etapa: e so compilador mecanico, sem acesso a modelo/Agent tool/orca-cli.

### Passo 3: Apresente o Plano de Voo
Mostre o Plano de Voo e o caminho do JSON salvo (`<pasta-do-plano>/.orca-flight-plan.json`). Convide o usuario a abrir e editar (harness, modelo, subagent_type, prompt, parent-worktree) antes de confirmar. Nunca prossiga sem dar essa chance de revisao.

### Passo 4: Peça confirmação explícita
De que o Plano de Voo (editado ou não) está aprovado. Nunca fabrique aprovação.

### Passo 5: Execução

**Regra fixa, valendo pros 3 ambientes:** o plano só é marcado como EM EXECUÇÃO de verdade (e só é movido fisicamente para `docs/planos/fazendo/`) **no instante em que a execução real começa aqui** — nunca antes (nunca no dry-run, nunca na compilação do Plano de Voo). Para **Git Worktree nativo**, isso já acontece automaticamente dentro do próprio `ecossistema.py orchestrate --ambiente gitworktree` (sem passo manual). Para **Subagentes** e **ORCA**, este CLI nunca executa nada sozinho — então, **antes de disparar a primeira frente**, rode manualmente:
```bash
python ecossistema.py plan iniciar-execucao <caminho-do-plano>
```

- **Git Worktree nativo:** rode `python ecossistema.py orchestrate <plano> --ambiente gitworktree --harness ... --yes [--resume]`. ⛔ **Proibição total de subagentes/background tasks continua valendo nesta via** (regra de `orca-plan-orchestrator/SKILL.md`) — o assistente não interfere na execução, só monitora o terminal que o próprio motor abre.

- **Subagentes:** rode `plan iniciar-execucao` (acima), depois releia `.orca-flight-plan.json` (possivelmente editado pelo usuário) e, para CADA frente em ordem, chame a tool Agent com `subagent_type`/`model`/`prompt` exatamente como gravado no JSON. Nunca invente aprovação intermediária — se uma frente falhar ou o subagente reportar bloqueio, pare e informe o usuário antes de seguir pra próxima frente. Não há isolamento de arquivo neste modo.

- **ORCA (aplicativo real):** rode `plan iniciar-execucao` (acima). Este CLI nunca executa nada aqui — quem dirige o app ORCA de verdade e o assistente da sessao, via `orca-cli`.

  **Passo 0 obrigatorio — carregue o manual da versao instalada:**
  ```bash
  orca skills get orca-cli
  ```
  Esse comando imprime o guia oficial casado com o binario que vai rodar os
  comandos. Flags mudam de versao pra versao — **nunca chute subcomando ou flag
  de memoria**. As regras abaixo descrevem a sequencia e as travas fixas; a
  sintaxe exata vem sempre do guia impresso agora.

  Para CADA frente do `.orca-flight-plan.json`, em ordem:

  1. **Garanta o repositorio registrado** no ORCA (liste primeiro; registre so
     se faltar).
  2. **Crie a mesa da frente em um unico comando**, ja com o agente e o prompt:
     `worktree create --name <rotulo-da-frente> --no-parent --agent <harness> --prompt "<texto da frente>" --json`
     (o `<rotulo-da-frente>` e o campo `rotulo` do JSON, ex.: `PLAN-0016-fase-04-eliminar-timesleep-injetar`).
     Essa e a forma preferida do manual: cria a mesa, sobe o agente no primeiro
     terminal e entrega o prompt sem passo manual. Use `--parent-worktree` so
     se o usuario pediu trabalho empilhado.
  3. **⛔ Nunca lance o harness com `--resume <id-de-sessao>`.** Cada frente e
     uma sessao nova. Religar uma sessao antiga so funciona enquanto o
     transcript existir; quando ele nao existe, o harness morre na hora com
     `No conversation found with session ID` e a mesa fica sendo um terminal
     vazio — que parece "aberta e trabalhando" no painel, mas nao tem IA nenhuma
     dentro. Foi exatamente assim que 4 de 5 mesas ficaram penduradas sem fazer
     nada.
  4. **Se (e so se) precisar de argv custom** (modelo/effort especifico que o
     `--agent` nao cobre), va pelo caminho de dois passos — e ai a trava e
     obrigatoria:
     - `terminal create --worktree id:<repoId>::<caminho> --command '<harness ...>' --json`
     - `terminal wait --terminal <handle> --for tui-idle --timeout-ms 60000 --json`
     - **So envie o prompt se o resultado do wait trouxer `satisfied: true`.**
       Um wait que estourou o tempo tambem imprime resultado normal — leia o
       campo, nao o fato de ter impresso algo. Se vier `false`, repita o wait
       uma vez com timeout maior; se continuar `false`, **reporte a frente como
       nao iniciada e nao envie nada**. Prompt digitado numa TUI que ainda esta
       subindo se perde, e a frente morre em silencio.
     - `terminal send --terminal <handle> --text "<texto da frente>" --enter --wait-submit 10 --json`
  5. **⛔ Nunca reenvie no silencio.** `accepted: true` prova que a entrada foi
     aceita, nao que o turno comecou — quem prova isso e o estagio
     `turn_started` do recibo (`--wait-submit`). Se houve falha de transporte
     ambigua, repita o MESMO comando com o `--retry-request <id>` que o recibo
     devolveu. O antigo "mande um envio vazio de reforco" esta proibido: ele
     duplica prompt e e uma das fontes do efeito de loop.
  6. **Monitore periodicamente** (nao so no fim): `terminal read` com cursor pra
     ver o que cada mesa esta fazendo, e o painel de mesas pra achar cedo a IA
     travada ou esquecida.
  7. **Nunca invente aprovacao intermediaria** — se uma frente falhar ou travar,
     pare e informe o usuario antes de seguir pra proxima.
  8. **Auditoria real antes de integrar**: rode `python ecossistema.py audit`
     (ou `pre-commit run --all-files`) dentro da mesa — os gates sao herdados do
     repo principal —, alem de testes de verdade, `git status`/`git diff`,
     leitura dos arquivos modificados e execucao real do app. Nunca confie so na
     palavra da IA da mesa.
  9. **Integracao**: traga o commit aprovado daquela mesa pro branch principal
     (ex.: `cherry-pick`), resolvendo conflito real preservando as mudancas de
     ambas as frentes quando fizer sentido.
  10. **Limpeza (sempre, mesmo se a frente falhou)**: feche os terminais da mesa
      e remova a mesa. Mesa orfa com terminal vivo e o que enche a tela de
      arvore inutil e consome token de fundo. Se a frente vai continuar depois,
      use Sleep do workspace em vez de fechar.

## Quando NÃO usar esta skill

- Execução real do motor de worktrees nativo (branch/merge/gates/circuit breaker) já em andamento → isso é `orca-plan-orchestrator`, não esta.
- Gerar a estrutura do plano em si (`00-PROCESSO-E-DECISOES.md` + `NN-*.md`) → isso é `planos-auditoria-runner`.
- Operar o app ORCA fora do fluxo de um plano (worktrees avulsas, terminais soltos, etc.) → isso é a skill global `orca-cli`, não esta.
