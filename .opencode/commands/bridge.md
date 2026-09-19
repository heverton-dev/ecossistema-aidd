# Comando /bridge

Dispara o Fluxo 03 (`aidd-bridge`) da Tríade Canônica: desacoplamento e libertação de projetos exportados de ferramentas low-code (Lovable, v0, Bolt).

## Uso:
`/bridge <caminho_do_export> [nome_do_projeto]`

## Ação:
Executa a skill `aidd-bridge` (ou `fluxo-03-runner`), que coleta os parâmetros e dispara deterministicamente o comando CLI:
`python ecossistema.py bridge --nome "<nome>" --slug <slug> --dominio <dominio> --pasta ./projetos/<slug> --origem <caminho_do_export>`
(ou `python ecossistema.py run-fluxo --fluxo bridge ...`)