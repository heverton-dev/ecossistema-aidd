# Comando /bridge

Dispara o Fluxo 03 (`aidd-bridge`) da Tríade Canônica: desacoplamento e libertação de projetos exportados de ferramentas low-code (Lovable, v0, Bolt).

## Uso:
`/bridge <caminho_do_export> [nome_do_projeto]`

## Ação:
Executa a esteira síncrona completa:
`[FORGE -> PLANNER] -> BRIDGE -> [MASTER -> ENTERPRISE -> OPS]`
Elimina vendor lock-in, migra banco para PostgreSQL e conecta ao Monólito Modular VSA, preservando estritamente a identidade visual original.

Equivalente CLI:
`python ecossistema.py run-fluxo --fluxo bridge --nome "<nome>" --slug <slug> --dominio <dominio> --pasta ./projetos/<slug> --origem <caminho_do_export>`