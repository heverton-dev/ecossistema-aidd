# PROCESSO E DECISOES — qualidade-testes-e-mutacao

> **Origem:** Planejamento estruturado no monorepo ecossistema-aidd.
> **Proposito deste arquivo:** Registro unico do processo e governanca desta iniciativa.
> **Aviso de Governanca:** Todos os itens comecam como rascunhos. Nenhuma aprovacao ou decisao pode ser fabricada.

---

## 1. O que este esforco busca

- **Origem:** Auditoria de Qualidade de Testes, Mutação e Determinismo registrada em `docs/relatorios/QUALIDADE-TESTES-MUTACAO-BASELINE.md` (2026-09-09).
- **Objetivo Principal:** Eliminar asserções fracas/tautológicas, erradicar `time.sleep` em testes unitários e de integração (substituindo por clock injection e polling com deadline), proteger pontos críticos contra mutantes de segurança (SHA-256 no injector) e financeiro (sizing exato), aprimorar o gate `G_TESTES_REAIS` com parsing estruturado via JUnitXML e orçamento de skipped tests, e introduzir teste de mutação (`mutmut`) nos módulos de regras exatas.
- **Limites de Escopo:**
  - Não reescreve testes funcionais existentes; aprofunda e blinda as asserções contra mutações.
  - Zero tolerância para mocks de lógica interna; mocks restritos a bordas de I/O externo.
  - Testes executados com ferramentas de mercado (pytest, mutmut) sob o princípio Anti-NIH.

## 2. Processo Adotado

Diagnostico rapido → Definicao de Pronto checavel → Prompt de Execucao autocontido (PT-BR + EN-US) → Auditoria por reproducao real → Registro do veredito.

## 3. Onde vive o conteudo tecnico

| # | Item | Documento |
|---|---|---|
| 1 | testes-conteudo-sha256-injector-enterprise | `01-testes-conteudo-sha256-injector-enterprise.md` |
| 2 | testes-exatidao-sizing-ops-fixtures-ouro | `02-testes-exatidao-sizing-ops-fixtures-ouro.md` |
| 3 | testes-resiliencia-outbox-crash-pos-emit-dead-letter | `03-testes-resiliencia-outbox-crash-pos-emit-dead-letter.md` |
| 4 | eliminar-timesleep-injetar-relogio-cqrs-polling-deadline | `04-eliminar-timesleep-injetar-relogio-cqrs-polling-deadline.md` |
| 5 | portas-efemeras-testes-integracao-servidor | `05-portas-efemeras-testes-integracao-servidor.md` |
| 6 | g-testes-reais-v2-junitxml-orcamento-skipped | `06-g-testes-reais-v2-junitxml-orcamento-skipped.md` |
| 7 | testes-contrato-rls-e-wal-pragmas | `07-testes-contrato-rls-e-wal-pragmas.md` |
| 8 | teste-contrato-sizing-para-helm-values | `08-teste-contrato-sizing-para-helm-values.md` |
| 9 | gate-g-mutacao-mutmut-regras-exatas | `09-gate-g-mutacao-mutmut-regras-exatas.md` |
| 10 | politica-warnings-pytest-deprecations | `10-politica-warnings-pytest-deprecations.md` |

## 4. Regras Fixas

1. **A skill/agente nunca decide ou aprova sozinho.** Rascunhos aguardam aprovacao explicita de pessoa real.
2. **Sem disparos autonomos:** Prompts de execucao nao devem ser enviados a subagentes sem consentimento.
3. **Sem commit/push automatico:** Commits dependem de aprovacao do usuario.
4. **Isolamento:** Testes devem ocorrer sem poluir arquivos de producao.

## 5. Registro de Progresso

| # | Item | Status | Documento |
|---|---|---|---|
| 1 | testes-conteudo-sha256-injector-enterprise | ⏳ Rascunho gerado, aguardando aprovacao | `01-testes-conteudo-sha256-injector-enterprise.md` |
| 2 | testes-exatidao-sizing-ops-fixtures-ouro | ⏳ Rascunho gerado, aguardando aprovacao | `02-testes-exatidao-sizing-ops-fixtures-ouro.md` |
| 3 | testes-resiliencia-outbox-crash-pos-emit-dead-letter | ⏳ Rascunho gerado, aguardando aprovacao | `03-testes-resiliencia-outbox-crash-pos-emit-dead-letter.md` |
| 4 | eliminar-timesleep-injetar-relogio-cqrs-polling-deadline | ⏳ Rascunho gerado, aguardando aprovacao | `04-eliminar-timesleep-injetar-relogio-cqrs-polling-deadline.md` |
| 5 | portas-efemeras-testes-integracao-servidor | ⏳ Rascunho gerado, aguardando aprovacao | `05-portas-efemeras-testes-integracao-servidor.md` |
| 6 | g-testes-reais-v2-junitxml-orcamento-skipped | ⏳ Rascunho gerado, aguardando aprovacao | `06-g-testes-reais-v2-junitxml-orcamento-skipped.md` |
| 7 | testes-contrato-rls-e-wal-pragmas | ⏳ Rascunho gerado, aguardando aprovacao | `07-testes-contrato-rls-e-wal-pragmas.md` |
| 8 | teste-contrato-sizing-para-helm-values | ⏳ Rascunho gerado, aguardando aprovacao | `08-teste-contrato-sizing-para-helm-values.md` |
| 9 | gate-g-mutacao-mutmut-regras-exatas | ⏳ Rascunho gerado, aguardando aprovacao | `09-gate-g-mutacao-mutmut-regras-exatas.md` |
| 10 | politica-warnings-pytest-deprecations | ⏳ Rascunho gerado, aguardando aprovacao | `10-politica-warnings-pytest-deprecations.md` |

Esta tabela so e atualizada para Concluido apos auditoria por reproducao real.
