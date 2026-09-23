# Ficha de Auditoria Bit a Bit: `aidd-bridge` (Fluxo 03 — Low-Code / Desacoplamento)

> **Ferramenta:** `tools/aidd-bridge`  
> **Data da Auditoria:** 2026-09-22  
> **Status:** AUDITADO / ÍNTEGRO  
> **Responsável:** Antigravity / Eco-AIDD Agent

---

## SESSÃO I: ESTADO ATUAL (Diagnóstico Pré-Implementação)

### 1. Matriz Contratual das 11 Dimensões

| Dimensão | Detalhamento Técnico no Código |
|---|---|
| **1. RECEBE (Input)** | CLI argparse: subcomandos `scan`, `convert-db`, `merge`, `pack`, `migrate-auth`, `destroy`, `unpack`. Consome projetos exportados do Lovable/v0/Bolt contendo React + Vite + Tailwind + migrações Supabase. |
| **2. CRIA / PROCESSA** | `scanner.py` (análise de páginas, rotas e migrações), `data_bridge.py` + `sql_transpiler.py` (sanitização de SQL Supabase para PostgreSQL padrão), `unifier.py` (agregação multi-app em fatias VSA), `devops.py` (geração de Dockerfile, Compose e Swarm), `auth_migrator.py` (migração de hashes de senha de `auth.users`), `frontend_liberator.py` (remoção de bibliotecas proprietárias), `vsa_exporter.py` (exportação do Quarteto Sine Qua Non dinâmico), `pipeline_bridge.py` (orquestração 6 fases). |
| **3. ENTREGA (Output)** | Aplicação 100% livre de lock-in, banco PostgreSQL consolidado (`init-db.sql`), stack Docker Swarm pronta para VPS, fatias verticais VSA em `src/modules/` e diretório `quarteto_sine_qua_non/` contendo Swagger, Webhook, MCP e Guia de Uso. |
| **4. CONFIGURAÇÕES (Configs)** | Flags CLI `--stack <lite\|full>`, `--domain`, `--output`, `--traefik-network`, `--certresolver`, `--apply`, `--yes`, `--with-gotrue`. |
| **5. GUARDAS (Gates)** | Quality gates dedicados em `gates/`: `G_BRIDGE_VENDOR_LOCKIN`, `G_BRIDGE_DOCKER_OCI`, `G_BRIDGE_POSTGRESQL`, `G_BRIDGE_VSA_COMPAT`. |
| **6. SCRIPTS DETERMINÍSTICOS (0 LLM)** | 100% determinístico. Transpilação SQL por regex e gramática estática, manipulação de AST TypeScript/JavaScript para substituição de importações do cliente `@supabase/supabase-js` e empacotamento de templates Docker. |
| **7. CAMPAINHAS DE ALERTA (Hooks)** | `_forcar_utf8_stdio` para compatibilidade multi-plataforma (Windows cp1252), verificações de credenciais obrigatórias para ações remotas em VPS / Cloudflare DNS e prompt interativo obrigatório no comando destrutivo `destroy`. |
| **8. PESSOAS / PERSONAS (Agents)** | Agente especialista em desmonte de lock-in e unificação de apps legadas. |
| **9. TAREFAS ÚNICAS (Skills)** | Skills associadas: `aidd-bridge-runner`, `aidd-freedom`, `freedom`, `fluxo-03-runner`. |
| **10. TELEFONES EXTERNOS (MCPs)** | Módulo de automação de DNS com Cloudflare API (`cloudflare_dns.py`) e orquestração SSH para provisionamento de VPS. |
| **11. BILHETES (Rules / AGENTS.md)** | `tools/aidd-bridge/AGENTS.md`: Desacoplamento estrito, migração segura de credenciais, rollback em teardown e Quarteto Sine Qua Non mandatório. |

### 2. Evidência de Testes e Portões
- **Comando executado:** `pytest tools/aidd-bridge/tests`
- **Resultado:** 64 testes passaram, 0 falhas em 1.19s.
- **Invariantes testadas:** Transpilação SQL Supabase -> PostgreSQL, empacotamento de stack Swarm, unificação de fatias VSA, migração de hashes de auth e pipeline e2e do Fluxo 03.

### 3. Diagnóstico de Não-Conformidades
- Nenhum bug impeditivo. Módulo atende 100% às exigências do ecossistema.

---

## SESSÃO II: PLANO DE CORREÇÃO & TICKETS DE MELHORIA

*(Nenhum ticket impeditivo aberto. Módulo plenamente funcional).*

---

## SESSÃO III: ESTADO PÓS-IMPLEMENTAÇÃO (Certificação)

- **Status do Módulo:** APROVADO & CERTIFICADO
- **Nível de Autonomia:** Pipeline determinístico de 6 fases com extração limpa e zero dependência de IA para sanitização.
- **Handoff:** Registrado no `manifesto_auditoria.json`. Próximo módulo: `aidd-master` (Meso-camada e convergência).
