# Ficha de Auditoria Bit a Bit: `aidd-factory` (Fluxo 02 — Motores Open-Source)

> **Ferramenta:** `tools/aidd-factory`  
> **Data da Auditoria:** 2026-09-22  
> **Status:** AUDITADO / ÍNTEGRO  
> **Responsável:** Antigravity / Eco-AIDD Agent

---

## SESSÃO I: ESTADO ATUAL (Diagnóstico Pré-Implementação)

### 1. Matriz Contratual das 11 Dimensões

| Dimensão | Detalhamento Técnico no Código |
|---|---|
| **1. RECEBE (Input)** | Consome estritamente `PLANO-INFRAESTRUTURA.json` em conformidade com `componentes/compartilhado/specs/plano-infraestrutura.schema.json` gerado pelo intake do `aidd-planner` ou `aidd-ops`. CLI: `python scripts/pipeline_factory.py --plano <path.json> --destino <dir>`. |
| **2. CRIA / PROCESSA** | Pipeline de integração de serviços open-source em fatias VSA: Fase 1 (`01_analisador.py` — análise de nicho e desdobramento em blocos), Fase 4 (`04_compose.py` — geração determinística de `docker-compose.yml`), Fase 5 (`05_init_db.py` — scripts SQL de inicialização multi-tenant/bancos lógicos), Fase 6 (`06_env.py` — variáveis de ambiente seguras com fallbacks tipados), Fase 9 (`09_integracao.py` — gateway de integração VSA e Quarteto Sine Qua Non). |
| **3. ENTREGA (Output)** | Contrato canônico `FACTORY_OUTPUT.json`, manifesto de serviços, compose funcional, scripts de banco de dados, gateway FastAPI VSA e stack frontend Next.js + TS + Tailwind. |
| **4. CONFIGURAÇÕES (Configs)** | Parâmetros de CLI (`--plano`, `--destino`, `--dry-run`, `--skip-frontend`). Suporte a nichos de catálogo fixo (`clinicas`, `delivery`, `farmacias`, `b2b_industrial`, `energia_solar`) e nicho dinâmico (`dinamico_<slug>`). |
| **5. GUARDAS (Gates)** | `G_FACTORY_INPUT` (validação estrita do schema do plano de infraestrutura), `G_FACTORY_OUTPUT` (verificação do manifesto de entrega), `G_FACTORY_DETERMINISTIC` (garantia de zero LLM nas fases 1, 4, 5 e 6). |
| **6. SCRIPTS DETERMINÍSTICOS (0 LLM)** | 100% determinístico nas fases estruturais: análise de topologia, geração do Docker Compose com Traefik, particionamento de bancos lógicos PostgreSQL e geração de `.env`. |
| **7. CAMPAINHAS DE ALERTA (Hooks)** | Validações em tempo de execução via `contrato_factory.py` emitindo interrupção com traceback rastreável ao detectar ausência de dependências. |
| **8. PESSOAS / PERSONAS (Agents)** | Agente orquestrador de fábrica open-source e fatiador de integração VSA. |
| **9. TAREFAS ÚNICAS (Skills)** | Skills associadas: `aidd-factory-runner`, `aidd-open`, `open`, `fluxo-02-runner`. |
| **10. TELEFONES EXTERNOS (MCPs)** | Totalmente autônomo na orquestração de templates e fatias de código. |
| **11. BILHETES (Rules / AGENTS.md)** | `tools/aidd-factory/AGENTS.md`: Consumo exclusivo do envelope de infraestrutura canônico, Zero Stubs, reuso compulsório de `result.py` e `escritor_atomico.py`. |

### 2. Evidência de Testes e Portões
- **Comando executado:** `pytest tools/aidd-factory/tests`
- **Resultado:** 19 testes passaram, 0 falhas em 94.95s.
- **Invariantes testadas:** Validação de planos de clínicas e delivery, compilação de compose e init_db, gateway generator, frontend factory real compilando sem erros e suporte a nicho dinâmico sem LLM.

### 3. Diagnóstico de Não-Conformidades
- Nenhum bug impeditivo. Módulo atende plenamente à governança e à Lei #11.

---

## SESSÃO II: PLANO DE CORREÇÃO & TICKETS DE MELHORIA

*(Nenhum ticket impeditivo aberto. Módulo plenamente funcional).*

---

## SESSÃO III: ESTADO PÓS-IMPLEMENTAÇÃO (Certificação)

- **Status do Módulo:** APROVADO & CERTIFICADO
- **Nível de Autonomia:** Pipeline de integração determinística multi-serviços com validação real de compilação.
- **Handoff:** Registrado no `manifesto_auditoria.json`. Próximo módulo: `aidd-bridge` (Fluxo 03).
