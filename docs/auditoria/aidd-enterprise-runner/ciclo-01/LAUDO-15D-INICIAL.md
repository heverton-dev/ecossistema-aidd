# Template de Auditoria de Ferramenta (Lens 15-D)

Este documento descreve a estrutura canônica para auditar qualquer ferramenta (Skill/Tool) do ecossistema, dissecando sua arquitetura através do framework Lens 15-D (The Agentic Anatomical Matrix).

## 1. Identificação da Ferramenta
- **Nome da Ferramenta:** `aidd-enterprise-runner` (`aidd-enterprise`, `enterprise`)
- **Descrição Breve:** Motor soberano de integridade criptográfica, injeção de componentes de missão crítica com validação SHA-256 e conformidade Zero-Trust, responsável por garantir a integridade de manifests, schemas JSON e exportação para o orquestrador de operações (`aidd-ops-runner`).
- **Comando de Gatilho:** `/enterprise <tipo> <nome>`, `python ecossistema.py enterprise inject <tipo> <nome>`

## 2. A Matriz Anatômica (Lens 15-D)

### Fase 1: Governança e Blindagem
- **D1. Contratos e Regras:** Leis invioláveis #8 e #13; conformidade com `component_manifest.schema.json`, `handoff-master-to-enterprise.schema.json` e `handoff-enterprise-to-ops.schema.json`. Rejeição total de qualquer payload com hash divergente ou adulterado.
- **D2. Input e Gatilhos:** Interface via CLI rica (`python ecossistema.py enterprise [inject|audit|status]`) e comando slash `/enterprise`.
- **D3. Raio de Impacto e Isolamento:** Modificação restrita aos diretórios alvo de injeção formal de componentes, com rollback atômico e verificações de integridade antes da persistência em disco.
- **D4. Componentes e Fractalidade:** Implementação modular em `tools/aidd-enterprise/` e `componentes/compartilhado/injetor/`, apoiada pelo Quality Gate determinístico `gates/G_aidd_enterprise.py`.

### Fase 2: O Chão de Fábrica (Workflow Agêntico)
- **D5. Visão e Escopo:** Garantir a autenticidade e a rastreabilidade absoluta de cada artefato injetado na aplicação corporativa através de assinaturas criptográficas determinísticas.
  - **[Estágio 1 - Parsing e Schema Check] D6. O que o Estágio Faz:** Lê o manifest e valida contra o JSON Schema Draft 2020-12.
  - **[Estágio 1 - Parsing e Schema Check] D7. O que o Estágio Recebe:** Arquivo de manifest ou payload JSON.
  - **[Estágio 1 - Parsing e Schema Check] D8. O que o Estágio Processa:** Validação sintática e estrutural.
  - **[Estágio 1 - Parsing e Schema Check] D9. O que o Estágio Entrega:** Manifesto validado estruturalmente.
  - **[Estágio 2 - Checagem Criptográfica SHA-256] D6. O que o Estágio Faz:** Recalcula o hash da carga útil e confere com os bytes físicos em disco.
  - **[Estágio 2 - Checagem Criptográfica SHA-256] D7. O que o Estágio Recebe:** Arquivo materializado e SHA declarado.
  - **[Estágio 2 - Checagem Criptográfica SHA-256] D8. O que o Estágio Processa:** `hashlib.sha256` sobre bytes ou JSON ordenado.
  - **[Estágio 2 - Checagem Criptográfica SHA-256] D9. O que o Estágio Entrega:** Prova binária de não-adulteração.
  - **[Estágio 3 - Emissão de Handoff Ops] D6. O que o Estágio Faz:** Consolida a suíte e emite o manifesto para a esteira de operações (`aidd-ops-runner`).
  - **[Estágio 3 - Emissão de Handoff Ops] D7. O que o Estágio Recebe:** Componentes integrados e íntegros.
  - **[Estágio 3 - Emissão de Handoff Ops] D8. O que o Estágio Processa:** Serialização e assinatura do handoff.
  - **[Estágio 3 - Emissão de Handoff Ops] D9. O que o Estágio Entrega:** Manifesto em conformidade com `handoff-enterprise-to-ops.schema.json`.
- **D10. Orquestração e Topologia:** Pipeline sequencial síncrono (`schema_validate -> sha_verify -> handoff_emit`) estritamente determinístico.

### Fase 3: Resiliência e Economia (Engenharia Operacional)
- **D11. Tratamento de Exceções e Fallback:** Divergência de bytes dispara reprovação imediata (`exit 1`) e aborta qualquer injeção, sem escrita residual.
- **D12. Observabilidade e Frugalidade:** Execução local ultrarrápida via Python nativo, sem consumo de LLM ou tráfego externo.

### Fase 4: O Inspetor e a Expedição (Validação)
- **D13. Quality Gates (Portões):** Portão determinístico `gates/G_aidd_enterprise.py` e testes de fronteira `test_fronteira_enterprise.py` com exit 0.
- **D14. Critério de Rejeição (Rollback):** Qualquer hash incompatível resulta em rejeição estrita (zero tolerância a componentes adulterados).
- **D15. Output Consolidado e Handoff:** Manifesto estruturado validado contra `handoff-enterprise-to-ops.schema.json`.

---

## 3. Matriz de Avaliação da Execução
- [x] A ferramenta isolou seu raio de impacto corretamente? Sim, injeção controlada e atômica.
- [x] O workflow seguiu as fases sem alucinações de LLM em tarefas mecânicas? Sim, motor 100% determinístico e criptográfico.
- [x] O output final passou em todos os Quality Gates e emitiu o Handoff? Sim, validado por `G_aidd_enterprise.py` e schema formal.
