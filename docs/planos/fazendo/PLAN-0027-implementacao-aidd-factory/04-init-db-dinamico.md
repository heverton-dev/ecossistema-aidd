# Item 04: Fase 5 — Gerador de init-multiple-databases.sh

## Escopo
Implementar `src/core/init_db_generator.py` que gera o script bash de inicializacao do PostgreSQL centralizado.

## Definicao de Pronto
- [ ] `init_db_generator.py` implementado com 100% determinismo
- [ ] Le bancos_logicos[] do factory_analysis.json
- [ ] Para cada banco: gera CREATE DATABASE + CREATE USER + GRANT
- [ ] Suporta PostgreSQL (padrao) e MySQL/MariaDB (via `banco_detectado`)
- [ ] Gera `init-multiple-databases.sh` no diretorio de saida
- [ ] Script e idempotente (CREATE IF NOT EXISTS)
- [ ] Testes com 1, 3 e 5 bancos logicos
- [ ] Gate G_FACTORY_INIT_DB.py valida sintaxe bash

## Dependencias
- Item 02 (analisador)

## Evidencia
- Template existente: `templates/infra/postgres/init-multiple-databases.sh` (82 linhas)
- `requisitos_recursos.json` tem `banco_detectado` por ferramenta
