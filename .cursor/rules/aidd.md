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
