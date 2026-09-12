# Item 6 — Unificar as 4 implementacoes paralelas do dominio Injector (forge-generator-master-enterprise)

> **Escopo:** Unificar as 4 implementações independentes do domínio "injetar componente" — uma em cada ferramenta (forge, generator, master, enterprise) — que hoje têm 4 APIs de resultado incompatíveis, nomes de conceito diferentes para a mesma coisa, e reimplementam o mesmo algoritmo de rollback. Não entra: a unificação genérica de Result monad fora do escopo do Injector (Item 7, tratado separadamente por atravessar mais código que só o injector).
> **Status:** [EM EXECUCAO]

---

## Contexto ja investigado

Fonte: relatório de auditoria, achado #7 e seção 8.3 (tabela comparativa completa).

| Ferramenta | Arquivos | API de resultado | Nome do "Request" |
|---|---|---|---|
| forge | `aidd_forge/core/{materializador,universal_injector,injection_schema,injector_profiles}.py` | `Result` frozen `value/error` + `MaterializationResult` + `UniversalInjectionResult` | `InjectionRequest` |
| generator | `scripts/core/injector/{materializador,injetor,contrato,detector_camada,sincronizador_harness,profiles_registry}.py` | `ResultadoMaterializacao` (`sucesso/erro`) | `InjectorRequest` |
| master | `src/core/{materializador,profiles_registry,detector_camada,sincronizador_harness}.py` | `Result.ok/fail(codigo, erro, detalhes)` | `payload dict + construir_request` |
| enterprise | clone do master + perfis próprios | idem master | idem master |

- Algoritmo de rollback **idêntico** (staging → publicar com `os.replace` → desfazer publicado) reimplementado nas 4 ferramentas.
- `_default_ecossistema_root()` com o **mesmo corpo** em 3 ferramentas.
- Detecção de camada com assinaturas diferentes: `detectar_camada` (forge/master/enterprise) vs `detectar_tipo` (generator).
- **N4 puro (nomenclatura):** `InjectionRequest` (forge) vs `InjectorRequest` (generator) — mesmo conceito, nome quase igual mas não idêntico, o que engana quem lê rápido.
- Avaliação do relatório: a implementação do **forge é a mais limpa das quatro** (funções de 4–67 linhas, `Result` congelado, testes sem mock) — o relatório sugere que ela é a candidata natural a virar a fonte única, mas isso é uma recomendação, não uma decisão fechada.
- Assinatura divergente adicional (achado #23, relacionado): o materializador do generator usa função solta `materializar(root, arquivos, force)` em vez de método de classe como as outras 3 ferramentas — mesma operação, forma de chamar diferente. Considerar corrigir junto, já que é o mesmo domínio.

## Decisao Registrada (confirmada com o usuario em 2026-09-09, com condicao)

- **Decisao:** a implementacao do domínio Injector do `forge` (avaliada pelo relatorio como
  a mais limpa das 4) vira a base da versao unica, extraida para o "almoxarifado
  compartilhado" do Item 1 — nao como uma dependencia direta de "generator/master/enterprise
  importam do forge", e sim como um pacote comum que as 4 ferramentas (incluindo o proprio
  forge) consomem igualmente.
- **Condicao explicita do usuario:** só prosseguir se isso **não quebrar o uso individual de
  cada ferramenta** (cada ferramenta continua instalavel/executavel sozinha, sem precisar
  arrastar as outras 3 como dependencia). Isso está alinhado com a diretriz anti-NIH/anti-
  lock-in já registrada em `docs/planos/fazendo/02-direcionamento-estrategico-anti-nih/`.
- Se ao implementar ficar claro que extrair pro almoxarifado exigiria que uma ferramenta
  dependesse fisicamente da outra (em vez de as 4 dependerem so do almoxarifado comum), a
  condicao do usuario NAO esta satisfeita — nesse caso, pare e reporte o impasse em vez de
  prosseguir.

## Definicao de Pronto

1. Decisão registrada (humana) sobre a estratégia: uma única implementação do domínio Injector é extraída (com a versão do forge como candidata avaliada, não assumida), OU as 4 implementações continuam existindo mas com uma API de resultado, nomes de conceito e assinatura de chamada unificados.
2. `InjectionRequest`/`InjectorRequest`/`payload dict` convergem para um único nome e uma única forma de representar a requisição de injeção.
3. O algoritmo de rollback (staging → publicar → desfazer) existe em um único lugar, consumido pelas 4 ferramentas — não 4 reimplementações.
4. `materializar()` (generator) e as chamadas equivalentes nas outras 3 ferramentas usam a mesma convenção de chamada (função solta OU método de classe, não uma mistura).
5. Testes reais de injeção de componente (os 19 testes do forge, mais os testes equivalentes de generator/master/enterprise) passam com exit 0 após a unificação.

## Criterio de saida

- Uma implementação (ou uma API unificada sobre implementações que restarem) do domínio Injector, sem nomes divergentes para o mesmo conceito.
- Rollback implementado uma vez, reusado 4 vezes.
- Testes reais das 4 ferramentas passando.

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item 6: unificar as 4 implementacoes paralelas do dominio "injetar
componente" (forge, generator, master, enterprise) - 4 APIs de resultado incompativeis,
nomes diferentes pro mesmo conceito, mesmo algoritmo de rollback reimplementado (ver
docs/relatorios/relatorio-auditoria-codigo-limpo-ecossistema-aidd.html, achado #7 e tabela
completa da secao 8.3).

Fatos que voce precisa saber antes de comecar:
- forge: Result frozen value/error + MaterializationResult + UniversalInjectionResult,
  request chamado InjectionRequest.
- generator: ResultadoMaterializacao (sucesso/erro), request chamado InjectorRequest,
  materializador e funcao solta (nao metodo de classe, diferente das outras 3).
- master/enterprise: Result.ok/fail(codigo, erro, detalhes), request e um payload dict +
  construir_request.
- Algoritmo de rollback (staging -> publicar via os.replace -> desfazer) e IDENTICO nas 4,
  so reimplementado 4 vezes.
- _default_ecossistema_root() tem o mesmo corpo em 3 ferramentas.
- O relatorio avalia a implementacao do forge como a mais limpa das 4 (funcoes de 4-67
  linhas, Result congelado, testes sem mock) - isso e uma AVALIACAO, nao uma decisao ja
  tomada de que o forge vira a fonte.

Regras obrigatorias:
1. JA FOI DECIDIDO (ver secao "Decisao Registrada" acima), COM UMA CONDICAO OBRIGATORIA:
   a implementacao do forge vira a base, extraida para o almoxarifado compartilhado do Item
   1 - MAS somente se isso nao quebrar o uso individual/standalone de cada ferramenta. Antes
   de declarar este item concluido, teste explicitamente que generator, master e enterprise
   continuam instalaveis e executaveis sozinhos (sem depender fisicamente do pacote do
   forge, e sim do almoxarifado compartilhado). Se isso nao for possivel tecnicamente sem
   quebrar o uso standalone, PARE e reporte o impasse em vez de forcar a unificacao.
2. Siga rigorosamente a Definicao de Pronto acima.
3. Nao invente aprovacoes. So marque como concluido apos rodar os testes reais das 4
   ferramentas (incluindo os 19 testes de injecao do forge, sem mock) E confirmar o uso
   standalone de cada uma.
4. Mantenha as regras de governanca do monorepo (AGENTS.md).
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 6: unify the 4 parallel implementations of the "inject
component" domain (forge, generator, master, enterprise) - 4 incompatible result APIs,
different names for the same concept, the same rollback algorithm reimplemented (see
docs/relatorios/relatorio-auditoria-codigo-limpo-ecossistema-aidd.html, finding #7 and the
full table in section 8.3).

Facts you need before starting:
- forge: frozen Result value/error + MaterializationResult + UniversalInjectionResult,
  request called InjectionRequest.
- generator: ResultadoMaterializacao (sucesso/erro), request called InjectorRequest,
  materializador is a loose function (not a class method, unlike the other 3).
- master/enterprise: Result.ok/fail(codigo, erro, detalhes), request is a payload dict +
  construir_request.
- Rollback algorithm (staging -> publish via os.replace -> undo) is IDENTICAL across all 4,
  just reimplemented 4 times.
- _default_ecossistema_root() has the same body in 3 tools.
- The report evaluates forge's implementation as the cleanest of the 4 (4-67 line functions,
  frozen Result, mock-free tests) - this is an ASSESSMENT, not an already-made decision that
  forge becomes the source.

Mandatory rules:
1. This has ALREADY BEEN DECIDED (see "Decisao Registrada" section above), WITH A MANDATORY
   CONDITION: forge's implementation becomes the base, extracted into Item 1's shared
   package - BUT only if that does not break each tool's standalone use. Before declaring
   this item done, explicitly test that generator, master and enterprise remain installable
   and runnable on their own (depending on the shared package, not physically on forge's
   package). If that is not technically possible without breaking standalone use, STOP and
   report the impasse instead of forcing the unification.
2. Strictly follow the Definition of Done above.
3. Do not fabricate approvals. Only mark this done after running the real tests of all 4
   tools (including forge's 19 injection tests, mock-free) AND confirming each tool's
   standalone use.
4. Maintain monorepo governance rules (AGENTS.md).
```
