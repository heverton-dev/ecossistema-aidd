# Comando /aidd-livro-texto

Gera e atualiza livros-texto corporativos em PDF, com estrutura macro-meso-micro,
rastreabilidade por capítulo e auditoria determinística. Funciona em qualquer projeto —
não é específico deste ecossistema.

## Uso:
`/aidd-livro-texto <criar|atualizar> <pasta> [descrição do que documentar]`

## Ação:
Executa a skill `aidd-livro-texto` (dona única deste comando), que decide entre obra
nova e atualização pelo manifesto `livro.json` da pasta alvo, escreve as partes em
Markdown e delega todo o trabalho mecânico ao motor determinístico `livro.py`
(concatenação, auditoria, compilação, versionamento e registro de revisão).

Equivalente CLI (a skill traz o motor dentro dela):
```
python <skill>/scripts/livro.py doctor
python <skill>/scripts/livro.py init <pasta> --titulo "<Título>" --autor "<Autor>"
python <skill>/scripts/livro.py check <pasta> --raiz-evidencia <raiz-do-projeto>
python <skill>/scripts/livro.py build <pasta>
python <skill>/scripts/livro.py update <pasta> --nota "<o que mudou>"
python <skill>/scripts/livro.py preview <pasta>
```

Dentro deste monorepo, `<skill>` resolve para
`componentes/compartilhado/skills/aidd-livro-texto`.
