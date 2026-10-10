# Definição de Pronto (Definition of Done - DoD) — aidd-master

> Critérios estáticos de conformidade arquitetural baseados no framework Lens 15-D para a ferramenta `aidd-master`.

## Metas e Critérios Binários de Aceitação

1. **DoD 1: Isolamento de Raio de Impacto e Sandbox (D3)**
   - As operações de scaffolding e integração de fatias verticais devem operar com raio de impacto estritamente delimitado e suporte a execução isolada dentro de Git Worktree efêmera, bloqueando escritas fora dos diretórios autorizados (`src/modules/<module>/`).

2. **DoD 2: Componentes, Fractalidade e Scripts Locais (D4)**
   - A pasta `.agents/skills/aidd-master/` deve possuir scripts locais estruturados em `scripts/` (e micro-rotinas modulares) em vez de depender exclusivamente de prompts conversacionais passivos ou dependência opaca não encapsulada.

3. **DoD 3: Processamento e Scaffolding Determinístico (D8)**
   - O processamento de geração de fatias verticais (modelos, serviços, rotas, testes e UI) deve ser 100% determinístico e validado contra contratos e schemas estritos, sem depender de alucinações livres de LLM.

4. **DoD 4: Orquestração e Topologia Multi-Estágio (D10)**
   - O fluxo da skill deve seguir topologia sequencial estruturada com validação intermediária de integridade de dados e persistência formal de estado entre etapas de scaffolding.

5. **DoD 5: Resiliência Operacional e Tratamento de Exceções (D11)**
   - Mecanismos de tolerância a falhas, tratamento de colisões de módulos existentes, retry loops estruturados e captura graciosa de erros operacionais sem corrupção do repositório.

6. **DoD 6: Observabilidade e Auditoria Estruturada (D12)**
   - Registro de telemetria, logs de auditoria estruturados e medição de frugalidade/tempo de processamento e tokens persistidos em `secoes/`.

7. **DoD 7: Quality Gate Próprio e Rótulo Honesto (D13)**
   - Criação e aprovação do Quality Gate determinístico `gates/G_aidd_master.py`, provando que reprova (exit 1) violações de governança da skill e passa (exit 0) sob conformidade total (Lei #13).

8. **DoD 8: Critério de Rejeição, Limpeza e Rollback Automático (D14)**
   - Em caso de falha de validação estrutural ou quebra nos testes de contrato gerados, a ferramenta deve disparar rollback imediato, descartando artefatos parciais e retornando exit 1.

9. **DoD 9: Output Consolidado e Handoff Estruturado (D15)**
   - Emissão de manifesto JSON de handoff formal e assinado (`handoff-master.json`), comprovando o status da fatia vertical gerada para as próximas ferramentas da Tríade (`aidd-enterprise` e `aidd-ops`).
