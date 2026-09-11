# Item 8 — Refatorar compose_suite.py (multiplas responsabilidades e HTML em f-string) e remover constante morta WEBHOOK_DEMO_URL

> **Escopo:** Decompor `compose_suite()` e `generate_superapp_index_html()` em `scripts/compose_suite.py` (master e enterprise), que hoje misturam scaffolding de diretórios, geração de HTML/CSS/JS inline, governança multi-IDE e manifestos. Remover a constante morta `WEBHOOK_DEMO_URL`. Não entra: a unificação da CLI `aidd.py` que chama essas funções (Item 4).
> **Status:** [RASCUNHO — Aguardando Aprovacao Humana]

---

## Contexto ja investigado

Fonte: relatório de auditoria, achados #5 e #16, seção 5.3.

- `compose_suite()`: **266 linhas, 4 responsabilidades** no mesmo corpo — scaffolding de diretórios, geração de HTML/CSS/JS inline, governança multi-IDE e manifestos.
- `generate_superapp_index_html()`: **192 linhas de HTML/JS/CSS em f-strings** com chaves escapadas (`{{`/`}}`) — geração de interface inteira embutida em código Python.
- `scripts/compose_suite.py` master ↔ enterprise: **682 linhas comuns de ~685/683 linhas totais** (medido por `difflib`) — ou seja, é essencialmente o mesmo arquivo nas duas ferramentas (ver Item 1/4 sobre a duplicação estrutural entre as ferramentas gêmeas).
- `WEBHOOK_DEMO_URL` (`:40`, em ambas as ferramentas): constante definida e **zero referências de uso** (confirmado via `grep`, excluindo a própria linha de definição) — resquício do "seed de demo" removido pelo Item 5 do plano `docs/planos/fazendo/01-correcao-pos-auditoria-sem-maquiagem/`.
- Contexto de risco: a geração de HTML via f-string é o mesmo padrão que já causou o XSS real do Item 16 daquele mesmo plano 01 (em `get_studio_html`) — o relatório aponta isso como um padrão recorrente que facilita esquecer escapamento ao copiar um bloco.

## Definicao de Pronto

1. `compose_suite()` é decomposta em funções com responsabilidade única (scaffolding de diretórios, geração de HTML, governança multi-IDE, manifestos como funções separadas e testáveis isoladamente).
2. `generate_superapp_index_html()` não gera mais 192 linhas de HTML/JS/CSS diretamente em f-string no corpo Python — extraído para template(s) separado(s) ou função(ões) de geração com escapamento centralizado (reduzindo o risco de XSS recorrente, achado relacionado ao Item 16 do plano 01).
3. `WEBHOOK_DEMO_URL` removida de ambas as ferramentas, com `grep` confirmando 0 referências antes da remoção (checagem, não suposição).
4. Testes reais de composição de suíte (master e enterprise) passam com exit 0 após a refatoração, incluindo geração real do HTML de saída comparada byte-a-byte com o comportamento anterior (quando não houver mudança de comportamento pretendida).

## Criterio de saida

- `compose_suite.py` com funções de responsabilidade única, sem HTML gigante embutido em f-string sem escapamento centralizado.
- `WEBHOOK_DEMO_URL` removida.
- Testes reais passando, sem regressão no HTML/CSS/JS gerado para o usuário final.

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item 8: decompor compose_suite() e generate_superapp_index_html() em
scripts/compose_suite.py (master e enterprise), que hoje misturam scaffolding, geracao de
HTML/CSS/JS inline, governanca multi-IDE e manifestos no mesmo corpo, e remover a constante
morta WEBHOOK_DEMO_URL (ver docs/relatorios/relatorio-auditoria-codigo-limpo-ecossistema-aidd.html,
achados #5 e #16, secao 5.3).

Fatos que voce precisa saber antes de comecar:
- compose_suite(): 266 linhas, 4 responsabilidades no mesmo corpo.
- generate_superapp_index_html(): 192 linhas de HTML/JS/CSS em f-string com chaves escapadas.
- compose_suite.py master e enterprise: 682 linhas comuns de ~685/683 (essencialmente o
  mesmo arquivo - ver Itens 1 e 4 sobre duplicacao estrutural entre as ferramentas).
- WEBHOOK_DEMO_URL (:40, ambas as ferramentas): definida, ZERO usos confirmados por grep -
  resquicio do seed de demo ja removido pelo Item 5 do plano 01.
- Geracao de HTML via f-string ja causou um XSS real (Item 16 do plano 01, em
  get_studio_html) - mesmo padrao de risco aqui.

Regras obrigatorias:
1. Antes de remover WEBHOOK_DEMO_URL, rode o grep de novo voce mesmo para confirmar 0 usos -
   nao assuma que o relatorio ainda reflete o estado atual do codigo.
2. Ao extrair o HTML de generate_superapp_index_html() para fora do corpo Python, garanta
   escapamento consistente - esta e uma correcao de seguranca implicita (mesma classe de
   bug do XSS ja corrigido), entao trate com o mesmo rigor de teste comportamental real
   (nao so revisao visual).
3. Siga rigorosamente a Definicao de Pronto acima.
4. Nao invente aprovacoes. So marque como concluido apos rodar os testes reais de composicao
   de suite nas duas ferramentas.
5. Mantenha as regras de governanca do monorepo (AGENTS.md).
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 8: decompose compose_suite() and
generate_superapp_index_html() in scripts/compose_suite.py (master and enterprise), which
today mix scaffolding, inline HTML/CSS/JS generation, multi-IDE governance and manifests in
the same body, and remove the dead constant WEBHOOK_DEMO_URL (see
docs/relatorios/relatorio-auditoria-codigo-limpo-ecossistema-aidd.html, findings #5 and #16,
section 5.3).

Facts you need before starting:
- compose_suite(): 266 lines, 4 responsibilities in the same body.
- generate_superapp_index_html(): 192 lines of HTML/JS/CSS in an f-string with escaped
  braces.
- compose_suite.py master and enterprise: 682 common lines out of ~685/683 (essentially the
  same file - see Items 1 and 4 about structural duplication between the tools).
- WEBHOOK_DEMO_URL (:40, both tools): defined, ZERO uses confirmed by grep - leftover from
  the demo seed already removed by Item 5 of plan 01.
- HTML generation via f-string already caused a real XSS (Item 16 of plan 01, in
  get_studio_html) - same risk pattern here.

Mandatory rules:
1. Before removing WEBHOOK_DEMO_URL, re-run the grep yourself to confirm 0 uses - do not
   assume the report still reflects the current state of the code.
2. When extracting the HTML out of generate_superapp_index_html()'s Python body, ensure
   consistent escaping - this is an implicit security fix (same bug class as the already
   fixed XSS), so treat it with the same rigor of real behavioral testing (not just visual
   review).
3. Strictly follow the Definition of Done above.
4. Do not fabricate approvals. Only mark this done after running the real suite-composition
   tests on both tools.
5. Maintain monorepo governance rules (AGENTS.md).
```
