# Arquitetura de Modularização VSA + Monólito Modular no Ecossistema AIDD

> **Status:** Proposta Arquitetural & Especificação Canônica  
> **Objetivo:** Erradicar a dispersão de contexto, o desperdício de tokens e a fragilidade de manutenção através da autocontenção por Domínio de Capacidade.

---

## 1. O Diagnóstico: O Problema Atual da Dispersão Horizontal

Atualmente, o ecossistema organiza o código por **camada técnica horizontal**:
- Todas as ferramentas ficam amontoadas em `tools/`.
- Todos os 54 quality gates ficam soltos em `gates/`.
- As skills ficam fragmentadas entre `componentes/compartilhado/skills/` e `.agents/skills/`.
- Scripts de automação operam na raiz de `scripts/`.

### Sintomas e Impactos Negativos:
1. **Queima Excessiva de Tokens:** Para alterar uma única linha no fluxo *Freedom*, o agente de IA precisa inspecionar diretórios globais, ler dezenas de referências cruzadas e carregar contextos gigantescos (40.000 a 80.000 tokens por iteração).
2. **Blast Radius (Raio de Destruição) Descontrolado:** Uma alteração pontual em uma ferramenta corre o risco de quebrar portões distantes ou scripts sem relação direta.
3. **Fadiga Cognitiva do Desenvolvedor:** Localizar onde uma regra nasce, onde é executada e onde é validada consome horas de depuração.

---

## 2. A Lógica da Modularização: Por Domínio de Capacidade (VSA)

A solução **NÃO** é quebrar em mais pastas técnicas (ex: pasta de controllers, pasta de schemas) e nem retalhar em 30 microrrepositórios que exigem orquestração complexa.

A solução é o **Monólito Modular com Vertical Slice Architecture (VSA)**:
- Mantemos **um único repositório git** (Monólito), garantindo versionamento atômico, facilidade de refatoração e integridade dos testes.
- Dividimos o repositório em **Fatias Verticais de Domínio**, agrupando tudo o que pertence ao mesmo ciclo de vida dentro da mesma pasta.

---

## 3. Mapa Estrutural Proposto (`modulos/`)

```
ecossistema-aidd/
│
├── modulos/
│   ├── 01-governanca-e-qualidade/     # O "Cérebro" de Regras, Diagnóstico e Auditoria
│   │   ├── core/                      # aidd-forge, orquestrador 4f, scaffold, compilador
│   │   ├── skills/                    # aidd-grill, aidd-spec, aidd-tdd, aidd-audit-4f, aidd-evolution
│   │   ├── gates/                     # G_DETERMINISMO, G_DOCS_ROT, G_PORTAO_PROVA_QUE_MORDE...
│   │   ├── tests/                     # Testes de regressão e provas de portão
│   │   └── README.md                  # Mapa de contexto mínimo (< 500 tokens)
│   │
│   ├── 02-triade-motores/             # A "Fábrica" de Software (Os 3 Fluxos Canônicos)
│   │   ├── fluxo-01-pure/             # Motor do Zero Puro (TDD Red-Green, Geradores)
│   │   │   ├── core/                  # aidd-pure engine
│   │   │   ├── templates/             # TanStack Start, React, Tailwind PWA
│   │   │   ├── skills/                # aidd-pure
│   │   │   ├── gates/                 # G_STACK_PADRAO_OURO, G_TESTES_REAIS...
│   │   │   └── tests/
│   │   ├── fluxo-02-open/             # Motor Open-Source Integrado
│   │   │   ├── core/                  # aidd-open factory, compose generator
│   │   │   ├── catalogo/              # Curadoria de motores open-source testados
│   │   │   ├── skills/                # aidd-open
│   │   │   ├── gates/                 # G_INFRA_COMPOSE, G_COMPONENTE_AGNOSTICO...
│   │   │   └── tests/
│   │   └── fluxo-03-freedom/          # Motor de Libertação Low-Code
│   │       ├── core/                  # aidd-freedom bridge, conversores de DB
│   │       ├── skills/                # aidd-freedom
│   │       ├── gates/                 # G_ANT_LOCKIN_LEGADO, G_MIGRATION_ROT...
│   │       └── tests/
│   │
│   ├── 03-plataforma-e-entrega/       # A "Esteira" de Harmonização e Produção
│   │   ├── fatiamento-master/         # aidd-master, mesocamada VSA, dispatch worktrees
│   │   ├── blindagem-enterprise/      # aidd-enterprise, injeção SHA-256
│   │   ├── operacoes-ops/             # aidd-ops, VPS sizing, Docker, SOPS+Age, Cloudflare
│   │   ├── quarteto-studios/          # OpenAPI (/api), Webhooks, MCP Studio, Docs (/docs)
│   │   ├── skills/                    # aidd-master, aidd-dispatch, aidd-enterprise, aidd-ops
│   │   ├── gates/                     # G_QUARTETO_SINE_QUA_NON, G_ISOLATION_AUDIT...
│   │   └── tests/
│   │
│   └── 04-nucleo-compartilhado/       # O "Chassi" Comum (Kernel & Facade)
│       ├── cli/                       # Fachada de comandos e roteamento central
│       ├── sync/                      # Sincronizador agnóstico de harnesses
│       ├── contratos/                 # Schemas JSON universais (PLANNER, DISPATCH, HANDOFF)
│       ├── utilitarios/               # Helpers determinísticos de AST, Git e filesystem
│       └── gates/                     # G_SAIDA_BINARIA, G_ECOSSISTEMA_INTEGRIDADE...
│
├── ecossistema.py                     # Thin Facade (Roteador fino de linha de comando)
└── AGENTS.md                          # Governança Canônica com ponteiro para os módulos
```

---

## 4. Análise Profunda dos Ganhos

### 4.1. Manutenibilidade (Organização Intuitiva e Isolamento)
- **Princípio de Alta Coesão:** Cada pasta de módulo possui sua trinca viva: Código de Execução (`core`), Interface Agêntica (`skills`), Validações (`gates`) e Garantias (`tests`).
- **Zero Efeito Colateral:** Se você precisa alterar o conversor de banco do *Freedom*, você mexe estritamente em `modulos/02-triade-motores/fluxo-03-freedom/`. Nenhuma outra parte do repositório é tocada.
- **Onboarding e Descoberta Imediata:** Um desenvolvedor ou agente novo sabe exatamente onde cada funcionalidade nasce e morre apenas navegando pela árvore de pastas.

### 4.2. Performance de Uso e Economia Extrema de Tokens
- **Carregamento Cirúrgico de Contexto:** Em vez de fornecer todo o repositório ou dezenas de regras globais para o modelo de linguagem, o harness carrega apenas o `README.md` específico do módulo em edição (< 500 tokens).
- **Redução Drástica de Consumo:**
  - *Antes:* 40k a 90k tokens gastos em varreduras de arquivos soltos para resolver um ajuste simples.
  - *Depois:* Menos de 4k a 8k tokens no ciclo completo da tarefa.
- **Menor Latência:** Prompts enxutos geram respostas quase instantâneas dos modelos (Gemini Flash, Claude Sonnet, etc.).

### 4.3. Rastreabilidade de Bugs e Diagnóstico Rápido
- **Portões Vizinhos ao Código:** O portão de qualidade (`gate`) não fica perdido a quilômetros de distância; ele mora na mesma fatia vertical do código que valida.
- **Isolamento de Falha:** Se um teste ou portão reprovar, o caminho do arquivo no log já entrega exatamente a fatia responsável (`modulos/03-plataforma-e-entrega/...`).
- **Reprodução Determinística:** Fica trivial rodar os testes unitários e de integração de apenas uma fatia vertical isoladamente sem precisar acionar a bateria de testes do ecossistema inteiro.

---

## 5. Haverá Diferença de Uso para o Usuário Final?

**A resposta é: Nenhuma mudança traumática, apenas melhoria drástica de velocidade e acerto.**

### O que NÃO muda (Compatibilidade 100% Preservada):
1. **Linha de Comando Idêntica:** O comando principal `python ecossistema.py <comando>` continua funcionando exatamente igual. O `ecossistema.py` passa a atuar como uma **Fachada Fina (Thin Facade)** que apenas delega para o módulo correspondente.
2. **Slash Commands Inalterados:** Comandos como `/pure`, `/open`, `/freedom`, `/dispatch`, `/audit-4f`, `/evolucao` continuam operando da mesma forma em qualquer harness (Gemini/Antigravity, Claude Code, Cursor, OpenCode).
3. **Saídas e Contratos Padronizados:** Os arquivos gerados, artefatos de entrega e documentações mantêm a conformidade com as 13 Leis Invioláveis.

### O que MUDA para o usuário (Para Muito Melhor):
1. **Agentes Não Ficam Mais "Perdidos":** As IAs deixam de alucinar ou rodar em círculos buscando scripts perdidos em pastas desconexas.
2. **Tarefas Resolvidas em Minutos:** Bugs e novas funcionalidades são implementados em 1 a 3 passos diretos, sem estourar limites de contexto.
3. **Transparência Visual:** Ao abrir a pasta do projeto no VS Code / editor, você vê 4 diretórios limpos e autoexplicativos em vez de uma floresta de dezenas de pastas enigmáticas.
