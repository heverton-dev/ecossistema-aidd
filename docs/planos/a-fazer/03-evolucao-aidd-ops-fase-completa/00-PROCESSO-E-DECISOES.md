# PROCESSO E DECISOES — evolucao-aidd-ops-fase-completa

> **Origem:** Planejamento estruturado no monorepo ecossistema-aidd.
> **Proposito deste arquivo:** Registro unico do processo e governanca desta iniciativa.
> **Aviso de Governanca:** Todos os itens comecam como rascunhos. Nenhuma aprovacao ou decisao pode ser fabricada.
> **🔒 BLOQUEADO em 2026-09-07 — nenhum item inicia antes de uma decisão do usuário.**

---

## 0. Por que está bloqueado

O levantamento NIH (`docs/features/oportunidades-reaproveitamento-oss-nih.md`, itens 18-21) e a Fase 2 de `docs/planos/a-fazer/direcionamento-estrategico-anti-nih/` apontam que as 4 frentes abaixo (intake web, cofre de credenciais, appshell, isolamento em VPS compartilhada) são, em conjunto, essencialmente o escopo inteiro de plataformas self-hosted maduras como **Coolify**, **CapRover** ou **Dokku** — já prontas, open source, ativas.

Construir qualquer uma das 4 agora, antes da decisão sobre adotar uma dessas plataformas, arrisca jogar fora o trabalho depois — exatamente o erro de NIH que motivou o levantamento. Por isso: **nenhum item desta iniciativa inicia implementação até o usuário decidir "adotar Coolify/CapRover/Dokku" ou "manter infraestrutura própria"** (mesma decisão registrada como pendente na Fase 2 do plano estratégico). O diagnóstico técnico de cada item abaixo continua válido como especificação de feature — só a execução espera.

## 1. O que este esforco busca

Defina aqui os objetivos claros, escopo e limites desta iniciativa.
- **Objetivo Principal:** [Descrever objetivo]
- **Limites de Escopo:** Nao inclui decisoes nao aprovadas por humano.

## 2. Processo Adotado

Diagnostico rapido → Definicao de Pronto checavel → Prompt de Execucao autocontido (PT-BR + EN-US) → Auditoria por reproducao real → Registro do veredito.

## 3. Onde vive o conteudo tecnico

| # | Item | Documento |
|---|---|---|
| 1 | Intake Interativo Web Sem Friccao | `01-intake-interativo-web-sem-friccao.md` |
| 2 | Cofre Local e Coleta Segura de Credenciais | `02-cofre-local-e-coleta-segura-de-credenciais.md` |
| 3 | AppShell White-Label e Studios OpenAPI Webhook MCP | `03-appshell-white-label-e-studios-openapi-webhook-mcp.md` |
| 4 | Isolamento Estrito em VPS Compartilhada e Uninstall Atomico | `04-isolamento-estrito-em-vps-compartilhada-e-uninstall-atomico.md` |

## 4. Regras Fixas

1. **A skill/agente nunca decide ou aprova sozinho.** Rascunhos aguardam aprovacao explicita de pessoa real.
2. **Sem disparos autonomos:** Prompts de execucao nao devem ser enviados a subagentes sem consentimento.
3. **Sem commit/push automatico:** Commits dependem de aprovacao do usuario.
4. **Isolamento:** Testes devem ocorrer sem poluir arquivos de producao.

## 5. Registro de Progresso

| # | Item | Status | Documento |
|---|---|---|---|
| 1 | Intake Interativo Web Sem Friccao | 🔒 Bloqueado — aguardando decisão sobre Coolify/CapRover/Dokku (ver §0) | `01-intake-interativo-web-sem-friccao.md` |
| 2 | Cofre Local e Coleta Segura de Credenciais | 🔒 Bloqueado — aguardando decisão sobre Coolify/CapRover/Dokku (ver §0) | `02-cofre-local-e-coleta-segura-de-credenciais.md` |
| 3 | AppShell White-Label e Studios OpenAPI Webhook MCP | 🔒 Bloqueado — aguardando decisão sobre Coolify/CapRover/Dokku (ver §0) | `03-appshell-white-label-e-studios-openapi-webhook-mcp.md` |
| 4 | Isolamento Estrito em VPS Compartilhada e Uninstall Atomico | 🔒 Bloqueado — aguardando decisão sobre Coolify/CapRover/Dokku (ver §0) | `04-isolamento-estrito-em-vps-compartilhada-e-uninstall-atomico.md` |

Esta tabela so e atualizada para Concluido apos auditoria por reproducao real.
