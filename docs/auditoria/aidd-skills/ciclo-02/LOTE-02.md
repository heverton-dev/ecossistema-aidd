# Lote 02 — Entrega e orquestração (aidd-skills ciclo-02)

> **Data:** 03/10/2026. **Skills:** aidd-ops, aidd-orchestrate, aidd-pipeline, aidd-dispatch, aidd-handoff, aidd-orca, aidd-9router.
> **O que mudou:** cada `SKILL.md` ganhou `## Negative Guardrails`, `## Failure Modes & Fallback` e `## Stopping Checklist`. Onde a skill fecha com lista de referências, as seções entraram antes dela (`## References` em aidd-ops e aidd-orchestrate, `## Files` em aidd-orca); nas outras, no fim. Frontmatter e o resto do corpo ficaram iguais (o diff só tem adições: 170 linhas a mais e 0 removidas).

## 1. Seções por skill

| Skill | Linhas | Negative Guardrails (o que cita) | Failure Modes & Fallback (o que cita) | Stopping Checklist (prova) |
|---|---|---|---|---|
| aidd-ops | 48 | `ops bootstrap`/`ops deploy --real` antes do dry-run (`ansible/playbooks/hardening.yml` pode trancar a VPS); forma legada sem `--pasta` (`_cmd_legado`) e `ops plan` sem `--pasta` (vai para pasta temporária); editar `PLANO-INFRAESTRUTURA.json` à mão (`validar_plano_contrato`, `tools/aidd-ops/gates/G_OPS_MVP.py --dir`); `.env` puro (`ops cofre init/encrypt`, `rotate_secrets.py`); deploy com falha não desfaz nada (`rollback_recomendado`) | `etapa_com_falha` das 6 etapas do `DeployOrchestrator`; SSH recusado → `ops preflight --json` e pedir console ao usuário; `INFRA_NAO_GERADA` (planta `HANDOFF_PLANNER_ENGINE.json`); Coolify → `ops coolify health/status` | `ops plan --pasta` rc 0 + plano existe; `G_OPS_MVP.py --dir` rc 0; `--real` só após dry-run e OK; `ops preflight` rc 0; `git status --short` sem `.env`/chave age |
| aidd-orchestrate | 81 | `--ambiente`/`--harness`/`--yes` não escolhidos (sem TTY cai calado em `gitworktree`); `worktree create` do `.orca-flight-plan.json` sai com `--parent-worktree active` (`compilar_plano_orca`) e o passo 1 exige `--no-parent`; `plan iniciar-execucao` em dry-run move para `docs/planos/fazendo/`; `--dangerously-force-headless`/`--resume <session-id>` (mesa que commitou+pushou 3x pulando gate); `orca orchestration check` manual derruba a fase; integrar sem `ecossistema.py audit` na mesa ou com `--no-verify` | `terminal wait` com `satisfied: false` 2x; recibo ambíguo → `--retry-request <id>`; frente de Subagentes falhou → parar; Flight Plan editado → `--from-flight-plan` | dry-run rc 0 + `.orca-flight-plan.json`; aprovação real do usuário; nome da mesa = `rotulo`; `audit` rc 0 na mesa; `git worktree list` limpo |
| aidd-pipeline | 75 | trabalho próprio em `.worktrees/<task_id>`/`task/<task_id>` (`_create_worktree` faz `git worktree remove --force`); validação trivial/`TODO` no `handoff_evolution.json` (`G_PIPELINE_HANDOFF.py`); `--dry-run` não prova nada; merge manual de `task/*` após `git merge --abort` da barreira; `--barreira-gate` com gate inexistente (invariante 5) | manifesto rejeitado → `G_PIPELINE_HANDOFF.py --manifesto` + `run-plan --no-exec`; tarefa paralela falhou (abort total); conflito na barreira → dividir tickets; worktree órfã → `git worktree prune` | `run-plan --no-exec` rc 0; `G_PIPELINE_HANDOFF.py --manifesto` rc 0; execução real rc 0; sem `.worktrees/` nem `task/*` |
| aidd-dispatch | 60 | invariante 4 não é aplicada por código (`arquivos_permitidos` não é lido; o campo real é `arquivos_esperados`) → conferir `git diff --name-only` por `slice/<id>`; edição manual em `.worktrees/<slice_id>` (auto-commit `git add -A`; até o `--dry-run` faz `shutil.rmtree`); quebrar ciclo editando `vsa_dispatch.json`; `--dry-run` não converge; fatia importando outra/sem Quarteto | `G_DISPATCH_PIPELINE_VSA` rejeitou → `--manifesto`; compilação do `PLANNER.json` falhou (`compilar_grafo_topologico_vsa`) → `planner validate`; `ERRO FATAL na fatia`; `post_merge_suite` falhou após merge → reportar, sem reset | `G_DISPATCH_PIPELINE_VSA.py --manifesto` rc 0; `dispatch --planner` real rc 0; diff de cada fatia dentro de `arquivos_esperados`; sem `.worktrees/<slice_id>` nem `slice/*` |
| aidd-handoff | 45 | "Quality Gate State" de memória / rodar `ecossistema.py audit` dentro de fase orquestrada; `docs/secoes/*.md` está no `.gitignore` (não chega a outra worktree); "Completed Work" sem `git diff --stat` (caso do checkbox falso); aprovação inventada em "Next Actions"; confundir com `G_HANDOFF_MELHORIA.py` (aidd-improvement) e `secoes/historico_sessoes.json` (aidd-session) | outra sessão escrevendo na mesma pasta → sufixo `-2`, nunca sobrescrever; contexto pesado → montar a partir de `git log`/`git diff --stat`; gate desconhecido → "not run" | `test -f` do arquivo; `grep -c` das 5 seções = 5; cada caminho aparece no `git diff --stat`/`git log --name-only`; `grep -cE '^(def|class|import|function) '` = 0 |
| aidd-orca | 66 | apagar `.orca/.orca_state.json` em vez de `--resume`; auditor = harness da própria frente (`gate_auditor.audit_front` roda `ecossistema.py audit` quando toca `gates/`/`scripts/`); merge fora de `GATE_PASSED` ou com `--no-verify`; subir limites do `CircuitBreakerConfig` (1800 s / 300 s); `task create`/`invoke_subagent`/responder pelo usuário no `_confirm` (exit 2) | `--resume` sem estado; circuit breaker matou a frente → `.orca/memory.md` + `--resume`; frente `RUNNING` após crash (`classify_resume`) → perguntar; harness ausente → `--harness-map` | `orchestrate --dry-run` rc 0; todas as frentes `MERGED`; `pytest .../aidd-orca/tests` rc 0 se o motor mudou; `git worktree list` limpo |
| aidd-9router | 68 | usar `chamar.py`/`NINEROUTER_KEY` como LLM de pipeline do ecossistema (o modelo é o harness); vazar a chave (usar `orca_9router.py --estado`, que mascara); `ANTHROPIC_AUTH_TOKEN` no Environment do Orca; `deploy_vps.py --sobrescrever-dados` sem OK; membro de combo sem `bench.py codigo` 21/21 + `bench.py harness`, ou Groq free | `doctor.py` `FALHA crítica` → `harness_9router.py --desligar`; `chamar.py` exit 2 → dividir; `deploy_vps.py` `ERRO etapa <n>` → `docker service logs` / `docker stack rm ninerouter`; `orca_9router.py --aplicar` exit 2 → Settings > Agents > Command | `doctor.py` rc 0 + `RESULTADO: ok`; `orca_9router.py --estado` rc 0; `bench.py harness sonnet` com `code-fast`; nenhuma chave no diff |

Todo item de checklist manda gravar a saída em arquivo e ler o `$?` na mesma linha (`> x.log 2>&1; echo $? > x.rc`), nunca por pipe.

## 2. Verificação (exit code real, lido de arquivo)

| Comando | Exit |
|---|---|
| `python ecossistema.py components sync --tipo skill` | 0 |
| `python gates/G_SKILL_FORMATO.py --secoes-estritas --apenas aidd-ops,aidd-orchestrate,aidd-pipeline,aidd-dispatch,aidd-handoff,aidd-orca,aidd-9router` | 0 |
| Controle negativo: o mesmo gate com `--apenas aidd-diagnose` (lote ainda não feito) | 1 (`SEM_SECOES_DE_ROBUSTEZ`) |
| `python gates/G_SKILL_ROT.py` (314 referências, 0 falhas) | 0 |
| `python ecossistema.py components verify --tipo skill` | 0 |
| `python gates/G_HARNESS_COMPAT.py` | 0 |
| Varredura de itens idênticos entre as seções de todas as skills (DoD item 2) | 0 duplicados |
| `git diff --numstat` das 7 skills | só adições (23 a 26 por skill), 0 remoções |

Na primeira rodada o `G_SKILL_ROT` reprovou (exit 1): o guardrail do aidd-ops citava `gates/G_OPS_MVP.py`, que não existe na raiz. Corrigido para `tools/aidd-ops/gates/G_OPS_MVP.py` e a rodada inteira foi repetida.

Não rodados, por regra da fase: `python ecossistema.py audit` e `scripts/e2e_foto.py` (ficam com o orquestrador).

## 3. Achados no código, fora do escopo deste lote

1. **Fronteira de arquivos do dispatch não existe no código:** o corpo do aidd-dispatch (invariante 4) promete abortar o merge quando a fatia sai de `arquivos_permitidos`, mas nenhum `.py` do repositório lê esse campo; o manifesto usa `arquivos_esperados` e `tools/aidd-master/scripts/dispatch_pipeline.py` não compara o diff com ele.
2. **`dispatch --dry-run` apaga pasta:** `_cleanup_single_worktree` faz `shutil.rmtree` em `.worktrees/<slice_id>` mesmo no modo de simulação.
3. **Mesa ORCA solta × filha:** `orca_real_plan.compilar_plano_orca` gera `--parent-worktree active` ("nunca --no-parent, por design"), mas o passo 1 do aidd-orchestrate e `references/orca-app.md` mandam `--no-parent`. As duas fontes precisam de uma decisão do usuário.
4. **`orchestrate` sem TTY escolhe o ambiente sozinho:** sem `--ambiente`, com `--yes`/`--dry-run` ou sem terminal interativo, `cmd_orchestrate` cai em `gitworktree` sem perguntar, contra o "ask, never assume" do passo 1.
5. **`ops deploy` não faz rollback:** em falha só imprime `rollback_recomendado`; a ajuda do comando diz "com Result monad e rollback".
6. **Handoff fora do git:** `docs/secoes/*.md` está no `.gitignore`, então o artefato do aidd-handoff não chega a outra worktree nem a outra máquina.
