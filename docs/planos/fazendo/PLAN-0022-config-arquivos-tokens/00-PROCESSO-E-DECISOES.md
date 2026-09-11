# PROCESSO E DECISOES — 03-config-arquivos-tokens-agentes

> **Origem:** Planejamento estruturado no monorepo ecossistema-aidd.
> **Proposito deste arquivo:** Registro unico do processo e governanca desta iniciativa.
> **Aviso de Governanca:** Todos os itens comecam como rascunhos. Nenhuma aprovacao ou decisao pode ser fabricada.

---

## 1. O que este esforco busca

Defina aqui os objetivos claros, escopo e limites desta iniciativa.
- **Objetivo Principal:** [Descrever objetivo]
- **Limites de Escopo:** Nao inclui decisoes nao aprovadas por humano.

### Metrica da Iniciativa (0-10)

- **Nota Atual:** 7 — evidencia: docs/melhorias/11-09-2026_melhoria-config-arquivos-tokens.html
- **Nota Alvo:** 9
- **Nota Real (pos-implementacao):** [Pendente - preencher somente apos o fechamento real deste item/iniciativa, via o mesmo mecanismo que mediu a Nota Atual]

Nunca preencher Nota Atual sem evidencia real (relatorio de auditoria, comando ou
teste efetivamente rodado). Sem evidencia, o campo permanece `NAO AUDITADO`.

## 2. Processo Adotado

Diagnostico rapido → Definicao de Pronto checavel → Prompt de Execucao autocontido (PT-BR + EN-US) → Auditoria por reproducao real → Registro do veredito.

## 3. Onde vive o conteudo tecnico

| # | Item | Documento |
|---|---|---|
| 1 | Corrigir path de skills no ecossistema.py status (falso negativo) | `01-corrigir-path-skills.md` |
| 2 | Avaliar e dividir AGENTS.md em nucleo obrigatorio vs secoes sob demanda | `02-avaliar-dividir-agentsmd.md` |
| 3 | Atualizar PLANO-EXECUCAO-ESTRUTURADO.json com telemetria real | `03-atualizar-plano-execucao.md` |
| 4 | Auditar MCPs inativos/idle na stack (6 servidores) | `04-auditar-mcps-inativosidle.md` |

## 4. Regras Fixas

1. **A skill/agente nunca decide ou aprova sozinho.** Rascunhos aguardam aprovacao explicita de pessoa real.
2. **Sem disparos autonomos:** Prompts de execucao nao devem ser enviados a subagentes sem consentimento.
3. **Sem commit/push automatico:** Commits dependem de aprovacao do usuario.
4. **Isolamento:** Testes devem ocorrer sem poluir arquivos de producao.

## 5. Registro de Progresso

| # | Item | Status | Nota Atual | Nota Alvo | Nota Real | Documento |
|---|---|---|---|---|---|---|
| 1 | Corrigir path de skills no ecossistema.py status (falso negativo) | 🔶 Em execucao | NAO AUDITADO | 10 | [Pendente - preencher somente apos o fechamento real deste item/iniciativa, via o mesmo mecanismo que mediu a Nota Atual] | `01-corrigir-path-skills.md` |
| 2 | Avaliar e dividir AGENTS.md em nucleo obrigatorio vs secoes sob demanda | 🔶 Em execucao | NAO AUDITADO | 8 | [Pendente - preencher somente apos o fechamento real deste item/iniciativa, via o mesmo mecanismo que mediu a Nota Atual] | `02-avaliar-dividir-agentsmd.md` |
| 3 | Atualizar PLANO-EXECUCAO-ESTRUTURADO.json com telemetria real | 🔶 Em execucao | NAO AUDITADO | 9 | [Pendente - preencher somente apos o fechamento real deste item/iniciativa, via o mesmo mecanismo que mediu a Nota Atual] | `03-atualizar-plano-execucao.md` |
| 4 | Auditar MCPs inativos/idle na stack (6 servidores) | 🔶 Em execucao | NAO AUDITADO | 8 | [Pendente - preencher somente apos o fechamento real deste item/iniciativa, via o mesmo mecanismo que mediu a Nota Atual] | `04-auditar-mcps-inativosidle.md` |

Esta tabela so e atualizada para Concluido apos auditoria por reproducao real.
A coluna Nota Real so e preenchida no fechamento de cada item, rodando o MESMO
mecanismo real que mediu a Nota Atual (nunca um comando "parecido").
