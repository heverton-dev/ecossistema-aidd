# Item 1 — prompt-por-composicao-e-fixloop-diff-fase-08

> **Escopo:** Substituir o prompt monolitico de geracao da Fase 8 por composicao modular condicional por features do script, e refatorar o fix-loop de autocorrecao para enviar diff pontual e traceback isolado em vez de arquivos inteiros.
> **Status:** [EM EXECUCAO]

---

## Contexto ja investigado

- PROMPT_GERAR_SCRIPT carrega regras fixas (SQLite/FK/Swagger/MCP/UI) para qualquer script indiscriminadamente [TK-4].
- No fix-loop (08_implementador.py:405-421), PROMPT_CORRIGIR_SCRIPT reenvia CODE + TEST + ERRORS completos a cada tentativa [TK-3]. O metodo PostMortemAnalyzer._isolar_traceback ja existe na linha 232, mas nao esta conectado ao prompt de correcao.

## Definicao de Pronto

1. Refatorar PROMPT_GERAR_SCRIPT para compor dinamicamente blocos de regras apenas se a feature for requerida no script_spec.
2. Integrar PostMortemAnalyzer._isolar_traceback no PROMPT_CORRIGIR_SCRIPT.
3. Modificar o prompt de correcao para enviar o diff do erro e as funcoes sob suspeita (via AST), reduzindo tokens enviados no retry.
4. Teste comprovando reducao >= 40% de tokens medidos por tiktoken na 2a tentativa vs reenvio integral.

## Criterio de saida

- Prompt montado para script sem UI/API nao contem blocos Swagger/MCP.
- Fix-loop na 2a tentativa envia < 50% dos tokens da 1a chamada.
- Testes da Fase 08 aprovados.

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

`
Voce vai implementar o Item 1: prompt-por-composicao-e-fixloop-diff-fase-08.
1. Em tools/aidd-generator/scripts/phases/08_implementador.py:
   - Decomponha PROMPT_GERAR_SCRIPT em blocos modulares ativados por features do script_spec.
   - Conecte PostMortemAnalyzer._isolar_traceback no PROMPT_CORRIGIR_SCRIPT.
   - Envie apenas o trecho do traceback isolado e o contexto cirurgico da falha.
2. Comprove com teste usando tiktoken que a 2a tentativa envia < 50% dos tokens originais.
3. Rode pytest tools/aidd-generator/tests/ com exit 0.
`

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

`
You are going to implement Item 1: prompt-por-composicao-e-fixloop-diff-fase-08.
1. In tools/aidd-generator/scripts/phases/08_implementador.py:
   - Modularize PROMPT_GERAR_SCRIPT into conditional blocks based on script_spec requirements.
   - Wire PostMortemAnalyzer._isolar_traceback into PROMPT_CORRIGIR_SCRIPT.
   - Transmit isolated tracebacks and targeted error diffs rather than full file dumps.
2. Verify via tiktoken that retry attempts consume < 50% tokens compared to full retransmission.
3. Run pytest tools/aidd-generator/tests/ with exit 0.
`
