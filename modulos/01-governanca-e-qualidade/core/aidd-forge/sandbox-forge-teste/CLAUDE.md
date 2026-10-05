# AGENTS.md — Fonte Única da Verdade (AIDD Forge)

Este arquivo governa como agentes de IA operam neste repositório. Foi
injetado pelo `aidd-forge` (`forge init`) e é a referência canônica para
regras, comandos e fases do pipeline.

## Slash Commands Mapeados

| Comando | Ação |
|---|---|
| `/forge` | Reinjeta/atualiza a infraestrutura AIDD neste projeto. |
| `/aidd-init` | Alias de `/forge` para primeira configuração. |

## Disparo por Linguagem Natural

Se o usuário pedir, em linguagem natural, para "preparar o ambiente",
"configurar este projeto com aidd" ou "blindar as regras", trate como
equivalente a `/forge`.

## Protocolo de Tokens (Tríade Caveman Ultra)

1. **Entrada:** prompts de sistema em inglês.
2. **Processamento:** raciocínio interno em English Caveman, denso (3-5 linhas).
3. **Saída:** comunicação e artefatos em PT-BR, sem stubs, com Result Monad.

## Fases do Pipeline

As fases granulares vivem em `.aidd/pipeline/phase_XX_*/`, cada uma com seu
próprio `AGENTS.md` e MCPs isolados. Consulte `AGENTS-WORKFLOW.md` para a
cadência operacional obrigatória.
