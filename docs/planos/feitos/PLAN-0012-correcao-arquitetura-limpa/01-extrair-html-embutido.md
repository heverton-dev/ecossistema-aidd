# Item 1 — Extrair HTML embutido gigante para arquivo proprio (get_swagger_html e get_studio_html)

> **Escopo:** Entra: mover o HTML/CSS/JS de `get_swagger_html` e `get_studio_html` para arquivo(s) próprio(s) (`.html`), carregado em runtime no lugar do `.replace("__TITLE__", ...)` manual dentro da função Python. Não entra: mudar o visual, o comportamento ou a estrutura da página; não entra migrar para um motor de template real (Jinja2) — troca de mecanismo é decisão maior, fora deste item.

> **Status:** [CONCLUÍDO — Implementado e auditado por reprodução real em 2026-09-08]

---

## Contexto já investigado

- Achado via `code-review-graph` (`find_large_functions`, min_lines=150) em 2026-09-08.
- `get_swagger_html` (958 linhas): `tools/aidd-master/src/core/openapi.py:289`, `tools/aidd-enterprise/src/core/openapi.py:289`, `tools/aidd-enterprise/templates/core/openapi.py:289`, `tools/aidd-enterprise/templates/v2/openapi.py:289`, `tools/aidd-master/templates/core/openapi.py:289`, `tools/aidd-master/templates/v2/openapi.py:289` (6 cópias).
- `get_studio_html` (892 linhas): mesmo padrão em `src/core/webhooks.py`, `templates/core/webhooks.py`, `templates/v2/webhooks.py` de `aidd-master`/`aidd-enterprise` (6 cópias) + variante menor em `src/core/mcp_server.py`/`templates/core/mcp_server.py`/`templates/v2/mcp_server.py` de `aidd-master`/`aidd-enterprise` (6 cópias).
- Mecanismo atual: `html_template = """<!DOCTYPE html>...__TITLE__...__ENDPOINTS_JSON__..."""` seguido de `return html_template.replace("__TITLE__", title).replace("__ENDPOINTS_JSON__", endpoints_json)` (`openapi.py:1246`) — substituição literal de string, não um motor de template.
- As 6 cópias de cada função já são candidatas a entrar no baseline do item 2 deste plano (`G_DRIFT_NUCLEO_COMPARTILHADO`), então a ordem de execução entre item 1 e item 2 importa — ver nota no item 2.

## Decisão de escopo tomada na execução (aprovada pelo usuário em 2026-09-08)

A variante `get_studio_html` de `mcp_server.py` (6 cópias) **entrou no escopo do Item 1** junto com `openapi.py` e `webhooks.py`, totalizando 18 funções tratadas (não 12). Decisão colocada explicitamente para o usuário antes de implementar (regra "a skill/agente nunca decide sozinho") — resposta: incluir, mesmo padrão mecânico, evita reabrir o mesmo achado depois.

## Nota técnica sobre a técnica de substituição (descoberta durante a implementação)

O mecanismo real não era uniforme como o "Contexto já investigado" registrava:
- `openapi.py::get_swagger_html`: já usava `html_template = """...__TOKEN__..."""` + `.replace()` — extração trivial, só mudou a origem do texto (arquivo em vez de string inline).
- `webhooks.py::get_studio_html` e `mcp_server.py::get_studio_html`: usavam **f-string** (`return f"""...{variavel}..."""`), não substituição de placeholder. Uma f-string não pode ser carregada de um arquivo em runtime (a interpolação é resolvida em tempo de parse do código-fonte Python). Para extrair essas duas para arquivo, a técnica foi convertida para o mesmo padrão já usado em `openapi.py`: tokens `__NOME__` (ex.: `__EVENT_OPTIONS__`, `__TOOLS_JSON__`) + `.replace()` encadeado após carregar o arquivo — mesma técnica já estabelecida no próprio código-base, agora aplicada de forma consistente às 3 famílias de função. Extração feita via script Python baseado em `ast` (parse da f-string em `JoinedStr`/`FormattedValue`), não manualmente, para eliminar risco de erro humano na separação entre chaves literais de CSS/JS (`{{`/`}}`) e interpolações reais.

## Definição de Pronto

1. HTML/CSS/JS de `get_swagger_html` extraído para arquivo(s) próprio(s) dentro do mesmo diretório do módulo Python que hoje o contém, carregado via leitura de arquivo em runtime (não `import` de outro módulo Python, para não criar acoplamento novo).
2. Mesma extração aplicada a `get_studio_html`.
3. Placeholders (`__TITLE__`, `__ENDPOINTS_JSON__` e equivalentes) continuam funcionando exatamente como hoje — mesma técnica de substituição, só mudando de onde o texto-base vem.
4. Aplicado de forma consistente nas 6 cópias de cada função (não só numa), preservando a duplicação atual entre `aidd-master`/`aidd-enterprise` (a decisão de consolidar essa duplicação é escopo do item 2, não deste item).
5. Nenhuma mudança de comportamento visível: página renderizada antes e depois é byte-idêntica (comparar HTML final gerado, não só o código-fonte).
6. Testes reais de cada ferramenta (`pytest`) passando sem falha nova.

## Critério de saída

- Arquivos `.html` criados no local correto, um por função (ou compartilhado entre as 2, se fizer sentido técnico — decisão de quem implementar, documentada no commit).
- Página gerada antes/depois comparada e idêntica (reprodução real, não suposição).
- `python gates/G_TESTES_REAIS.py` (ou pytest direto) aprovado nas ferramentas tocadas.
- `python gates/G_HARNESS_COMPAT.py` e `python gates/G_DRIFT_NUCLEO_COMPARTILHADO.py` continuam aprovados (nenhuma das 6 cópias pode ficar para trás).

## Veredito da auditoria (reprodução real, 2026-09-08)

- **18 arquivos `.py` alterados** (6 cópias × 3 funções: `openapi.py`, `webhooks.py`, `mcp_server.py`, em `aidd-master` e `aidd-enterprise` × `src/core`, `templates/core`, `templates/v2`), **18 arquivos `.html` novos** criados ao lado de cada `.py` (`swagger.html`, `webhook_studio.html`, `mcp_studio.html`).
- Verificação real por reprodução, não leitura: para cada um dos 18 arquivos, o método foi executado via `exec()` isolado ANTES da alteração (capturando a string HTML retornada com dados de amostra contendo aspas, `&`, `<script>`, acentuação) e DEPOIS da alteração, comparando as duas strings byte a byte. Resultado: **18/18 idênticas** (nenhuma diferença de um único byte).
- `python gates/G_DRIFT_NUCLEO_COMPARTILHADO.py`: **APROVADO** (100% OK) — `openapi.py` e `webhooks.py` continuam sincronizados entre `aidd-master`/`aidd-enterprise`; `mcp_server.py` mantém a mesma divergência já conhecida e documentada (`register_injected_tools`), não relacionada a este item.
- `python gates/G_TESTES_REAIS.py`: **APROVADO** — 1699 passed, 0 failed, 9 skipped (todas as 5 ferramentas do monorepo, incluindo `aidd-master` e `aidd-enterprise`).
- `scripts/gates/G_HARNESS_COMPAT.py` em `aidd-master` e `aidd-enterprise`: **APROVADO** em ambos ("Ambiente 100% compatível").
- Nenhum arquivo `.bak`/temporário deixado no repositório; `git status` mostra apenas os 18 `.py` modificados + 18 `.html` novos.

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item 1: Extrair HTML embutido gigante para arquivo proprio (get_swagger_html e get_studio_html).
Siga rigorosamente a Definicao de Pronto acima.
Nao invente aprovacoes e mantenha as regras do monorepo.
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 1: Extrair HTML embutido gigante para arquivo proprio (get_swagger_html e get_studio_html).
Strictly follow the Definition of Done above.
Do not fabricate approvals and maintain monorepo governance rules.
```
