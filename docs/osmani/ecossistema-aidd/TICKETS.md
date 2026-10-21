# TICKETS — Resolução Pós-Auditoria Osmani

### TICKET-01: Sincronização Universal do Componente `aidd-site-dominator` [CONCLUÍDO]
- **Status:** CONCLUÍDO (100% OK)
- **Ações Realizadas:**
  - Qualificação de paths dinâmicos com `<target>/` em `componentes/compartilhado/skills/aidd-site-dominator/SKILL.md`.
  - Remoção de referências a gates inexistentes fora da árvore padrão.
  - Sincronização bidirecional executada via `python ecossistema.py sync`.
- **Evidência:** `G_HARNESS_COMPAT`, `G_UNIVERSAL_HARNESS`, `G_COMPONENTE_AGNOSTICO` e `G_SKILL_ROT` (457 referências) aprovados com exit 0.

---

### TICKET-02: Normalização do Catálogo de Peças e Mapas Visuais [CONCLUÍDO]
- **Status:** CONCLUÍDO (100% OK)
- **Ações Realizadas:**
  - Registro da descrição PT-BR em `docs/mapas-visuais/moldes-nao-tecnicos/descricoes-pt.json`.
  - Regeneração do catálogo via `scripts/catalogo_pecas.py`.
  - Compilação dos 16 mapas visuais técnicos e não-técnicos via `scripts/mapa_visual.py`.
  - Emissão do manifesto canônico via `handoff.emitir_manifesto(0)`.
  - Ajuste dinâmico de `RAIZ` no gate `G_aidd_visual_maps.py` para suportar fixtures de teste isoladas.
- **Evidência:** `G_mapa_pecas` e `G_aidd_visual_maps` aprovados com exit 0; testes unitários passando 100%.

---

### TICKET-03: Resiliência de Path Windows no Linter Bash do `G_INFRA_COMPOSE` [CONCLUÍDO]
- **Status:** CONCLUÍDO (100% OK)
- **Ações Realizadas:**
  - Eliminação de interpolação direta de caminho Windows para subshell bash.
  - Envio do script via pipe binário direto (`rb`) com substituição `b'\r\n'` por `b'\n'`.
  - Normalização do arquivo físico `init-multiple-databases.sh` para terminação Unix LF.
- **Evidência:** `G_INFRA_COMPOSE` aprovado com exit 0 (9 composes Checkov + script PostgreSQL).
