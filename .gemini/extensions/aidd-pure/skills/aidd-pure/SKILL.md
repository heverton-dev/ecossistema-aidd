---
name: aidd-pure
description: Dispara o Fluxo 01 (Do Zero Puro | Slash: /pure) da Tríade Canônica. Geração autoral via TDD Red-Green estrito e Monólito Modular VSA.
---

# aidd-pure — Fluxo 01 Canônico (Do Zero Puro | /pure)

Dispara e conduz o Fluxo 01 (`aidd-pure`) da Tríade Canônica de criação de software no Ecossistema AIDD:
`[FORGE -> PLANNER] -> GENERATOR -> [MASTER -> ENTERPRISE -> OPS]`

## Gatilhos Universais:
- Comando Slash: `/pure <nome_ou_ideia> [dominio]`
- Invocação por Skill: `/aidd-pure` ou skill `aidd-pure`
- Linguagem Natural: "criar projeto do zero puro", "gerar software via pure", "novo projeto com TDD"

## Como Executar

### 1. Via CLI Central (Zero Fricção):
```bash
python ecossistema.py pure --nome "Meu Projeto" --slug meu-projeto --dominio gestao --pasta ./projetos/meu-projeto
```
Ou via comando legado:
```bash
python ecossistema.py run-fluxo --fluxo pure --nome "Meu Projeto" --slug meu-projeto --dominio gestao --pasta ./projetos/meu-projeto
```

### 2. Simulação (Dry-Run):
```bash
python ecossistema.py pure --nome "Meu Projeto" --slug meu-projeto --dominio gestao --pasta ./projetos/meu-projeto --dry-run
```

## Ação do Agente:
1. Coleta ou valida o nome, slug, domínio e pasta de destino do projeto com o usuário.
2. Executa a esteira determinística de ponta a ponta com validação síncrona de handoffs em cada fase.
3. Garante o cumprimento do *Quarteto Sine Qua Non* (`/swagger`, `/webhooks`, `/mcp`, `/docs/guia`) e Next.js no Frontend.
