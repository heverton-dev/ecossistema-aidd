# PROCESSO E DECISOES — evolucao-engenharia-software-ecossistema

> **Origem:** Planejamento estruturado no monorepo ecossistema-aidd.
> **Proposito deste arquivo:** Registro unico do processo e governanca desta iniciativa.
> **Aviso de Governanca:** Todos os itens comecam como rascunhos. Nenhuma aprovacao ou decisao pode ser fabricada.

---

## 1. O que este esforco busca

Defina aqui os objetivos claros, escopo e limites desta iniciativa.
- **Objetivo Principal:** [Descrever objetivo]
- **Limites de Escopo:** Nao inclui decisoes nao aprovadas por humano.

### Metrica da Iniciativa (0-10)

- **Nota Atual:** 8.0 — evidencia: docs/melhorias/11-09-2026_melhoria-engenharia-software-ecossistema.html
- **Nota Alvo:** 9.5
- **Nota Real (pos-implementacao):** [Pendente - preencher somente apos o fechamento real deste item/iniciativa, via o mesmo mecanismo que mediu a Nota Atual]

Nunca preencher Nota Atual sem evidencia real (relatorio de auditoria, comando ou
teste efetivamente rodado). Sem evidencia, o campo permanece `NAO AUDITADO`.

## 2. Processo Adotado

Diagnostico rapido → Definicao de Pronto checavel → Prompt de Execucao autocontido (PT-BR + EN-US) → Auditoria por reproducao real → Registro do veredito.

## 3. Onde vive o conteudo tecnico

| # | Item | Documento |
|---|---|---|
| 1 | Reativar G_ARQUITETURA_DELIVERABLE corrigindo 212 violacoes SQL-fora-infra nos templates | `01-reativar-g-arquitetura-deliverable-corrigindo-212-violacoes-sql-fora-infra-nos-templates.md` |
| 2 | Adicionar testes reais as 2 entregas sem cobertura (enterprise-suite-v4, logistica-hub-v4) | `02-adicionar-testes-reais-as-2-entregas-sem-cobertura-enterprise-suite-v4-logistica-hub-v4.md` |
| 3 | Quebrar funcoes gigantes get_swagger_html (736 linhas) e compose_suite (277/273) | `03-quebrar-funcoes-gigantes-get-swagger-html-736-linhas-e-compose-suite-277273.md` |
| 4 | Documentar e eliminar divergencia master-enterprise (3 src/core + 6 scripts + mcp/) | `04-documentar-e-eliminar-divergencia-master-enterprise-3-srccore-6-scripts-mcp.md` |
| 5 | Corrigir drift de documentacao do G_HONESTIDADE_ROTULO (AGENTS.md + termos_proibidos_marketing.json) | `05-corrigir-drift-de-documentacao-do-g-honestidade-rotulo-agentsmd-termos-proibidos-marketingjson.md` |
| 6 | Reduzir timeout do G_TESTES_REAIS no audit completo | `06-reduzir-timeout-do-g-testes-reais-no-audit-completo.md` |

## 4. Regras Fixas

1. **A skill/agente nunca decide ou aprova sozinho.** Rascunhos aguardam aprovacao explicita de pessoa real.
2. **Sem disparos autonomos:** Prompts de execucao nao devem ser enviados a subagentes sem consentimento.
3. **Sem commit/push automatico:** Commits dependem de aprovacao do usuario.
4. **Isolamento:** Testes devem ocorrer sem poluir arquivos de producao.

## 5. Registro de Progresso

| # | Item | Status | Nota Atual | Nota Alvo | Nota Real | Documento |
|---|---|---|---|---|---|---|
| 1 | Reativar G_ARQUITETURA_DELIVERABLE corrigindo 212 violacoes SQL-fora-infra nos templates | 🔒 Aprovado, aguardando execucao | 3.0 | 10.0 | [Pendente - preencher somente apos o fechamento real deste item/iniciativa, via o mesmo mecanismo que mediu a Nota Atual] | `01-reativar-g-arquitetura-deliverable-corrigindo-212-violacoes-sql-fora-infra-nos-templates.md` |
| 2 | Adicionar testes reais as 2 entregas sem cobertura (enterprise-suite-v4, logistica-hub-v4) | 🔒 Aprovado, aguardando execucao | 2.0 | 9.0 | [Pendente - preencher somente apos o fechamento real deste item/iniciativa, via o mesmo mecanismo que mediu a Nota Atual] | `02-adicionar-testes-reais-as-2-entregas-sem-cobertura-enterprise-suite-v4-logistica-hub-v4.md` |
| 3 | Quebrar funcoes gigantes get_swagger_html (736 linhas) e compose_suite (277/273) | 🔒 Aprovado, aguardando execucao | 4.0 | 8.0 | [Pendente - preencher somente apos o fechamento real deste item/iniciativa, via o mesmo mecanismo que mediu a Nota Atual] | `03-quebrar-funcoes-gigantes-get-swagger-html-736-linhas-e-compose-suite-277273.md` |
| 4 | Documentar e eliminar divergencia master-enterprise (3 src/core + 6 scripts + mcp/) | 🔒 Aprovado, aguardando execucao | 5.0 | 9.0 | [Pendente - preencher somente apos o fechamento real deste item/iniciativa, via o mesmo mecanismo que mediu a Nota Atual] | `04-documentar-e-eliminar-divergencia-master-enterprise-3-srccore-6-scripts-mcp.md` |
| 5 | Corrigir drift de documentacao do G_HONESTIDADE_ROTULO (AGENTS.md + termos_proibidos_marketing.json) | 🔒 Aprovado, aguardando execucao | 6.0 | 10.0 | [Pendente - preencher somente apos o fechamento real deste item/iniciativa, via o mesmo mecanismo que mediu a Nota Atual] | `05-corrigir-drift-de-documentacao-do-g-honestidade-rotulo-agentsmd-termos-proibidos-marketingjson.md` |
| 6 | Reduzir timeout do G_TESTES_REAIS no audit completo | 🔒 Aprovado, aguardando execucao | 5.0 | 9.0 | [Pendente - preencher somente apos o fechamento real deste item/iniciativa, via o mesmo mecanismo que mediu a Nota Atual] | `06-reduzir-timeout-do-g-testes-reais-no-audit-completo.md` |

Esta tabela so e atualizada para Concluido apos auditoria por reproducao real.
A coluna Nota Real so e preenchida no fechamento de cada item, rodando o MESMO
mecanismo real que mediu a Nota Atual (nunca um comando "parecido").
