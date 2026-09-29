# Definição de Pronto (Definition of Done - DoD) — aidd-enterprise

> Critérios estáticos de conformidade arquitetural baseados no framework Lens 15-D para a ferramenta `aidd-enterprise`.

## Metas e Critérios Binários de Aceitação

1. **DoD 1: Isolamento de Raio de Impacto (D3)**
   - As operações de injeção e validação devem operar com raio de impacto estritamente delimitado e suporte a execução isolada dentro de Git Worktree efêmera, bloqueando escritas fora dos diretórios autorizados.

2. **DoD 2: Componentes, Fractalidade e Scripts Locais (D4)**
   - A pasta `.agents/skills/aidd-enterprise/` deve possuir scripts locais estruturados em `scripts/` (e micro-rotinas modulares) em vez de depender exclusivamente de prompts conversacionais passivos.

3. **DoD 3: Processamento Criptográfico e Analítico Determinístico (D8)**
   - O processamento de injeção e cálculo SHA-256 deve ser 100% determinístico, validado estritamente contra JSON Schema, rejeitando payloads ou componentes adulterados.

4. **DoD 4: Orquestração e Topologia Multi-Estágio (D10)**
   - O fluxo deve seguir topologia sequencial estruturada com validação intermediária de integridade de dados e persistência formal de estado entre etapas.

5. **DoD 5: Resiliência Operacional e Tratamento de Exceções (D11)**
   - Mecanismos de tolerância a falhas, retry loops estruturados e captura graciosa de erros operacionais sem corrupção do repositório.

6. **DoD 6: Observabilidade e Auditoria Estruturada (D12)**
   - Registro de telemetria, logs de auditoria estruturados e medição de frugalidade/tempo de processamento em `secoes/`.

7. **DoD 7: Quality Gate Próprio e Rótulo Honesto (D13)**
   - Criação e aprovação do Quality Gate determinístico `gates/G_aidd_enterprise.py`, provando que reprova (exit 1) violações de integridade e passa (exit 0) sob conformidade total.

8. **DoD 8: Critério de Rejeição, Limpeza e Rollback Automático (D14)**
   - Em caso de falha de validação ou divergência de hash SHA-256, a ferramenta deve disparar rollback imediato, descartando artefatos parciais e retornando exit 1.

9. **DoD 9: Output Consolidado e Handoff Estruturado (D15)**
   - Emissão de manifesto JSON de handoff formal e assinado (`handoff-enterprise.json`), comprovando o status da injeção/auditoria para os próximos estágios.
