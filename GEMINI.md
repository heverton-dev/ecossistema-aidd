# Ponte do Gemini — regras canônicas em [AGENTS.md](AGENTS.md)

## Forma da Resposta (Rule 10 / Lei #4)
Fale em português simples e direto, sem jargão hermético. Dupla fala: “Na Festa” (linguagem clara do dia a dia) e “Na Casa” (comando completo para copiar).

1. Primeira frase: o que fazer ou o que aconteceu na prática. Sem enrolação.
2. Depois: tópicos objetivos com fatos, números e impacto real (O que mudou ➔ Por que mudou ➔ Resultado prático). Sem narrar passos internos ou filosofias conceituais.
3. Por fim: uma sugestão de próximo passo direto.

Proibido: saudação, repetir o pedido, recapitular o que acabou de ser dito, listar opções sem recomendar uma, usar abstrações vazias ("respaldo canônico", "invariante topológica") sem dizer claramente o efeito tangível no código.

**Siglas e termos técnicos:** traduza na primeira vez com exemplo prático (ex.: VSA — fatias verticais isoladas de código).  
**Comandos e caminhos:** sempre completos, clicáveis e copiáveis.

*Sobre a campainha automática:* no Gemini CLI / Antigravity não há hook de interceptação de resposta. O cumprimento aqui é por convenção + o portão `G_USER_FACING_PTBR` no fim do fluxo.

## Nomenclatura (sem ambiguidade)
- **Rule 10 (Formato de Resposta)** — a forma da resposta. Nunca chame isso de “Lei #10”.
- **Lei #10 (Quarteto)** — os 4 estúdios obrigatórios: `/api`, `/webhook`, `/mcp`, `/docs`. Nunca chame isso de “Rule 10”.
- **Lei #4 (Idioma)** — PT-BR simples para o usuário; inglês compacto no núcleo do agente.

## Ativação universal dos fluxos (Lei #6)
- Qualquer menção a `/freedom`, `freedom`, `/pure`, `pure`, `/open`, `/aidd-open`, `open`, `/factory`, `/bridge`, `bridge`, `/run-plan`, `run-plan`, `/pipeline`, `pipeline`, `/dispatch`, `dispatch`, `/aidd-dispatch`, `/audit-4f`, `audit-4f`, `/aidd-auditor`, `/evolucao`, `evolucao`, `/aidd-evolucao`, `/sessao`, `sessao`, `/session`, `session`, `/id` — ou linguagem natural equivalente (ex.: “desacoplar lovable”, “criar do zero”, “migrar open source”, “executar plano”, “rodar pipeline”, “rodar auditoria 4f”, “evoluir ferramenta”, “rodar evolucao”, “salvar id da sessao”) — DEVE ser tratada como a invocação imediata do fluxo correspondente.
- **Importante para o Fluxo 02 no Antigravity/AGY:** o comando `/open <path>` é reservado para abrir arquivos no editor. Use `/aidd-open` (ou `/factory`) para disparar o Fluxo 02.
- **NUNCA** responda que o comando é desconhecido ou inválido.
- Execute a skill (`aidd-pure`, `aidd-open`, `aidd-freedom`, `aidd-pipeline`, `aidd-dispatch`, `aidd-audit-4f`, `aidd-evolution`, `aidd-session`) ou o CLI (`python ecossistema.py freedom|pure|open|freedom-motor|run-plan|pipeline|dispatch|audit-4f|evolucao|sessao <args>`).
- Se faltar argumento, peça só o necessário (caminho do export, do plano ou do JSON) e confirme que o fluxo está ativo.
