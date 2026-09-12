# PROCESSO E DECISOES — bootstrap-ambiente-e-preflight-host

> **Origem:** Planejamento estruturado no monorepo ecossistema-aidd.
> **Proposito deste arquivo:** Registro unico do processo e governanca desta iniciativa.
> **Aviso de Governanca:** Todos os itens comecam como rascunhos. Nenhuma aprovacao ou decisao pode ser fabricada.

---

## 1. O que este esforco busca

- **Origem:** Auditoria de Bootstrap de Ambiente, Pré-requisitos e Preflight de Sistema registrada em `docs/relatorios/BOOTSTRAP-PREFLIGHT-SISTEMA-BASELINE.md` (2026-09-09).
- **Objetivo Principal:** Eliminar crashes crús em máquinas virgens (ImportError de `click`/`dotenv`, ausência de Node/npx, ausência de Docker ou Git), implementar o comando determinístico `python ecossistema.py preflight-host` com diagnóstico instantâneo JSON/tabela, unificar os 4 detectores de binários espalhados nos gates, e fornecer bootstrapper assistido multi-SO com fallback em espaço de usuário (`~/.aidd/bin`).
- **Limites de Escopo:**
  - Nunca executa instalação global invasiva sem consentimento explícito do usuário.
  - O preflight de host deve executar em menos de 2 segundos com custo zero de rede/tokens.
  - Preserva compatibilidade integral com Windows, macOS e Linux.

## 2. Processo Adotado

Diagnostico rapido → Definicao de Pronto checavel → Prompt de Execucao autocontido (PT-BR + EN-US) → Auditoria por reproducao real → Registro do veredito.

## 3. Onde vive o conteudo tecnico

| # | Item | Documento |
|---|---|---|
| 1 | self-healing-imports-python-ecossistema | `01-self-healing-imports.md` |
| 2 | preflight-host-diagnostico-binarios-sistema | `02-preflight-host-diagnostico.md` |
| 3 | tratamento-falhas-npx-bootstrap-skills | `03-tratamento-falhas-npx.md` |
| 4 | bootstrapper-assistido-multi-os-fix | `04-bootstrapper-assistido-multi-fix.md` |
| 5 | campo-preflight-manifesto-dependencias-externas | `05-campo-preflight-manifesto.md` |
| 6 | unificar-detectores-binarios-nos-gates | `06-unificar-detectores-binarios.md` |
| 7 | preflight-ops-antecipado-ansible-sops-docker | `07-preflight-ops-antecipado.md` |
| 8 | atualizar-agents-md-bootstrap-preflight-sessao | `08-atualizar-agents-md.md` |
| 9 | sincronizacao-textual-quickstart-readme | `09-sincronizacao-textual-quickstart.md` |

## 4. Regras Fixas

1. **A skill/agente nunca decide ou aprova sozinho.** Rascunhos aguardam aprovacao explicita de pessoa real.
2. **Sem disparos autonomos:** Prompts de execucao nao devem ser enviados a subagentes sem consentimento.
3. **Sem commit/push automatico:** Commits dependem de aprovacao do usuario.
4. **Isolamento:** Testes devem ocorrer sem poluir arquivos de producao.

## 5. Registro de Progresso

| # | Item | Status | Documento |
|---|---|---|---|
| 1 | self-healing-imports-python-ecossistema | 🔶 Em execucao | `01-self-healing-imports.md` |
| 2 | preflight-host-diagnostico-binarios-sistema | 🔶 Em execucao | `02-preflight-host-diagnostico.md` |
| 3 | tratamento-falhas-npx-bootstrap-skills | ⏳ Rascunho — parte ja implementada (ver auditoria) | `03-tratamento-falhas-npx.md` |
| 4 | bootstrapper-assistido-multi-os-fix | 🔶 Em execucao | `04-bootstrapper-assistido-multi-fix.md` |
| 5 | campo-preflight-manifesto-dependencias-externas | 🔶 Em execucao | `05-campo-preflight-manifesto.md` |
| 6 | unificar-detectores-binarios-nos-gates | 🔶 Em execucao | `06-unificar-detectores-binarios.md` |
| 7 | preflight-ops-antecipado-ansible-sops-docker | 🔶 Em execucao | `07-preflight-ops-antecipado.md` |
| 8 | atualizar-agents-md-bootstrap-preflight-sessao | 🔶 Em execucao | `08-atualizar-agents-md.md` |
| 9 | sincronizacao-textual-quickstart-readme | 🔶 Em execucao | `09-sincronizacao-textual-quickstart.md` |

Esta tabela so e atualizada para Concluido apos auditoria por reproducao real.
