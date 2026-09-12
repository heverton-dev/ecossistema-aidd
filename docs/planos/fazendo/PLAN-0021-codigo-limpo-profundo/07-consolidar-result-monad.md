# Item 7 — Consolidar Result monad (4 APIs incompativeis) em torno de returns

> **Escopo:** Consolidar as 4 formas incompatíveis de representar "deu certo ou deu erro" espalhadas pelo ecossistema, usando a biblioteca `returns` (já adotada em master/enterprise/ops) como padrão único. Não entra: a API de resultado específica do domínio Injector, que é tratada dentro do Item 6 (mesmo assunto, escopo mais amplo aqui cobre qualquer uso de Result fora do Injector).
> **Status:** [EM EXECUCAO]

---

## Contexto ja investigado

Fonte: relatório de auditoria, achados #10 e #11, seção 4.1 e 8.4.

- `master`/`enterprise`/`ops` já importam `from returns` — este já é o padrão dominante do ecossistema.
- `scripts/phases/08_implementador.py:60` (generator): `class Result` **caseira de 70 linhas** (`ok/fail/unwrap/unwrap_or/map/flat_map`) reimplementando o que `returns` já oferece.
- `core/result.py` idêntico em 2 ferramentas — mais uma duplicação dentro do próprio problema de Result.
- forge: `Result` frozen (`@dataclass(frozen=True)`) com semântica `value/error` própria (ver Item 6 para o uso específico no domínio Injector).
- **N4 (achado #11):** duas classes chamadas `ResultadoValidacao` com campos completamente diferentes — `scripts/gates/G_INTEGRACAO_CROSS_SCRIPT.py:140` (`check_id/descricao/passou`) vs `scripts/core/injector/contrato.py:60` (`valido/erros/request`). Mesmo nome, dois conceitos — quem lê o nome não sabe qual dos dois está em uso sem checar o import.
- Total inventariado: **4 APIs de Result incompatíveis** no ecossistema (`returns` padrão + caseira do generator + frozen do forge + família `Resultado*` de formato próprio no generator).

## Decisao Registrada (confirmada com o usuario em 2026-09-09)

- **Result caseiro do generator (08_implementador.py):** substituir por `returns`, o padrao
  ja adotado pela maioria (master/enterprise/ops).
- **Result frozen do forge:** fica como excecao documentada, ligada a decisao do Item 6 (se
  o forge virar a base do dominio Injector, o Result frozen dele e a API dessa area
  especifica) — sujeito a mesma condicao de nao quebrar uso standalone registrada no Item 6.
- **As duas classes `ResultadoValidacao`:** NAO unificar — representam conceitos diferentes
  de verdade (uma e resultado de um check de gate: `check_id/descricao/passou`; a outra e
  resultado de validacao de uma requisicao de injecao: `valido/erros/request`). Decisao:
  renomear cada uma para um nome que descreva seu conteudo real (ex.:
  `ResultadoCheckGate` e `ResultadoValidacaoRequisicao`, ou equivalente), sem fundir os dois.

## Definicao de Pronto

1. Todo uso de `class Result` caseira (`08_implementador.py:60`) é substituído por `returns` ou removido em favor do padrão já adotado por master/enterprise/ops.
2. As duas classes `ResultadoValidacao` são renomeadas para nomes distintos que descrevem seus campos reais, ou unificadas se representarem o mesmo conceito de fato (decisão a confirmar durante a implementação, documentando qual dos dois casos se aplicou).
3. `core/result.py` duplicado entre as 2 ferramentas é resolvido dentro do escopo do Item 1 (núcleo compartilhado) — este item apenas garante que o conteúdo migrado seja consistente com `returns`.
4. Testes reais de `08_implementador.py` e dos módulos que usam `ResultadoValidacao` passam com exit 0 após a migração.
5. Rodando `grep -rn "class Result"` no repositório, sobra no máximo 1 implementação caseira documentada como intencional (ex.: o `Result` frozen do forge, se a decisão for mantê-lo por motivo específico) — nenhuma reimplementação acidental.

## Criterio de saida

- `returns` como padrão único fora dos casos documentados como exceção intencional.
- Nomes de classe únicos para conceitos distintos (`ResultadoValidacao` não pode significar duas coisas).
- Testes reais passando.

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item 7: consolidar as 4 formas incompativeis de representar "deu
certo ou deu erro" no ecossistema, usando returns (ja adotado em master/enterprise/ops) como
padrao (ver docs/relatorios/relatorio-auditoria-codigo-limpo-ecossistema-aidd.html, achados
#10 e #11, secoes 4.1 e 8.4).

Fatos que voce precisa saber antes de comecar:
- master/enterprise/ops ja usam returns - e o padrao dominante.
- scripts/phases/08_implementador.py:60 (generator): class Result caseira de 70 linhas
  (ok/fail/unwrap/unwrap_or/map/flat_map) reimplementando o que returns ja oferece.
- Duas classes chamadas ResultadoValidacao com campos diferentes: G_INTEGRACAO_CROSS_SCRIPT.py:140
  (check_id/descricao/passou) vs contrato.py:60 (valido/erros/request) - mesmo nome, dois
  conceitos.
- forge tem seu proprio Result frozen (value/error) - ver Item 6 para o uso dele no dominio
  Injector especificamente.

Regras obrigatorias:
1. JA FOI DECIDIDO (ver secao "Decisao Registrada" acima): Result caseiro do generator vira
   returns; Result frozen do forge fica como excecao documentada (sujeita a mesma condicao
   de uso standalone do Item 6 - verifique o status do Item 6 antes de mexer no Result do
   forge); as duas ResultadoValidacao NAO se fundem, cada uma recebe um nome distinto que
   descreva seu conteudo real.
2. Siga rigorosamente a Definicao de Pronto acima.
4. Nao invente aprovacoes. So marque como concluido apos rodar os testes reais de
   08_implementador.py e dos modulos que usam ResultadoValidacao.
5. Mantenha as regras de governanca do monorepo (AGENTS.md).
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 7: consolidate the 4 incompatible ways of representing
"succeeded or failed" across the ecosystem, using returns (already adopted in
master/enterprise/ops) as the standard (see
docs/relatorios/relatorio-auditoria-codigo-limpo-ecossistema-aidd.html, findings #10 and
#11, sections 4.1 and 8.4).

Facts you need before starting:
- master/enterprise/ops already use returns - it is the dominant standard.
- scripts/phases/08_implementador.py:60 (generator): a homegrown 70-line class Result
  (ok/fail/unwrap/unwrap_or/map/flat_map) reimplementing what returns already offers.
- Two classes named ResultadoValidacao with different fields:
  G_INTEGRACAO_CROSS_SCRIPT.py:140 (check_id/descricao/passou) vs contrato.py:60
  (valido/erros/request) - same name, two concepts.
- forge has its own frozen Result (value/error) - see Item 6 for its specific use in the
  Injector domain.

Mandatory rules:
1. This has ALREADY BEEN DECIDED (see "Decisao Registrada" section above): the generator's
   homegrown Result becomes returns; forge's frozen Result stays as a documented exception
   (subject to the same standalone-use condition from Item 6 - check Item 6's status before
   touching forge's Result); the two ResultadoValidacao classes do NOT merge, each gets a
   distinct name describing its real content.
2. Strictly follow the Definition of Done above.
4. Do not fabricate approvals. Only mark this done after running the real tests of
   08_implementador.py and the modules using ResultadoValidacao.
5. Maintain monorepo governance rules (AGENTS.md).
```
