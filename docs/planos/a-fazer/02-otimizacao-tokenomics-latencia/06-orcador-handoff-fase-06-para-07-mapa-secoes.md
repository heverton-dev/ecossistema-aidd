# Item 6 — orcador-handoff-fase-06-para-07-mapa-secoes

> **Escopo:** Substituir o envio integral de documentos HTML/Markdown gerados pela Fase 6 para a Fase 7 (Auto-critica) por um mapa estruturado de secoes e resumos, reduzindo a sobrecarga da fase critica.
> **Status:** [RASCUNHO — Aguardando Aprovacao Humana]

---

## Contexto ja investigado

- A Fase 7 recebe todos os artefatos gerados (incluindo manuais HTML e documentacoes verborragicas completas), representando alto consumo com baixo valor marginal [TK-2].
- A auto-critica precisa avaliar conformidade de topicos, arquitetura e cobertura de requisitos, o que pode ser verificado atraves de resumos e metadados estruturados.

## Definicao de Pronto

1. Modificar a entrada da Fase 07 para consumir indice/mapa de secoes dos documentos da Fase 06 em vez de HTML bruto.
2. Manter a checagem de integridade documental sem inflar a janela de contexto.
3. Validar reducao de pelo menos 50% dos tokens de entrada da Fase 7 em testes comparativos.

## Criterio de saida

- Fase 7 consome <= 50% dos tokens em relacao ao baseline anterior.
- Avaliacao de conformidade da Fase 7 mantida integra.

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

`
Voce vai implementar o Item 6: orcador-handoff-fase-06-para-07-mapa-secoes.
1. Em tools/aidd-generator/scripts/phases/07_analisador.py:
   - Substitua o carregamento de HTML/MD integral pelo parser de mapa de secoes e sumario executivo.
2. Adicione teste comprovando que a entrada da Fase 7 cai pela metade mantendo a capacidade analitica.
3. Execute pytest tools/aidd-generator/tests/ com exit 0.
`

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

`
You are going to implement Item 6: orcador-handoff-fase-06-para-07-mapa-secoes.
1. In tools/aidd-generator/scripts/phases/07_analisador.py:
   - Replace raw HTML/MD full ingestion with a structural section map and executive summary.
2. Add unit test verifying that Phase 7 token payload is halved while maintaining critique coverage.
3. Run pytest tools/aidd-generator/tests/ with exit 0.
`
