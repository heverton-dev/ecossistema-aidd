# Item 11 — Adotar instructor e terminar migração MCP SDK no núcleo compartilhado (Onda 5 remanescente)

**STATUS: ✅ CONCLUÍDO em 2026-09-09 — implementação por Buffy (sessão de fechamento dos itens 10–11 do plano anti-NIH).**

## Definição de Feito

1. **(11a)** instructor adotado no núcleo do generator com `response_model` no caminho **real de produção** (não só no mecanismo utilitário).
2. **(11b)** `mcp_server.py` do núcleo compartilhado master/enterprise sobre o **SDK oficial do MCP** (`modelcontextprotocol/python-sdk`), com testes reais.
3. Zero testes falsos: os novos testes exercitam list_tools/call_tool reais.

## 11a — instructor com response_model no caminho real

- `scripts/phases/schemas/registry.py` (mecanismo preexistente) agora é usado de fato: `08_implementador.py` (Fase 8, a fase que gera código) parseia a resposta do LLM via `parsear_resposta_codegen()` com `response_model=ModeloCodegen` quando pydantic+instructor estão disponíveis — o retry automático do instructor passa a valer em produção, não só em teste.
- `_validar_pydantic_com_retry` ganhou costura de injeção (`_loads`) para testes determinísticos sem depender do instructor instalado.
- Testes novos em `tests/test_utils_delegacao.py`: caminho feliz com payload válido, retry em JSON malformado (prova de que o retry ativa) — 46 testes passando no arquivo.

## 11b — mcp_server.py sobre o SDK oficial

- `src/core/mcp_server.py` (master + enterprise, idênticos) reescrito: transporte, negociação de protocolo e códigos de erro JSON-RPC 2.0 delegados ao SDK via `FastMCP` (`build_fastmcp()` / `run_stdio_server()`); integração por subclass de `FastMCP` com `list_tools`/`call_tool` lendo o registro vivo da classe (mesma API pública de antes: `register_tool`, `register_module_tools`, `execute_tool`, `handle_json_rpc`, `get_studio_html` — zero quebra de chamadores).
- Import condicional do SDK: ambientes sem `mcp` instalado continuam 100% funcionais via camada de compat JSON-RPC própria (fallback legado no stdio).
- Espalhado para todos os derivados, mantendo os pares do drift gate idênticos: `templates/core/mcp_server.py` (×2, sem `register_injected_tools`, CRLF) e `templates/v2/mcp_server.py` (×2) — este último alimentava suítes geradas com a versão antiga.
- `scripts/compose_suite.py` (×2): adiciona `mcp>=1.28.0` ao `requirements.txt` gerado e passa a copiar os assets `webhook_studio.html`/`mcp_studio.html` para `src/core/` das suítes geradas (referenciados por `webhooks.py` e `mcp_server.py`; sem eles a rota /webhooks e o check comportamental de XSS quebram).
- Os 2 exemplos de `materiais-extras/examples/*/src/core/mcp_server.py` (enterprise) receberam o mesmo bridge do SDK via patch cirúrgico (lógica de domínio e portal preservados).

## Prova

- `tests/unit/test_mcp_server_sdk.py` (novo, ×2 ferramentas): 11 testes cada — list_tools reflete o registro, call_tool despacha para handler real, initialize/ping, stdio com SDK e fallback sem SDK. **11+11 passando.**
- Suítes completas: master 267 passed (unit) / enterprise 244 passed (unit) / generator 929 passed.
- `G_DRIFT_NUCLEO_COMPARTILHADO.py`: APROVADO (100% OK) — todos os pares idênticos.
- Reprodução ponta a ponta: suíte composta real (compose_suite → G_TESTES → G_SEGURANCA → G_CONTRACTS) executada; o `mcp_server.py` da suíte gerada importa e registra ferramentas com o SDK.
