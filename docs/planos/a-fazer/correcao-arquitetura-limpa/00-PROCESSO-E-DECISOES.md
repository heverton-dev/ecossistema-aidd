# PROCESSO E DECISOES — correcao-arquitetura-limpa

> **Origem:** Planejamento estruturado no monorepo ecossistema-aidd.
> **Proposito deste arquivo:** Registro unico do processo e governanca desta iniciativa.
> **Aviso de Governanca:** Todos os itens comecam como rascunhos. Nenhuma aprovacao ou decisao pode ser fabricada.

---

## 1. O que este esforco busca

- **Origem:** análise arquitetural pedida pelo usuário em 2026-09-08, feita via `code-review-graph` (`get_architecture_overview`, `list_communities`, `get_hub_nodes`, `find_large_functions`, `get_surprising_connections`) sobre o crescimento do monorepo. Achados aprovados pelo usuário para virar plano formal.
- **Objetivo Principal:** corrigir 4 achados concretos de organização de código (função gigante com HTML embutido, ponto cego no monitoramento de duplicação, um achado só de registro, e execução redundante de teste) — não é uma reescrita nem uma reestruturação de pastas.
- **Limites de Escopo:** não inclui decisões não aprovadas por humano; não inclui reescrever nenhuma ferramenta do zero; não inclui unificar `aidd-generator`'s fleet discovery com o schema de `aidd-master`/`aidd-enterprise` (decisão separada, já registrada em `docs/planos/feitos/.../06-fase-4...md`).

## 2. Processo Adotado

Diagnostico rapido → Definicao de Pronto checavel → Prompt de Execucao autocontido (PT-BR + EN-US) → Auditoria por reproducao real → Registro do veredito.

## 3. Onde vive o conteudo tecnico

| # | Item | Documento |
|---|---|---|
| 1 | Extrair HTML embutido gigante para arquivo proprio (get_swagger_html e get_studio_html) | `01-extrair-html-embutido-gigante-para-arquivo-proprio-get-swagger-html-e-get-studio-html.md` |
| 2 | Ampliar G_DRIFT_NUCLEO_COMPARTILHADO para cobrir outros pares duplicados entre aidd-master e aidd-enterprise | `02-ampliar-g-drift-nucleo-compartilhado-para-cobrir-outros-pares-duplicados-entre-aidd-master-e-aidd-enterprise.md` |
| 3 | Registrar duplicacao de codigo real da skill orca-plan-orchestrator nas 7 pastas de harness (sem acao corretiva) | `03-registrar-duplicacao-de-codigo-real-da-skill-orca-plan-orchestrator-nas-7-pastas-de-harness-sem-acao-corretiva.md` |
| 4 | Eliminar execucao redundante de suite de teste de skills materializadas 7x | `04-eliminar-execucao-redundante-de-suite-de-teste-de-skills-materializadas-7x.md` |

## 4. Regras Fixas

1. **A skill/agente nunca decide ou aprova sozinho.** Rascunhos aguardam aprovacao explicita de pessoa real.
2. **Sem disparos autonomos:** Prompts de execucao nao devem ser enviados a subagentes sem consentimento.
3. **Sem commit/push automatico:** Commits dependem de aprovacao do usuario.
4. **Isolamento:** Testes devem ocorrer sem poluir arquivos de producao.
5. **Nenhum acoplamento de runtime entre ferramentas (regra específica desta iniciativa):** nenhuma correção pode fazer `tools/aidd-*` importar código de outro `tools/aidd-*` em tempo de execução, nem quebrar a premissa de "cada ferramenta roda sozinha, standalone" — mesmo quando o achado é duplicação de código entre ferramentas (itens 1 e 2 abaixo lidam exatamente com isso). Consolidação, quando fizer sentido, é via fonte única em `componentes/` + materialização física (mesmo padrão já usado para skills/commands), nunca via import cruzado. Motivo: essas ferramentas também são mantidas como repositórios standalone independentes (backport para `proj_aidd`), e uma dependência de runtime quebraria esse fluxo.

## 5. Registro de Progresso

| # | Item | Status | Documento |
|---|---|---|---|
| 1 | Extrair HTML embutido gigante para arquivo proprio (get_swagger_html e get_studio_html) | ⏳ Rascunho gerado, aguardando aprovacao | `01-extrair-html-embutido-gigante-para-arquivo-proprio-get-swagger-html-e-get-studio-html.md` |
| 2 | Ampliar G_DRIFT_NUCLEO_COMPARTILHADO para cobrir outros pares duplicados entre aidd-master e aidd-enterprise | ⏳ Rascunho gerado, aguardando aprovacao | `02-ampliar-g-drift-nucleo-compartilhado-para-cobrir-outros-pares-duplicados-entre-aidd-master-e-aidd-enterprise.md` |
| 3 | Registrar duplicacao de codigo real da skill orca-plan-orchestrator nas 7 pastas de harness (sem acao corretiva) | ⏳ Rascunho gerado, aguardando aprovacao | `03-registrar-duplicacao-de-codigo-real-da-skill-orca-plan-orchestrator-nas-7-pastas-de-harness-sem-acao-corretiva.md` |
| 4 | Eliminar execucao redundante de suite de teste de skills materializadas 7x | ⏳ Rascunho gerado, aguardando aprovacao | `04-eliminar-execucao-redundante-de-suite-de-teste-de-skills-materializadas-7x.md` |

Esta tabela so e atualizada para Concluido apos auditoria por reproducao real.
