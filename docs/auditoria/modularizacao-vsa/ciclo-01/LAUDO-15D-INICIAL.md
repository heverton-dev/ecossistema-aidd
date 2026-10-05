# Template de Auditoria de Ferramenta (Lens 15-D) — modularizacao-vsa (Ciclo 01)

Este documento descreve a estrutura canônica para auditar a arquitetura do ecossistema AIDD, dissecando sua arquitetura através do framework Lens 15-D (The Agentic Anatomical Matrix) com foco em 'modularizacao-vsa' (Vertical Slice Architecture e Monólito Modular).

## 1. Identificação da Ferramenta
- **Nome da Ferramenta:** `modularizacao-vsa` (Arquitetura do Ecossistema AIDD)
- **Descrição Breve:** Estruturação arquitetural global do ecossistema-aidd para transição de camadas técnicas horizontais dispersas (`tools/`, `gates/`, `componentes/`, `.agents/skills/`) para Monólito Modular orientado a Vertical Slice Architecture (VSA).
- **Comando de Gatilho:** `python ecossistema.py <comando>` / `python ecossistema.py modularizacao-vsa` (previsto no DoD)

---

## 2. A Matriz Anatômica (Lens 15-D)

### Fase 1: Governança e Blindagem
- **D1. Contratos e Regras:**
  - *Estado Atual:* As regras de governança estão espalhadas entre `AGENTS.md`, `CLAUDE.md`, `docs/padroes/` e diretivas dispersas. Embora existam 13 Leis Canônicas declaradas em `AGENTS.md`, o ecossistema opera organizado por camadas técnicas horizontais (`tools/`, `gates/`, `componentes/`, `scripts/`). A especificação canônica proposta em `docs/padroes/ARQUITETURA-MODULARIZACAO-VSA-ECOSSISTEMA.md` define 4 macro-módulos verticais (`01-governanca-e-qualidade`, `02-triade-motores`, `03-plataforma-e-entrega`, `04-nucleo-compartilhado`), mas não há contrato estrutural formal em código que force essa contenção hoje.
  - *Nota:* 3 / 10 (Contratos apenas documentais sem garantia sintática estrutural de fronteira).
- **D2. Input e Gatilhos:**
  - *Estado Atual:* Entrada centralizada através do monólito de despacho `ecossistema.py:1485` (`comandos_disponiveis()`), que mapeia 54+ comandos e apelidos legados. O subcomando específico `python ecossistema.py modularizacao-vsa` exigido pelo DoD 1 (D4) ainda não está implementado na CLI raiz, retornando erro `comando desconhecido`.
  - *Nota:* 4 / 10 (Despacho monolítico funcional para ferramentas legadas, ausente para `modularizacao-vsa`).
- **D3. Raio de Impacto e Isolamento:**
  - *Estado Atual:* Faltam barreiras físicas de isolamento entre domínios. A pasta `tools/` abriga 8 ferramentas heterogêneas (`aidd-enterprise`, `aidd-forge`, `aidd-freedom`, `aidd-master`, `aidd-open`, `aidd-ops`, `aidd-planner`, `aidd-pure`). A ferramenta `aidd-master` realiza chamadas diretas para múltiplos domínios (fan-out=940 e 463 chamadas para `compartilhado`, conforme apurado no grafo). Qualquer alteração em `tools/` ou `gates/` tem raio de impacto irrestrito sobre todo o repositório. O isolamento em Git Worktrees efêmeras só ocorre quando disparado por scripts específicos de orquestração externa, não sendo intrínseco aos módulos.
  - *Nota:* 2 / 10 (Ausência de isolamento por subdomínio; blast radius descontrolado).
- **D4. Componentes e Fractalidade:**
  - *Estado Atual:* Severa dispersão horizontal. Existem 43 skills duplicadas em `.agents/skills/` e replicadas em `componentes/compartilhado/skills/` (gerando espelhamento forçado para 7 harnesses via `gestor_componentes.py`). As ferramentas em `tools/` não possuem estrutura fractal autocontida de `skills/`, `gates/`, `tests/` e `README.md` (< 500 tokens). Por exemplo, `gates/` abriga 69 arquivos soltos na raiz horizontal de validação em vez de alocar cada gate junto à sua respectiva fatia vertical.
  - *Nota:* 2 / 10 (Inchaço de contexto e ausência de autocontenção fractal nos submódulos).

### Fase 2: O Chão de Fábrica (Workflow Agêntico)
- **D5. Visão e Escopo:**
  - *Estado Atual:* A visão arquitetural visa migrar o ecossistema de uma estrutura horizontal inflada para fatias verticais VSA autocontidas por domínio de capacidade, reduzindo o consumo de tokens de 40k-90k para 4k-8k por tarefa. No estado atual, essa visão existe como especificação técnica (`ARQUITETURA-MODULARIZACAO-VSA-ECOSSISTEMA.md`), mas o chão de fábrica real ainda opera no modelo antigo de ferramentas isoladas e gates globais centralizados.
  - *Nota:* 5 / 10 (Visão sólida e documentada, mas pendente de materialização estrutural).
- **[Estágio 1 - Governança e Regras] D6. O que o Estágio Faz:** Centraliza regras de auditoria, diagnóstico e compilação de planos (aidd-forge, orquestrador 4F, scaffolds).
- **[Estágio 1 - Governança e Regras] D7. O que o Estágio Recebe:** Demandas de evolução, planos de auditoria, laudos e requisições de scaffold.
- **[Estágio 1 - Governança e Regras] D8. O que o Estágio Processa:** Fatores de acoplamento: ferramentas de governança (`tools/aidd-forge`) estão desconectadas das skills de governança (`.agents/skills/aidd-audit-4f`, `aidd-grill`, `aidd-spec`) e dos gates de integridade em `gates/`. O processamento depende de scripts soltos em `scripts/` (`orquestrador_4f.py`, `scaffold_auditoria.py`).
- **[Estágio 1 - Governança e Regras] D9. O que o Estágio Entrega:** Manifestos de ciclo, planos compilados e validações de conformidade.
- **[Estágio 2 - Motores de Geração (Tríade)] D6. O que o Estágio Faz:** Executa a geração e transformação de software através dos 3 fluxos canônicos (Pure: do zero com TDD; Open: open-source integrado; Freedom: conversão low-code).
- **[Estágio 2 - Motores de Geração (Tríade)] D7. O que o Estágio Recebe:** Especificações funcionais, templates, schemas de banco e requisitos de infraestrutura.
- **[Estágio 2 - Motores de Geração (Tríade)] D8. O que o Estágio Processa:** Os motores residem soltos em `tools/aidd-pure`, `tools/aidd-open` e `tools/aidd-freedom`, enquanto seus templates e catalogo estão dispersos entre `componentes/compartilhado/templates` e subpastas de ferramentas, exigindo importações cruzadas e busca cega de arquivos pelo harness.
- **[Estágio 2 - Motores de Geração (Tríade)] D9. O que o Estágio Entrega:** Código-fonte gerado, arquitetura base e baterias de testes.
- **[Estágio 3 - Plataforma e Operações] D6. O que o Estágio Faz:** Fatiamento, blindagem corporativa e esteira de infraestrutura/deploy (aidd-master, aidd-enterprise, aidd-ops).
- **[Estágio 3 - Plataforma e Operações] D7. O que o Estágio Recebe:** Aplicações prontas para homologação, fatiamento em worktrees ou deploy.
- **[Estágio 3 - Plataforma e Operações] D8. O que o Estágio Processa:** Alto acoplamento técnico. `aidd-master` atua como hotspot com 696 execuções de dispatch registradas no grafo, chamando intensivamente `compartilhado` e rotas estáticas sem encapsulamento de API pública.
- **[Estágio 3 - Plataforma e Operações] D9. O que o Estágio Entrega:** Pacotes docker, infraestrutura configurada e worktrees despachadas.
- **D10. Orquestração e Topologia:**
  - *Estado Atual:* Topologia híbrida desarticulada. A orquestração depende de scripts ad-hoc na raiz de `scripts/` (`orquestrador_4f.py`, `orquestrador_sincrono.py`, `faz_commit.py`) que realizam varreduras brutas e subprocessos diretos, sem barramento de eventos ou contratos tipados formais de handoff entre os estágios.
  - *Nota:* 3 / 10 (Falta de padronização topológica entre motores e plataforma).

### Fase 3: Resiliência e Economia (Engenharia Operacional)
- **D11. Tratamento de Exceções e Fallback:**
  - *Estado Atual:* Falta de resiliência estruturada e ausência de retries idempotentes universais. Comandos como `ecossistema.py dependencia verify/bootstrap` interrompem bruscamente com falha de hash (ex: divergência em `impeccable`) sem estratégias de autocura ou isolamento por fatia. Se um componente falha, o ecossistema inteiro é bloqueado no pre-commit ou na CLI.
  - *Nota:* 3 / 10 (Falha em cascata sem fallback local por fatia de domínio).
- **D12. Observabilidade e Frugalidade:**
  - *Estado Atual:* Severo desperdício de tokens. A injeção estática e redundante de dezenas de skills nos harnesses consome de 15.000 a 30.000 tokens de contexto logo no início de cada sessão (conforme evidenciado pela lista massiva de skills declaradas no preâmbulo). A ausência de grafos federados por módulo força consultas ao grafo global (67.980 nós e 210.696 arestas), aumentando o ruído e o custo computacional.
  - *Nota:* 2 / 10 (Token bloat crítico; sem poda de contexto nem lazy-loading).

### Fase 4: O Inspetor e a Expedição (Validação)
- **D13. Quality Gates (Portões):**
  - *Estado Atual:* O ecossistema possui 69 quality gates em `gates/`, mas todos operam horizontalmente. O gate específico de conformidade de fatias verticais (`gates/G_MODULO_FRONTEIRA.py`) e o portão determinístico `gates/G_modularizacao_vsa.py` (exigido no DoD 6) ainda não foram criados. Não existe portão que barre via AST importações cruzadas proibidas entre as ferramentas em `tools/`.
  - *Nota:* 2 / 10 (Macro-gates horizontais existentes, mas ausência de gate de fronteira VSA).
- **D14. Critério de Rejeição (Rollback):**
  - *Estado Atual:* Ausência de mecanismo determinístico de rollback de arquivos corrompidos ou fatias incompletas em caso de falha de execução. Se um script em `tools/` ou `scripts/` falha no meio do processo, arquivos residuais sobrevivem no workspace sem limpeza garantida.
  - *Nota:* 2 / 10 (Sem rollback transacional em caso de erro no processo de geração/transformação).
- **D15. Output Consolidado e Handoff:**
  - *Estado Atual:* Inexistência de um manifesto formal de modularização (`MANIFESTO-MODULOS.json`) ou contratos universais de handoff entre as camadas. A comunicação entre ferramentas é feita via escrita solta de arquivos em diretórios transitórios sem assinatura criptográfica de integridade.
  - *Nota:* 2 / 10 (Handoff frágil, não estruturado entre ferramentas).

---

## 3. Matriz de Avaliação da Execução
- [ ] A ferramenta isolou seu raio de impacto corretamente?
- [ ] O workflow seguiu as fases sem alucinações de LLM em tarefas mecânicas?
- [ ] O output final passou em todos os Quality Gates e emitiu o Handoff?

**Nota Geral da Arquitetura Atual:** 2.5 / 10.  
**Diagnóstico:** Arquitetura horizontal clássica com alto acoplamento (hotspots em `aidd-master`), inchaço de contexto por replicação de 43 skills e ausência de gates de fronteira sintática. A transição para VSA em `modulos/` é urgente para estancar a queima de tokens e conferir estabilidade operacional.
