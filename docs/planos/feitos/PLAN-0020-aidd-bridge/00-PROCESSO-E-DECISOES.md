# PROCESSO E DECISOES — aidd-bridge

> **Origem:** Planejamento estruturado no monorepo ecossistema-aidd.
> **Proposito deste arquivo:** Registro unico do processo e governanca desta iniciativa.
> **Aviso de Governanca:** Todos os itens comecam como rascunhos. Nenhuma aprovacao ou decisao pode ser fabricada.

---

## 1. O que este esforco busca

Defina aqui os objetivos claros, escopo e limites desta iniciativa.
- **Objetivo Principal:** [Descrever objetivo]
- **Limites de Escopo:** Nao inclui decisoes nao aprovadas por humano.

## 2. Processo Adotado

Diagnostico rapido → Definicao de Pronto checavel → Prompt de Execucao autocontido (PT-BR + EN-US) → Auditoria por reproducao real → Registro do veredito.

## 3. Onde vive o conteudo tecnico

| # | Item | Documento |
|---|---|---|
| 1 | Scanner e Ingestor de Projetos Lovable | `01-scanner-ingestor-projetos.md` |
| 2 | Data Bridge: Supabase SQL para PostgreSQL e PostgREST | `02-data-bridge-supabase.md` |
| 3 | Multi-App Unifier: Fusao de Telas, Rotas e Tailwind | `03-multi-app-unifier.md` |
| 4 | DevOps e VPS Packager: Docker Compose, Nginx e SSL Automatico | `04-devops-vps-packager.md` |

## 4. Regras Fixas

1. **A skill/agente nunca decide ou aprova sozinho.** Rascunhos aguardam aprovacao explicita de pessoa real.
2. **Sem disparos autonomos:** Prompts de execucao nao devem ser enviados a subagentes sem consentimento.
3. **Sem commit/push automatico:** Commits dependem de aprovacao do usuario.
4. **Isolamento:** Testes devem ocorrer sem poluir arquivos de producao.

## 5. Registro de Progresso

| # | Item | Status | Documento |
|---|---|---|---|
| 1 | Scanner e Ingestor de Projetos Lovable | ✅ Concluído (implementado e auditado via test_bridge.py) | `01-scanner-ingestor-projetos.md` |
| 2 | Data Bridge: Supabase SQL para PostgreSQL e PostgREST | ✅ Concluído (implementado e auditado via test_bridge.py) | `02-data-bridge-supabase.md` |
| 3 | Multi-App Unifier: Fusao de Telas, Rotas e Tailwind | ✅ Concluído (implementado e auditado via test_bridge.py) | `03-multi-app-unifier.md` |
| 4 | DevOps e VPS Packager: Docker Compose, Nginx e SSL Automatico | ✅ Concluído (implementado e auditado via test_bridge.py) | `04-devops-vps-packager.md` |

Todos os módulos foram implementados em `tools/aidd-bridge/` com cobertura de testes reais (4/4 aprovados em pytest) e integrados na CLI canônica `python ecossistema.py bridge`.
