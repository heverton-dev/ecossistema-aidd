# Diagnóstico — modularizacao-vsa ciclo-03

> Auditoria por reprodução real (comandos e exit codes medidos) em 06/10/2026, sobre `main` em `232cac4`.
> Escopo: `docs/auditoria/modularizacao-vsa/ciclo-01`, `docs/auditoria/vsa-migration` (ciclo-02, 7 salvaguardas), `docs/auditoria/fronteiras-ferramentas/ciclo-01` e `docs/padroes/ARQUITETURA-MODULARIZACAO-VSA-ECOSSISTEMA.md`.

## Decisões do usuário (06/10/2026)

| # | Decisão |
|---|---|
| A | `modulos/` é a cópia canônica. O que só existe em `tools/` é juntado em `modulos/` (prova: zero órfão) e `tools/` é removido. |
| B | Lei #2 mantida: todo gate sai só com 0 ou 1. A escala 0–5 de `scripts/exit_codes.py` vale apenas para scripts e CLIs (orquestradores, micro-gates, self-healing). |
| C | Cada gate mora na fatia dona, sem cópia. Gates transversais vão para `modulos/04-nucleo-compartilhado/gates/`. A pasta `gates/` da raiz deixa de existir. Revisa a decisão D2 de fronteiras-ferramentas ciclo-01. |

## Achados

### 1. Migração VSA foi cópia, não mudança (padrão §3, salvaguarda 5)
- Commits `21847f3`, `854a844`, `44d7bad`, `3622981`: só arquivos adicionados (A), zero removidos.
- `tools/` mantém ~1.860 arquivos versionados; `modulos/` tem a segunda cópia.
- Divergências (ignorando cache): pure 6, open 6, master 9, enterprise 17, ops 6, freedom 1, forge 0. `aidd-planner` não foi migrado.
- `scripts/contar_duplicatas.py`: 1.450 pares duplicados (base fronteiras: 727) e 106 cópias de gate.
- 83 arquivos `.py` fora de `tools/` e `modulos/` ainda apontam para `tools/`. O pacote editável `aidd_forge` aponta para `tools/aidd-forge` e falha no import a partir da raiz (testes do forge com exit 4).
- `ecossistema.py` usa `modulos/` se existir, senão `tools/`; o resto do ecossistema usa `tools/`.

### 2. Gates duplicados e nunca executados nas fatias
- 69 gates em `modulos/*/gates` idênticos aos de `gates/` (diferença só de CRLF no disco); `G_PORTAO_PROVA_QUE_MORDE` diverge de verdade.
- `.pre-commit-config.yaml` tem 0 referências a `modulos/`.

### 3. Gates de fronteira cegos (salvaguarda 4, DoD 4)
- `G_AST_BOUNDED_CONTEXT` e `G_modularizacao_vsa` só procuram `import tools.`/`modulos.`. Pastas com hífen não são importáveis como pacote, então nunca acham nada; o acoplamento real é por `sys.path` (221 arquivos em `modulos/`).
- 0 arquivos `interface.py`/`public.py`. `G_MODULO_FRONTEIRA` do padrão não existe. Nenhum dos dois gates está no pre-commit.
- Colisão real: `tests/test_fronteira_factory.py` do open importa `core` e recebe o pacote `core` do pure.

### 4. Stubs e scripts órfãos (ciclo-01)
- `modularizacao-vsa inspect|verify|status`: texto fixo + exit 0; `status` afirma "4 macro-módulos íntegros" sem checar. `RELATORIO-CONSTRUTOR.md` declara "Zero Stubs".
- Sem consumidor fora do próprio teste: `isolamento_vsa`, `analisador_acoplamento_vsa`, `resiliencia_vsa`, `observabilidade_vsa`, `rollback_vsa`, `handoff_vsa`, `manifesto_modulos`.

### 5. Exit codes (salvaguarda 1)
- 0 de 71 gates usam `scripts/exit_codes.py`; a convenção contradiz `G_SAIDA_BINARIA` (Lei #2). Resolvido pela decisão B.

### 6. Micro-gates (salvaguarda 3)
- Os 3 comandos `pytest modulos/0N-... -q --maxfail=1` saem com exit 1 na coleta: `sandbox-forge-teste`, `materiais-extras/examples` e a colisão `core`.
- Mudança em `tools/` dispara teste da cópia em `modulos/`.

### 7. Contexto (salvaguardas 6 e 7, padrão §4)
- Subgrafos: 9 projetos `vsa-*` indexados; nomes diferentes do padrão; grafo global mantido; ~15 grafos órfãos de worktrees.
- `lazy_skills_scope.py` só é usado por `micro_gates.py`; `components sync` não lê skills das fatias; 4 skills em `modulos/**/skills` são cópias de `componentes/compartilhado/skills`.
- `AGENTS.md` local: 1 de 7 fatias. `mcps/` por módulo: nenhum.
- Pastas casca (só `__init__.py`): `04/cli`, `04/sync`, `04/contracts`, `04/scripts`, `03/quarteto-studios`, `03/contracts`.

### 8. Lixo versionado e fronteira do almoxarifado
- Em `modulos/`: `sandbox-forge-teste` (64), `secoes/`, `_destino_teste_almoxarifado` (teste escreveu dentro de `modulos/`: a guarda de `almoxarifado.py` só protege `tools/`).
- `materiais-extras` (D4 de fronteiras: sair do repo) segue em `tools/` (635) e foi copiado para `modulos/` (630).

### 9. Fronteiras-ferramentas ciclo-01
- 100%: testes dos tickets 1–8, 11–18, 22 e 23 com exit 0; tag `pre-fronteiras-ciclo-01` existe.
- Parcial: T9/T10 (testes do forge só rodam de dentro da pasta); T19 (só olha `tools/`); T20 (modo bloqueio, mas 100 violações perdoadas na allowlist); T21 (comparação de 04/10, antes da VSA; 3 fluxos com exit 1 e Quarteto 0/4; pasta `TESTES_E2E-ecossistema-aidd` não existe mais).

### 10. Bateria
- `python ecossistema.py audit`: exit 1, 62 aprovados e 1 reprovado (`G_SEGREDOS`, hook regrava `.secrets.baseline` → "files were modified"), 1.360 s no total (`G_SEGREDOS` 8 min, `G_TESTES_REAIS` 12 min).
