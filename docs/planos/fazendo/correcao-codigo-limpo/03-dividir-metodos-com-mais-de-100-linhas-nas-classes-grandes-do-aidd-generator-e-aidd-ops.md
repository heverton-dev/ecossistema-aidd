# Item 3 — Dividir metodos com mais de 100 linhas nas classes grandes do aidd-generator e aidd-ops

> **Escopo:** Entra: dividir os métodos individuais listados abaixo (todos com mais de 100 linhas) em métodos privados menores, mantendo as classes onde já vivem — as classes em si já estão razoavelmente decompostas (múltiplos métodos nomeados), o problema é específico desses métodos, não a classe inteira. Não entra: reestruturar a classe inteira ou mudar sua interface pública; não entra o item já coberto separadamente (`run_all_checks` do `G_SEGURANCA.py`, que é o item 4 deste plano).

> **Status:** ⏳ Rascunho gerado, aguardando aprovação

---

## Contexto já investigado

- Achado real (`.code-review-graph/graph.db`, 2026-09-08): 3 classes do `aidd-generator` são as maiores do ecossistema por número de linhas — `ImplementadorFase8` (894L, `scripts/phases/08_implementador.py`), `AnalisadorCriticoAutomatico` (718L, `scripts/phases/07_analisador.py`), `CriadorProjetoFase5` (659L, `scripts/phases/05_criador.py`). Abrindo por dentro, essas classes já têm 12 a 22 métodos nomeados cada — não é uma função-monstro única, é um conjunto de métodos onde alguns ainda passam de 100 linhas:
  - `CriadorProjetoFase5._criar_arquivos_configuracao` — 198 linhas
  - `ImplementadorFase8._implementar_script_com_verificacao` — 125 linhas
  - `ImplementadorFase8._validar_contrato_ast` — 112 linhas
  - `AnalisadorCriticoAutomatico._calcular_score` — 106 linhas
  - `AnalisadorCriticoAutomatico._gerar_relatorio_markdown` — 102 linhas
- Em `aidd-ops`: `OpsMvpGate._validar_saida` (`gates/G_OPS_MVP.py`) — 111 linhas, único método acima de 100 linhas confirmado nessa ferramenta.
- `aidd-forge`: nenhum método acima de 70 linhas — não entra neste item.

## Definição de Pronto

1. Cada um dos 6 métodos listados acima dividido em sub-métodos privados menores (~50 linhas ou menos como referência, não regra rígida), com nome que descreva a responsabilidade de cada pedaço.
2. Resultado observável de cada método (o que ele retorna, o que ele escreve em disco/log) idêntico ao anterior — reproduzido rodando o fluxo/teste que exercita cada método antes e depois da divisão.
3. Testes existentes que cobrem `08_implementador.py`, `07_analisador.py`, `05_criador.py` e `G_OPS_MVP.py` executados com exit 0 após a mudança.

## Criterio de saida

- Arquivos criados ou alterados no local correto.
- Testes reais passando sem stubs falsos.
- Gates de integridade aprovados.

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item 3: Dividir metodos com mais de 100 linhas nas classes grandes do aidd-generator e aidd-ops.
Siga rigorosamente a Definicao de Pronto acima.
Nao invente aprovacoes e mantenha as regras do monorepo.
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 3: Dividir metodos com mais de 100 linhas nas classes grandes do aidd-generator e aidd-ops.
Strictly follow the Definition of Done above.
Do not fabricate approvals and maintain monorepo governance rules.
```
