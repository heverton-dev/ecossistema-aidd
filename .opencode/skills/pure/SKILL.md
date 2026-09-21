---
name: pure
description: Dispara o Fluxo 01 (Do Zero Puro | Slash: /pure) da Tríade Canônica. Geração autoral via TDD Red-Green estrito e Monólito Modular VSA.
---

# /pure — Fluxo 01 Canônico (Do Zero Puro)

Dispara e conduz o Fluxo 01 (`aidd-pure`) da Tríade Canônica de criação de software no Ecossistema AIDD:
`[FORGE -> PLANNER] -> GENERATOR -> [MASTER -> ENTERPRISE -> OPS]`

## Gatilhos Universais:
- Comando Slash: `/pure <nome_ou_ideia> [dominio]`
- Invocação por Skill: `/pure` ou skill `pure`
- Linguagem Natural: "criar projeto do zero puro", "gerar software via pure", "novo projeto com TDD"

## Como Executar

### 1. Via CLI Central (Alta Ergonomia):
```bash
python ecossistema.py pure "Meu Projeto" gestao
```
Ou com flags explícitas:
```bash
python ecossistema.py pure --nome "Meu Projeto" --slug meu-projeto --dominio gestao --pasta ./projetos/meu-projeto
```

### 2. Simulação (Dry-Run):
```bash
python ecossistema.py pure "Meu Projeto" --dry-run
```

## Ação do Agente:
1. Coleta ou valida o nome, slug, domínio e pasta de destino do projeto com o usuário.
2. Executa a esteira determinística de ponta a ponta com validação síncrona de handoffs em cada fase.
3. Garante o cumprimento do *Quarteto Sine Qua Non* (`/docs`, `/webhooks`, `/mcp`, `/docs/guia`) e Next.js no Frontend.
