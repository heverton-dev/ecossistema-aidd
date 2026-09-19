# PROCESSO E DECISOES — Testes Do Motor Orquestrador E Cobertura De Gate

> **Origem:** Planejamento estruturado no monorepo ecossistema-aidd.
> **Proposito deste arquivo:** Registro unico do processo e governanca desta iniciativa.
> **Aviso de Governanca:** Todos os itens comecam como rascunhos. Nenhuma aprovacao ou decisao pode ser fabricada.

---

## 1. O que este esforco busca

Defina aqui os objetivos claros, escopo e limites desta iniciativa.
- **Objetivo Principal:** [Descrever objetivo]
- **Limites de Escopo:** Nao inclui decisoes nao aprovadas por humano.

### Metrica da Iniciativa (0-10)

- **Nota Atual:** 3 — evidencia: pytest componentes/compartilhado/skills/orca-plan-orchestrator/tests -q = 4 failed, 113 passed (exit 1), reproduzido tambem no commit anterior
- **Nota Alvo:** 9
- **Nota Real (pos-implementacao):** [Pendente - preencher somente apos o fechamento real deste item/iniciativa, via o mesmo mecanismo que mediu a Nota Atual]

Nunca preencher Nota Atual sem evidencia real (relatorio de auditoria, comando ou
teste efetivamente rodado). Sem evidencia, o campo permanece `NAO AUDITADO`.

## 2. Processo Adotado

Diagnostico rapido → Definicao de Pronto checavel → Prompt de Execucao autocontido (PT-BR + EN-US) → Auditoria por reproducao real → Registro do veredito.

## 3. Onde vive o conteudo tecnico

| # | Item | Documento |
|---|---|---|
| 1 | Diagnosticar as 4 falhas de test_orchestrator_engine ate a causa raiz | `01-diagnosticar-4-falhas.md` |
| 2 | Corrigir o que a causa raiz apontar no motor ou nos testes | `02-corrigir-causa-raiz.md` |
| 3 | Estender G_TESTES_REAIS para cobrir tambem componentes | `03-estender-g-testes.md` |

## 4. Regras Fixas

1. **A skill/agente nunca decide ou aprova sozinho.** Rascunhos aguardam aprovacao explicita de pessoa real.
2. **Sem disparos autonomos:** Prompts de execucao nao devem ser enviados a subagentes sem consentimento.
3. **Sem commit/push automatico:** Commits dependem de aprovacao do usuario.
4. **Isolamento:** Testes devem ocorrer sem poluir arquivos de producao.

## 5. Registro de Progresso

| # | Item | Status | Nota Atual | Nota Alvo | Nota Real | Documento |
|---|---|---|---|---|---|---|
| 1 | Diagnosticar as 4 falhas de test_orchestrator_engine ate a causa raiz | ⏳ Rascunho gerado, aguardando aprovacao | 3 | 9 | [Pendente - preencher somente apos o fechamento real deste item/iniciativa, via o mesmo mecanismo que mediu a Nota Atual] | `01-diagnosticar-4-falhas.md` |
| 2 | Corrigir o que a causa raiz apontar no motor ou nos testes | ⏳ Rascunho gerado, aguardando aprovacao | NAO AUDITADO | 9 | [Pendente - preencher somente apos o fechamento real deste item/iniciativa, via o mesmo mecanismo que mediu a Nota Atual] | `02-corrigir-causa-raiz.md` |
| 3 | Estender G_TESTES_REAIS para cobrir tambem componentes | ⏳ Rascunho gerado, aguardando aprovacao | NAO AUDITADO | 9 | [Pendente - preencher somente apos o fechamento real deste item/iniciativa, via o mesmo mecanismo que mediu a Nota Atual] | `03-estender-g-testes.md` |

Esta tabela so e atualizada para Concluido apos auditoria por reproducao real.
A coluna Nota Real so e preenchida no fechamento de cada item, rodando o MESMO
mecanismo real que mediu a Nota Atual (nunca um comando "parecido").
