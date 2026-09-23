# Ficha de Auditoria Bit a Bit: `aidd-planner`

> **Ferramenta:** `tools/aidd-planner`  
> **Data da Auditoria:** 2026-09-22  
> **Status:** AUDITADO / ÍNTEGRO  
> **Responsável:** Antigravity / Eco-AIDD Agent

---

## SESSÃO I: ESTADO ATUAL (Diagnóstico Pré-Implementação)

### 1. Matriz Contratual das 11 Dimensões

| Dimensão | Detalhamento Técnico no Código |
|---|---|
| **1. RECEBE (Input)** | CLI argparse (`init`, `validate`, `export`, `audit`). Parâmetros: `--fluxo <1\|2\|3>`, `--nome`, `--slug`, `--descricao`, `--dominio`, `--pasta`, `--arquivo`, `--formato <factory\|pipeline\|dispatch>`, `--saida`. |
| **2. CRIA / PROCESSA** | `planner_engine.py`: `gerar_template_plano`, `validar_plano` (JSON Schema + regras semânticas), `exportar_para_fluxo_factory`, `exportar_para_pipeline_execucao`, `compilar_grafo_topologico_vsa`. `design_system.py`: geração determinística (hash do projeto) de paleta cromática e identidade visual única. |
| **3. ENTREGA (Output)** | Arquivos: `PLANNER.json`, `DESIGN-SYSTEM.json`, `HANDOFF_PLANNER_ENGINE.json`, artefatos exportados para pipeline/dispatch. |
| **4. CONFIGURAÇÕES (Configs)** | Mapeamento `MAPA_FLUXOS` suportando aliases numéricos e textuais (`1`, `2`, `3`, `pure`, `open`, `freedom`). Flags `--force`, `--dry-run`. |
| **5. GUARDAS (Gates)** | Validação integrada contra `schemas/planner_schema.json`, verificação obrigatória do Quarteto Sine Qua Non (`/docs`, `/webhooks`, `/mcp`, `/docs/guia`), BDD Gherkin obrigatório, detecção de ciclos em grafo de dependências VSA. |
| **6. SCRIPTS DETERMINÍSTICOS (0 LLM)** | 100% determinístico. Cálculos de hash para paleta cromática, validação estrita JSON Schema, algoritmo topológico de Kahn para ordenação DAG de fatias VSA. |
| **7. CAMPAINHAS DE ALERTA (Hooks)** | Emite códigos de saída binários (`exit 0` sucesso, `exit 1` falha) e relatórios formatados em stderr para interceptação por orquestradores superiores. |
| **8. PESSOAS / PERSONAS (Agents)** | Atua como motor de intake alimentando personas dos geradores especializados (`aidd-generator`, `aidd-factory`, `aidd-bridge`). |
| **9. TAREFAS ÚNICAS (Skills)** | Skills associadas no ecossistema: `aidd-planner-runner`, `aidd-plan`, `aidd-planos`. |
| **10. TELEFONES EXTERNOS (MCPs)** | Totalmente desacoplado e autônomo (não necessita de MCP externo para execução de intake e exportação). |
| **11. BILHETES (Rules / AGENTS.md)** | `tools/aidd-planner/AGENTS.md` fixa: Invariante Zero Stubs, Quarteto Sine Qua Non ativado por default, envelope estrito aidd-ops para export factory. |

### 2. Evidência de Testes e Portões
- **Comando executado:** `pytest tools/aidd-planner/tests`
- **Resultado:** 24 testes passaram, 0 falhas (tempo de execução: 1.25s).
- **Invariantes testadas:** Rejeição de plano sem quarteto, rejeição de plano sem BDD, exportação para factory envelope ops, compilação de grafo VSA com detecção de ciclo.

### 3. Diagnóstico de Não-Conformidades
- Nenhum bug impeditivo. Conformidade 100% comprovada na geração de envelopes de handoff formal e compatibilidade com VSA.

---

## SESSÃO II: PLANO DE CORREÇÃO & TICKETS DE MELHORIA

*(Nenhum ticket impeditivo aberto. Módulo plenamente funcional).*

---

## SESSÃO III: ESTADO PÓS-IMPLEMENTAÇÃO (Certificação)

- **Status do Módulo:** APROVADO & CERTIFICADO
- **Nível de Autonomia:** 100% Determinístico
- **Handoff:** Registrado no `manifesto_auditoria.json`. Próximo módulo: `aidd-generator` (Fluxo 01).
