# Item 1 — Extrair HTML embutido gigante para arquivo proprio (get_swagger_html e get_studio_html)

> **Escopo:** Entra: mover o HTML/CSS/JS de `get_swagger_html` e `get_studio_html` para arquivo(s) próprio(s) (`.html`), carregado em runtime no lugar do `.replace("__TITLE__", ...)` manual dentro da função Python. Não entra: mudar o visual, o comportamento ou a estrutura da página; não entra migrar para um motor de template real (Jinja2) — troca de mecanismo é decisão maior, fora deste item.

> **Status:** [RASCUNHO — Aguardando Aprovação Humana]

---

## Contexto já investigado

- Achado via `code-review-graph` (`find_large_functions`, min_lines=150) em 2026-09-08.
- `get_swagger_html` (958 linhas): `tools/aidd-master/src/core/openapi.py:289`, `tools/aidd-enterprise/src/core/openapi.py:289`, `tools/aidd-enterprise/templates/core/openapi.py:289`, `tools/aidd-enterprise/templates/v2/openapi.py:289`, `tools/aidd-master/templates/core/openapi.py:289`, `tools/aidd-master/templates/v2/openapi.py:289` (6 cópias).
- `get_studio_html` (892 linhas): mesmo padrão em `src/core/webhooks.py`, `templates/core/webhooks.py`, `templates/v2/webhooks.py` de `aidd-master`/`aidd-enterprise` (6 cópias) + variante menor (465 linhas) em `src/core/mcp_server.py`/`templates/core/mcp_server.py` (verificar se está no mesmo escopo ou é item separado, ao investigar).
- Mecanismo atual: `html_template = """<!DOCTYPE html>...__TITLE__...__ENDPOINTS_JSON__..."""` seguido de `return html_template.replace("__TITLE__", title).replace("__ENDPOINTS_JSON__", endpoints_json)` (`openapi.py:1246`) — substituição literal de string, não um motor de template.
- As 6 cópias de cada função já são candidatas a entrar no baseline do item 2 deste plano (`G_DRIFT_NUCLEO_COMPARTILHADO`), então a ordem de execução entre item 1 e item 2 importa — ver nota no item 2.

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
