# Item 3 — Extrair e proteger scripts-gates e templates-gates duplicados entre master e enterprise

> **Escopo:** Resolver a duplicação sem proteção em `scripts/gates/` e `templates/gates/`, entre master e enterprise, e entre `scripts/gates`/`templates/gates` dentro de cada ferramenta. Não entra: `src/core` (Item 1) nem `templates/core`/`v2` de produto (Item 2) — este item é especificamente sobre os gates de qualidade/segurança.
> **Status:** [EM EXECUCAO]

---

## Contexto ja investigado

Fonte: relatório de auditoria, achado #3 e tabela §8.1.

- `scripts/gates/` master ≡ enterprise: **10 arquivos idênticos, 1.973 linhas**.
- `templates/gates/` master ≡ enterprise: **8 arquivos idênticos, 1.083 linhas**.
- `scripts/gates/` ≡ `templates/gates/` dentro da mesma ferramenta: **6 arquivos idênticos, 575 linhas — em cada ferramenta** (ou seja, o mesmo conteúdo aparece 4 vezes só nesse par: 2 diretórios × 2 ferramentas).
- **Nenhum gate monitora esses pares hoje.** Isso é particularmente sensível porque são os próprios **gates de qualidade e segurança** que estão duplicados sem verificação — se uma correção de segurança for aplicada num gate e esquecida na cópia, o produto gerado pelo usuário final pode ficar protegido por uma versão desatualizada do próprio gate de segurança.
- Prova de custo: o Item 16 do plano 01 (XSS em `get_studio_html`) foi corrigido "nas 6 cópias" — texto literal do relatório de conclusão daquele item — o mesmo padrão de risco descrito aqui.

## Decisao Registrada (verificada tecnicamente e confirmada com o usuario em 2026-09-09)

- **Verificacao feita:** `provision_project.py:74-78` copia `templates/gates/*.py` para
  `project_dir/scripts/gates/` no momento de gerar um projeto novo para o cliente final.
  `aidd.py:345-353` (comando `cmd_audit`) le gates de `target_dir/scripts/gates` (a copia
  dentro do projeto gerado) com fallback para `tools/aidd-master/scripts/gates` (a copia da
  propria ferramenta) quando o projeto ainda nao tem gates proprios.
- **Conclusao:** a duplicacao `scripts/gates` vs `templates/gates` **nao e um erro** — sao
  papeis diferentes por design: `scripts/gates` e a fonte/copia de trabalho da propria
  ferramenta; `templates/gates` e o instantaneo de distribuicao entregue a cada projeto
  gerado. O problema real e que os dois sao mantidos a mao, podendo divergir sem aviso.
- **Decisao:** manter os dois diretorios com seus papeis atuais, mas parar de edita-los a
  mao de forma independente — `templates/gates` passa a ser **gerado mecanicamente** a
  partir de `scripts/gates` (comando/gate de sincronizacao, no mesmo espirito do mecanismo
  de sync de componentes ja usado no forge), nao mais copiado manualmente.
- **Duplicacao master vs enterprise** (scripts/gates e templates/gates identicos entre as
  duas ferramentas) resolve dentro do "almoxarifado compartilhado" do Item 1.

## Definicao de Pronto

1. Decisão registrada (humana) sobre a estratégia: fonte única de gates com sincronização mecânica para os 3 destinos (scripts/gates de cada ferramenta + templates/gates de cada ferramenta), ou no mínimo gate de drift cobrindo os 4 pares hoje sem proteção.
2. Gate de drift novo (ou `G_DRIFT_NUCLEO_COMPARTILHADO` estendido) cobrindo explicitamente `scripts/gates` × `templates/gates` × as 2 ferramentas.
3. Rodando de novo o hash MD5 desses diretórios (mesmo método do §1.3 do relatório, adaptado), o resultado bate com a cobertura do gate — nenhum arquivo fica de fora do monitoramento.
4. Suíte de testes real dos gates (os testes que já existem para master/enterprise) passa com exit 0 após a mudança.

## Criterio de saida

- Duplicação de gates protegida por sincronização mecânica ou gate de drift ativo.
- Nenhum gate de segurança/qualidade pode divergir silenciosamente entre suas 4 cópias.
- Testes reais passando.

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item 3: resolver a duplicacao sem protecao em scripts/gates/ e
templates/gates/, entre master e enterprise e dentro de cada ferramenta (ver
docs/relatorios/relatorio-auditoria-codigo-limpo-ecossistema-aidd.html, achado #3 e tabela
da secao 8.1, para evidencia completa).

Fatos que voce precisa saber antes de comecar:
- scripts/gates/ master === enterprise (10 arquivos, 1.973 linhas).
- templates/gates/ master === enterprise (8 arquivos, 1.083 linhas).
- scripts/gates === templates/gates dentro da mesma ferramenta (6 arquivos, 575 linhas, em
  cada ferramenta - o mesmo conteudo aparece 4 vezes).
- Nenhum gate monitora esses pares hoje. Sao os proprios gates de seguranca/qualidade que
  estao duplicados sem verificacao.
- O Item 16 do plano 01 corrigiu um XSS "nas 6 copias" - mesma classe de risco.

Regras obrigatorias:
1. JA FOI VERIFICADO E DECIDIDO (ver secao "Decisao Registrada" acima): scripts/gates e
   templates/gates NAO sao um erro de duplicacao - templates/gates e distribuido para cada
   projeto gerado (confirmado lendo provision_project.py e aidd.py). A correcao e gerar
   templates/gates mecanicamente a partir de scripts/gates, nunca editar os dois a mao.
2. Siga rigorosamente a Definicao de Pronto acima.
3. Nao invente aprovacoes. So marque como concluido apos rodar de novo o hash MD5 e os
   testes reais dos gates.
4. Mantenha as regras de governanca do monorepo (AGENTS.md).
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 3: resolve the unprotected duplication in scripts/gates/
and templates/gates/, between master and enterprise and within each tool (see
docs/relatorios/relatorio-auditoria-codigo-limpo-ecossistema-aidd.html, finding #3 and the
table in section 8.1, for full evidence).

Facts you need before starting:
- scripts/gates/ master === enterprise (10 files, 1,973 lines).
- templates/gates/ master === enterprise (8 files, 1,083 lines).
- scripts/gates === templates/gates within the same tool (6 files, 575 lines, in each tool -
  the same content appears 4 times).
- No gate monitors these pairs today. These are the security/quality gates themselves,
  duplicated without verification.
- Item 16 of plan 01 fixed an XSS "in the 6 copies" - same class of risk.

Mandatory rules:
1. This has ALREADY BEEN VERIFIED AND DECIDED (see "Decisao Registrada" section above):
   scripts/gates and templates/gates are NOT a duplication mistake - templates/gates is
   distributed to every generated project (confirmed by reading provision_project.py and
   aidd.py). The fix is to mechanically generate templates/gates from scripts/gates, never
   hand-edit both.
2. Strictly follow the Definition of Done above.
3. Do not fabricate approvals. Only mark this done after re-running the MD5 hash and the
   real gate tests.
4. Maintain monorepo governance rules (AGENTS.md).
```
