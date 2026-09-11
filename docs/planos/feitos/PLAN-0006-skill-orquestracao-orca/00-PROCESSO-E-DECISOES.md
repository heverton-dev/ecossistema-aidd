# PROCESSO E DECISÕES — Skill de Orquestração ORCA ADE (`/orchestrate`)

> **Origem:** pedido do usuário, 06/09/2026 — analisar viabilidade e planejar a construção da "Skill Universal de Orquestração ORCA ADE" descrita em `docs/features/orquestracao-orca-ade/MANUAL-UNIFICADO-ORQUESTRACAO-ORCA-ADE.md` (+ 12 documentos de detalhamento na mesma pasta), no mesmo formato usado em `docs/planos/skill-gerador-planos-auditoria/`.
> **Propósito deste arquivo:** registro único do *processo* — o conteúdo técnico de cada item vive em documento próprio (ver §3).

---

## 1. Veredito de viabilidade

**Possível, mas não é uma skill simples/barata.** A skill anterior (`planos-auditoria-runner`) era um único arquivo de instrução em linguagem natural. Esta é um motor de orquestração real: 6 módulos Python, gerenciamento de `git worktree` (ciclo de vida completo add→merge→remove), spawn de subprocessos reais de 4 CLIs externas (`agy`, `mimo`, `claude`, `opencode`), máquina de estados com crash-recovery, hooks reativos pre/post, circuit breaker com heartbeat, fila de merge serializada, e um novo subcomando `ecossistema.py orchestrate`. Nada aqui é tecnicamente impossível — mas é escopo de projeto de engenharia real, não um documento de instrução.

**Distinção de custo que organiza todo o plano:** a parte mecânica (parser de plano, máquina de estados, ciclo de vida de worktree, integração com os gates já existentes) é 100% determinística e testável com **zero custo de LLM**. A parte que dispara agentes reais (`agent_spawner` de fato invocando `agy`/`mimo`/`claude`/`opencode`) gasta chamadas reais de LLM em paralelo em até 4 ferramentas — isso exige a mesma trava já usada no Protocolo Delegado do `aidd-generator`: **núcleo mecânico primeiro, teste end-to-end com agentes reais só com aprovação explícita separada, depois.**

## 2. Verificação real feita antes de travar qualquer item (achado que motivou reordenar o trabalho)

Antes de escrever a Definição de Pronto de qualquer item, os 4 binários citados no manual (`agy`, `mimo`, `claude`, `opencode`) foram confirmados como instalados nesta máquina e seus `--help` reais foram lidos (custo zero — não é chamada de LLM, só o próprio binário imprimindo sua ajuda estática). Resultado: **2 dos 4 perfis de harness do manual (`§5` do Manual Unificado) têm o campo `prompt_flag` errado** — `mimo` e `opencode` declaram `"prompt_flag": "-p"`, mas `-p` nesses dois binários significa `--password` (autenticação básica do servidor local), não o texto do prompt. O flag real e correto para os dois é `--prompt <texto>` (nível raiz do comando, aceita valor).

Tabela de correção (usada em todos os itens desta pasta, substitui o `harness_profiles.json` de exemplo do manual):

| Harness | Binário confirmado no PATH | Flag de auto-aprovação real | `prompt_flag` real | Observação |
|---|---|---|---|---|
| Antigravity | `agy` | `--dangerously-skip-permissions` (confirmado) | **não confirmado** — `--print`/`-p`/`--prompt` são flags booleanas (ativam modo não-interativo), não recebem valor; o texto do prompt provavelmente é um argumento posicional | Precisa de confirmação em runtime no Item 3 (ver regras) |
| MimoCode | `mimo` | `--dangerously-skip-permissions` (alias real: `--yolo`) | `--prompt <texto>` (top-level, confirmado no `--help`) | Manual errado (`-p`) — corrigido aqui |
| Claude Code | `claude` | `--dangerously-skip-permissions` (também existe `--allow-dangerously-skip-permissions`, mais restrito) | `-p`/`--print` é boolean; o texto do prompt é argumento posicional (`claude [options] [command] [prompt]`) | Nome do flag do manual está certo, mas o mecanismo (posicional, não valor de flag) precisa ser tratado corretamente no `agent_spawner` |
| OpenCode | `opencode` | `--auto` (confirmado, alias equivalente ao `--dangerously-skip-permissions` de mimo) | `--prompt <texto>` (top-level, confirmado no `--help`) | Manual errado (`-p`) — corrigido aqui |

**Nenhuma chamada real de LLM foi feita para produzir esta tabela** — só leitura de `--help` estático dos binários já instalados.

## 3. Onde vive o conteúdo técnico de cada item

| # | Item | Custo real de LLM | Documento |
|---|---|---|---|
| 1 | Núcleo mecânico: `plan_parser.py` + `state_engine.py` + `worktree_engine.py` | Zero | `01-nucleo-mecanico-parser.md` |
| 2 | `gate_auditor.py` integrado ao `ecossistema.py audit` já existente | Zero | `02-gate-auditor-integracao.md` |
| 3 | `harness_profiles.json` (corrigido) + `agent_spawner.py` (compilação de comando, sem disparar LLM real ainda) | Zero (só compila string de comando, não executa) | `03-harness-profiles-agent.md` |
| 4 | Hooks pre/post + circuit breaker/heartbeat/timeout | Zero | `04-hooks-circuit-breaker.md` |
| 5 | CLI `ecossistema.py orchestrate` + Plano de Voo (`--dry-run`/`--resume`/`--yes`) | Zero (`--dry-run` nunca invoca agente real) | `05-cli-orchestrate-plano.md` |
| 6 | Validação end-to-end com agentes reais | **Real e não-trivial** (até 4 CLIs em paralelo) | `06-validacao-end-to.md` (gate de aprovação, sem Definição de Pronto travada ainda) |

## 4. Regras fixas que valem para todos os itens

1. **Itens 1-5 nunca invocam um agente real de LLM.** Todo teste desses itens roda com binários mockados/fake (scripts de teste que simulam `agy`/`mimo`/`claude`/`opencode` sem gastar tokens) ou, quando testar o binário real fizer sentido, só até o ponto de gerar o comando final (string), nunca executá-lo de fato.
2. **Item 6 não começa sem aprovação explícita e separada do usuário**, informando antes: quais harnesses serão realmente invocados, com qual prompt, e uma estimativa honesta de custo — mesma trava do Protocolo Delegado do `aidd-generator`. Por isso o documento do Item 6 nesta pasta não tem Definição de Pronto travada ainda — só o registro da trava e o que precisa ser decidido quando chegar a vez.
3. **Nunca testar contra o repositório real como alvo de escrita.** Testes de `worktree_engine` criam e destroem worktrees em um repositório git temporário isolado (nunca `git worktree add` dentro do próprio `ecossistema-aidd` como cobaia), pela mesma razão que gates/scripts de teste do próprio ecossistema já isolam em `tmp_path`/diretório temporário.
4. **Reprodução real, nunca simulada.** Nenhum item é considerado concluído sem comando rodado de verdade, exit code real, saída real citada — mesma regra de todas as iniciativas anteriores desta pasta.
5. **Sem git commit/push** feito pelos scripts desta skill em nenhum repositório, exceto o que o próprio `worktree_engine` precisa fazer dentro de worktrees efêmeras de teste (sempre em repositório git temporário isolado, nunca no real).
6. **Cada Prompt de Execução gerado passa pela checagem de cercas de código aninhadas** (```` ```  ````contadas, pares isolados) antes de ser considerado pronto.

## 5. Registro de progresso

| # | Item | Status | Documento |
|---|---|---|---|
| 1 | Núcleo mecânico (parser/state/worktree) | ✅ Concluído (Auditado) | `01-nucleo-mecanico-parser.md` |
| 2 | Gate auditor integrado | ✅ Concluído (Auditado) | `02-gate-auditor-integracao.md` |
| 3 | Harness profiles + agent spawner (sem disparo real) | ✅ Concluído (Auditado) | `03-harness-profiles-agent.md` |
| 4 | Hooks + circuit breaker | ✅ Concluído (Auditado) | `04-hooks-circuit-breaker.md` |
| 5 | CLI orchestrate + Plano de Voo | ✅ Concluído (Auditado) | `05-cli-orchestrate-plano.md` |
| 6 | Validação end-to-end com agentes reais | ✅ Concluído (Auditado E2E com Stub / Zero Token) | `06-validacao-end-to.md` |




Esta tabela é atualizada para ✅ Concluído só depois que o resultado real de cada item existir, auditado por reprodução.

