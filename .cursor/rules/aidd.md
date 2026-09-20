# Cursor Rules — Ecossistema AIDD Unificado
Consulte a governança canônica em AGENTS.md.
Todas as 4 ferramentas estão organizadas em tools/:
- tools/aidd-forge
- tools/aidd-generator
- tools/aidd-master
- tools/aidd-enterprise

Auditoria completa (todos os Quality Gates da raiz): python ecossistema.py audit
CLI Unificada: python ecossistema.py

No início da sessão: rodar `python ecossistema.py dependencia verify`; se
falhar, rodar `python ecossistema.py dependencia bootstrap` e informar o
resultado — nunca pedir pro usuário digitar isso (ver AGENTS.md §0).

## Mandatory Answer Shape (Rule 10 / Law #4)
1. One top sentence stating what to do or what happened. No preamble.
2. Short bulleted body. Facts, numbers, findings. No narration of steps taken.
3. One closing suggestion block, separated from the body.
Forbidden: introductions, restating the request, recapping what was just said, listing options without a recommendation.

*Note on Hook Enforcement:* Automated stop-hook enforcement is unavailable in Cursor due to lack of a native response-interception hook event; compliance is maintained by convention.
