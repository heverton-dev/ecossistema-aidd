# Protocolo de Orquestração Dual: ORCA ADE e Subagentes Nativos

**Conceito Fundamental:** Zero Contaminação de Contexto. O framework AIDD v5.1 adapta-se automaticamente ao ambiente de desenvolvimento disponível.

---

## 1. Modos de Operação Híbridos

| Ambiente Detectado | Mecanismo de Isolamento | Como o Maestro Opera |
| :--- | :--- | :--- |
| **Modo A: ORCA ADE Ativo** | Processos OS e Terminais Virtuais (`orca worktree create`). | Maestro cria mesas de trabalho filhas no ORCA, despacha a tarefa e audita antes do merge. |
| **Modo B: Subagentes / Git Padrão** | Subagentes nativos do Harness ou `git worktree` local. | Maestro invoca subagentes especializados (`claude_code`, `self`, `research`) coordenando via `PLANO-EXECUCAO-ESTRUTURADO.json`. |

---

## 2. As 4 Regras de Ouro da Economia de Tokens

1. **Não use o chat principal como terminal:** Testes (`pytest`), compilação e scaffolding rodam em background ou subprocessos locais.
2. **Isole frentes grandes:** Use Mesas do ORCA (se disponível) ou Subagentes dedicados (Modo B).
3. **Reinicie sessões pelo Plano JSON:** Restauração de contexto a partir de `PLANO-EXECUCAO-ESTRUTURADO.json` (~500 tokens).
4. **Governança por Gates Mecânicos:** Aprovação obrigatória (exit 0) em `G_ESTRUTURA`, `G_TESTES`, `G_CONTRACTS`, `G_QUALIDADE`, `G_SEGREDOS`, `G_HARNESS_COMPAT`.
