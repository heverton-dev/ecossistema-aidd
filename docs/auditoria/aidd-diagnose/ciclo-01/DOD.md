# Definição de Pronto (Definition of Done - DoD) — aidd-diagnose

> Critérios estáticos de conformidade arquitetural baseados no framework Lens 15-D.

## Critérios Obrigatórios de Aceite

1. **DoD 1: CLI Fallback e Fractalidade (D4)**
   - A ferramenta deve possuir invocação declarativa via CLI (`python ecossistema.py diagnose`) ou scripts locais em Python, com interface agnóstica.

2. **DoD 2: Isolamento de Raio de Impacto (D3)**
   - O código não pode realizar operações de I/O em arquivos fora de seu escopo permitido sem estar contido em Git Worktree efêmera.

3. **DoD 3: Motor Analítico Determinístico (D8)**
   - Proibida dependência de inferência livre de LLM sem envelope ou validação de JSON Schema estrito.

4. **DoD 4: Resiliência Operacional (D11)**
   - Mecanismos de retry com backoff e tratamento estruturado de falhas implementados.

5. **DoD 5: Observabilidade e Frugalidade (D12)**
   - Rastreamento de métricas e tempos de execução persistidos de forma auditável.

6. **DoD 6: Quality Gate e Rótulo Honesto (D13)**
   - Portão determinístico `gates/G_aidd_diagnose.py` implementado provando que barra saídas ilusórias (Lei #8 e Lei #13).

7. **DoD 7: Limpeza e Rollback (D14)**
   - Em caso de exceção ou rejeição, nenhum arquivo corrompido ou temporário sobrevive no repositório.

8. **DoD 8: Output Consolidado e Handoff (D15)**
   - Emissão de manifesto formal estruturado e laudo 15-D aprovado com EXIT 0.
