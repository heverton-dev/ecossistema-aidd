# aidd-forge

Injeta em qualquer projeto a infraestrutura AIDD: regras de IDE por harness, subagentes efêmeros, gates determinísticos e o almoxarifado de peças canônicas verificadas por SHA-256.

## Uso rápido

```bash
python ecossistema.py forge init <pasta>
```

- Guia completo (instalação, arquitetura, testes): [GUIA.md](GUIA.md)
- Regras e invariantes para agentes: [AGENTS.md](AGENTS.md)

## Fronteiras Canônicas e Responsabilidades

Conforme o mapa oficial de arquitetura (`MAPA-DONOS-FERRAMENTAS.json` e `G_FRONTEIRA_FERRAMENTAS.py`):

- **Responsabilidades:**
  - `preparo_terreno_e_prontidao_projeto`
  - `guarda_e_distribuicao_almoxarifado_pecas`
  - `instalacao_e_auditoria_leis_guardas`
  - `governanca_harnesses_e_regras_globais`
- **Pode guardar peças do catálogo:** Sim (`pode_guardar_pecas: true`) — único dono legítimo do almoxarifado no ecossistema.
- **Dono do conteúdo de:** `gates_projeto`, `catalogo_almoxarifado`, `regras_harness`, `governance_kit`.
- **Pode conter:** `src/**`, `scripts/**`, `schemas/**`, `tests/**`, `templates/**`, `gates/**`, `almoxarifado/**`.
- **Nunca conter (violações de fronteira):**
  - `**/vsa_generator*`
  - `**/dispatch_pipeline*`
  - `**/docker-compose*`
- **Zona de escrita no projeto:** `.git/hooks/**`, `gates/**`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.aidd/**`, `.aidd/HANDOFF_FORGE_PLANNER.json`.

---
