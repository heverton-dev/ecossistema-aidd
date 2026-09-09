# Item 16 — XSS armazenado real em `get_studio_html` (núcleo compartilhado)

> **Escopo:** Entra: escapar corretamente `ev["modulo"]`/`ev["descricao"]` (e qualquer outro campo de evento vindo de `register_module_events`) antes de inserir no HTML retornado por `get_studio_html`, em `core/webhooks.py` — nas 3 cópias (`src/core`, `templates/core`, `templates/v2`) de `aidd-enterprise` e `aidd-master` (6 arquivos ao todo). Não entra: reescrever o Studio de Webhooks inteiro nem mudar o formato dos eventos.
> **Status:** [✅ CONCLUÍDO em 2026-09-09 — corrigido nas 6 cópias, reproduzido antes/depois com payload real, testes automatizados adicionados, suíte completa e gates de integridade verdes.]
> **Origem:** achado real pela sessão que implementava o Item 7, ao construir o teste comportamental de XSS — não suposição, código lido e confirmado.

---

## Contexto já investigado

- `core/webhooks.py`, método `get_studio_html` (~linhas 222-236): os campos `modulo` e `descricao` de cada evento cadastrado via `register_module_events` são inseridos direto no HTML da página do Studio de Webhooks, sem escapar caracteres especiais (`<`, `>`, `"`, etc.).
- Efeito real: se um módulo for cadastrado com um nome/descrição contendo um script (ex.: `<script>...</script>`), esse script roda de verdade no navegador de quem abrir essa página depois — é um XSS armazenado clássico, não teórico.
- Confirmado idêntico nas 6 cópias do núcleo compartilhado: `tools/aidd-enterprise/src/core/webhooks.py`, `templates/core/webhooks.py`, `templates/v2/webhooks.py` e os 3 equivalentes em `tools/aidd-master`.
- Todo projeto gerado por `compose_suite.py` (master/enterprise) herda essa falha automaticamente, porque o Studio de Webhooks é copiado como está.

## Definição de Pronto

1. Os campos de evento são escapados (ex.: `html.escape()` ou equivalente) antes de entrar no HTML gerado, nas 6 cópias.
2. Teste automatizado que cadastra um evento com um payload de ataque real (ex.: `<script>alert(1)</script>`) e confirma que o HTML retornado por `get_studio_html` não contém o script executável — só a versão escapada.
3. Suíte de testes completa de `aidd-enterprise` e `aidd-master` continua 100% verde depois da correção.
4. `gates/G_DRIFT_NUCLEO_COMPARTILHADO.py` continua aprovando (as 6 cópias seguem sincronizadas).

## Critério de saída

- Vulnerabilidade reproduzida antes da correção (payload real executando) e neutralizada depois (payload real bloqueado) — não assumir, confirmar.
- Testes reais passando sem stubs falsos.
- Gates de integridade aprovados.

## Prompt de Execução (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item 16: XSS armazenado real em get_studio_html (nucleo compartilhado).
Siga rigorosamente a Definicao de Pronto acima.
Nao invente aprovacoes e mantenha as regras do monorepo.
```

## Prompt de Execução — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 16: real stored XSS in get_studio_html (shared core).
Strictly follow the Definition of Done above.
Do not fabricate approvals and maintain monorepo governance rules.
```

---

## Execução real e evidências (2026-09-09)

### 1. Correção aplicada

`html.escape()` (stdlib, `import html`) aplicado a `ev["event"]`, `ev["modulo"]`,
`ev["descricao"]` (os três campos de evento renderizados em HTML dentro de
`get_studio_html`) e também ao parâmetro `title` (mesmo padrão de risco,
mesma função) — nas 6 cópias:

- `tools/aidd-enterprise/src/core/webhooks.py`
- `tools/aidd-enterprise/templates/core/webhooks.py`
- `tools/aidd-enterprise/templates/v2/webhooks.py`
- `tools/aidd-master/src/core/webhooks.py`
- `tools/aidd-master/templates/core/webhooks.py`
- `tools/aidd-master/templates/v2/webhooks.py`

As 6 cópias foram verificadas byte-a-byte idênticas entre si após a correção
(`diff` direto, sem diferenças).

Campo `EVENT_TEMPLATES_JSON` (contexto `<script>`, via `json.dumps`) e
`INITIAL_EVENT` (contexto de string literal JS, `trocarTemplateEvento('...')`)
foram deliberadamente **não** alterados nesta correção — ambos usam `event`
(derivado de `slug`, não do texto livre `name`) e ficam fora do escopo pedido
("modulo"/"descricao" e demais campos renderizados em **HTML**). Registrado
aqui como observação para decisão futura, não como pendência deste item.

### 2. Reprodução ANTES da correção (payload real, código revertido via `git stash`)

Comando:
```
python -c "
import sys; sys.path.insert(0, 'src')
from core.webhooks import WebhookDispatcher
WebhookDispatcher.register_module_events('poc-antes-da-correcao', '<script>alert(1)</script>')
wd = WebhookDispatcher(db=None)
html_out = wd.get_studio_html()
print('payload cru presente:', '<script>alert(1)</script>' in html_out)
"
```
Saída real:
```
payload cru presente: True
...poc-antes-da-correcao.criado">poc-antes-da-correcao.criado (<script>alert(1)</script>)</option>...
```
Confirma o payload executável de verdade no HTML antes da correção.

### 3. Reprodução DEPOIS da correção (mesmo payload, código corrigido)

Mesmo script, após aplicar `html.escape`:
```
RAW PAYLOAD STILL PRESENT (should be False): False
ESCAPED PAYLOAD PRESENT (should be True): True
...xsstest2.criado">xsstest2.criado (&lt;script&gt;alert(1)&lt;/script&gt;)</option>...
```
Confirma neutralização real — o payload não roda mais, aparece só como texto.

### 4. Testes automatizados adicionados

`tools/aidd-enterprise/tests/unit/test_webhooks_xss.py` e o equivalente em
`tools/aidd-master/tests/unit/test_webhooks_xss.py` (3 testes cada):
- `test_nome_de_modulo_com_payload_xss_volta_escapado`
- `test_titulo_customizado_com_payload_xss_volta_escapado`
- `test_sem_escape_o_payload_apareceria_executavel` (prova que a asserção
  acima de fato pegaria a regressão — simula a interpolação antiga e confirma
  que o payload cru aparece nesse cenário)

Resultado: `3 passed` em cada ferramenta (`pytest tests/unit/test_webhooks_xss.py -q`).

### 5. Suíte completa — antes/depois (contagem real, `pytest -q`)

| Ferramenta | Antes (código revertido via `git stash`) | Depois (com a correção + novos testes) |
|---|---|---|
| aidd-enterprise | 235 passed, 4 skipped | 242 passed, 4 skipped¹ |
| aidd-master | 261 passed, 4 skipped | 268 passed, 4 skipped¹ |

¹ O delta de 7 (não 3) inclui também os 4 testes novos de
`tests/unit/test_g_seguranca_gate.py`, adicionados junto no Item 7 (mesma
sessão) — ver `07-corrigir-gate-de-seguranca-rotulado-blindagem-militar-rotulo-ou-cobertura-real.md`
para o detalhamento desses 4. Isolando só os 3 testes deste item
(`test_webhooks_xss.py`): 235→238 (enterprise) e 261→264 (master), conferido
em execução isolada antes de somar os testes do Item 7.

### 6. Gates de integridade

- `gates/G_DRIFT_NUCLEO_COMPARTILHADO.py`: **[SUCESSO]** — as 6 cópias de
  `webhooks.py` seguem sincronizadas (`[OK] .../webhooks.py: sincronizado`
  para os pares comparados pelo gate).
- Suíte completa (`pytest -q`, ambas as ferramentas): 0 falhas depois da
  correção (ver tabela acima).

### 7. Achado colateral (fora do escopo deste item, registrado apenas como observação)

Ao testar o Item 7 contra uma suíte recém-composta via `compose_suite.py`,
descobriu-se que `core_files` em `scripts/compose_suite.py` (linha ~453) **não
copia `webhook_studio.html`** para o app gerado — só os `.py`. Isso significa
que `get_studio_html()` já vinha quebrando com `FileNotFoundError` em todo
app gerado por essa rota, independente do XSS. Não é uma vulnerabilidade
(é uma falha de empacotamento que impede o recurso de funcionar), e corrigi-la
está fora do escopo declarado deste item e do Item 7 (ambos restritos a
`get_studio_html`/`G_SEGURANCA.py`). Reportado ao usuário na mesma sessão;
nenhuma ação tomada sobre `compose_suite.py` até nova decisão.
