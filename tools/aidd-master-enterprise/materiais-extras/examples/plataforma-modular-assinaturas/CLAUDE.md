# AGENTS — Projeto Modular plataforma-de-assinaturas (AIDD v2.0)

**Descrição:** Plataforma de Assinaturas e Cursos Modular
**Arquitetura:** AIDD v2.0 Modular (Data-Driven Modules + Dual DB + OpenAPI Swagger + Docker)
**Regra Zero:** Zero Fricção de API Key & Zero Emojis em Interfaces (Design Impeccable).

---

## 🏛️ 1. Governança Modular do Mestre de Obras
1. **Módulos Desacoplados:** Cada nova feature deve viver em `src/modules/<nome>/` com seus próprios models, services e rotas.
2. **Criação de Novos Módulos:** Use sempre `python scripts/add_module.py <nome>` para manter o padrão.
3. **Comunicação por Eventos:** Use `core.events.EventBus` para trocar dados entre módulos sem acoplamento direto.
4. **Documentação Automática:** Toda rota registrada em `core.openapi.RouteRegistry` aparece imediatamente em `/docs`.

---

## 🏆 AS 3 REGRAS DE OURO DA ENGENHARIA AGÊNTICA (Anti-Estouro de Tokens)
| Regra de Ouro | Por que evita estourar o limite semanal |
| :--- | :--- |
| **1. Não use o chat principal como terminal** | Deixe compilação, testes (pytest) e tarefas mecânicas rodando via Python local. Isso economiza 90% do seu consumo semanal. |
| **2. Use Worktrees do ORCA para frentes grandes** | Cada tarefa separada em sua mesa limpa evita que o contexto principal acumule 100k+ tokens desnecessários. |
| **3. Reinicie sessões usando o Plano JSON** | Ao começar um novo dia ou módulo, abra uma sessão nova apontando para o `PLANO-EXECUCAO-ESTRUTURADO.json`. O agente retoma o estado exato consumindo apenas 500 tokens em vez de 80.000 do histórico passado. |
