# 🏭 AIDD Factory

> **Gerador de Código de Aplicação e Integração para Stacks Multi-Serviço.**

O **AIDD Factory** é a fábrica de código e templates de aplicação do ecossistema-aidd, especializada na orquestração determinística e síntese de código limpo orientada a planos de infraestrutura.

---

## 🚀 Invariantes e Diretrizes

1. **Entrada Única (G_FACTORY_INPUT):** Consome exclusivamente `PLANO-INFRAESTRUTURA.json` validado contra schema JSON.
2. **Saída Única (G_FACTORY_OUTPUT):** Produz `FACTORY_OUTPUT.json` listando artefatos e status para o orquestrador de deploy.
3. **Fases Determinísticas:** Fases 1, 4, 5 e 6 são 100% determinísticas (zero LLM). Fases 2, 3 e 7 utilizam gates AST e bandit.
4. **Zero Stubs:** Todo código gerado é funcional, sem stubs ou placeholders.

---

## 💻 Uso via CLI

```bash
# Execução via orquestrador raiz:
python ecossistema.py factory --plano PLANO-INFRAESTRUTURA.json --pasta ./saida
```

---

## Fronteiras Canônicas e Responsabilidades

Conforme o mapa oficial de arquitetura (`MAPA-DONOS-FERRAMENTAS.json` e `G_FRONTEIRA_FERRAMENTAS.py`):

- **Responsabilidades:**
  - `curadoria_motores_opensource`
  - `integracao_fatias_dominio_factory`
- **Pode guardar peças do catálogo:** Não (`pode_guardar_pecas: false`).
- **Dono do conteúdo de:** `fatias_dominio_open`, `adaptadores_motores_opensource`.
- **Pode conter:** `src/**`, `scripts/**`, `schemas/**`, `tests/**`, `templates/dominio/**`.
- **Nunca conter (violações de fronteira):**
  - `**/Dockerfile*`
  - `**/docker-compose*`
  - `**/deploy.sh`
  - `**/nginx/**`
  - `**/mcp_server*`
  - `**/webhook*`
  - `**/openapi*`
  - `**/swagger*`
  - `**/G_*.py`
  - `**/*inject*`
- **Zona de escrita no projeto:** `src/modules/*/**`, `frontend/app/*/**`, `HANDOFF_ENGINE_MASTER.json`, `.aidd/cache/**`.

