# Item 1 — Inventario do que fica vs o que troca por ferramenta (o trabalho que continua de pe)

> **Escopo:** Entra: produzir e publicar a tabela definitiva "o que fica / o que troca" por ferramenta, respondendo formalmente "perdemos o trabalho?". Não entra: executar nenhuma troca em si (isso são os itens 3-6/Fases 1-4).
> **Status:** [RASCUNHO — Aguardando Aprovacao Humana]
> **Modelo sugerido:** Claude Sonnet · Antigravity Gemini 3.7 · MiMo mimo-v2.5-pro (síntese e redação, não decisão técnica nova)

---

## Contexto ja investigado

Resposta já esboçada em conversa com o usuário em 2026-09-07 — este item formaliza por escrito:

- **aidd-forge:** quase tudo fica — é a ferramenta mais madura, menos NIH do levantamento (`docs/features/oportunidades-reaproveitamento-oss-nih.md`).
- **aidd-generator:** fica o pipeline de 8 fases, o protocolo delegado, o fleet discovery, a lógica de domínio de cada fase. Troca: empacotamento de contexto (item NIH #22 → Repomix), parsing de saída de LLM (#23 → instructor), formato de doc (#25 → Pandoc), MCP (#24 → SDK oficial).
- **aidd-master/aidd-enterprise:** fica a modelagem (fatias verticais, CQRS, consciência de RLS, WAL) — é decisão de arquitetura de domínio, não código descartável. Troca: motor de templating (#6 → Cookiecutter/Copier), adapter de banco (#8 → SQLAlchemy/aiosqlite), CSP (#9 → secure.py), Result Monad (#7 → lib `returns`), RLS via regex (#10 → sqlglot).
- **aidd-ops:** fica a inteligência de sizing/classificação de nicho. Troca: 3 das 4 features planejadas em `evolucao-aidd-ops-fase-completa/` (itens 18-21 do levantamento NIH) provavelmente viram integração via API de Coolify/CapRover em vez de construção do zero — decisão formal fica pra Fase 2 (item 4 deste plano).
- **raiz (componentes/gates):** fica o materializador multi-harness (`componentes/` → `.claude/`, `.opencode/`, etc.) — é o item mais valioso do ecossistema, sem equivalente de mercado. Troca: o runner dos 8 gates migra pra framework `pre-commit` (#4 do levantamento NIH), mas as regras que cada gate checa continuam as mesmas, só rodam dentro de um framework testado.
- **O que de fato não valeu:** o scanner de entropia caseiro (G_SEGREDOS), o dashboard que fabricou dado (aidd-ops), o gate de segurança inflado de linguagem de marketing (G_SEGURANCA do enterprise) — esforço específico e pequeno, não o projeto inteiro.

## Definicao de Pronto

1. Tabela "o que fica / o que troca" publicada como documento de referência (pode viver neste próprio item ou linkar pra `docs/features/oportunidades-reaproveitamento-oss-nih.md` seção 2, que já cobre o detalhe por ferramenta).
2. Cada linha da tabela cita o número do achado correspondente no levantamento NIH (rastreabilidade, não afirmação solta).
3. Usuário confirma que a leitura "o trabalho não foi perdido, o motor por baixo troca" está correta antes de qualquer execução das Fases 1-4.

## Criterio de saida

- Arquivos criados ou alterados no local correto.
- Testes reais passando sem stubs falsos.
- Gates de integridade aprovados.

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item 1: Inventario do que fica vs o que troca por ferramenta (o trabalho que continua de pe).
Siga rigorosamente a Definicao de Pronto acima.
Nao invente aprovacoes e mantenha as regras do monorepo.
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 1: Inventario do que fica vs o que troca por ferramenta (o trabalho que continua de pe).
Strictly follow the Definition of Done above.
Do not fabricate approvals and maintain monorepo governance rules.
```
