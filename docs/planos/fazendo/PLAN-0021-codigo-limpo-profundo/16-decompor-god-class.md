# Item 16 — Decompor God class SecurityGate (G_SEGURANCA) e renomear metodos camada-N

> **Escopo:** Decompor `SecurityGate` (`scripts/gates/G_SEGURANCA.py`, 502 linhas) que acumula varredura de código, execução comportamental, leitura de configs e geração de relatório, e renomear os métodos `_camada1_`...`_camada8_` (prefixo numérico usado só para ordenar). Afeta master e enterprise (arquivo duplicado — ver Itens 1 e 3).
> **Status:** [EM EXECUCAO]

---

## Contexto ja investigado

Fonte: relatório de auditoria, achados #21 e #30, seções 2.3 e 6.

- `SecurityGate` (`scripts/gates/G_SEGURANCA.py:49`): **502 linhas, 11 camadas** de verificação acumulando: varredura estática de código, execução comportamental real (testes de JWT, SQLi, XSS), leitura de arquivos de configuração, e geração do relatório final — 4 responsabilidades distintas na mesma classe.
- `_camada3b` (achado específico): cria uma tabela `_sqli_probe` num banco de dados temporário **gerenciado manualmente** dentro do gate — isso é, na prática, responsabilidade de *fixture de teste* embutida dentro de um gate de produção, misturando o papel de "verificar" com o papel de "montar cenário de teste".
- Métodos com **prefixo numérico no nome** (N1/N5, achado #30): `_camada1_`, `_camada2_`, `_camada2_5_`, `_camada8_` — o número no nome está fazendo o trabalho de ordenar uma lista de checks dentro de `run_all_checks`, quando deveria ser uma lista/sequência explícita e ordenável no código, não codificada no nome do método (renomear um método hoje exige also reordenar chamadas espalhadas, porque o nome carrega posição).
- **Boa prática já existente no mesmo gate**, citada no relatório: o relatório final do `G_SEGURANCA` já separa resultados por categoria (comportamental/config/estático) com rótulo honesto — isso é o padrão correto de transparência que deve ser preservado na decomposição, não descartado.

## Definicao de Pronto

1. `SecurityGate` decomposta em classes/módulos separados por responsabilidade: varredura estática, execução comportamental (JWT/SQLi/XSS), leitura de config, e geração de relatório — cada um testável isoladamente.
2. `_camada3b` (fixture de banco temporário para prova de SQLi) extraída para um helper de teste explícito, separado da lógica de verificação do gate.
3. Métodos `_camadaN_` renomeados para nomes que descrevem o que cada check faz (ex.: `_verificar_jwt`, `_verificar_sqli`), com a ordem de execução definida por uma lista/sequência explícita em `run_all_checks`, não pelo nome do método.
4. A separação de relatório por categoria (comportamental/config/estático) — já citada como boa prática — é preservada exatamente como está na decomposição.
5. Testes reais do gate de segurança (master e enterprise) passam com exit 0 após a decomposição, incluindo os testes comportamentais reais de JWT/SQLi/XSS que o relatório já confirmou existirem sem mock.

## Criterio de saida

- `SecurityGate` decomposta, sem God class de 502 linhas com 4 responsabilidades.
- Métodos renomeados, ordem de execução explícita e não codificada no nome.
- Testes reais (incluindo os comportamentais de ataque) passando sem regressão.

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item 16: decompor SecurityGate (scripts/gates/G_SEGURANCA.py, 502
linhas, 11 camadas) e renomear metodos _camadaN_ que usam numero no nome so para ordenar
(ver docs/relatorios/relatorio-auditoria-codigo-limpo-ecossistema-aidd.html, achados #21 e
#30, secoes 2.3 e 6). Afeta master e enterprise (arquivo duplicado - ver Itens 1 e 3).

Fatos que voce precisa saber antes de comecar:
- SecurityGate (:49): 502 linhas, 11 camadas, misturando varredura estatica + execucao
  comportamental (JWT/SQLi/XSS) + leitura de config + geracao de relatorio.
- _camada3b: cria tabela _sqli_probe num banco temporario gerenciado a mao dentro do gate -
  responsabilidade de fixture de teste embutida em codigo de producao.
- Metodos _camada1_, _camada2_, _camada2_5_, _camada8_: numero no nome ordena o que deveria
  ser uma lista explicita em run_all_checks.
- BOA PRATICA JA EXISTENTE a preservar: o relatorio final do gate ja separa resultados por
  categoria (comportamental/config/estatico) com rotulo honesto - NAO descarte isso ao
  decompor.

Regras obrigatorias:
1. Os testes comportamentais reais de JWT/SQLi/XSS sao a parte mais valiosa deste gate - a
   decomposicao NAO PODE reduzir a cobertura real desses testes para mock. Se em algum ponto
   a decomposicao parecer exigir trocar um teste comportamental real por mock para simplificar,
   PARE e pergunte antes de fazer isso.
2. Preserve a separacao de relatorio por categoria (comportamental/config/estatico) - e
   citada como boa pratica no relatorio de auditoria.
3. Siga rigorosamente a Definicao de Pronto acima.
4. Nao invente aprovacoes. So marque como concluido apos rodar os testes reais do gate de
   seguranca (incluindo os comportamentais) nas duas ferramentas.
5. Mantenha as regras de governanca do monorepo (AGENTS.md).
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 16: decompose SecurityGate (scripts/gates/G_SEGURANCA.py,
502 lines, 11 layers) and rename the _camadaN_ methods that use a number in the name only to
order execution (see docs/relatorios/relatorio-auditoria-codigo-limpo-ecossistema-aidd.html,
findings #21 and #30, sections 2.3 and 6). Affects master and enterprise (duplicated file -
see Items 1 and 3).

Facts you need before starting:
- SecurityGate (:49): 502 lines, 11 layers, mixing static scanning + real behavioral
  execution (JWT/SQLi/XSS) + config reading + report generation.
- _camada3b: creates a _sqli_probe table in a manually managed temporary database inside the
  gate - test-fixture responsibility embedded in production code.
- Methods _camada1_, _camada2_, _camada2_5_, _camada8_: a number in the name orders what
  should be an explicit list in run_all_checks.
- EXISTING GOOD PRACTICE to preserve: the gate's final report already separates results by
  category (behavioral/config/static) with honest labeling - do NOT discard this while
  decomposing.

Mandatory rules:
1. The real behavioral tests for JWT/SQLi/XSS are the most valuable part of this gate - the
   decomposition MUST NOT reduce their real coverage to mocks. If at any point the
   decomposition seems to require swapping a real behavioral test for a mock to simplify
   things, STOP and ask before doing that.
2. Preserve the report's separation by category (behavioral/config/static) - it is cited as
   good practice in the audit report.
3. Strictly follow the Definition of Done above.
4. Do not fabricate approvals. Only mark this done after running the real security gate
   tests (including the behavioral ones) on both tools.
5. Maintain monorepo governance rules (AGENTS.md).
```
