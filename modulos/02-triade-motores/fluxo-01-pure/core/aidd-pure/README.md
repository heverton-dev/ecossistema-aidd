# aidd-pure

Fluxo 01 da Tríade: motor de 8 fases que leva uma ideia em linguagem natural a um projeto testado (schemas, scripts, testes e documentação), com TDD Red-Green estrito.

## Uso rápido

```bash
python ecossistema.py pure-motor "Minha ideia"
```

- Guia completo (instalação, arquitetura, testes): [GUIA.md](GUIA.md)
- Regras e invariantes para agentes: [AGENTS.md](AGENTS.md)

## Fronteiras Canônicas e Responsabilidades

Conforme o mapa oficial de arquitetura (`MAPA-DONOS-FERRAMENTAS.json` e `G_FRONTEIRA_FERRAMENTAS.py`):

- **Responsabilidades:**
  - `construcao_do_zero_tdd_red_green`
  - `geracao_fatias_dominio_vsa_zero`
- **Pode guardar peças do catálogo:** Não (`pode_guardar_pecas: false`).
- **Dono do conteúdo de:** `fatias_dominio_pure`, `testes_unitarios_dominio_pure`.
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
## Configuração de LLM e Modos de Execução

O motor opera em dois modos:
1. **Modo Delegado (default):** Se houver uma ADE ativa (Claude Code, Antigravity, OpenCode, etc.), o motor delega as decisões diretamente na conversa via arquivos de protocolo JSON em `.aidd/cache/`.
2. **Modo Headless (fallback):** Se a ADE estiver ausente ou offline, o motor recorre à variável de ambiente `LLM_MODEL`:
   - Defina `LLM_MODEL` no seu `.env` (ex.: `anthropic/claude-haiku-4-5-20251001`, `openai/gpt-4o`, `ollama/llama3`).
   - Configure a respectiva chave de API (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, etc.).
   - Se a ADE estiver offline e `LLM_MODEL` não estiver configurado, o motor falha rapidamente com **código de saída 3** e instruções de configuração claras.

---
