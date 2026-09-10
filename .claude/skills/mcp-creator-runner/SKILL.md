---
name: mcp-creator-runner
description: Cria um novo servidor MCP para uma ferramenta deste ecossistema (ou compartilhado), garantindo que o resultado seja materializado em componentes/ e sincronizado em todos os harnesses — usa ferramenta/função nativa de autoria MCP quando disponível no harness, ou o padrão FastMCP/mcp já usado no projeto quando não.
---

# MCP Creator Runner

Coordenador fino. **Não reimplementa** protocolo MCP do zero — delega para
ferramenta nativa de autoria MCP quando o harness atual dispuser dela, e garante
que o resultado siga a convenção física deste projeto: fonte única em
`componentes/<ferramenta ou compartilhado>/mcps/<nome>/`, nunca escrito
direto num `.mcp.json`/pasta de harness.

**Diferente do `dependencia-runner`:** aquele registra MCP de **terceiro** já
pronto (ex.: Playwright, GitHub oficial, Context7) que o agente consome como
ferramenta de desenvolvimento. Esta skill é pra construir um MCP **novo, que
vira parte de um produto/ferramenta gerada** (ex.: o `cloudflare-mcp` que o
`aidd-ops` expõe, o `mcp-verificador-cve` do `aidd-generator`). Se o pedido for
"adicionar servidor MCP de terceiro que eu uso pra trabalhar aqui", redirecione
pro `dependencia-runner`.

## Protocolo ao ser acionada

1. **Descubra o harness ativo e suas capacidades.** Se o harness dispuser de
   ferramenta/função nativa de criação/geração de MCP servers, invoque-a para
   decidir estrutura de tools/resources, schema de entrada/saída e tratamento
   de erro do servidor novo. Não decida essas questões sozinho quando a
   ferramenta nativa puder decidir.

2. **Se o harness não tiver ferramenta nativa de autoria MCP**, construa sobre as libs
   Python já usadas neste ecossistema (`mcp`/`fastmcp` — já são dependência
   real via `code-review-graph`, confira `pip show fastmcp` antes de assumir
   que precisa instalar de novo) em vez de implementar JSON-RPC 2.0 na mão.
   Use como referência estrutural real um MCP já existente no ecossistema
   (`tools/aidd-ops/mcps/cloudflare-mcp/server.py` ou
   `tools/aidd-generator/mcps/mcp-verificador-cve/`) — leia um antes de
   escrever o novo.

3. **Sempre grave a fonte em `componentes/<ferramenta ou compartilhado>/mcps/<nome>/server.py`**
   (mais `requirements.txt`/README próprios se precisar) — nunca direto na
   pasta de um harness.

4. **Materialize e confirme:**
   ```bash
   python ecossistema.py components sync --tipo mcp --ferramenta <ferramenta ou compartilhado>
   python ecossistema.py components verify --tipo mcp
   ```
   Só reporte sucesso depois do `verify` retornar exit 0.

5. **Nunca peça nem grave valor de segredo/API key dentro do servidor ou do
   commit** — se o MCP precisar de credencial, exponha só o **nome** da
   variável de ambiente esperada (mesma regra do `dependencia-runner`), e
   documente no README do MCP que o usuário exporta o valor real na própria
   máquina.

## Quando NÃO usar esta skill

- MCP de terceiro pronto que o agente consome pra trabalhar neste repo (Playwright, GitHub, Context7, code-review-graph) → `dependencia-runner`.
- Editar um MCP já materializado sem passar pelo passo 4 → nunca edite as cópias em `.claude/`/`tools/<x>/.claude/` etc. diretamente, edite em `componentes/` e resincronize.
