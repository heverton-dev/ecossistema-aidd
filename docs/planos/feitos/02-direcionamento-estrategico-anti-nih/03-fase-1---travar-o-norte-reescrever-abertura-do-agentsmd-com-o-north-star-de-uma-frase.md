# Item 3 — Fase 1 - Travar o norte: reescrever abertura do AGENTS.md com o north star de uma frase

> **Escopo:** Entra: escrever e aprovar com o usuário um "north star" de uma frase só pro ecossistema, e refletir isso na abertura do `AGENTS.md`/`README.md` (seção 1, "Visão Geral"). Não entra: mudar a lista de ferramentas ou slash commands existentes.
> **Status:** ✅ Concluído (2026-09-07) — north star aprovado explicitamente pelo usuário via `orca orchestration ask` antes de qualquer edição; AGENTS.md §1 e README.md citam a frase.
> **Modelo sugerido:** Claude Opus · Antigravity Gemini 3.8 · MiMo mimo-v2.5-pro (decisão de posicionamento de produto, não é redação mecânica)

---

## Contexto ja investigado

- Hoje o `AGENTS.md` §1 lista as 5 ferramentas com papéis técnicos, mas não declara em uma frase qual é o diferencial real do ecossistema — isso deixou espaço pra cada ferramenta "competir" internamente por relevância reinventando infraestrutura (scaffolding, segurança, dashboard) em vez de focar no que só o conjunto resolve.
- Proposta de north star discutida em 2026-09-07 (a validar com o usuário, não gravar sem confirmação): *"Transformar uma ideia em software testado, e distribuir a mesma governança pra qualquer harness de IA."* — os dois únicos pilares sem equivalente de mercado identificados no levantamento NIH (protocolo delegado do generator + materializador multi-harness de `componentes/`).

## Definicao de Pronto

1. North star de uma frase aprovado explicitamente pelo usuário (esta frase ou outra) antes de qualquer edição em arquivo.
2. `AGENTS.md` §1 e `README.md` (abertura) passam a citar essa frase como a razão de ser do ecossistema, antes da tabela de ferramentas.
3. Nenhuma outra alegação de "diferencial" nesses dois arquivos que não seja rastreável a essa frase ou a um achado real do relatório de auditoria/levantamento NIH (nada de "certeza"/"garantia" solta).

## Criterio de saida

- Arquivos criados ou alterados no local correto.
- Testes reais passando sem stubs falsos.
- Gates de integridade aprovados.

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item 3: Fase 1 - Travar o norte: reescrever abertura do AGENTS.md com o north star de uma frase.
Siga rigorosamente a Definicao de Pronto acima.
Nao invente aprovacoes e mantenha as regras do monorepo.
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 3: Fase 1 - Travar o norte: reescrever abertura do AGENTS.md com o north star de uma frase.
Strictly follow the Definition of Done above.
Do not fabricate approvals and maintain monorepo governance rules.
```
