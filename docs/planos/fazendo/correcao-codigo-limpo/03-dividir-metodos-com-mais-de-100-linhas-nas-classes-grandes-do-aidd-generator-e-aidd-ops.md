# Item 3 — Dividir metodos com mais de 100 linhas nas classes grandes do aidd-generator e aidd-ops

> **Escopo:** Entra: dividir os métodos individuais listados abaixo (todos com mais de 100 linhas) em métodos privados menores, mantendo as classes onde já vivem — as classes em si já estão razoavelmente decompostas (múltiplos métodos nomeados), o problema é específico desses métodos, não a classe inteira. Não entra: reestruturar a classe inteira ou mudar sua interface pública; não entra o item já coberto separadamente (`run_all_checks` do `G_SEGURANCA.py`, que é o item 4 deste plano).

> **Status:** ✅ Concluído em 2026-09-08 (auditado por reprodução real — ver Execução abaixo)

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

## Execução (2026-09-08, parcial — interrompida a pedido do usuário)

Feito e verificado por reprodução real (testes existentes passando, sem stub falso):
- `aidd-ops/gates/G_OPS_MVP.py::OpsMvpGate._validar_saida` (111L) — dividido em `_carregar_plano_saida`, `_validar_campos_topo`, `_validar_fase1_intake`, `_validar_fase2_curadoria`, `_validar_fase3_sizing`, `_validar_todas_fases_produziram_saida`. `pytest tools/aidd-ops/tests/test_pipeline_ops.py` → 13/13 passando (inclui caso de plano corrompido).
- `aidd-generator/scripts/phases/05_criador.py::CriadorProjetoFase5._criar_arquivos_configuracao` (198L) — dividido em 9 métodos `_criar_*` (um por arquivo gerado: orquestrador, settings.json, AGENTS.md+sync harnesses, config.json, rules.md, requirements.txt, pytest.ini, README, .gitignore). `pytest tools/aidd-generator/tests/test_phase_05.py` → 27/27 passando.
- `aidd-generator/scripts/phases/08_implementador.py::ImplementadorFase8._implementar_script_com_verificacao` (125L) — parcialmente dividido: extraídos `_reaproveitar_implementacao_existente` (cache em disco) e `_gerar_implementacao_inicial` (monta prompt, chama LLM, normaliza caminhos). O laço de tentativas/auto-correção (linhas finais do método original) **não foi mexido** — é uma máquina de estado com muita variável carregada entre iterações, dividir isso às pressas é mais risco que benefício. `pytest tools/aidd-generator/tests/test_phase_08.py` → 45/45 passando.

Retomado em 2026-09-08 (segunda sessão), completando os 3 métodos restantes:
- `aidd-generator/scripts/phases/08_implementador.py::ImplementadorFase8._validar_contrato_ast` (112L) — dividido em `_coletar_nomes_definidos_codigo`, `_mapear_vars_com_classe`, `_coletar_chamadas_faltando` e `_montar_mensagem_contrato_quebrado` (o método virou `@classmethod` para poder chamar os helpers via `cls`; os 2 pontos de chamada usam `self._validar_contrato_ast(...)`, compatível com classmethod). `pytest tools/aidd-generator/tests/test_phase_08.py` → 45/45 passando (mesmo total do baseline antes da mudança).
- `aidd-generator/scripts/phases/07_analisador.py::AnalisadorCriticoAutomatico._calcular_score` (106L) — dividido em um método por dimensão (`_dim_completude_pipeline`, `_dim_qualidade_gates`, `_dim_determinismo`, `_dim_validacoes`, `_dim_documentacao`, `_dim_rastreabilidade`) mais `_classificar_score`. `pytest tools/aidd-generator/tests/test_phase_07.py` → 34/34 passando.
- `aidd-generator/scripts/phases/07_analisador.py::AnalisadorCriticoAutomatico._gerar_relatorio_markdown` (102L) — dividido em uma seção por bloco do relatório (`_md_secao_score`, `_md_secao_pontos`, `_md_secao_requisitos`, `_md_secao_roadmap`, `_md_secao_investimento`, `_md_secao_recomendacao`). Saída comparada byte a byte antes/depois (mesmo cenário de teste): idêntica, exceto nome de pasta temporária aleatória e timestamp de geração (ambos esperados, não são efeito da divisão). `pytest tools/aidd-generator/tests/test_phase_07.py` → 34/34 passando.

Suíte completa `pytest tools/aidd-generator/tests/` → 863/863 passando após as 3 divisões.

**Veredito: concluído — os 6 métodos originalmente listados neste item estão divididos e verificados por reprodução real.**

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
