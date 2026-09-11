# Item 15 — Corrigir violacao de Lei de Demeter em database.py e unificar reescrita SQL (AST vs regex)

> **Escopo:** Corrigir o acesso "por baixo do pano" ao driver de banco em `src/core/database.py` (`EngineFacadeConnection`) e unificar as duas técnicas diferentes de reescrita de SQL (AST via `sqlglot` para INSERT/SELECT, regex para UPDATE/DELETE) no mesmo módulo. Este item afeta master e enterprise (arquivo duplicado — ver Item 1).
> **Status:** [RASCUNHO — Aguardando Aprovacao Humana]

---

## Contexto ja investigado

Fonte: relatório de auditoria, achado #20, seção 5.4.

- `EngineFacadeConnection.__init__` (`src/core/database.py:119`): faz `driver = sqlalchemy_conn.connection.driver_connection` — **acesso de 3 níveis** — e ainda **muta** `driver.row_factory = sqlite3.Row` diretamente, ou seja, a fachada (`facade`) do banco entra no driver DBAPI por baixo do SQLAlchemy e o altera, violando o propósito da própria fachada (esconder o driver de quem consome).
- **Contraste interno no mesmo arquivo:** `PostgresCursorProxy` encapsula o acesso ao driver **sem** violar Lei de Demeter — ou seja, o próprio arquivo já tem o padrão correto ao lado do incorreto, o que é evidência de que a correção é viável sem redesenhar tudo.
- **Inconsistência adicional no mesmo módulo (achado relacionado, seção 5.4):** duas técnicas diferentes de reescrita de SQL convivem no arquivo — `_rewrite_insert`/`_rewrite_select` usam AST via `sqlglot`, enquanto `_rewrite_update`/`_rewrite_delete` usam regex. A versão por regex **re-deriva o nome da tabela via string matching**, quando a versão AST já teria essa informação estruturada — abordagem inconsistente para o mesmo tipo de problema dentro do mesmo arquivo.
- Nota do relatório: a arquitetura geral de fachada (adapter por `DATABASE_URL`, RLS separado, tradução DDL) é avaliada como **boa** — o problema é pontual (o acesso de 3 níveis + a inconsistência AST/regex), não estrutural no arquivo todo.

## Definicao de Pronto

1. `EngineFacadeConnection.__init__` não acessa mais `sqlalchemy_conn.connection.driver_connection` diretamente — o acesso ao driver é encapsulado da mesma forma que `PostgresCursorProxy` já faz no mesmo arquivo (usado como referência de padrão correto já existente).
2. `_rewrite_update`/`_rewrite_delete` passam a usar a mesma técnica AST via `sqlglot` que `_rewrite_insert`/`_rewrite_select` já usam, eliminando a re-derivação do nome da tabela por regex quando a informação já está disponível estruturalmente.
3. Testes reais de banco de dados (rollback transacional, RLS multi-tenant ponta-a-ponta, os testes que o relatório já verificou como comportamentais e reais em master/enterprise) continuam passando com exit 0 após a mudança — nenhuma regressão na camada de dados, que é área de alto risco.
4. Aplicado nas duas ferramentas (master e enterprise), já que o arquivo é duplicado (ver Item 1) — ou a correção é feita uma vez na fonte única, se o Item 1 já tiver sido concluído antes deste.

## Criterio de saida

- Acesso ao driver encapsulado sem violar Lei de Demeter.
- Reescrita de SQL consistente (AST em todos os casos, sem regex re-derivando o que a AST já sabe).
- Testes reais de banco passando, sem regressão.

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item 15: corrigir o acesso de 3 niveis ao driver de banco em
src/core/database.py (EngineFacadeConnection) e unificar a reescrita de SQL (AST vs regex)
no mesmo arquivo (ver docs/relatorios/relatorio-auditoria-codigo-limpo-ecossistema-aidd.html,
achado #20, secao 5.4). Afeta master e enterprise - verifique primeiro se o Item 1 (nucleo
compartilhado) ja foi concluido, porque isso muda onde a correcao deve ser aplicada (fonte
unica vs 2 copias).

Fatos que voce precisa saber antes de comecar:
- EngineFacadeConnection.__init__ (:119): driver = sqlalchemy_conn.connection.driver_connection
  (3 niveis), depois muta driver.row_factory = sqlite3.Row - a fachada entra no driver DBAPI
  por baixo do SQLAlchemy.
- Contraste no MESMO arquivo: PostgresCursorProxy ja encapsula sem violar - use como
  referencia de padrao correto.
- _rewrite_insert/_rewrite_select usam AST via sqlglot; _rewrite_update/_rewrite_delete usam
  regex e re-derivam o nome da tabela por string matching quando a AST ja teria essa
  informacao.
- A arquitetura geral do arquivo (fachada por DATABASE_URL, RLS separado) e avaliada como
  boa - o problema e pontual, nao estrutural.

Regras obrigatorias:
1. Esta e uma area de ALTO RISCO (camada de dados, RLS multi-tenant, rollback transacional).
   Nao faca a mudanca sem rodar a suite completa de testes de banco antes e depois - se
   qualquer teste comportamental real quebrar, PARE e investigue antes de prosseguir, nao
   ajuste o teste para passar.
2. Ao unificar a reescrita de SQL para AST, confirme que o comportamento de UPDATE/DELETE
   nao muda para nenhum caso ja coberto por teste real.
3. Siga rigorosamente a Definicao de Pronto acima.
4. Nao invente aprovacoes. So marque como concluido apos rodar os testes reais de banco
   (rollback, RLS) nas ferramentas afetadas.
5. Mantenha as regras de governanca do monorepo (AGENTS.md).
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 15: fix the 3-level database driver access in
src/core/database.py (EngineFacadeConnection) and unify the SQL rewriting (AST vs regex) in
the same file (see docs/relatorios/relatorio-auditoria-codigo-limpo-ecossistema-aidd.html,
finding #20, section 5.4). Affects master and enterprise - check first whether Item 1
(shared core) has already been completed, since that changes where the fix should be applied
(single source vs 2 copies).

Facts you need before starting:
- EngineFacadeConnection.__init__ (:119): driver = sqlalchemy_conn.connection.driver_connection
  (3 levels), then mutates driver.row_factory = sqlite3.Row - the facade reaches into the
  DBAPI driver underneath SQLAlchemy.
- Contrast in the SAME file: PostgresCursorProxy already encapsulates without violating it -
  use it as the reference for the correct pattern.
- _rewrite_insert/_rewrite_select use AST via sqlglot; _rewrite_update/_rewrite_delete use
  regex and re-derive the table name via string matching when the AST would already have
  that information.
- The file's overall architecture (facade by DATABASE_URL, separate RLS) is assessed as good
  - the problem is localized, not structural across the whole file.

Mandatory rules:
1. This is a HIGH-RISK area (data layer, multi-tenant RLS, transactional rollback). Do not
   make the change without running the full database test suite before and after - if any
   real behavioral test breaks, STOP and investigate before proceeding, do not adjust the
   test to pass.
2. When unifying SQL rewriting to AST, confirm UPDATE/DELETE behavior does not change for any
   case already covered by a real test.
3. Strictly follow the Definition of Done above.
4. Do not fabricate approvals. Only mark this done after running the real database tests
   (rollback, RLS) on the affected tools.
5. Maintain monorepo governance rules (AGENTS.md).
```
