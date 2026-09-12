# Item 17 — Polimento estrutural: materializador do generator, idioma try-except-import duplicado, sys.path fragil no ops, funcoes sem decomposicao no ops

> **Escopo:** 4 achados menores, de ferramentas diferentes, agrupados por serem polimento estrutural de baixo risco: (a) assinatura divergente do materializador do generator; (b) idioma `try/except ImportError` duplicado em `aidd.py`; (c) `sys.path.insert` frágil no `pipeline_ops.py`; (d) funções sem decomposição no `ops`.
> **Status:** [EM EXECUCAO]

---

## Contexto ja investigado

Fonte: relatório de auditoria, achados #23, #26, #28 e #32.

**(a) Assinatura divergente do materializador (#23):** `scripts/core/injector/materializador.py:47` (generator) expõe uma **função solta** `materializar(root, arquivos, force)`, enquanto forge/master/enterprise expõem a mesma operação como **método de classe**. Mesma operação de domínio, duas formas de chamar — relacionado ao Item 6 (unificação do Injector), mas registrado aqui separadamente porque pode ser corrigido independente da decisão maior de unificação.

**(b) Idioma try/except-import duplicado (#26):** em `scripts/aidd.py` (master/enterprise), o padrão `try: from compose_suite import ... except ImportError: from scripts.compose_suite import ...` se repete em **5+ pontos** da CLI (`cmd_init`, `cmd_compose`, `cmd_add_module`, `cmd_apply`, `cmd_export_frontend`, `cmd_scaffold_infra`). Na prática, as duas rotas de import resolvem o mesmo arquivo — o padrão carrega um pressuposto de "dois layouts possíveis" que não corresponde à realidade atual do projeto.

**(c) `sys.path.insert` frágil no ops (#28):** `scripts/pipeline_ops.py:20–34` tem **4 `sys.path.insert`** no topo do arquivo, mais importação dinâmica de fases por nome de arquivo (`import_module("01_intake")`) — acopla a ferramenta ao layout físico de diretórios e a nomes de arquivo que começam com dígito (um detalhe frágil: nomes de módulo Python normalmente não podem começar com dígito, então isso depende de um mecanismo especial de import).

**(d) Funções sem decomposição no ops (#32):** `src/core/uptime_kuma.py:89` — `extrair_monitores_de_compose_conteudo` (100 linhas: parsing de YAML → identificação de serviços → geração de monitores, tudo num corpo só); `src/core/ssh_runner.py:190` — `_executar_playbook` (69 linhas: montagem de comando + execução + parsing de saída + construção do Result, tudo junto).

## Definicao de Pronto

1. **(a)** O Item 6 já decidiu que a implementação do forge (método de classe) vira a base do domínio Injector — se o Item 6 já estiver concluído, este subitem já está resolvido automaticamente (verificar antes de duplicar esforço). Se o Item 6 ainda não tiver rodado, ajustar `materializar()` do generator para a mesma convenção de chamada (método de classe) das outras 3 ferramentas, como correção isolada e reversível quando o Item 6 for executado depois.
2. **(b)** O idioma try/except-import duplicado é substituído por um único ponto de import (ou confirma-se, com teste real, que os dois layouts realmente coexistem — e nesse caso o padrão é documentado como intencional, não apenas repetido sem explicação).
3. **(c)** Os 4 `sys.path.insert` de `pipeline_ops.py` são substituídos por importação baseada em pacote empacotado (namespace/`pyproject.toml`), eliminando a dependência do layout físico de diretórios — ou, se o empacotamento completo não for viável neste item, ao menos centralizados num único ponto documentado (não repetidos).
4. **(d)** `extrair_monitores_de_compose_conteudo` e `_executar_playbook` decompostas em funções menores com responsabilidade única cada.
5. Testes reais das 3 ferramentas afetadas (generator, master/enterprise, ops) passam com exit 0 após as mudanças.

## Criterio de saida

- Os 4 achados corrigidos ou documentados como intencionais com justificativa.
- Testes reais passando nas ferramentas afetadas.

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item 17: 4 achados menores de polimento estrutural (ver
docs/relatorios/relatorio-auditoria-codigo-limpo-ecossistema-aidd.html, achados #23, #26,
#28 e #32).

Fatos que voce precisa saber antes de comecar:
(a) scripts/core/injector/materializador.py:47 (generator): funcao solta materializar(root,
    arquivos, force), diferente das outras 3 ferramentas que usam metodo de classe.
(b) scripts/aidd.py (master/enterprise): try/except ImportError duplicado em 5+ pontos
    (cmd_init, cmd_compose, cmd_add_module, cmd_apply, cmd_export_frontend,
    cmd_scaffold_infra) - as duas rotas resolvem o mesmo arquivo na pratica.
(c) scripts/pipeline_ops.py:20-34 (ops): 4 sys.path.insert + import_module("01_intake") -
    acopla ao layout fisico e a nomes de arquivo com digito.
(d) src/core/uptime_kuma.py:89 (ops): extrair_monitores_de_compose_conteudo, 100 linhas sem
    decomposicao. src/core/ssh_runner.py:190: _executar_playbook, 69 linhas sem decomposicao.

Regras obrigatorias:
1. Item (a) tem relacao direta com o Item 6 (unificacao do Injector) - verifique se o Item 6
   ja foi concluido antes de comecar, para nao duplicar esforco ou entrar em conflito com a
   decisao arquitetural la tomada.
2. Item (c): se o empacotamento completo (pyproject/namespace) parecer grande demais para
   este item, documente isso e faca a correcao minima (centralizar os inserts), sem tentar
   reescrever a estrutura de pastas do ops sem aprovacao - isso seria uma mudanca maior que
   o escopo aqui.
3. Siga rigorosamente a Definicao de Pronto acima.
4. Nao invente aprovacoes. So marque como concluido apos rodar os testes reais das 3
   ferramentas afetadas.
5. Mantenha as regras de governanca do monorepo (AGENTS.md).
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 17: 4 minor structural-polish findings (see
docs/relatorios/relatorio-auditoria-codigo-limpo-ecossistema-aidd.html, findings #23, #26,
#28 and #32).

Facts you need before starting:
(a) scripts/core/injector/materializador.py:47 (generator): a loose function
    materializar(root, arquivos, force), unlike the other 3 tools which use a class method.
(b) scripts/aidd.py (master/enterprise): duplicated try/except ImportError in 5+ places
    (cmd_init, cmd_compose, cmd_add_module, cmd_apply, cmd_export_frontend,
    cmd_scaffold_infra) - both routes resolve the same file in practice.
(c) scripts/pipeline_ops.py:20-34 (ops): 4 sys.path.insert + import_module("01_intake") -
    couples the tool to the physical directory layout and to file names starting with a
    digit.
(d) src/core/uptime_kuma.py:89 (ops): extrair_monitores_de_compose_conteudo, 100 lines with
    no decomposition. src/core/ssh_runner.py:190: _executar_playbook, 69 lines with no
    decomposition.

Mandatory rules:
1. Item (a) directly relates to Item 6 (Injector unification) - check whether Item 6 has
   already been completed before starting, to avoid duplicating effort or conflicting with
   the architectural decision made there.
2. Item (c): if full packaging (pyproject/namespace) seems too large for this item, document
   that and make the minimal fix (centralize the inserts), without attempting to rewrite the
   ops folder structure without approval - that would be a larger change than this scope.
3. Strictly follow the Definition of Done above.
4. Do not fabricate approvals. Only mark this done after running the real tests of the 3
   affected tools.
5. Maintain monorepo governance rules (AGENTS.md).
```
