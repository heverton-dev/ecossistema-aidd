# Template de Auditoria de Ferramenta (Lens 15-D)

Este documento descreve a estrutura canônica para auditar qualquer ferramenta (Skill/Tool) do ecossistema, dissecando sua arquitetura através do framework Lens 15-D (The Agentic Anatomical Matrix).

## 1. Identificação da Ferramenta
- **Nome da Ferramenta:** `aidd-componentes` (`aidd-components`, `componentes-runner`)
- **Descrição Breve:** Gerenciamento, distribuição e sincronização determinística de componentes agnósticos (skills, mcps, comandos, hooks, scripts, specs) da fonte soberana `componentes/` para todos os harnesses com verificação SHA-256.
- **Comando de Gatilho:** `/aidd-components`, `/componentes`, `python ecossistema.py components sync|verify`

## 2. A Matriz Anatômica (Lens 15-D)

### Fase 1: Governança e Blindagem
- **D1. Contratos e Regras:** Contrato formalizado em `gates/manifesto_harnesses.json`, definindo mapeamento exato de tipos de componentes e diretórios de destino em cada harness. Proibição estrita de edição manual em pastas de harnesses.
- **D2. Input e Gatilhos:** Comandos via CLI determinística `python ecossistema.py components sync --tipo <tipo>` e `python ecossistema.py components verify --tipo <tipo>`.
- **D3. Raio de Impacto e Isolamento:** Operações de escrita restritas aos diretórios de destino mapeados nos harnesses (`.claude/`, `.agents/`, `.opencode/`, `.gemini/`, `.cursor/`, etc.). Preservação da integridade de arquivos soberanos em `componentes/`.
- **D4. Componentes e Fractalidade:** Motor modularizado em `scripts/gestor_componentes.py` e integrado organicamente à CLI raiz unificada em `ecossistema.py`.

### Fase 2: O Chão de Fábrica (Workflow Agêntico)
- **D5. Visão e Escopo:** Garantir paridade bit a bit absoluta entre a fonte única da verdade e os 7 harnesses agênticos do ecossistema.
  - **[Estágio 1 - Leitura e Descoberta] D6. O que o Estágio Faz:** Lê a árvore soberana em `componentes/` e o manifesto de harnesses.
  - **[Estágio 1 - Leitura e Descoberta] D7. O que o Estágio Recebe:** Parâmetros de tipo (`skills`, `mcps`, `todos`) e escopo.
  - **[Estágio 1 - Leitura e Descoberta] D8. O que o Estágio Processa:** Indexação e cálculo de hash dos arquivos de origem.
  - **[Estágio 1 - Leitura e Descoberta] D9. O que o Estágio Entrega:** Mapa de sincronização.
  - **[Estágio 2 - Replicação e Verificação] D6. O que o Estágio Faz:** Grava os arquivos nos harnesses e verifica correspondência por hash.
  - **[Estágio 2 - Replicação e Verificação] D7. O que o Estágio Recebe:** Mapa de sincronização em memória.
  - **[Estágio 2 - Replicação e Verificação] D8. O que o Estágio Processa:** Cópia determinística, remoção de sobras internas e asserção de hashes SHA-256.
  - **[Estágio 2 - Replicação e Verificação] D9. O que o Estágio Entrega:** Relatório de sincronização e exit code 0/1.
- **D10. Orquestração e Topologia:** Pipeline procedural determinístico `read -> sync -> verify` executado localmente via script Python sem intervenção de modelos de linguagem.

### Fase 3: Resiliência e Economia (Engenharia Operacional)
- **D11. Tratamento de Exceções e Fallback:** Detecção automática de órfãos (`G_SKILL_ROT.py`) e mecanismo de `auto_ingest` controlado para evitar perda de artefatos criados diretamente em harnesses.
- **D12. Observabilidade e Frugalidade:** Execução ultra-rápida em milissegundos sem chamadas de rede ou consumo de tokens. Relatório detalhado listando destinos atualizados.

### Fase 4: O Inspetor e a Expedição (Validação)
- **D13. Quality Gates (Portões):** Validado pelos gates soberanos `gates/G_COMPONENTE_AGNOSTICO.py`, `gates/G_SKILL_ROT.py` e `gates/G_SYNC_CMD_ROT.py`, impondo conformidade estrita nos pre-commits.
- **D14. Critério de Rejeição (Rollback):** Divergência detectada pelo `components verify` aborta o pipeline e reprova o gate pré-commit.
- **D15. Output Consolidado e Handoff:** Manifesto estruturado de verificação com hashes SHA-256 auditáveis comprovando paridade total.

---

## 3. Matriz de Avaliação da Execução
- [x] A ferramenta isolou seu raio de impacto corretamente? Sim, gerenciada exclusivamente por `gestor_componentes.py`.
- [x] O workflow seguiu as fases sem alucinações de LLM em tarefas mecânicas? Sim, motor 100% determinístico em Python.
- [x] O output final passou em todos os Quality Gates e emitiu o Handoff? Sim, validado por `components verify` e `G_COMPONENTE_AGNOSTICO.py` com exit 0.
