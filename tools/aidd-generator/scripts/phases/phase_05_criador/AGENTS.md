# Phase 05 — Criador (Micro-Ambiente)

## Escopo
Criação determinística do projeto: diretórios, configs, SQLite, git init, symlinks.

## Restrições
- 100% determinístico (Zero Token de LLM)
- Métricas medidas via rglob/git (nunca hardcoded)
- AGENTS.md como fonte única; .claude/CLAUDE.md como symlink real
- config_fase4 (GLOBAL/LOCAL) → symlinks reais

## Linter AST
- Todo código gerado DEVE passar por `ast.parse()` antes de ser escrito em disco
- Se `ast.parse()` falhar, o arquivo NÃO é criado e o erro é registrado no índice
- Validação AST é mecânica (Zero Token): Python `ast` module
- Aplica-se a: templates Python, scripts de configuração, schemas
- Exceção: arquivos não-Python (JSON, YAML, TOML, MD) passam por validação de formato próprio

## Gates
- E1: Arquivos criados em disco
- E2: Git init + commit bem-sucedido
- E3: SQLite inicializado
- E4: Permissões corretas
- S1: Segurança (.gitignore, sem secrets hardcoded)

## Saída
- `_phase_05_index.json` em `.aidd/cache/data/`

## Tokens
- Consumo: 0 (100% determinístico)
- Justificativa: Python puro + shutil + subprocess, zero LLM
