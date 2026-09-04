# Análise Técnica, Posicionamento Realista e Roadmap de Superação — aidd-generator

> **Documento:** Posicionamento Factual, Limitações Inerentes e Estratégia de Evolução Arquitetural.  
> **Framework / Ferramenta:** `aidd-generator` (Versão: 2.1 / Tag/Commit: `7d63085` em `main`).  
> **Repositório:** `https://github.com/heverton-dev/aidd-generator`  
> **Objetivo:** Estabelecer com rigor de engenharia o que o gerador entrega, suas fronteiras técnicas reais auditadas em produção e o roadmap concreto de superação.

---

## 1. O Que o `aidd-generator` É (Posicionamento Factual)

O **`aidd-generator`** é um **Gerador Autônomo de Projetos de Software baseado na Metodologia AIDD (AI-Driven Development)**, concebido com a visão de ser um *"Lovable turbinado com AIDD"*. Ele recebe uma ideia descrita em linguagem natural e percorre um pipeline de 7 a 8 fases sequenciais para produzir um projeto completo de software: contratos/schemas JSON, scripts Python, testes automatizados, documentação detalhada e — opcionalmente — código funcional gerado e corrigido automaticamente por IA.

Sua arquitetura assenta-se nas **5 Camadas de Engenharia Agêntica**:
1. **Contratos e Schemas Rígidos:** Modelagem prévia via JSON Schema Draft 2020-12, garantindo que os dados tenham tipagem estrita antes do código existir.
2. **Determinismo Primeiro (Zero Token):** Todas as rotinas mecânicas (estruturação de diretórios, validação AST, scaffolding e compilação de artefatos) rodam em Python puro local, sem gastar tokens de LLM.
3. **Gates Mecânicos Bloqueantes:** Validações binárias estritas (`exit 0` para aprovação e `exit 1` para bloqueio), eliminando qualquer falha silenciosa ou propagação de erros em cascata.
4. **Persistência Estruturada:** O estado de execução, o plano do projeto e os rastros de métricas são salvos em JSONs estruturados (`PLANO-EXECUCAO-ESTRUTURADO.json` e cache em `.aidd/cache/data/`).
5. **Universalidade e Protocolo Delegado:** Compatibilidade agnóstica com qualquer Ambiente de Desenvolvimento Agêntico (Claude Code, Gemini CLI, Cursor, OpenCode, MimoCode) através do protocolo delegado de troca de arquivos, com fallback headless via `litellm` (TogetherAI, Groq, NVIDIA NIM, OpenRouter).

---

## 2. Limitações Técnicas Reais Identificadas (Base Factual de Auditoria)

A auditoria interna de produção e a análise empírica do repositório revelam **6 fronteiras técnicas reais**:

| # | Limitação Técnica Real | Impacto Prático no `aidd-generator` |
| :---: | :--- | :--- |
| **1** | **Taxa de Sucesso Probabilística da Fase 8 (55% a 91%)** | A geração de código funcional executável via LLM não atinge 100% de acerto determinístico. O loop de autocorreção mitiga erros de sintaxe e testes básicos, mas projetos complexos exigem intervenção humana (`requer_intervencao_manual: true`). |
| **2** | **Ausência de Fallback Automático Delegado ➔ Headless** | Se o orquestrador/ADE não responder no tempo estipulado em modo delegado, o pipeline dispara timeout em vez de chavear dinamicamente para o provedor headless configurado no `.env`. |
| **3** | **Falta de Testes de Integração Cruzada Cross-Script** | A Fase 8 gera testes unitários isolados por script. Falhas de contrato entre scripts interdependentes (ex: script A gera um retorno consumido de forma incompatível pelo script B) podem passar despercebidas se não houver suíte E2E composta. |
| **4** | **Generalização de Tipos Complexos em SQLite / JSON** | Schemas que utilizam estruturas JSON aninhadas e relações com chaves estrangeiras complexas podem apresentar inconsistências de serialização e desserialização no código gerado. |
| **5** | **Persistência de Cache Baseada em Arquivos Locais** | O cache das fases e os estados do pipeline são mantidos em arquivos JSON sob `.aidd/cache/data/`. Não há replicação distribuída ou suporte nativo para múltiplos nós sem compartilhamento de sistema de arquivos. |
| **6** | **Dependência de Latência e Janela de Contexto de Provedores LLM** | Provedores com rate limits restritivos ou latências elevadas podem gerar estouro de timeout durante as chamadas da Fase 3 (5 subagentes) e da Fase 8 (loop de correção). |

---

## 3. Roadmap de Superação: Como Vencer as Limitações

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                         ROADMAP DE SUPERAÇÃO (v2.2 ➔ v3.0)                       │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  VERSÃO v2.2: RESILIÊNCIA DE PROTOCOLO & VALIDAÇÃO END-TO-END                    │
│  ├── 1. Fallback Automático Transparente (Modo Delegado ➔ Headless no Timeout)  │
│  ├── 2. Validador de Fluxo Cross-Script (Gate I3 de Integração Contínua)         │
│  ├── 3. Suporte Aprofundado a Tipos JSON Ricos e Validação de FK em SQLite       │
│  └── 4. Cache Incremental com Hash SHA-256 de Schemas e Prompts                  │
│                                                                                  │
│  VERSÃO v3.0: AUTO-HEALING DISTRIBUÍDO & MULTI-AGENT SWARM                      │
│  ├── 5. Loop de Correção Multi-LLM em Consenso (Juiz + Implementador)            │
│  ├── 6. Orquestração com Worktrees Paralelas via ORCA Integrado                  │
│  └── 7. Gerador de Código Poliglota (Python + TypeScript / FastAPI + React)      │
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Detalhamento das Soluções de Engenharia

### A. Fallback Automático Delegado ➔ Headless
- **Como superar:** Refatorar o módulo `scripts/phases/utils_delegacao.py`.
- **Implementação:** Quando uma chamada em modo delegado aguardar mais de 30 segundos sem que a ADE responda ao arquivo `_llm_request_*.json`, o sistema emite um log estruturado, comuta imediatamente para o cliente `litellm` utilizando as credenciais salvas no `.env`, conclui a etapa e registra no índice da fase a ocorrência do fallback.

### B. Integração Cross-Script e Gate I3
- **Como superar:** Implementar um verificador estático e gerador de testes de fluxo completo pós-Fase 8.
- **Implementação:** Uma rotina analisa a AST de todos os scripts gerados, mapeia chamadas entre módulos e constrói o arquivo `tests/test_fluxo_integrado.py`, que executa o ciclo de vida ponta a ponta dos dados gerados, garantindo que retornos (como IDs e objetos persistidos) satisfaçam os parâmetros de entrada dos scripts consumidores.

### C. Elevação da Confiabilidade da Fase 8
- **Como superar:** Decomposição em etapas atômicas com verificação intermediária de tipos.
- **Implementação:** Em vez de gerar o script completo em um único bloco, o implementador sintetiza separadamente: modelos de dados ➔ funções de serviço ➔ rotinas de persistência ➔ testes de mutação. Cada bloco passa por linter AST antes de ser montado no arquivo final.
