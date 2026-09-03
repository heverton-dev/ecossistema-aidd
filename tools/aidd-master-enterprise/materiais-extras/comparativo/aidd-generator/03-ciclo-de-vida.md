# Ciclo de Vida Completo — aidd-generator (v2.1 / Commit `7d63085`)

## 1. Visão Geral do Ciclo de Execução

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ FASE 0: PREPARAÇÃO, DIAGNÓSTICO E PRÉ-VOO                                   │
│ 1. Clonagem e verificação do ambiente Python (>= 3.10)                      │
│ 2. Instalação das dependências (requirements.txt / requirements-dev.txt)    │
│ 3. Verificação de LLM ativo via scripts/preflight_llm.py                    │
│ 4. Inicialização da Interface Web Local (python web_app.py) ou CLI direta   │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ FASE 1: PESQUISA E COLETA DE REQUISITOS (01_pesquisador.py)                 │
│ 1. Entrada da ideia em linguagem natural pelo usuário                      │
│ 2. Decomposição semântica determinística (Python puro, Zero Token)          │
│ 3. Identificação do domínio, escopo, atores e fluxos primários             │
│ 4. Persistência do relatório e dados em .aidd/cache/data/_phase_01_*.json   │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ FASE 2: ANÁLISE E DECOMPOSIÇÃO CONTRATUAL (02_analisador.py)                │
│ 1. Síntese de domínio e entidades com LLM (Delegado ou Headless)            │
│ 2. Definição formal das entidades, relacionamentos e regras de negócio      │
│ 3. Rastreamento estrito de tokens consumidos e modelo utilizado              │
│ 4. Registro no banco de verdade e persistência dos dados da Fase 2          │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ FASE 3: DESIGN E ARQUITETURA SISTÊMICA (03_designer.py)                     │
│ 1. Orquestração de 5 subagentes especializados em paralelo/sequencial:       │
│    - Subagente de Banco de Dados e Persistência                             │
│    - Subagente de Schemas e Contratos JSON                                  │
│    - Subagente de Módulos e Componentes                                     │
│    - Subagente de Estratégia de Testes                                      │
│    - Subagente de UX e Fluxo de Uso                                         │
│ 2. Produção de JSON Schemas estritos (Draft 2020-12)                        │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ FASE 4: DECISÕES TÉCNICAS E PILHA TECNOLÓGICA (04_decisor.py)               │
│ 1. Seleção determinística ou interativa da pilha de tecnologias             │
│ 2. Definição do motor de banco (SQLite WAL), bibliotecas e convenções       │
│ 3. Validação dos critérios de compatibilidade arquitetural                  │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ FASE 5: CRIAÇÃO DE ARTEFATOS MECÂNICOS E SCAFFOLDING (05_criador.py)        │
│ 1. Geração da árvore de diretórios do projeto de destino                     │
│ 2. Escrita dos contratos JSON Schemas validados em schemas/                 │
│ 3. Criação de scripts base, testes iniciais e arquivos de infraestrutura    │
│ 4. Geração do manifesto PLANO-EXECUCAO-ESTRUTURADO.json no projeto gerado   │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
        ┌──────────────────────────────┴──────────────────────────────┐
        │ SE --implementar-codigo ATIVADO                             │ NÃO ATIVADO
        ▼                                                             ▼
┌──────────────────────────────────────────────┐                      │
│ FASE 8: IMPLEMENTAÇÃO FUNCIONAL (08_*.py)    │                      │
│ 1. Síntese de scripts Python funcionais      │                      │
│ 2. Geração automática de suíte de testes     │                      │
│ 3. Execução real com pytest em loop          │                      │
│ 4. Auto-correção via LLM (até N tentativas)  │                      │
│ 5. Relato honesto de status (OK / FALHOU)    │                      │
└──────────────────────┬───────────────────────┘                      │
                       │                                              │
                       └──────────────────────┬───────────────────────┘
                                              │
                                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ FASE 6: DOCUMENTAÇÃO COMPLETA E VIVA (06_documentador.py)                   │
│ 1. Leitura do estado real gerado (reflete código da Fase 8 se houver)       │
│ 2. Geração de README.md detalhado, guias de arquitetura e exemplos de uso    │
│ 3. Documentação de endpoints, contratos e instruções de execução            │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ FASE 7: AUTOCRÍTICA, AUDITORIA CEGA E GATES (07_analisador.py)              │
│ 1. Auditoria cega de conformidade com os schemas e contratos                │
│ 2. Execução dos gates mecânicos bloqueantes (segredos, schemas, sintaxe)     │
│ 3. Geração do relatório final de qualidade e integridade do projeto         │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. As 5 Camadas da Metodologia AIDD Implementadas

| # | Camada AIDD | Implementação no `aidd-generator` | Risco Eliminado |
| :---: | :--- | :--- | :--- |
| **1** | **Contratos e Schemas** | JSON Schema Draft 2020-12 gerados na Fase 3 e validados estritamente na Fase 5. | Ambiguidade de tipos e inconsistência entre módulos. |
| **2** | **Determinismo Primeiro** | Fases 1, 4 (modo auto), 5 e checagens executadas em Python puro (Zero Token). | Desperdício desnecessário de tokens e alucinações em tarefas mecânicas. |
| **3** | **Gates Mecânicos** | Scripts dedicados em `scripts/gates/` com retorno binário `exit 0` / `exit 1`. | Liberação de projetos com segredos vazados ou contratos quebrados. |
| **4** | **Persistência Estruturada** | Gravação de dados reais em `.aidd/cache/data/` e atualização do plano JSON. | Perda de contexto entre etapas e alucinações cumulativas. |
| **5** | **Bundles Modulares** | Projeto entregue na pasta `--pasta` de forma autocontida e com testes próprios. | Código espalhado ou dependência de ambiente externo não documentado. |

---

## 3. Ordem Estratégica do Pipeline com Implementação Funcional

Um dos diferenciais arquiteturais do `aidd-generator` é a ordenação estrita quando o parâmetro `--implementar-codigo` é acionado:

- **Fluxo Convencional (Design e Scaffold):** `1 ➔ 2 ➔ 3 ➔ 4 ➔ 5 ➔ 6 ➔ 7`
- **Fluxo com Implementação Funcional:** `1 ➔ 2 ➔ 3 ➔ 4 ➔ 5 ➔ 8 ➔ 6 ➔ 7`

A **Fase 8 roda ANTES da Fase 6 e da Fase 7**. Essa inversão garante que:
1. A **Documentação (Fase 6)** descreve o código real existente, com suas funções, parâmetros e comportamentos efetivos, em vez de descrever uma intenção teórica de design.
2. A **Autocrítica e Auditoria (Fase 7)** audita o projeto completo implementado, verificando se os testes reais passaram e se há inconsistências no produto entregue.
