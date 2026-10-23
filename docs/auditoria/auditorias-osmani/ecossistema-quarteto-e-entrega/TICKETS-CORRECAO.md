# Backlog Consolidado de Micro-Tickets — AIDD-Osmani

> **Origem:** Auditoria Factual dos Geradores e Orquestrador da Tríade AIDD.  
> **Diretivas:** Lei #1 (Determinismo & Single Source of Truth), Lei #10 (Quarteto Dinâmico do Planner), Lei #11 (Modo Claro Soberano).  
> **Total de Tickets:** 4 Micro-Tickets Mapeados.

---

## Matriz de Priorização de Tickets

| Ticket ID | Camada / Arquivos-Alvo | Descrição Resumida | Severidade | Bloqueado Por | Portão Vinculado |
| :--- | :--- | :--- | :---: | :---: | :---: |
| **TCK-OSM-01** | idd-master/src/core/, idd-enterprise/src/core/, moldes | Sincronizar moldes do Quarteto em Modo Claro soberano e eliminar cópias em Dark Mode | **CRÍTICA** | - | G_CRAFT_VISUAL, G_QUARTETO_SINE_QUA_NON |
| **TCK-OSM-02** | provision_project.py, server.py, quarteto_studios.py | Construir o Quarteto dinamicamente a partir dos contratos do PLANNER.json | **CRÍTICA** | TCK-OSM-01 | G_CONTRACT_ROT, G_QUARTETO_SINE_QUA_NON |
| **TCK-OSM-03** | 	emplates/v2/server.py, 	emplates/core/server.py | Unificar entrega: servir rontend/dist com SPA fallback em / e evitar directory listing | **CRÍTICA** | - | G_STACK_PADRAO_OURO, G_SAIDA_BINARIA |
| **TCK-OSM-04** | server.py, metrics.py, orquestrador_sincrono.py | Dashboard visual de métricas em /metrics, API JSON /api/metrics e build Vite no orquestrador | Alta | TCK-OSM-03 | G_OBSERVABILIDADE, G_USER_FACING_PTBR |
