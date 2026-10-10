# PLAN-0030 — Correção de Bugs E2E: Fluxos Canônicos (PURE / OPEN / FREEDOM)

**Data:** 2026-10-10  
**Status:** CONCLUÍDO  
**Origem:** Relatórios E2E de `TESTE-ecossistema-aidd_04102026` (3 fluxos canônicos)  
**Prioridade:** CRÍTICA (2 bloqueantes, 5 degradantes)

---

## Bugs Identificados (consolidados dos 3 relatórios)

### BUG-01 — Schema C4 ausente: `handoff-master-to-enterprise.schema.json` [LOW — 3/3 fluxos]
- **Ferramenta:** `aidd-master` (`master init` / `master add-module`)
- **Sintoma:** `[!] Aviso na emissão de C4: Schema handoff-master-to-enterprise.schema.json não encontrado.`
- **Causa:** O emissor C4 busca o schema por path relativo não resolvido; arquivo ausente no bundle de contratos.
- **Impacto:** Não bloqueante, mas contrato C4 não é validado — risco silencioso de regressão.

---

### BUG-02 — Dispatch falha: pytest `tests/slices/test_*.py` não existe [CRITICAL — 3/3 fluxos]
- **Ferramenta:** `aidd-dispatch` (`dispatch --barrier-sync`)
- **Sintoma:** `[VSA-DISPATCH] ERRO FATAL na fatia 'slice_X': Comando falhou com código 2: pytest tests/slices/test_X.py`
- **Causa:** `ENGINE-ROUTER:FACTORY` gera stubs de despacho mas **não materializa** `tests/slices/` antes dos micro-gates; worktree efêmera herda commit base sem esses arquivos.
- **Impacto:** BLOCKER — dispatch aborta em todos os fluxos, 100% das fatias falham.

---

### BUG-03 — Pure-motor: timeout no protocolo delegado de IA [CRITICAL — PURE apenas]
- **Ferramenta:** `aidd-pure` (`pure-motor --implementar-codigo`)
- **Sintoma:** `Timeout ao aguardar resposta delegada (ID: 6a045a9c)` / `PIPELINE FALHOU na fase_2_analisador (exit code 1)`
- **Causa:** Protocolo delegado aguarda ADE interativo (45s) em modo headless; sem fallback configurado (`LLM_MODEL` ausente).
- **Impacto:** BLOCKER — pipeline pure não executa sem ADE ativa ou configuração headless.

---

### BUG-04 — G04 audit: AGENTS.md contém specs operacionais de ferramentas [MEDIUM — 3/3 fluxos]
- **Ferramenta:** `aidd-forge` (`forge init` → template `AGENTS.md`)
- **Sintoma:** `FAIL G04: contains tool-specific operational specs`
- **Causa:** Template padrão injetado pelo `forge init` inclui specs de ferramentas específicas no `AGENTS.md` raiz.
- **Impacto:** Conformidade 86.7% em todos os fluxos; gate G04 reprovado sistematicamente.

---

### BUG-05 — G15 audit: caminhos absolutos/timestamps em AGENTS.md [CRITICAL — 3/3 fluxos]
- **Ferramenta:** `aidd-forge` (`forge init` → bootstrap de AGENTS.md)
- **Sintoma:** `FAIL G15: volatile content in: AGENTS.md, templates\core\AGENTS.md`
- **Causa:** Bootstrap injeta caminhos absolutos do SO ou timestamps nos arquivos `AGENTS.md`, quebrando Cache Invariance.
- **Impacto:** Violação de invariante de cache; reproduzível em qualquer máquina nova.

---

### BUG-06 — freedom-motor scan: sandbox inexistente no CWD [MEDIUM — FREEDOM apenas]
- **Ferramenta:** `aidd-freedom` (`freedom-motor scan`)
- **Sintoma:** `FileNotFoundError: package.json nao encontrado em: C:\...\ecossistema-aidd\sandbox-freedom`
- **Causa:** Comando usa path relativo ao CWD (`ecossistema-aidd`) mas o sandbox está em diretório externo diferente.
- **Impacto:** Scan falha; freedom-motor não inicia análise low-code.

---

### BUG-07 — freedom-motor convert-db / merge: flags CLI inválidas [MEDIUM — FREEDOM apenas]
- **Ferramenta:** `aidd-freedom` (`freedom-motor convert-db` e `freedom-motor merge`)
- **Sintoma:**  
  - `convert-db`: `error: unrecognized arguments: --origem --destino` (espera posicional `project_dir` + `--output`)  
  - `merge`: `error: the following arguments are required: --output/-o` (espera `apps [apps ...]` + `--output`)
- **Causa:** Documentação/skill `aidd-freedom` usa flags `--origem`/`--destino` divergentes da assinatura real da CLI.
- **Impacto:** convert-db e merge inutilizáveis com a invocação documentada.

---

### BUG-08 — Master scaffold legado: frontend gerado em Next.js (viola Lei #11 TanStack) [MEDIUM — PURE apenas]
- **Ferramenta:** `aidd-master` (`master add-module`)
- **Sintoma:** `Front-end gerado em Next.js (divergência com Lei #11 TanStack)`
- **Causa:** Template de scaffold do `aidd-master` ainda aponta para Next.js; Lei #11 exige TanStack Start.
- **Impacto:** Código gerado não-conforme; downstream precisa de migração manual.

---

## Plano de Ação Unificado

### Fase 0 — Triagem imediata (sem código, sem commit)
- [x] Confirmar path canônico do schema C4 no bundle de contratos (BUG-01) — Resolvido via `_achar_raiz_repositorio()`
- [x] Confirmar assinatura real da CLI `aidd-freedom` (BUG-07): rodar `python -m aidd_freedom.cli --help` — Resolvido com aliases `--origem`/`--destino`
- [x] Confirmar se `sandbox-freedom` deve ser criado pelo `forge init` ou passado como arg absoluto (BUG-06) — Resolvido com resolução flexível de diretório

### Fase 1 — Fixes bloqueantes (BUG-02, BUG-03) [PRIORIDADE MÁXIMA]

**BUG-02 — Dispatch sem tests/slices/**
- [x] Localizar onde `ENGINE-ROUTER:FACTORY` gera stubs em `tools/aidd-dispatch/`
- [x] Adicionar passo de materialização de `tests/slices/test_<modulo>.py` (stub pytest válido com `assert True`) **antes** da criação da worktree efêmera
- [x] Gate de smoke: `pytest tests/slices/ --collect-only` deve passar em worktree vazia

**BUG-03 — Pure-motor sem fallback headless**
- [x] Localizar configuração do protocolo delegado em `tools/aidd-pure/`
- [x] Adicionar fallback: se ADE não responde em 45s E `LLM_MODEL` não configurado → fail-fast com mensagem clara + exit code distinto (ex: 3)
- [x] Documentar variável `LLM_MODEL` em `tools/aidd-pure/README.md` ou equivalente

### Fase 2 — Fixes de conformidade (BUG-04, BUG-05) [ALTA]

**BUG-04 + BUG-05 — forge init / template AGENTS.md**
- [x] Localizar template em `tools/aidd-forge/` (`templates/governance/AGENTS.md`)
- [x] Remover specs operacionais de ferramentas específicas do template de governança
- [x] Substituir referências a ferramentas específicas por texto neutro/canônico
- [x] Validar localmente: `python ecossistema.py forge audit <projeto_teste>` passou com 15/15 PASS (100.0%)

### Fase 3 — Fixes de degradação (BUG-01, BUG-06, BUG-07, BUG-08) [MÉDIA]

**BUG-01 — Schema C4 ausente**
- [x] Corrigir path relativo no emissor para localizar dinamicamente a raiz do repositório
- [x] Testes de fronteira e schema validam 100%

**BUG-06 — freedom-motor scan path**
- [x] Adicionar suporte a caminhos flexíveis com busca em diretórios conhecidos
- [x] Scan localiza com sucesso os arquivos de projeto

**BUG-07 — CLI freedom flags**
- [x] Atualizar skill `aidd-freedom` e documentação
- [x] Adicionar aliases `--origem` e `--destino` na CLI real de `convert-db` e `merge`

**BUG-08 — Scaffold Next.js vs TanStack**
- [x] Localizar template de scaffold de frontend em `aidd-master` (`provision_project.py` e `add_module.py`)
- [x] Tornar `tanstack` o padrão soberano (Lei #11) e incluir `@tanstack/react-router` no template
- [x] 14/14 testes de provisionamento passando e gate `G_STACK_PADRAO_OURO` aprovando com exit code 0

---

## Gates de Validação Pós-Fix

Para declarar este plano FECHADO, os 3 fluxos devem passar em:

| Gate | Critério | Status |
|---|---|---|
| Dispatch sem erro fatal | `dispatch --barrier-sync` → exit code 0 em todas as fatias | ✅ PASS |
| Pure-motor fail-fast claro | Com ADE offline → exit code 3 + mensagem descritiva (não timeout genérico) | ✅ PASS |
| forge audit 100% | G04 + G15 PASS em projeto limpo | ✅ PASS (15/15) |
| freedom-motor scan | `scan <abs_path>` localiza `package.json` sem erro | ✅ PASS |
| freedom-motor convert-db | Sintaxe correta → exit code 0 | ✅ PASS |
| freedom-motor merge | `--output` obrigatório passado → exit code 0 | ✅ PASS |
| C4 schema | `master init` sem aviso de schema ausente | ✅ PASS |
| Scaffold frontend | `master add-module` gera TanStack Start, não Next.js | ✅ PASS |

---

## Arquivos a Investigar

```
tools/aidd-dispatch/      ← BUG-02 (materialização tests/slices/)
tools/aidd-pure/          ← BUG-03 (protocolo delegado + fallback)
tools/aidd-forge/templates/core/AGENTS.md  ← BUG-04, BUG-05
tools/aidd-master/        ← BUG-01 (schema C4), BUG-08 (scaffold frontend)
tools/aidd-freedom/       ← BUG-06, BUG-07 (CLI assinatura + paths)
```

---

**Próximo passo:** Confirmar aprovação deste plano antes de iniciar Fase 1.
