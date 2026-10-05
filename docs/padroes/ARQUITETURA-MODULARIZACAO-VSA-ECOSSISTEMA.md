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

A anatomia canônica de qualquer módulo ou submódulo obedece a **12 camadas atômicas padronizadas + 2 documentos de contexto**, regidas pela regra de **Sparse Scaffolding** (pastas só são criadas quando contêm artefatos reais, sem stubs vazios):

```
modulos/<dominio>/ (ou modulos/<dominio>/<submodulo>/)
├── core/         # Código executivo, motores e lógica central da fatia
├── scripts/      # Scripts CLI locais e utilitários de automação interna
├── skills/       # Skills agênticas especializadas expostas aos agentes
├── mcps/         # Servidores MCP dedicados a este domínio (se houver)
├── hooks/        # Gatilhos locais de ciclo de vida e pre-commit
├── gates/        # Quality gates determinísticos exclusivos da fatia
├── tests/        # Testes unitários, de integração, e2e e provas de portão
├── contracts/    # Schemas JSON, contratos OpenAPI e tipos Pydantic
├── templates/    # Blueprints, scaffolds e esqueletos geráveis da fatia
├── prompts/      # Prompts de sistema fechados e personas do domínio
├── specs/        # Especificações executáveis e critérios de aceite (BDD)
├── docs/         # Documentação viva, diagramas e ADRs locais da fatia
├── README.md     # Guia executivo humano (< 500 tokens)
└── AGENTS.md     # Invariantes e leis locais da IA (< 400 tokens)
```

### 3.1. Distribuição dos Grandes Domínios

```
ecossistema-aidd/
│
├── modulos/
│   ├── 01-governanca-e-qualidade/     # O "Cérebro" de Regras, Diagnóstico e Auditoria
│   │   ├── core/                      # aidd-forge, orquestrador 4f, scaffold, compilador
│   │   ├── skills/                    # aidd-grill, aidd-spec, aidd-tdd, aidd-audit-4f, aidd-evolution
│   │   ├── gates/                     # G_DETERMINISMO, G_DOCS_ROT, G_PORTAO_PROVA_QUE_MORDE...
│   │   ├── tests/                     # Provas de portão e testes de integridade
│   │   ├── prompts/                   # Prompts das 4 fases (Inspetor, Arquiteto, Construtor, Retorno)
│   │   ├── docs/                      # Protocolos e convenções de autoria
│   │   ├── README.md                  # Contexto executivo (< 500 tokens)
│   │   └── AGENTS.md                  # Invariantes de governança (< 400 tokens)
│   │
│   ├── 02-triade-motores/             # A "Fábrica" de Software (Os 3 Fluxos Canônicos)
│   │   ├── fluxo-01-pure/             # Motor do Zero Puro (TDD Red-Green)
│   │   │   ├── core/                  # aidd-pure engine
│   │   │   ├── templates/             # TanStack Start, React, Tailwind PWA
│   │   │   ├── skills/                # aidd-pure
│   │   │   ├── gates/                 # G_STACK_PADRAO_OURO, G_TESTES_REAIS...
│   │   │   ├── tests/                 # Baterias TDD Red-Green
│   │   │   ├── README.md
│   │   │   └── AGENTS.md
│   │   ├── fluxo-02-open/             # Motor Open-Source Integrado
│   │   │   ├── core/                  # aidd-open factory, gerador de compose
│   │   │   ├── templates/             # Compose bases e stacks curadas
│   │   │   ├── skills/                # aidd-open
│   │   │   ├── gates/                 # G_INFRA_COMPOSE, G_COMPONENTE_AGNOSTICO...
│   │   │   ├── tests/
│   │   │   ├── README.md
│   │   │   └── AGENTS.md
│   │   └── fluxo-03-freedom/          # Motor de Libertação Low-Code
│   │       ├── core/                  # aidd-freedom bridge, conversores de DB
│   │       ├── scripts/               # Scripts de varredura e extração de schemas
│   │       ├── skills/                # aidd-freedom
│   │       ├── gates/                 # G_ANT_LOCKIN_LEGADO, G_MIGRATION_ROT...
│   │       ├── tests/
│   │       ├── README.md
│   │       └── AGENTS.md
│   │
│   ├── 03-plataforma-e-entrega/       # A "Esteira" de Harmonização e Produção
│   │   ├── fatiamento-master/         # aidd-master, mesocamada VSA, dispatch worktrees
│   │   ├── blindagem-enterprise/      # aidd-enterprise, injeção SHA-256
│   │   ├── operacoes-ops/             # aidd-ops, VPS sizing, Docker, SOPS+Age, Cloudflare
│   │   ├── quarteto-studios/          # OpenAPI (/api), Webhooks, MCP Studio, Docs (/docs)
│   │   ├── skills/                    # aidd-master, aidd-dispatch, aidd-enterprise, aidd-ops
│   │   ├── gates/                     # G_QUARTETO_SINE_QUA_NON, G_ISOLATION_AUDIT...
│   │   ├── contracts/                 # Schemas universais do Quarteto
│   │   ├── tests/
│   │   ├── README.md
│   │   └── AGENTS.md
│   │
│   └── 04-nucleo-compartilhado/       # O "Chassi" Comum (Kernel & Facade)
│       ├── cli/                       # Fachada de comandos e roteamento central
│       ├── sync/                      # Sincronizador agnóstico de harnesses
│       ├── contracts/                 # Schemas JSON universais (PLANNER, DISPATCH, HANDOFF)
│       ├── scripts/                   # Utilitários determinísticos de AST, Git e filesystem
│       ├── gates/                     # G_SAIDA_BINARIA, G_ECOSSISTEMA_INTEGRIDADE...
│       ├── tests/
│       ├── README.md
│       └── AGENTS.md
│
├── ecossistema.py                     # Thin Facade (Roteador fino de linha de comando)
└── AGENTS.md                          # Governança Canônica Global com Despacho Topológico
```

---

## 4. Autocontenção de Contexto por Módulo: README, AGENTS e MCPs

Para viabilizar a economia extrema de tokens e eliminar a confusão cognitiva, a gestão de regras e contexto segue uma disciplina em dois níveis (Local vs. Global):

### 4.1. O que reside dentro de CADA MÓDULO (`modulos/<fatia>/`)
Cada fatia vertical funciona como um subdomínio autocontido baseado nas 12 camadas atômicas:
1. **`README.md` (< 500 tokens):** Visão executiva da fatia, lista de comandos suportados, dependências internas e exemplos de uso direto.
2. **`AGENTS.md` Local (< 400 tokens):** Regras, invariantes de código e contratos específicos daquela fatia (ex: no *Freedom*, regras de substituição do Supabase; no *Pure*, o ciclo TDD Red-Green).
3. **`mcps/` ou Ferramentas MCP de Domínio:** Servidores MCP especializados residem dentro de sua própria pasta de domínio.
4. **`contracts/` e `specs/`:** Schemas formais e especificações de comportamento executáveis daquela fatia.
5. **`prompts/` e `templates/`:** Prompts isolados e modelos geráveis livres de acoplamento com outros fluxos.

### 4.2. O que permanece GLOBAL na Raiz do Repositório
A raiz deixa de acumular dezenas de manuais e regras pontuais, contendo exclusivamente:
1. **`AGENTS.md` Raiz:** Apenas as 13 Leis Invioláveis do Ecossistema e a Tabela de Despacho Topológico (Dispatch Table) que aponta para o `AGENTS.md` de cada módulo.
2. **Registro Agregado de MCPs (`.mcp` / harnesses):** O script `components sync` compila automaticamente os MCPs declarados nos módulos para a configuração do harness do desenvolvedor.
3. **`ecossistema.py`:** Fachada fina de execução de comandos.

### 4.3. Princípio Fractal: Submódulos Autocontidos e Idempotentes
A arquitetura é **fractal (auto-similar)**: qualquer módulo que agregue fluxos distintos (como `02-triade-motores/`) reproduz obrigatoriamente a mesma regra de autocontenção para cada um dos seus submódulos:
- Cada fluxo (`fluxo-01-pure/`, `fluxo-02-open/`, `fluxo-03-freedom/`) possui seu próprio `core/`, `skills/`, `gates/`, `tests/`, `README.md` e `AGENTS.md`.
- **Idempotência Estrita:** Qualquer comando executado dentro de um submódulo (geração de código, conversão de schemas, build de docker-compose) é estritamente idempotente — rodar 1 ou 100 vezes gera exatamente o mesmo resultado determinístico, sem efeitos colaterais em submódulos vizinhos.

---

## 5. Análise Profunda dos Ganhos

### 5.1. Manutenibilidade (Organização Intuitiva e Isolamento)
- **Princípio de Alta Coesão:** Cada pasta de módulo possui sua trinca viva: Código de Execução (`core`), Interface Agêntica (`skills`), Validações (`gates`) e Garantias (`tests`).
- **Zero Efeito Colateral:** Se você precisa alterar o conversor de banco do *Freedom*, você mexe estritamente em `modulos/02-triade-motores/fluxo-03-freedom/`. Nenhuma outra parte do repositório é tocada.
- **Onboarding e Descoberta Imediata:** Um desenvolvedor ou agente novo sabe exatamente onde cada funcionalidade nasce e morre apenas navegando pela árvore de pastas.

### 5.2. Performance de Uso e Economia Extrema de Tokens
- **Carregamento Cirúrgico de Contexto:** Em vez de fornecer todo o repositório ou dezenas de regras globais para o modelo de linguagem, o harness carrega apenas o `README.md` específico do módulo em edição (< 500 tokens).
- **Redução Drástica de Consumo:**
  - *Antes:* 40k a 90k tokens gastos em varreduras de arquivos soltos para resolver um ajuste simples.
  - *Depois:* Menos de 4k a 8k tokens no ciclo completo da tarefa.
- **Menor Latência:** Prompts enxutos geram respostas quase instantâneas dos modelos (Gemini Flash, Claude Sonnet, etc.).

### 5.3. Rastreabilidade de Bugs e Diagnóstico Rápido
- **Portões Vizinhos ao Código:** O portão de qualidade (`gate`) não fica perdido a quilômetros de distância; ele mora na mesma fatia vertical do código que valida.
- **Isolamento de Falha:** Se um teste ou portão reprovar, o caminho do arquivo no log já entrega exatamente a fatia responsável (`modulos/03-plataforma-e-entrega/...`).
- **Reprodução Determinística:** Fica trivial rodar os testes unitários e de integração de apenas uma fatia vertical isoladamente sem precisar acionar a bateria de testes do ecossistema inteiro.

---

## 6. Haverá Diferença de Uso para o Usuário Final?

**A resposta é: Nenhuma mudança traumática, apenas melhoria drástica de velocidade e acerto.**

### O que NÃO muda (Compatibilidade 100% Preservada):
1. **Linha de Comando Idêntica:** O comando principal `python ecossistema.py <comando>` continua funcionando exatamente igual. O `ecossistema.py` passa a atuar como uma **Fachada Fina (Thin Facade)** que apenas delega para o módulo correspondente.
2. **Slash Commands Inalterados:** Comandos como `/pure`, `/open`, `/freedom`, `/dispatch`, `/audit-4f`, `/evolucao` continuam operando da mesma forma em qualquer harness (Gemini/Antigravity, Claude Code, Cursor, OpenCode).
3. **Saídas e Contratos Padronizados:** Os arquivos gerados, artefatos de entrega e documentações mantêm a conformidade com as 13 Leis Invioláveis.

### O que MUDA para o usuário (Para Muito Melhor):
1. **Agentes Não Ficam Mais "Perdidos":** As IAs deixam de alucinar ou rodar em círculos buscando scripts perdidos em pastas desconexas.
2. **Tarefas Resolvidas em Minutos:** Bugs e novas funcionalidades são implementados em 1 a 3 passos diretos, sem estourar limites de contexto.
3. **Transparência Visual:** Ao abrir a pasta do projeto no VS Code / editor, você vê 4 diretórios limpos e autoexplicativos em vez de uma floresta de dezenas de pastas enigmáticas.

---

## 7. Salvaguardas Técnicas e Invariantes de Implementação

Para garantir que a arquitetura não sofra degradação ou acoplamento acidental ao longo do tempo, 6 garantias técnicas são formalmente incorporadas:

1. **Lazy Import Dinâmico na Fachada CLI (`ecossistema.py`):**
   - O roteador central não importa módulos antecipadamente. Utiliza carregamento dinâmico via `importlib` sob demanda, reduzindo o tempo de boot do CLI para ~15ms.
2. **Portão de Fronteira Estrita via AST (`G_MODULO_FRONTEIRA.py`):**
   - Quality gate determinístico que inspeciona a árvore sintática dos arquivos Python e bloqueia (`exit 1`) importações cruzadas não autorizadas entre módulos sem passar pelas APIs públicas oficiais (`__all__` / `interface.py`).
3. **Micro-Gates de Commit com Escopo Cirúrgico:**
   - Durante o desenvolvimento, o hook de pre-commit detecta o `git diff` e dispara apenas os testes e portões da fatia vertical modificada. A bateria completa de 54 macro-gates é acionada na barreira final de integração.
4. **Camada de Aliases e Retrocompatibilidade Invisível:**
   - Proxies leves nos caminhos herdados (`tools/`, `gates/`) garantem que referências em scripts externos ou comandos antigos continuem funcionando com avisos informativos durante o período de transição.
5. **Grafos Federados por Módulo no codebase-memory-mcp:**
   - Substituição do grafo monolítico global por subgrafos indexados por domínio (`aidd-nucleo`, `modulo-governanca`, `triade-fluxo-pure`, `triade-fluxo-open`, `triade-fluxo-freedom`, `modulo-plataforma-ops`). O agente consulta primeiro o subgrafo específico do módulo em edição, obtendo blast radius cirúrgico (< 10 nós), reindexação incremental rápida e consumo de tokens inferior a 300 tokens por consulta MCP.
6. **Poda Ativa de Inchaço e Escopo Cirúrgico de Skills (Context Pruning & Lazy Scoping):**
   - Eliminação da injeção estática e desenfreada de dezenas de skills irrelevantes no prompt de sistema. Cada módulo passa a declarar apenas as skills e MCPs estritamente necessários para sua execução. Skills especializadas ou de uso esporádico (ex: utilitários científicos, manipuladores office) são isoladas em plugins sob demanda e desativadas do perfil de desenvolvimento padrão, erradicando a queima silenciosa de 10.000 a 20.000 tokens a cada mensagem.

