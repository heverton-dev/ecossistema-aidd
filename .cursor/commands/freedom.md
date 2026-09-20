# Comando /freedom

Dispara o Fluxo 03 (`aidd-freedom`) da Tríade Canônica: desacoplamento completo e libertação de projetos exportados de ferramentas low-code (Lovable, v0, Bolt) para infraestrutura própria e Monólito Modular VSA.

## Uso:
`/freedom <caminho_do_export> [nome_do_projeto]`

## Ação:
Executa a skill `aidd-freedom` (ou `fluxo-03-runner`), que coleta os parâmetros e dispara deterministicamente o comando CLI:
`python ecossistema.py freedom --nome "<nome>" --slug <slug> --dominio <dominio> --pasta ./projetos/<slug> --origem <caminho_do_export>`
(ou `python ecossistema.py run-fluxo --fluxo freedom ...`)
