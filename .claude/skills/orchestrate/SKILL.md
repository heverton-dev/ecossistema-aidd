---
name: orchestrate
description: Roteador de ambiente e Plano de Voo para execução de planos ORCA — pergunta ORCA (app real), Subagentes (Agent tool desta sessão) ou Git Worktree nativo antes de tudo; cada ambiente compila um JSON no formato certo pra ele, e só depois executa.
---

# /orchestrate — Roteador de Ambiente e Plano de Voo

Contrato executável universal do slash command `/orchestrate [plano]`.

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

## Protocolo Interativo do Agente (/orchestrate)

Quando invocado:

### Passo 1: Gate de Ambiente (obrigatorio, sempre a primeira pergunta)
Pergunte explicitamente ao usuario, nunca assuma:

- **1) ORCA (aplicativo real, via orca-cli)** — worktree e terminal de verdade
  dentro do app ORCA instalado. Use quando o app esta instalado e voce quer
  acompanhar cada frente pela interface do ORCA. A mesa criada e **sempre
  filha** da mesa ativa (`--parent-worktree active` por padrao) — **nunca
  solta** (`--no-parent` nao e usado por este fluxo, salvo pedido explicito
  do usuario justificando uma tarefa 100% desacoplada).
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

- **ORCA (aplicativo real):** rode `plan iniciar-execucao` (acima). Este CLI nunca executa nada aqui — quem dirige o app ORCA de verdade é o assistente da sessão, via `orca-cli` (skill global, fora deste repo). Releia `.orca-flight-plan.json` e, para CADA frente em ordem:
  1. **Garanta o repositorio registrado** no ORCA (liste os repositorios existentes; registre este repositorio apenas se ainda não estiver lá).
  2. **Crie a mesa (worktree) da frente** usando o `branch` e o `base_branch` do JSON, **sempre com `--parent-worktree` igual ao `parent_worktree` do plano** (nunca `--no-parent` — regra fixa, mesa sempre filha, nunca solta).
  3. **Ligue o terminal da mesa** usando o `launch_command` do JSON **exatamente como está — nunca acrescente o prompt aqui**. Trate as pegadinhas de primeira execução de cada harness (ex.: prompt de confiança de pasta, diálogo de bypass de permissões) exatamente como documentado no manual de referência do `orca-cli`.
  4. **Só depois de a IA estar rodando na mesa**, envie o `prompt` do JSON como mensagem separada pro terminal daquela mesa. Se não houver atividade após o envio, mande um envio vazio de reforço (pegadinha documentada de envio incompleto).
  5. **Monitore periodicamente** (não só ao final) o painel de todas as mesas, pra detectar cedo qualquer IA travada ou esquecida.
  6. **Nunca invente aprovação intermediária** — se uma frente falhar ou travar, pare e informe o usuário antes de seguir pra próxima.
  7. **Auditoria real antes de integrar**: rode `python ecossistema.py audit` (ou `pre-commit run --all-files`) dentro da mesa — os gates são herdados do repo principal —, além de testes de verdade, `git status`/`git diff`, leitura dos arquivos modificados e execução real do app. Nunca confie só na palavra da IA da mesa.
  8. **Integração**: traga o commit aprovado daquela mesa para o branch principal (ex.: `cherry-pick` do commit), resolvendo qualquer conflito real preservando as mudanças de ambas as frentes quando fizer sentido.
  9. **Limpeza**: remova a mesa temporária depois de integrada.
  Para a sintaxe exata de cada comando (`repo add/list`, `worktree create/set/rm`, `terminal create/send/wait`, seletores `active`/`branch:`/`id:`), **sempre consulte a skill/documentação oficial do `orca-cli`** — este protocolo descreve a sequência e as regras fixas (mesa sempre filha, prompt separado do lançamento, auditoria real antes de integrar), não duplica flags que podem mudar de versão pra versão do app real.

## Quando NÃO usar esta skill

- Execução real do motor de worktrees nativo (branch/merge/gates/circuit breaker) já em andamento → isso é `orca-plan-orchestrator`, não esta.
- Gerar a estrutura do plano em si (`00-PROCESSO-E-DECISOES.md` + `NN-*.md`) → isso é `planos-auditoria-runner`.
- Operar o app ORCA fora do fluxo de um plano (worktrees avulsas, terminais soltos, etc.) → isso é a skill global `orca-cli`, não esta.
