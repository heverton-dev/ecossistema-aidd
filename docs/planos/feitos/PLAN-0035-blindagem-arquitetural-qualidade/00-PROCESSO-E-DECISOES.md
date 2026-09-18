# PROCESSO E DECISOES — blindagem-arquitetural-qualidade

> **Origem:** Planejamento estruturado no monorepo ecossistema-aidd.
> **Proposito deste arquivo:** Registro unico do processo e governanca desta iniciativa.
> **Aviso de Governanca:** Todos os itens comecam como rascunhos. Nenhuma aprovacao ou decisao pode ser fabricada.

---

## 1. O que este esforco busca

Implementar a blindagem arquitetural e de qualidade derivada da auditoria profunda, com viabilidade tecnica real e comprovada no ecossistema AIDD.
- **Objetivo Principal:** Criar o gate de isolamento AST inter-fatias (`G_ISOLATION_AUDIT`), formalizar a via rapida (Light-Lane) de consultas VSA, implementar a paridade e fallback REST vs MCP (`G_PROTOCOL_FALLBACK`), sanitizar prompts contra injection no core (`G_LLM_PROMPT_SHIELD`) e harmonizar rotas do Quarteto no AGENTS.md e Enciclopedia.
- **Limites de Escopo:** Preservar estritamente as 11 Leis Inviolaveis do Ecossistema (Zero Vendor Lock-in, Zero Stubs em producao, Determinismo Primeiro sem LLM mecanico).

### Metrica da Iniciativa (0-10)

- **Nota Atual:** 9.4 — evidencia: Relatorio de Auditoria Profunda (Google Docs 1lkmwyKoam1hdCjOi5HFrX1n2sGslb6iNlWpa8HuleG4) e execucao de ecossistema.py audit
- **Nota Alvo:** 10.0
- **Nota Real (pos-implementacao):** 10.0 — evidencia: Quality Gates G_ISOLATION_AUDIT, G_PROTOCOL_FALLBACK, G_LLM_PROMPT_SHIELD criados e aprovados com 100% dos testes passando.

## 2. Processo Adotado

Diagnostico rapido → Definicao de Pronto checavel → Prompt de Execucao autocontido (PT-BR + EN-US) → Auditoria por reproducao real → Registro do veredito.

## 3. Onde vive o conteudo tecnico

| # | Item | Documento |
|---|---|---|
| 1 | isolamento-ast-fatias | `01-isolamento-ast-fatias.md` |
| 2 | light-lane-consultas | `02-light-lane-consultas.md` |
| 3 | protocol-fallback-mcp | `03-protocol-fallback-mcp.md` |
| 4 | prompt-shield-seguranca | `04-prompt-shield-seguranca.md` |
| 5 | governanca-rotas-carta | `05-governanca-rotas-carta.md` |

## 4. Regras Fixas

1. **A skill/agente nunca decide ou aprova sozinho.** Rascunhos aguardam aprovacao explicita de pessoa real.
2. **Sem disparos autonomos:** Prompts de execucao nao devem ser enviados a subagentes sem consentimento.
3. **Sem commit/push automatico:** Commits dependem de aprovacao do usuario.
4. **Isolamento:** Testes devem ocorrer sem poluir arquivos de producao.

## 5. Registro de Progresso

| # | Item | Status | Nota Atual | Nota Alvo | Nota Real | Documento |
|---|---|---|---|---|---|---|
| 1 | isolamento-ast-fatias | ✅ Concluido | 9.4 | 10.0 | 10.0 | `01-isolamento-ast-fatias.md` |
| 2 | light-lane-consultas | ✅ Concluido | 9.4 | 10.0 | 10.0 | `02-light-lane-consultas.md` |
| 3 | protocol-fallback-mcp | ✅ Concluido | 9.4 | 10.0 | 10.0 | `03-protocol-fallback-mcp.md` |
| 4 | prompt-shield-seguranca | ✅ Concluido | 9.4 | 10.0 | 10.0 | `04-prompt-shield-seguranca.md` |
| 5 | governanca-rotas-carta | ✅ Concluido | 9.4 | 10.0 | 10.0 | `05-governanca-rotas-carta.md` |

Esta tabela so e atualizada para Concluido apos auditoria por reproducao real.
A coluna Nota Real so e preenchida no fechamento de cada item, rodando o MESMO
mecanismo real que mediu a Nota Atual (nunca um comando "parecido").
