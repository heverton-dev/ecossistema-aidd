# PROCESSO E DECISOES — upgrade-ferramentas-enterprise

> **Origem:** Planejamento estruturado no monorepo ecossistema-aidd.
> **Proposito deste arquivo:** Registro unico do processo e governanca desta iniciativa.
> **Aviso de Governanca:** Todos os itens comecam como rascunhos. Nenhuma aprovacao ou decisao pode ser fabricada.

---

## 1. O que este esforco busca

- **Objetivo Principal:** Elevar a maturidade estrutural e de engenharia das ferramentas `aidd-bridge`, `aidd-factory` e `aidd-forge` para o padrão corporativo Enterprise (9.6+), garantindo Vertical Slice Architecture, Quarteto Sine Qua Non dinâmico e auto-recuperação.
- **Limites de Escopo:** Não inclui alteração dos contratos imutáveis de entrada de planos de infraestrutura.

### Metrica da Iniciativa (0-10)

- **Nota Atual:** 8.5 — evidencia: docs/melhorias/16-09-2026_melhoria-elevacao-maturidade-ferramentas.json e homologação E2E CTT.
- **Nota Alvo:** 9.6
- **Nota Real (pos-implementacao):** [Pendente - preencher somente apos o fechamento real deste item/iniciativa, via o mesmo mecanismo que mediu a Nota Atual]

Nunca preencher Nota Atual sem evidencia real (relatorio de auditoria, comando ou
teste efetivamente rodado). Sem evidencia, o campo permanece `NAO AUDITADO`.

## 2. Processo Adotado

Diagnostico rapido → Definicao de Pronto checavel → Prompt de Execucao autocontido (PT-BR + EN-US) → Auditoria por reproducao real → Registro do veredito.

## 3. Onde vive o conteudo tecnico

| # | Item | Documento |
|---|---|---|
| 1 | Bridge-Robustez | `01-bridge-robustez.md` |
| 2 | Factory-Blueprints | `02-factory-blueprints.md` |
| 3 | Forge-SelfHealing | `03-forge-selfhealing.md` |

## 4. Regras Fixas

1. **A skill/agente nunca decide ou aprova sozinho.** Rascunhos aguardam aprovacao explicita de pessoa real.
2. **Sem disparos autonomos:** Prompts de execucao nao devem ser enviados a subagentes sem consentimento.
3. **Sem commit/push automatico:** Commits dependem de aprovacao do usuario.
4. **Isolamento:** Testes devem ocorrer sem poluir arquivos de producao.

## 5. Registro de Progresso

| # | Item | Status | Nota Atual | Nota Alvo | Nota Real | Documento |
|---|---|---|---|---|---|---|
| 1 | Bridge-Robustez | 🔶 Em execucao | 8.0 | 9.5 | [Pendente - preencher somente apos o fechamento real deste item/iniciativa, via o mesmo mecanismo que mediu a Nota Atual] | `01-bridge-robustez.md` |
| 2 | Factory-Blueprints | 🔶 Em execucao | 8.5 | 9.5 | [Pendente - preencher somente apos o fechamento real deste item/iniciativa, via o mesmo mecanismo que mediu a Nota Atual] | `02-factory-blueprints.md` |
| 3 | Forge-SelfHealing | 🔶 Em execucao | 8.8 | 9.8 | [Pendente - preencher somente apos o fechamento real deste item/iniciativa, via o mesmo mecanismo que mediu a Nota Atual] | `03-forge-selfhealing.md` |

Esta tabela so e atualizada para Concluido apos auditoria por reproducao real.
A coluna Nota Real so e preenchida no fechamento de cada item, rodando o MESMO
mecanismo real que mediu a Nota Atual (nunca um comando "parecido").
