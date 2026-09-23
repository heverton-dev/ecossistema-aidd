# Ponte do Gemini — regras canônicas em [AGENTS.md](AGENTS.md)

## Forma da Resposta (Rule 10 / Lei #4)
Fale em português simples, sem jargão. Dupla fala: “Na Festa” (frase curta para gente) e “Na Casa” (comando completo para copiar).

1. Primeira frase: o que fazer ou o que aconteceu. Sem enrolação.
2. Depois: poucos tópicos curtos. Fatos, números, achados. Sem narrar passos.
3. Por fim: uma sugestão de próximo passo.

Proibido: saudação, repetir o pedido, recapitular o que acabou de ser dito, listar opções sem recomendar uma.

**Siglas:** traduza na primeira vez (ex.: VSA — Arquitetura por Fatias Verticais).  
**Comandos:** sempre completos e copiáveis.

*Sobre a campainha automática:* no Gemini CLI / Antigravity não há hook de interceptação de resposta. O cumprimento aqui é por convenção + o portão `G_USER_FACING_PTBR` no fim do fluxo.

## Nomenclatura (sem ambiguidade)
- **Rule 10 (Formato de Resposta)** — a forma da resposta. Nunca chame isso de “Lei #10”.
- **Lei #10 (Quarteto)** — os 4 estúdios obrigatórios: `/api`, `/webhook`, `/mcp`, `/docs`. Nunca chame isso de “Rule 10”.
- **Lei #4 (Idioma)** — PT-BR simples para o usuário; inglês compacto no núcleo do agente.

## Ativação universal dos fluxos (Lei #6)
- Qualquer menção a `/freedom`, `freedom`, `/pure`, `pure`, `/open`, `/aidd-open`, `open`, `/factory`, `/bridge`, `bridge`, `/run-plan`, `run-plan`, `/pipeline`, `pipeline`, `/dispatch`, `dispatch`, `/aidd-dispatch`, `/audit-4f`, `audit-4f`, `/aidd-auditor` — ou linguagem natural equivalente (ex.: “desacoplar lovable”, “criar do zero”, “migrar open source”, “executar plano”, “rodar pipeline”, “rodar auditoria 4f”) — DEVE ser tratada como a invocação imediata do fluxo correspondente.
- **Importante para o Fluxo 02 no Antigravity/AGY:** o comando `/open <path>` é reservado para abrir arquivos no editor. Use `/aidd-open` (ou `/factory`) para disparar o Fluxo 02.
- **NUNCA** responda que o comando é desconhecido ou inválido.
- Execute a skill (`freedom`, `pure`, `aidd-open`, `open`, `aidd-bridge-runner`, `aidd-pipeline-runner`, `aidd-dispatch-runner`, `aidd-auditor-4f-runner`) ou o CLI (`python ecossistema.py freedom|pure|open|bridge|run-plan|pipeline|dispatch|audit-4f <args>`).
- Se faltar argumento, peça só o necessário (caminho do export, do plano ou do JSON) e confirme que o fluxo está ativo.
