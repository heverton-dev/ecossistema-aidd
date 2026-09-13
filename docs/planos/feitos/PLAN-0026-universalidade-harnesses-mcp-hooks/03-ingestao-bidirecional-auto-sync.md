# 03 — Ingestão Reativa e Reverse-Sync

> **Iniciativa:** PLAN-0026-universalidade-harnesses-mcp-hooks
> **Foco:** Permitir que skills e MCPs adicionados isoladamente em qualquer harness sejam ingeridos para a fonte canônica e replicados a todos.

---

## 1. Diagnóstico e Problema

Se o usuário ou um instalador de terceiros injeta uma skill em `.claude/skills/nova-skill` ou `.agents/skills/outra-skill`, ela permanece isolada. A Regra de Ouro do Ecossistema exige que a disponibilização seja universal e automática.

## 2. Definição de Pronto

1. Atualizar `scripts/gestor_componentes.py` para incluir o comando `--reverse` ou `--ingest`.
2. O algoritmo:
   - Examina todos os diretórios de harnesses conhecidos (`.claude`, `.agents`, `.cursor`, `.opencode`, `.gemini`, `.mimocode`, `.codebuddy`).
   - Identifica skills presentes nos harnesses mas ausentes em `componentes/compartilhado/skills/`.
   - Copia o componente para `componentes/compartilhado/skills/` (fonte canônica).
   - Em seguida, dispara o sync determinístico para todos os outros destinos.
3. Integrar no bootstrap do ecossistema (`python ecossistema.py dependencia bootstrap` / `python ecossistema.py components sync --auto-ingest`).
