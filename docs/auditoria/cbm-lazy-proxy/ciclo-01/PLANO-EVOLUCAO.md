# Plano de Evolução (Fase 4) — CBM & Lazy Gatekeeper

> **Ciclo:** ciclo-01  
> **Iniciativa:** Substituição do `code-review-graph` (CRG) pelo `codebase-memory-mcp` (CBM) e adoção do Lazy Gatekeeper para redução drástica de RAM e tokens em todos os harnesses.  
> **Status:** AGUARDANDO APROVAÇÃO DO USUÁRIO

---

## 1. Contexto e Diagnóstico Empírico (Fases 0 a 3)

1. **Crise de RAM e Latência no CRG:**
   - CRG exigia 1.6 GB de RAM por sessão com PyTorch no Windows (ou ~120 MB em idle com o bloqueio `crg_sem_torch.pth`).
   - Respostas do CRG eram prolixas (~1.200 tokens para callers de `run_command`).
2. **Superioridade Comprovada do CBM v0.11.0:**
   - Indexação completa da árvore limpa em **33,4 s** (61.414 nós, 199.103 arestas, cache `.codebase-memory/graph.db.zst`).
   - Consumo de RAM do CBM em modo MCP stdio: **7,5 MB** (redução de 99,5%).
   - Custo de tokens por consulta: **178 tokens** (~85% de economia).
   - Suporte nativo a acentuação PT-BR e update incremental após edição de arquivo (Exit 0).
3. **Comprovação do MCP Lazy Gatekeeper:**
   - Backends pesados (`playwright`, `context7`, `supabase`, `docker-mcp`, etc.) iniciam com **0.0 MB** de RAM.
   - Ativação instantânea sob demanda (spawn em 1,6 s na primeira chamada).
   - Encerramento limpo e liberação total de RAM (*idle reaping*) após inatividade.
4. **Decisão Arquitetural do CBM:**
   - O CBM permanece **EAGER / Nativo** (7,5 MB de RAM é irrelevante e o grafo mandatório por AGENTS.md deve estar sempre acessível ao modelo sem camadas indiretas).
   - Todos os demais MCPs secundários migram para trás do **Lazy Gatekeeper**.

---

## 2. Inventário de Arquivos e Mapeamento de Mudanças

### A. Fontes Canônicas (Únicas fontes editadas manualmente)
1. `componentes/compartilhado/src-core/mcp_gatekeeper.py` *(Novo componente nativo de proxy lazy)*
2. `componentes/compartilhado/hooks/cbm_session_start.py` *(Substitui crg_session_start.py)*
3. `componentes/compartilhado/hooks/cbm_update.py` *(Substitui crg_update.py)*
4. `componentes/compartilhado/skills/aidd-diagnose/scripts/cobertura_grafo.py` *(Adapta verificação para CBM CLI)*
5. `componentes/compartilhado/skills/aidd-diagnose/scripts/fallback.py` *(Sonda de disponibilidade CBM)*
6. `componentes/compartilhado/skills/aidd-diagnose/SKILL.md` *(Atualiza menção a CBM)*
7. `componentes/compartilhado/skills/aidd-improvement/SKILL.md` *(Atualiza menção a CBM)*
8. `componentes/compartilhado/skills/aidd-anatomy/SKILL.md` *(Atualiza menção a CBM)*
9. `componentes/compartilhado/comandos/melhoria.md` *(Atualiza menção a CBM)*
10. `AGENTS.md` e `docs/protocolos/AGENTS-REFERENCIA-COMPLETA.md` *(Atualiza Seção 5 e regra Graph-First para CBM)*

### B. Metadados de Gates e Dependências
1. `gates/dependencias_externas.json`:
   - Atualiza `mcps.codebase-memory-mcp` (comando apontando para CBM stdio ou binário no PATH).
   - Define o `mcp-gatekeeper` para orquestrar `playwright`, `context7`, `github`, etc.
2. `gates/manifesto_harnesses.json`:
   - Validação de paridade em todos os 7 harnesses.
3. `docs/auditoria/mapa-pecas/catalogo-pecas.json`:
   - Atualização do catálogo de MCPs e hooks de terceiros.
4. `secoes/handoff-melhoria.json` & `.secrets.baseline`:
   - Reassinatura HMAC SHA-256 de `AGENTS.md` (via hash LF `git show HEAD:AGENTS.md`).

### C. Destinos Gerados / Espelhos (Regenerados via CLI determinístico)
- Execução de `python ecossistema.py components sync --tipo todos`.
- Espelhos atualizados automaticamente nos 7 harnesses: `.mcp.json`, `.agents/mcp_config.json`, `.cursor/mcp.json`, `.gemini/settings.json`, `mimocode.jsonc`, `opencode.jsonc`, `.vscode/mcp.json`.

### D. Configurações Globais do Usuário (Backup prévio mandatório)
- Backup para `~/backup_mcp_2026-10-01/` antes de qualquer toque.
- Atualização em `~/.gemini/config/mcp_config.json`, `~/.claude/settings.json`, `~/.codex/config.toml`.
- **Zero desinstalação:** O binário e ambiente do CRG e o arquivo `crg_sem_torch.pth` permanecem intactos no sistema.

---

## 3. Tickets de Execução do Ciclo

### Ticket 1: Implementação do Gatekeeper Lazy Canônico (`mcp_gatekeeper.py`)
- **Objetivo:** Criar em `componentes/compartilhado/src-core/mcp_gatekeeper.py` o servidor proxy stdio com idle timeout (padrão 5 min), spawn sob demanda de backends secundários e repasse transparente de JSON-RPC 2.0.
- **Teste TDD:** `tests/test_mcp_gatekeeper.py` asserta:
  1. Backend inicia desligado (0 MB).
  2. Primeira chamada dispara backend com sucesso.
  3. Timeout de ociosidade encerra o processo e libera recursos.

### Ticket 2: Adaptação das Ferramentas de Diagnóstico e Hooks para CBM
- **Objetivo:** Criar `cbm_session_start.py` e `cbm_update.py` em `componentes/compartilhado/hooks/`.
- **Ajustar:** `cobertura_grafo.py` e `fallback.py` do `aidd-diagnose` para sondar `codebase-memory-mcp cli check_index_coverage` / `query_graph`.
- **Teste TDD:** `tests/test_cbm_hooks.py` valida execução silenciosa dos hooks com retorno 0.

### Ticket 3: Atualização de Diretrizes Canônicas (AGENTS.md e Skills)
- **Objetivo:** Atualizar a Seção 5 de `AGENTS.md` e `docs/protocolos/AGENTS-REFERENCIA-COMPLETA.md` para documentar `codebase-memory-mcp` (`search_graph`, `trace_path`, `query_graph`, `get_architecture`, `detect_changes`).
- **Ajustar:** Skills `aidd-diagnose`, `aidd-improvement`, `aidd-anatomy`.
- **Reassinatura:** Recalcular assinatura HMAC em `secoes/handoff-melhoria.json` e atualizar `.secrets.baseline`.

### Ticket 4: Wiring Universal de MCPs nos 7 Harnesses via `components sync`
- **Objetivo:** Atualizar `gates/dependencias_externas.json` e `gates/manifesto_harnesses.json`.
- **Execução:** Rodar `python ecossistema.py components sync --tipo todos`.
- **Validação:** Rodar `python gates/G_UNIVERSAL_HARNESS.py` garantindo paridade em Claude Code, Antigravity, OpenCode, Cursor, Gemini CLI, MimoCode e VS Code.

### Ticket 5: Bateria Completa de Quality Gates e Validação de RAM
- **Objetivo:** Rodar `python ecossistema.py audit` e medir o consumo real de RAM nas novas sessões.
- **Critério de Sucesso:** 100% dos portões verdes (exit 0) e economia confirmada (> 600 MB de RAM liberada por sessão).

---

## 4. Plano de Rollback Imediato
- Se qualquer instabilidade for observada:
  1. Restaurar configurações globais a partir de `~/backup_mcp_2026-10-01/`.
  2. No repo: `git checkout HEAD -- .mcp.json .agents/ gates/ AGENTS.md`.
  3. `python ecossistema.py components sync --tipo todos`.
  4. CRG continua instalado no ambiente Python global com o `.pth` ativo, pronto para retorno imediato.

---

## 5. Métricas de Sucesso

| Métrica | Antes (CRG + MCPs Ávidos) | Meta (CBM + Lazy Gatekeeper) | Medição Real Pós-Fase 3 |
| :--- | :--- | :--- | :--- |
| **RAM Ociosa por Sessão** | ~1.600 MB (com CRG/Torch) / ~750 MB (sem Torch) | < 35 MB | **7.5 MB (CBM) + 0 MB (Backends)** |
| **Tokens por Consulta de Grafo** | ~1.200 a 3.200 tokens | < 300 tokens | **178 tokens** |
| **Tempo de Indexação** | 101 segundos | < 40 segundos | **33.4 segundos** |
| **Bateria de Gates** | 100% Verde | 100% Verde | A validar no fechamento |
