# PROCESSO E DECISOES — reestruturacao-ddd-clean-architecture

> **Origem:** Planejamento estruturado no monorepo ecossistema-aidd.
> **Proposito deste arquivo:** Registro unico do processo e governanca desta iniciativa.
> **Aviso de Governanca:** Todos os itens comecam como rascunhos. Nenhuma aprovacao ou decisao pode ser fabricada.

---

## 1. O que este esforco busca

- **Origem:** Auditoria arquitetural profunda bidimensional registrada em `ARQUITETURA-BASELINE-DDD-CLEAN.md` (2026-09-09).
- **Objetivo Principal:** Reestruturar tanto o motor interno (Engines de `ecossistema.py` e `tools/aidd-*`) quanto os artefatos e softwares gerados (Deliverables) sob os preceitos canônicos de Clean Architecture (Robert C. Martin) e Domain-Driven Design (Eric Evans, Vaughn Vernon). Eliminar modelos anêmicos, acoplamento de SQL em services de negócio, duplicidade de orquestradores e manipulações de sys.path.
- **Limites de Escopo:**
  - Respeito estrito à Regra #6 e #7: Zero cross-tool runtime imports (cada ferramenta permanece 100% standalone e desacoplada).
  - Toda evolução é comprovada por Quality Gates binários (exit 0 / exit 1).
  - Nenhuma decisão técnica é fabricada sem aprovação humana.

## 2. Processo Adotado

Diagnostico rapido → Definicao de Pronto checavel → Prompt de Execucao autocontido (PT-BR + EN-US) → Auditoria por reproducao real → Registro do veredito.

## 3. Onde vive o conteudo tecnico

| # | Item | Documento |
|---|---|---|
| 1 | fechar-nucleo-compartilhado-e-honestidade-rotulos | `01-fechar-nucleo-compartilhado-e-honestidade-rotulos.md` |
| 2 | unificar-orquestradores-generator-e-ops | `02-unificar-orquestradores-generator-e-ops.md` |
| 3 | extrair-camada-aplicacao-dos-clis-master-enterprise | `03-extrair-camada-aplicacao-dos-clis-master-enterprise.md` |
| 4 | remover-hacks-syspath-no-generator | `04-remover-hacks-syspath-no-generator.md` |
| 5 | contrato-formal-schema-ops-para-master-enterprise | `05-contrato-formal-schema-ops-para-master-enterprise.md` |
| 6 | novo-molde-fatia-vertical-ddd-clean-master | `06-novo-molde-fatia-vertical-ddd-clean-master.md` |
| 7 | gate-g-arquitetura-deliverable | `07-gate-g-arquitetura-deliverable.md` |
| 8 | atualizar-scaffolders-master-enterprise-cookiecutter | `08-atualizar-scaffolders-master-enterprise-cookiecutter.md` |
| 9 | trazer-deliverables-generator-perimetro-gates | `09-trazer-deliverables-generator-perimetro-gates.md` |
| 10 | teste-integracao-helm-aidd-ops | `10-teste-integracao-helm-aidd-ops.md` |

## 4. Regras Fixas

1. **A skill/agente nunca decide ou aprova sozinho.** Rascunhos aguardam aprovacao explicita de pessoa real.
2. **Sem disparos autonomos:** Prompts de execucao nao devem ser enviados a subagentes sem consentimento.
3. **Sem commit/push automatico:** Commits dependem de aprovacao do usuario.
4. **Isolamento:** Testes devem ocorrer sem poluir arquivos de producao.

## 5. Registro de Progresso

| # | Item | Status | Documento |
|---|---|---|---|
| 1 | fechar-nucleo-compartilhado-e-honestidade-rotulos | ⏳ Rascunho gerado, aguardando aprovacao | `01-fechar-nucleo-compartilhado-e-honestidade-rotulos.md` |
| 2 | unificar-orquestradores-generator-e-ops | ⏳ Rascunho gerado, aguardando aprovacao | `02-unificar-orquestradores-generator-e-ops.md` |
| 3 | extrair-camada-aplicacao-dos-clis-master-enterprise | ⏳ Rascunho gerado, aguardando aprovacao | `03-extrair-camada-aplicacao-dos-clis-master-enterprise.md` |
| 4 | remover-hacks-syspath-no-generator | ⏳ Rascunho gerado, aguardando aprovacao | `04-remover-hacks-syspath-no-generator.md` |
| 5 | contrato-formal-schema-ops-para-master-enterprise | ⏳ Rascunho gerado, aguardando aprovacao | `05-contrato-formal-schema-ops-para-master-enterprise.md` |
| 6 | novo-molde-fatia-vertical-ddd-clean-master | ⏳ Rascunho gerado, aguardando aprovacao | `06-novo-molde-fatia-vertical-ddd-clean-master.md` |
| 7 | gate-g-arquitetura-deliverable | ⏳ Rascunho gerado, aguardando aprovacao | `07-gate-g-arquitetura-deliverable.md` |
| 8 | atualizar-scaffolders-master-enterprise-cookiecutter | ⏳ Rascunho gerado, aguardando aprovacao | `08-atualizar-scaffolders-master-enterprise-cookiecutter.md` |
| 9 | trazer-deliverables-generator-perimetro-gates | ⏳ Rascunho gerado, aguardando aprovacao | `09-trazer-deliverables-generator-perimetro-gates.md` |
| 10 | teste-integracao-helm-aidd-ops | ⏳ Rascunho gerado, aguardando aprovacao | `10-teste-integracao-helm-aidd-ops.md` |

Esta tabela so e atualizada para Concluido apos auditoria por reproducao real.
