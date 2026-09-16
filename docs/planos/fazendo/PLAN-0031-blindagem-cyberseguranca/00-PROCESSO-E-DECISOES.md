# PROCESSO E DECISOES — blindagem-cyberseguranca

> **Origem:** Planejamento estruturado no monorepo ecossistema-aidd.
> **Proposito deste arquivo:** Registro unico do processo e governanca desta iniciativa.
> **Aviso de Governanca:** Todos os itens comecam como rascunhos. Nenhuma aprovacao ou decisao pode ser fabricada.

---

## 1. O que este esforco busca

Defina aqui os objetivos claros, escopo e limites desta iniciativa.
- **Objetivo Principal:** [Descrever objetivo]
- **Limites de Escopo:** Nao inclui decisoes nao aprovadas por humano.

### Metrica da Iniciativa (0-10)

- **Nota Atual:** 6.5 — evidencia: docs/reports/16-09-2026_relatorio-cyberseguranca-ultra-blindagem.md
- **Nota Alvo:** 9.5
- **Nota Real (pos-implementacao):** [Pendente - preencher somente apos o fechamento real deste item/iniciativa, via o mesmo mecanismo que mediu a Nota Atual]

Nunca preencher Nota Atual sem evidencia real (relatorio de auditoria, comando ou
teste efetivamente rodado). Sem evidencia, o campo permanece `NAO AUDITADO`.

## 2. Processo Adotado

Diagnostico rapido → Definicao de Pronto checavel → Prompt de Execucao autocontido (PT-BR + EN-US) → Auditoria por reproducao real → Registro do veredito.

## 3. Onde vive o conteudo tecnico

| # | Item | Documento |
|---|---|---|
| 1 | Gate G_SUPPLY_CHAIN com pip-audit e scanner | `01-gate-g-supply.md` |
| 2 | Validador reputacao contra alucinacao pacotes | `02-validador-reputacao-contra.md` |
| 3 | Regras Semgrep para codigo gerado | `03-regras-semgrep-codigo.md` |
| 4 | Sandboxing efemero para testes subagentes | `04-sandboxing-efemero-testes.md` |

## 4. Regras Fixas

1. **A skill/agente nunca decide ou aprova sozinho.** Rascunhos aguardam aprovacao explicita de pessoa real.
2. **Sem disparos autonomos:** Prompts de execucao nao devem ser enviados a subagentes sem consentimento.
3. **Sem commit/push automatico:** Commits dependem de aprovacao do usuario.
4. **Isolamento:** Testes devem ocorrer sem poluir arquivos de producao.

## 5. Registro de Progresso

| # | Item | Status | Nota Atual | Nota Alvo | Nota Real | Documento |
|---|---|---|---|---|---|---|
| 1 | Gate G_SUPPLY_CHAIN com pip-audit e scanner | 🔶 Em execucao | 4.0 | 9.5 | [Pendente - preencher somente apos o fechamento real deste item/iniciativa, via o mesmo mecanismo que mediu a Nota Atual] | `01-gate-g-supply.md` |
| 2 | Validador reputacao contra alucinacao pacotes | 🔶 Em execucao | 3.0 | 9.0 | [Pendente - preencher somente apos o fechamento real deste item/iniciativa, via o mesmo mecanismo que mediu a Nota Atual] | `02-validador-reputacao-contra.md` |
| 3 | Regras Semgrep para codigo gerado | 🔶 Em execucao | 6.0 | 9.5 | [Pendente - preencher somente apos o fechamento real deste item/iniciativa, via o mesmo mecanismo que mediu a Nota Atual] | `03-regras-semgrep-codigo.md` |
| 4 | Sandboxing efemero para testes subagentes | 🔶 Em execucao | 5.0 | 9.0 | [Pendente - preencher somente apos o fechamento real deste item/iniciativa, via o mesmo mecanismo que mediu a Nota Atual] | `04-sandboxing-efemero-testes.md` |

Esta tabela so e atualizada para Concluido apos auditoria por reproducao real.
A coluna Nota Real so e preenchida no fechamento de cada item, rodando o MESMO
mecanismo real que mediu a Nota Atual (nunca um comando "parecido").
