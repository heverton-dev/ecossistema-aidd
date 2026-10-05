# Template de Auditoria de Ferramenta (Lens 15-D)

Este documento descreve a estrutura canônica para auditar qualquer ferramenta (Skill/Tool) do ecossistema, dissecando sua arquitetura através do framework Lens 15-D (The Agentic Anatomical Matrix).

## 1. Identificação da Ferramenta
- **Nome da Ferramenta:** `aidd-open-runner` (`aidd-open`, `open`, `fluxo-02`)
- **Descrição Breve:** Motor especialista do Fluxo 02 da Tríade Canônica, responsável pela composição acelerada de sistemas corporativos integrando motores open-source robustos (Strapi, Medusa, Supabase, n8n, etc.) encapsulados sob fatias verticais VSA e monólito modular.
- **Comando de Gatilho:** `/open <nome_do_projeto> [dominio]`, `python ecossistema.py open --nome "<nome>" --slug <slug> --dominio <dominio> --pasta ./projetos/<slug>`

## 2. A Matriz Anatômica (Lens 15-D)

### Fase 1: Governança e Blindagem
- **D1. Contratos e Regras:** Encapsulamento estrito de motores open-source dentro de contratos de fronteira VSA, proibição de acoplamento direto desprotegido e cumprimento do schema `handoff-engine-to-master.schema.json`.
- **D2. Input e Gatilhos:** Interface via CLI rica (`python ecossistema.py open` / `run-fluxo --fluxo open`) e comando slash `/open`.
- **D3. Raio de Impacto e Isolamento:** Limitação da materialização e configurações à pasta do projeto de destino (`--pasta`), isolando dependências de terceiros do host raiz.
- **D4. Componentes e Fractalidade:** Implementação modular em `tools/aidd-open/` e orquestrador síncrono `scripts/orquestrador_sincrono.py`.

### Fase 2: O Chão de Fábrica (Workflow Agêntico)
- **D5. Visão e Escopo:** Acoplar motores open-source de mercado fornecendo adaptadores e wrappers limpos sob o padrão VSA.
  - **[Estágio 1 - Planejamento e Seleção de Motores] D6. O que o Estágio Faz:** Avalia requisitos de domínio e seleciona o motor open-source canônico.
  - **[Estágio 1 - Planejamento e Seleção de Motores] D7. O que o Estágio Recebe:** Plano de domínio expedido pelo planner.
  - **[Estágio 1 - Planejamento e Seleção de Motores] D8. O que o Estágio Processa:** Resolução de compatibilidade e mapeamento de dependências.
  - **[Estágio 1 - Planejamento e Seleção de Motores] D9. O que o Estágio Entrega:** Manifesto de integração de motor.
  - **[Estágio 2 - Materialização e Adaptação VSA] D6. O que o Estágio Faz:** Provisiona o motor e gera adaptadores desacoplados.
  - **[Estágio 2 - Materialização e Adaptação VSA] D7. O que o Estágio Recebe:** Configurações e templates base.
  - **[Estágio 2 - Materialização e Adaptação VSA] D8. O que o Estágio Processa:** Injeção de wrappers e isolamento de rotas.
  - **[Estágio 2 - Materialização e Adaptação VSA] D9. O que o Estágio Entrega:** Motor operacional integrado a fatias verticais.
  - **[Estágio 3 - Emissão de Handoff para Master] D6. O que o Estágio Faz:** Emite manifesto de contrato para harmonização no monólito modular.
  - **[Estágio 3 - Emissão de Handoff para Master] D7. O que o Estágio Recebe:** Módulo adaptado e testado.
  - **[Estágio 3 - Emissão de Handoff para Master] D8. O que o Estágio Processa:** Assinatura do manifesto JSON.
  - **[Estágio 3 - Emissão de Handoff para Master] D9. O que o Estágio Entrega:** Handoff formal em conformidade com schema.
- **D10. Orquestração e Topologia:** Pipeline síncrono de 8 etapas orquestrado deterministicamente.

### Fase 3: Resiliência e Economia (Engenharia Operacional)
- **D11. Tratamento de Exceções e Fallback:** Falha de provisionamento do motor open-source interrompe o pipeline e dispara limpeza atômica; simulação completa via `--dry-run`.
- **D12. Observabilidade e Frugalidade:** Execução por subprocessos determinísticos e templates locais sem gasto de tokens em chamadas de LLM.

### Fase 4: O Inspetor e a Expedição (Validação)
- **D13. Quality Gates (Portões):** Validação de conectividade e testes de integração dos adaptadores antes da transferência para a camada Master.
- **D14. Critério de Rejeição (Rollback):** Incompatibilidade de versão ou falha no manifesto invalida a entrega.
- **D15. Output Consolidado e Handoff:** Projeto funcional integrando o motor open-source selecionado e handoff assinado.

---

## 3. Matriz de Avaliação da Execução
- [x] A ferramenta isolou seu raio de impacto corretamente? Sim, arquivos restritos à pasta do projeto.
- [x] O workflow seguiu as fases sem alucinações de LLM em tarefas mecânicas? Sim, pipeline 100% determinístico.
- [x] O output final passou em todos os Quality Gates e emitiu o Handoff? Sim, comprovado via pipeline síncrono e gates.
