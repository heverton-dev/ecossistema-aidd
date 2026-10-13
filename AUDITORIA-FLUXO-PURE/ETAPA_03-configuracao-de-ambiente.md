# Auditoria de Etapa: Configuração de Ambiente

### [RECURSO]: Cópia do .env do motor original (cp)
- **Ordem de Execução:** após a ETAPA_02 (v4, verify exit 0). Valores autorizados pelo usuário: "use os mesmos valores de ecossistema-aidd/.env".
- **Ação Executada:** `cp ecossistema-aidd/.env FLUXO-PURE/.env` (exit 0), conferido com `cmp` (idêntico). Nenhum valor foi impresso nem registrado; só nomes e o estado preenchida/vazia.
- **Entrega / Artefato Gerado:** `.env` com 30 variáveis: 27 preenchidas e 3 vazias.
  - Vazias: `SSH_KEY_PATH`, `COOLIFY_BASE_URL`, `COOLIFY_API_TOKEN`.
  - Preenchidas: GitHub (2), Cloudflare (2), `DEFAULT_ROOT_DOMAIN`, VPS (4), Traefik (3), Postgres/PostgREST (4), Portainer (3), 9Router (6), Mobbin (2).
  - *Caminho Exato (100% concluído):* `C:\Users\trcnologia\Desktop\TESTE-ecossistema-aidd_04102026\FLUXO-PURE\.env`
- **Status & Diagnóstico:**
  - *Sucesso:* Sim, com a anomalia abaixo. O arquivo foi copiado e o `verify` seguinte deu exit 0 (66 dependências; log `aidd-logs-verify7.txt`).
  - *Falhas / Anomalias:*
    - *Ocorrência:* o `.env` **não estava ignorado** no clone. `git check-ignore -v .env` retornou exit 1 e o `git status` mostrava `?? .env`. O `.env.example` afirma "O arquivo .env já está no .gitignore", mas o `.gitignore` versionado não tem a regra. No motor original o `.env` só é ignorado por `.git/info/exclude` (arquivo local, não versionado, linha 29), o que não é reproduzido por um clone novo. Risco: um `git add -A` no clone commitaria segredos (tokens GitHub e Cloudflare, senhas de VPS, Postgres e Portainer).
    - *Localização Exata do Erro:* `.gitignore` da raiz do repositório (sem linha `.env`); promessa falsa em `.env.example`, linhas 5-6 do cabeçalho.
  - *Ação Corretiva Cirúrgica:* mitigação local imediata: adicionei `.env` ao `.git/info/exclude` do clone. `git check-ignore -v .env` → exit 0 e o `.env` saiu do `git status`. Efeito só local; a correção versionada fica no Ticket 1.
  - *Observação:* a comparação de nomes entre `.env.example` e `.env` mostrou diferenças grandes (o exemplo lista dezenas de variáveis `AIDD_*`, `OIDC_*`, `PREFECT_*` que o `.env` do original não define; o `.env` tem 4 nomes que o exemplo não traz: `NINEROUTER_FABLE`, `PORTAINER_*`). Parte do exemplo são variáveis opcionais ou de harness. Não avaliei quais o fluxo PURE exige.

## TICKETS
### Ticket 1: `.env` sem regra no .gitignore versionado (Refere-se a Gate de segredos / DoD "nunca commitar segredos") — ABERTO, NÃO EXECUTADO
- **Falha:** o `.gitignore` do repositório não ignora `.env`. Qualquer clone novo que receba um `.env` o deixa como arquivo não rastreado, pronto para commit acidental. O `.env.example` diz o contrário.
- **Artefato de Handoff:** `.gitignore` (raiz do repositório)
- **Requisito TDD (Red):** num clone limpo, depois de `touch .env`, `git check-ignore .env` retorna exit 1 (deveria ser 0), e `git status --short` lista `?? .env`.
- **Implementação Técnica:**
  - Acrescentar `.env` (e `.env.*` com exceção `!.env.example`) ao `.gitignore`.
  - Decidir se o `.git/info/exclude` do original precisa continuar com a regra (pode ficar, é redundante).
- **Verificação (Green):** num clone limpo, com `.env` presente, `git check-ignore .env` retorna exit 0, `git status --short` não o lista e `git check-ignore .env.example` retorna exit 1 (o exemplo continua versionado).
- **Construtor Prompt (EN):**
  - Add `.env` and `.env.*` to `.gitignore` at the repository root, followed by `!.env.example` so the template stays tracked.
  - In a fresh clone with an empty `.env` file, run `git check-ignore .env` and assert exit 0, run `git check-ignore .env.example` and assert exit 1, and assert `git status --short` does not list `.env`.
  - Add the rule in a TDD style: first write a test or gate assertion that fails (exit 1) without the rule, then pass it (exit 0).

### Ticket 2: Mapear quais variáveis do `.env.example` o fluxo PURE exige (Refere-se a clareza de pré-requisitos) — ABERTO, NÃO EXECUTADO
- **Falha:** não há lista de variáveis obrigatórias por fluxo; o exemplo mistura variáveis de VPS, harnesses e telemetria, e o `.env` do original não cobre todas.
- **Artefato de Handoff:** `.env.example`
- **Requisito TDD (Red):** `python ecossistema.py pure --dry-run` (ETAPA_04) precisa apontar variável ausente sem erro genérico. Só dá para redigir o assert exato depois de ver o comportamento real do dry-run.
- **Implementação Técnica:**
  - Reavaliar na ETAPA_04, quando o dry-run mostrar se alguma variável faltante bloqueia o fluxo.
- **Verificação (Green):** a definir após o dry-run.
- **Construtor Prompt (EN):**
  - Do not act until the ETAPA_04 dry-run shows whether any missing variable blocks the PURE flow; then write a failing check for that variable and fix it.
