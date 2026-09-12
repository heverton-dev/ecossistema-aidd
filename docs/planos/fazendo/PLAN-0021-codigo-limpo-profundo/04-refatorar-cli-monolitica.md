# Item 4 — Refatorar CLI monolitica aidd.py de master-enterprise (funcoes com multiplas responsabilidades e roteamento duplo)

> **Escopo:** Decompor as funções de comando (`cmd_*`) e `main()` de `scripts/aidd.py` em master e enterprise, que hoje misturam parse de argumentos + política + geração de artefato + relatório no mesmo corpo. Resolver o duplo sistema de roteamento (dicionário de comandos + subparsers argparse + fallback de linguagem natural). Não entra: o conteúdo de `compose_suite.py` chamado por essas funções (Item 8) nem a unificação de vocabulário de domínio do `cmd_plan` (Item 5) — este item é sobre a estrutura da CLI em si.
> **Status:** [EM EXECUCAO]

---

## Contexto ja investigado

Fonte: relatório de auditoria, achado #4 e seção 5.1 (medido por AST parsing, tamanho real de função).

- `scripts/aidd.py` tem **1.162 linhas no master / 1.171 no enterprise** (código quase idêntico — ver Item 1 sobre a duplicação de CLI entre as duas ferramentas, achado relacionado).
- Funções mais longas (linha inicial e tamanho, via AST): `main` 146 linhas (`:1013`), `cmd_plan` 135 linhas (`:843`), `cmd_audit` 122 linhas (`:329`), `cmd_compose_orca` 96 linhas, `cmd_bench` 83 linhas.
- Cada `cmd_*` mistura, no mesmo corpo: parse de argumentos, decisão de política (ex.: quais ambientes são permitidos) e geração de artefato/relatório.
- `main()` mantém **dois sistemas de roteamento simultâneos**: um dicionário `cmds` + subparsers `argparse`, mais um **fallback de linguagem natural** que intercepta qualquer subcomando desconhecido e chama `cmd_plan` — ou seja, existe uma precedência implícita entre os dois mecanismos que não está documentada em nenhum lugar.
- `cmd_components` (40 linhas) e `cmd_dependencia` (60 linhas) repetem o mesmo padrão: constroem uma sub-CLI `click` **dentro da própria função** e usam `types.SimpleNamespace` para chamar gestores que já têm parsing próprio — um adaptador escrito duas vezes com a mesma forma.

## Definicao de Pronto

1. `main()` usa um único mecanismo de roteamento de comandos — o dicionário `cmds` + subparsers OU o fallback de linguagem natural, não os dois simultaneamente com precedência implícita. Se o fallback for mantido, sua regra de precedência fica documentada explicitamente no código (não só no comentário).
2. Cada `cmd_*` refatorado separa em funções distintas: parse/validação de argumentos, decisão de política, e geração de artefato/relatório — nenhuma função de comando ultrapassa ~40 linhas no corpo principal (o resto vira chamada a funções extraídas).
3. `cmd_components` e `cmd_dependencia` não recriam sub-CLI `click` dentro da função — reusam (ou extraem para) um adaptador comum, já que fazem exatamente a mesma coisa.
4. Suíte de testes real da CLI (master e enterprise) passa com exit 0, incluindo os casos de roteamento (comando conhecido, comando desconhecido caindo no fallback se ele for mantido).
5. Nenhuma função de comando nova introduzida no processo ultrapassa o limite de responsabilidade única verificável por leitura (uma função, um propósito).

## Criterio de saida

- `aidd.py` com funções de comando decompostas e roteamento com precedência clara e documentada.
- Testes reais passando (comportamento idêntico ao anterior, exceto o que for explicitamente corrigido).
- Nenhuma regressão nos comandos existentes (`cmd_plan`, `cmd_audit`, `cmd_compose_orca`, `cmd_bench`, `cmd_components`, `cmd_dependencia`, etc.).

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item 4: decompor as funcoes de comando de scripts/aidd.py em master
e enterprise, que hoje misturam parse + politica + geracao de artefato no mesmo corpo (ver
docs/relatorios/relatorio-auditoria-codigo-limpo-ecossistema-aidd.html, achado #4 e secao
5.1, para evidencia completa).

Fatos que voce precisa saber antes de comecar:
- aidd.py: 1.162 linhas (master) / 1.171 (enterprise).
- Funcoes mais longas: main 146L (:1013), cmd_plan 135L (:843), cmd_audit 122L (:329),
  cmd_compose_orca 96L, cmd_bench 83L.
- main() tem 2 sistemas de roteamento ao mesmo tempo: dict cmds + subparsers argparse + um
  fallback de linguagem natural que chama cmd_plan pra qualquer comando desconhecido -
  precedencia implicita nao documentada.
- cmd_components e cmd_dependencia recriam uma sub-CLI click dentro da propria funcao -
  mesmo padrao repetido.

Regras obrigatorias:
1. Este item NAO tem decisao arquitetural de alto risco como o Item 1 - e refatoracao
   estrutural de um arquivo ja existente, sem mudar comportamento observavel. Mesmo assim,
   se voce encontrar um caso onde os dois sistemas de roteamento dao resultados diferentes
   pro mesmo input, PARE e pergunte antes de decidir qual comportamento e o correto.
2. Siga rigorosamente a Definicao de Pronto acima.
3. Nao invente aprovacoes. So marque como concluido apos rodar a suite de testes real da
   CLI (master e enterprise) com exit 0.
4. Mantenha as regras de governanca do monorepo (AGENTS.md).
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 4: decompose the command functions in scripts/aidd.py in
master and enterprise, which today mix parsing + policy + artifact generation in the same
body (see docs/relatorios/relatorio-auditoria-codigo-limpo-ecossistema-aidd.html, finding #4
and section 5.1, for full evidence).

Facts you need before starting:
- aidd.py: 1,162 lines (master) / 1,171 (enterprise).
- Longest functions: main 146L (:1013), cmd_plan 135L (:843), cmd_audit 122L (:329),
  cmd_compose_orca 96L, cmd_bench 83L.
- main() has 2 routing systems at once: a cmds dict + argparse subparsers + a natural
  language fallback that calls cmd_plan for any unknown command - undocumented implicit
  precedence.
- cmd_components and cmd_dependencia rebuild a click sub-CLI inside the function itself -
  same pattern repeated.

Mandatory rules:
1. This item does not carry a high-risk architectural decision like Item 1 - it is
   structural refactoring of an existing file with no observable behavior change intended.
   Still, if you find a case where the two routing systems give different results for the
   same input, STOP and ask before deciding which behavior is correct.
2. Strictly follow the Definition of Done above.
3. Do not fabricate approvals. Only mark this done after running the real CLI test suite
   (master and enterprise) with exit 0.
4. Maintain monorepo governance rules (AGENTS.md).
```
