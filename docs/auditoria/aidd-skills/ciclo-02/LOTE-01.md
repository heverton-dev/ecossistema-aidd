# Lote 01 — Construção (aidd-skills ciclo-02)

> **Data:** 03/10/2026. **Skills:** aidd-forge, aidd-planner, aidd-pure, aidd-open, aidd-freedom, aidd-master, aidd-enterprise.
> **O que mudou:** cada `SKILL.md` ganhou, no fim, `## Negative Guardrails`, `## Failure Modes & Fallback` e `## Stopping Checklist`. Frontmatter e o resto do corpo ficaram iguais (o diff só tem adições: 158 linhas a mais e 0 removidas).

## 1. Seções por skill

| Skill | Linhas | Negative Guardrails (o que cita) | Failure Modes & Fallback (o que cita) | Stopping Checklist (prova) |
|---|---|---|---|---|
| aidd-forge | 46 | `forge init` sem `[path]`; `--force`; `handoff-forge.json` + `forge handoff emit` (caso 4db900a); `.FORGE-ROLLBACK-JOURNAL.json` + `scripts/rollback.py`; `--no-verify`; rota `.agents/skills/aidd-forge/scripts/cli.py` versus `python -m aidd_forge.cli` | crash no meio → `rollback.py <path>`; `forge handoff verify` com hash divergente; `gates/G_aidd_forge.py --alvo` reprovado → `forge audit` + `forge conform --dry-run`; falha do auto-reparo `pip -e` | `forge init` rc 0; `G_aidd_forge.py --alvo` rc 0; `forge handoff verify` rc 0; sem journal pendente; `git -C <path> status --short` |
| aidd-planner | 63 | `PLANNER.json` em `docs/planos/` (fronteira com aidd-plan); `--dominio`/`--slug` omitidos viram `logistica`; `--force`; `HANDOFF_PLANNER_ENGINE.json` (C2) + `handoff-planner-to-engine.schema.json`; `planner_schema.json`; stubs × `G_PLANNER_SINE_QUA_NON.py` | `planner init` "já existe"; `planner validate` exit 1 (3 rodadas e para); "A planta nao pode ser desenhada" → C1 `.aidd/HANDOFF_FORGE_PLANNER.json` via `forge init`; Quarteto ausente no `planner audit` | `planner validate` rc 0; `G_PLANNER_SCHEMA.py`, `G_PLANNER_SINE_QUA_NON.py` e `G_PLANNER_COERENCIA_FLUXO.py` rc 0; C2 + `DESIGN-SYSTEM.json` existem |
| aidd-pure | 77 | chave de API/`AIDD_MODO=headless` (o harness responde `.aidd/cache/_llm_request_<id>.json`); `--dry-run` não confere C1-C5; teste vermelho→verde na fase 8 (`--implementar-codigo`); `--pasta` em projeto existente (`git init` + `forge init --force`); `HANDOFF_*.json` escritos à mão | "não gravou HANDOFF…: o bastão não passa"; fase esperando `_llm_request` → escrever `_llm_response` + `pure-motor --resume`; `pure-motor` sem `--pasta`; `tools/aidd-pure/scripts/preflight_llm.py` "PRÉ-VOO FALHOU" | `pure` rc 0; `contratos_lidos` C1-C5 no `ORQUESTRACAO_EXECUCAO.json`; `G_QUARTETO_SINE_QUA_NON.py --target` rc 0 + frontend Next.js; `pytest <dest>` rc 0 após vermelho; nenhuma chave adicionada |
| aidd-open | 78 | chave de API (usar `--sem-llm`); `open-motor` sem `PLANO-INFRAESTRUTURA.json` do aidd-ops; `--dry-run`; segredos reais nos `.env`/compose gerados; `/open` no Antigravity (`agy`); `FACTORY_OUTPUT.json` com `resumo.erros` > 0 | "não gravou HANDOFF_ENGINE_MASTER.json" → `open-motor` isolado; fase esperando o modelo → protocolo delegado ou `--sem-llm`; motor open-source sem imagem/licença testada → perguntar ao usuário | `open` rc 0; `resumo.erros` = 0; `docker compose ... config` rc 0; `G_QUARTETO_SINE_QUA_NON.py --target` rc 0 (rotas no gateway FastAPI) |
| aidd-freedom | 80 | `convert-db` grava `init-db.sql` dentro do export sem `--output`; `freedom-motor destroy`/`--yes` (stack, volumes, DNS Cloudflare, pasta na VPS); `migrate-auth --apply` sem prévia; mexer na UI exportada; senha fixa no `init-db.sql` (achado do `G_SEGREDOS`) | `scan` com 0 migrations Supabase; teste da fatia `src/modules/<dominio>/` falhando; `destroy` "ERRO VPS" → parar; `merge` com mais de 4 apps ou rotas em conflito | `freedom` rc 0; `git -C <export> status --short` vazio; `git grep @supabase/supabase-js` rc 1; `G_QUARTETO_SINE_QUA_NON.py --target` rc 0 com UI intacta |
| aidd-master | 41 | `add-module` em módulo existente (`overwrite_if_exists=True`); sem `--dir` grava no próprio ecossistema; subcomando digitado errado vira intenção em linguagem natural (`tools/aidd-master/scripts/aidd.py`); import entre fatias; contrato sem vermelho→verde | `master test contracts` falhando → corrigir `services.py` / `refine-module`; `refine-module` sem `features/<module>.feature`; fatia em frontend exportado → `attach-vsa` | pasta do módulo não existia antes; `add-module --dir` rc 0; `master test contracts` rc 0 após vermelho; `master integrate` rc 0 + C4 `HANDOFF_MASTER_ENTERPRISE.json` |
| aidd-enterprise | 44 | `enterprise inject` sem `--dir` e sem `--dry-run` (grava no repo atual, achado das baterias AIDD-Ops); `--remover` sem OK; `.ENTERPRISE-SNAPSHOT/` e `.ENTERPRISE-ROLLBACK-JOURNAL.json` + `scripts/rollback.py`; reescrever hash no `CAPABILITIES.json`; subcomando errado vira injeção por linguagem natural; tokens reais em `--mcp-env` | falha no meio → `rollback.py <target>` "workspace limpo"; `verificar-drift` divergente → perguntar ao usuário; `gates/G_aidd_enterprise.py --manifest` exit 1 | `inject --dry-run` rc 0; `inject` rc 0; `verificar-drift` rc 0; sem journal pendente |

Todo item de checklist manda gravar a saída em arquivo e ler o `$?` na mesma linha (`> x.log 2>&1; echo $? > x.rc`), nunca por pipe.

## 2. Verificação (exit code real, lido de arquivo)

| Comando | Exit |
|---|---|
| `python ecossistema.py components sync --tipo skill` | 0 |
| `python gates/G_SKILL_FORMATO.py --secoes-estritas --apenas aidd-forge,aidd-planner,aidd-pure,aidd-open,aidd-freedom,aidd-master,aidd-enterprise` | 0 |
| Controle negativo: o mesmo gate com `--apenas aidd-ops` (lote ainda não feito) | 1 (`SEM_SECOES_DE_ROBUSTEZ`) |
| `python gates/G_SKILL_ROT.py` (276 referências, 0 falhas) | 0 |
| `python ecossistema.py components verify --tipo skill` | 0 |
| `python gates/G_HARNESS_COMPAT.py` | 0 |
| Varredura de itens idênticos entre as seções de todas as skills (DoD item 2) | 0 duplicados |

Não rodados, por regra da fase: `python ecossistema.py audit` e `scripts/e2e_foto.py` (ficam com o orquestrador).

## 3. Achados no código, fora do escopo deste lote

1. **`pure-motor` exige `--pasta`**: `tools/aidd-pure/scripts/pipeline_completo.py` declara `--pasta` como obrigatório, mas o exemplo do corpo da skill (`python ecossistema.py pure-motor "<idea>"`) não passa a opção. O corpo não foi alterado (regra do lote); o Failure Mode registra a recuperação.
2. **`master add-module` sobrescreve fatia existente** (`overwrite_if_exists=True` em `tools/aidd-master/scripts/add_module.py`), sem aviso.
3. **Subcomando desconhecido não falha** em `tools/aidd-master/scripts/aidd.py` e `tools/aidd-enterprise/scripts/aidd.py`: vira interpretação em linguagem natural (e até injeção).
4. **`freedom-motor convert-db`** grava `init-db.sql` dentro da pasta do export quando não há `--output`.
5. Os 7 `SKILL.md` estavam com CRLF na cópia de trabalho, mas o repositório declara `eol=lf`; foram normalizados para LF (o diff só tem adições).
