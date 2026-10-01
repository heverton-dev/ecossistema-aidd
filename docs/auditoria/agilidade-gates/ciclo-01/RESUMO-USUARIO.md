# Resumo — agilidade-gates ciclo-01

> **Status:** aprovado e mergeado na main (`c85eab2`) em 30/09/2026 · gate_final 54/54 verde

## O que mudou para quem usa
Commitar ficou rápido sem perder a segurança. No dia a dia, os dois gates mais lentos olham só o que mudou: o commit caiu de **20–25 min para 2–3 min** (medido nos tickets 5 a 8). A bateria completa roda uma vez por ciclo, no gate_final, e de novo no push só se aquele conteúdo ainda não passou nela.

| Antes | Agora |
|---|---|
| Bateria inteira em todo commit | Modo rápido no commit; modo completo no gate_final e no push |
| Handoff e baseline editados à mão (erro de CRLF) | `python ecossistema.py derivados regenerar` |
| Conflito nesses arquivos travava o merge | `--aprovar` resolve sozinho, só em arquivo derivado |
| Vários ciclos pesados juntos, "me chame em 30 min" | Fila de um ciclo por vez, com aviso ao terminar |

## Comandos
- Regenerar os arquivos derivados: `python ecossistema.py derivados regenerar`
- Ver quais são: `python ecossistema.py derivados listar`
- Medir o tempo de cada gate: `python scripts/medir_gates.py --modo completo`

## Fica para o próximo ciclo
Cache de resultado por ferramenta no gate_final (pular testes de ferramenta idêntica à última rodada verde).
