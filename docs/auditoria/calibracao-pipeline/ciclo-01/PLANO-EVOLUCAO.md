# PLANO-EVOLUCAO — Calibração do Pipeline (ciclo-01)

> **Iniciativa:** Calibrar o ecossistema no modelo de pipeline com contratos selados, barreira de sincronização, gates shift-left e comando canônico.
> **Sessão de Referência:** 5385ba52-35dc-4925-9489-f3d6d41457c2
> **Data:** 2026-10-04
> **Nota Atual:** 5/10 — Schemas JSON existem mas sem SHA-256 de payload, sem Pydantic no core, sem micro-gates de worktree, sem barreira explícita no dispatcher.
> **Nota Alvo:** 9/10

---

## Fase 1 — Contratos e Validação Formal de Handoff (Schemas SHA-256)

### Ticket 1: Adicionar campo `payload_sha256` nos 3 schemas centrais
- **Arquivos alvo:**
  - `componentes/compartilhado/specs/vsa-topological-dispatch.schema.json`
  - `componentes/compartilhado/specs/handoff-execucao.schema.json`
  - `tools/aidd-planner/schemas/planner_schema.json`
- **O que fazer:** Adicionar propriedade `payload_sha256` (string, pattern hex 64 chars) como `required` em cada schema. Bump de `versao_schema` para `1.1.0`.
- **Comando de validação:** `python -c "import json, jsonschema; s=json.load(open('componentes/compartilhado/specs/vsa-topological-dispatch.schema.json')); assert 'payload_sha256' in s['properties']"`

### Ticket 2: Criar módulo `contratos/validador_sha256.py`
- **Arquivos alvo:**
  - `contratos/validador_sha256.py`
  - `contratos/__init__.py`
  - `contratos/tests/test_validador_sha256.py`
- **O que fazer:** Módulo com funções `calcular_sha256_payload(data: dict) -> str` e `validar_integridade_contrato(path: Path, expected_hash: str) -> bool`. Gera o hash do JSON canonicalizado (json.dumps sort_keys=True, separators). Testes com 3 casos: payload válido, payload adulterado, arquivo inexistente.
- **Comando de validação:** `python -m pytest contratos/tests/test_validador_sha256.py -v --tb=short`

### Ticket 3: Integrar validação SHA-256 no dispatch_pipeline.py e planner CLI
- **Arquivos alvo:**
  - `tools/aidd-master/scripts/dispatch_pipeline.py` (método `validate_and_load_manifest`)
  - `tools/aidd-planner/src/cli.py` (comando `export`)
- **O que fazer:** No planner `export`, calcular e gravar `payload_sha256` no JSON emitido. No dispatch, validar hash antes de executar qualquer fatia. Rejeitar com exit 1 se hash inválido.
- **Comando de validação:** `python -m pytest tools/aidd-master/tests/unit/test_dispatch_pipeline.py tools/aidd-planner/tests/test_planner.py -v --tb=short`

---

## Fase 2 — Barreira de Sincronização e Rebase no Dispatcher

### Ticket 4: Implementar `--barrier-sync` no dispatch_pipeline.py
- **Arquivos alvo:**
  - `tools/aidd-master/scripts/dispatch_pipeline.py` (classe `VSADispatchPipeline`)
- **O que fazer:** Adicionar flag `--barrier-sync` no argparser e lógica na classe. Quando ativo: após validar cada nível topológico, executa `git rebase --onto` da branch base em cada worktree antes do merge. Se rebase falhar, aborta e faz rollback (`git rebase --abort` + cleanup da worktree).
- **Comando de validação:** `python -m pytest tools/aidd-master/tests/unit/test_dispatch_pipeline.py -v --tb=short -k barrier`

### Ticket 5: Rollback automático de worktree em conflito de merge
- **Arquivos alvo:**
  - `tools/aidd-master/scripts/dispatch_pipeline.py` (método `_merge_slice_branch`)
  - `tools/aidd-master/tests/unit/test_dispatch_pipeline.py`
- **O que fazer:** Quando `git merge --no-ff` falha (já faz `--abort`), registrar a fatia em lista `fatias_rollback` e emitir relatório JSON `dispatch_rollback_report.json` com slice_id, branch, motivo e timestamp. Adicionar teste unitário que simula conflito.
- **Comando de validação:** `python -m pytest tools/aidd-master/tests/unit/test_dispatch_pipeline.py -v --tb=short -k rollback`

### Ticket 6: Expor `--barrier-sync` no ecossistema.py
- **Arquivos alvo:**
  - `ecossistema.py` (função `cmd_orchestrate` e/ou seção dispatch)
- **O que fazer:** Propagar flag `--barrier-sync` da CLI raiz para o dispatch_pipeline. Default: ativo.
- **Comando de validação:** `python ecossistema.py --help | findstr barrier`

---

## Fase 3 — Estruturação dos Gates em 2 Níveis (Shift-Left)

### Ticket 7: Criar suíte de Micro-Gates de Worktree
- **Arquivos alvo:**
  - `gates/micro_gates_worktree.py`
  - `gates/tests/test_micro_gates_worktree.py`
- **O que fazer:** Script que executa sequencialmente: (1) `python -m py_compile` nos .py da fatia, (2) G_SEGREDOS apenas nos arquivos da fatia, (3) testes unitários da fatia (`pytest` com path filter), (4) ruff/flake8 lint nos arquivos da fatia. Recebe `--worktree-path` e `--slice-id`. Exit 0 = tudo ok, exit 1 = bloqueio.
- **Comando de validação:** `python -m pytest gates/tests/test_micro_gates_worktree.py -v --tb=short`

### Ticket 8: Integrar micro-gates no fechamento de worktree do dispatcher
- **Arquivos alvo:**
  - `tools/aidd-master/scripts/dispatch_pipeline.py` (método `_run_slice_validation`)
  - `tools/aidd-master/scripts/vsa_join_barrier.py` (função `executar_barreira_fatia`)
- **O que fazer:** Antes dos `comandos_teste` do contrato, executar `gates/micro_gates_worktree.py --worktree-path <path> --slice-id <id>`. Se micro-gate reprovar, a fatia é reprovada sem rodar os gates seguintes.
- **Comando de validação:** `python -m pytest tools/aidd-master/tests/unit/test_dispatch_pipeline.py tools/aidd-master/tests/unit/test_vsa_join_barrier.py -v --tb=short`

### Ticket 9: Documentar a separação Micro-Gates vs Macro-Gates
- **Arquivos alvo:**
  - `docs/auditoria/calibracao-pipeline/ciclo-01/GATES-2-NIVEIS.md`
- **O que fazer:** Documento explicando a pirâmide: Micro-Gates (worktree, shift-left, rápidos, por fatia) vs Macro-Gates (54 gates globais, pós-merge, via `python ecossistema.py audit`). Tabela com nome de cada micro-gate, o que valida e tempo estimado.
- **Comando de validação:** `python -c "from pathlib import Path; p=Path('docs/auditoria/calibracao-pipeline/ciclo-01/GATES-2-NIVEIS.md'); assert p.exists() and len(p.read_text(encoding='utf-8'))>500"`

---

## Fase 4 — Atualização do Comando Canônico e Documentação

### Ticket 10: Refatorar `run-fluxo` com encadeamento canônico
- **Arquivos alvo:**
  - `ecossistema.py` (novo comando `run-fluxo` ou refatoração do `cmd_orchestrate`)
- **O que fazer:** Criar/refatorar comando que siga rigorosamente: `[FORGE validate]` → `[PLANNER export]` → `[MASTER compile]` → `[DISPATCH (Worktrees + Micro-gates)]` → `[BARREIRA --barrier-sync]` → `[ENTERPRISE seal]` → `[OPS deploy-check]` → `[54 GATES audit]` → `[COMMIT]`. Cada etapa só executa se a anterior retornou exit 0. Flag `--dry-run` simula tudo.
- **Comando de validação:** `python ecossistema.py run-fluxo --help`

### Ticket 11: Atualizar AGENTS.md com o diagrama do novo pipeline
- **Arquivos alvo:**
  - `AGENTS.md`
- **O que fazer:** Adicionar seção `§ Pipeline Canônico Calibrado` com diagrama ASCII do encadeamento de 9 etapas, referência aos micro-gates/macro-gates e menção ao SHA-256 de contratos.
- **Comando de validação:** `python -c "t=open('AGENTS.md',encoding='utf-8').read(); assert 'Pipeline Canônico Calibrado' in t and 'SHA-256' in t"`

### Ticket 12: Atualizar templates de skills com referência ao pipeline calibrado
- **Arquivos alvo:**
  - `componentes/compartilhado/skills/aidd-evolution/SKILL.md`
  - `componentes/compartilhado/skills/aidd-pipeline/SKILL.md` (criar se não existir)
- **O que fazer:** Referenciar o encadeamento canônico, micro-gates e barreira de sincronização nas instruções da skill. Incluir exemplo de uso: `/evolucao calibracao-pipeline`.
- **Comando de validação:** `python -c "from pathlib import Path; assert Path('componentes/compartilhado/skills/aidd-evolution/SKILL.md').exists()"`
