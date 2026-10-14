# Auditoria de Etapa: Abolição do Coolify e deploy real do `compose-nativo` (Ticket 8-A da ETAPA_08)

> **EXECUTADO EM MODO AUTÔNOMO (`/goal`, 13/10/2026).** Decisão do usuário (tomada antes do modo autônomo): o **Coolify é abolido** e o deploy é só `compose-nativo`, para **todos** os fluxos. As decisões técnicas de como fazer foram minhas e estão marcadas como "Decisão autônoma".

### [RECURSO]: Guarda `tests/test_sem_coolify_vivo.py` (TDD Red-Green)
- **Ordem de Execução:** escrito **antes** de qualquer remoção.
- **Ação Executada:** varre `git ls-files -co --exclude-standard` e reprova qualquer rastro vivo de "coolify" (motor, API, `COOLIFY_*`, subcomando `ops coolify`, cliente) e qualquer arquivo com "coolify" no nome. Aceita linhas que declaram a abolição ("abolido", "sem Coolify", "removido"). Fora da varredura: documentos históricos datados, `AUDITORIA-FLUXO-PURE/`, baselines de segredos (hashes) e os testes que provam a ausência.
- **Entrega / Artefato Gerado:** `tests/test_sem_coolify_vivo.py`.
- **Status & Diagnóstico:**
  - *Sucesso:* Sim. Red: **206 rastros** (exit 1). Green: 2 passed depois da limpeza (a cópia da skill `aidd-ops` nos 6 espelhos foi o último passo: 6 rastros).
  - *Falhas / Anomalias:* nenhuma no guarda.

### [RECURSO]: Deploy real do `compose-nativo`
- **Ordem de Execução:** testes primeiro (`test_compose_deploy.py`, 20 testes), depois os módulos. *Nota honesta:* o Red desse arquivo foi só o erro de coleta (módulos inexistentes), não rodei os 20 individualmente em vermelho.
- **Ação Executada:**
  1. `src/core_ops/compose_deploy.py` (`ComposeDeployer`): valida o nome do ambiente (vira diretório remoto: `a b`, `x; rm -rf /`, `../fora`, `$(id)` são recusados **sem tocar na VPS**); empacota o projeto **sem** `.env`, `.env.*` (exceto `.env.example`), chaves (`*.pem`, `*.key`, `id_*`), `.git`, `node_modules`, caches, `dist` e `.aidd`; envia por SSH para `/opt/aidd/<ambiente>/`; roda `docker compose up -d --build`; confere `docker compose ps --format json` (todo serviço `running` e sem `unhealthy`). Códigos de erro: `AMBIENTE_INVALIDO`, `COMPOSE_AUSENTE`, `SSH_FALHOU`, `EXTRACAO_FALHOU`, `COMPOSE_UP_FALHOU` (com o final do log), `SERVICO_NAO_SAUDAVEL` (com a lista).
  2. `src/core_ops/cloudflare_dns.py` (`garantir_registro_a`): idempotente (cria, atualiza se o IP mudou, não mexe se está certo), valida nome e IP, **nunca** coloca o token em resultado ou erro, tem `dry_run`.
  3. `compose_preflight.verificar_isolamento_compose` (NIH #21 migrado do Coolify): reprova serviço que publica porta privilegiada (< 1024) do host além de 80 e 443.
  4. `scripts/pipeline_ops.py`: motor único (`DeployOrchestrator`, `motor` só aceita `compose-nativo`; outro valor devolve `MOTOR_DESCONHECIDO`); etapa 3 real cria o DNS (exige `CLOUDFLARE_API_TOKEN` e `CLOUDFLARE_ZONE_ID`; sem a zona: `DNS_ZONA_AUSENTE`); etapa 5 real roda isolamento + `ComposeDeployer` (o `REAL_NAO_IMPLEMENTADO` sumiu); fábricas injetáveis (`http_dns`, `fabrica_deployer`) para teste; a seleção automática de motor sumiu.
- **Entrega / Artefato Gerado:** os dois módulos novos, `tests/test_compose_deploy.py` (20) e `tests/test_deploy.py` migrado (12 testes, incluindo deploy real com SSH e HTTP injetados, falha que não vira sucesso e DNS sem zona).
- **Status & Diagnóstico:**
  - *Sucesso:* Sim, com **limite declarado**: o transporte SSH real (`TransporteParamiko`, paramiko, `RejectPolicy` + chaves do sistema) e a API real da Cloudflare **não foram exercitados** contra uma VPS e uma zona de verdade; o encadeamento está provado com SSH e HTTP injetados. Criar DNS no domínio do usuário é ação externa, não feita aqui.
  - *Prova real:* `ops plan --dir-projeto` → exit 0; `ops deploy teste --plano ... --host 127.0.0.1` (simulação) → exit 0, as 6 etapas `[OK]`, com o `docker-compose.yml` do projeto; `ops coolify health` → erro "unexpected extra argument" (o subcomando não existe mais); `aidd-ops` completo **197 passed** (exit 0).
  - *Falhas / Anomalias:* nenhuma.
  - *Decisão autônoma:* o `AppShell white-label` (NIH #20) e o registro do Intake Web no Coolify (NIH #19) **foram removidos junto**, pois dependiam do painel do Coolify; o Intake Web continua existindo como app Docker comum (README reescrito). O isolamento (NIH #21) foi preservado sobre o compose.

### [RECURSO]: Remoção e limpeza
- **Ação Executada:** removidos `src/core_ops/coolify.py` (`CoolifyClient` e `CoolifyManager`) e `tests/test_coolify.py` (62 menções); removidos o grupo `ops coolify` e a opção `--motor` do CLI; `GUIA.md` (seção reescrita como "Deploy compose-nativo, Isolamento VPS e DNS"), skill `aidd-ops` (e os 6 espelhos idênticos), README, Dockerfile, compose, requirements e `.dockerignore` do Intake Web, `.env.example` (as variáveis `COOLIFY_*` saíram) e uma linha histórica do gerador de relatório de evolução (agora diz que o Coolify foi depois abolido).
- **Status & Diagnóstico:** Sim. Documentos históricos datados (`docs/auditoria`, `docs/melhorias`, livros etc.) **ficam como estão**, conforme a decisão sobre o Next.js.

## TICKETS
- **Resolvidos neste relatório:** 8-A (abolição do Coolify e deploy real do `compose-nativo`).
- **Ticket 10-A: transporte SSH real e API real da Cloudflare não exercitados — ABERTO.** *Red:* rodar `ops deploy <env> --plano ... --host <vps> --domain <fqdn> --real` numa VPS descartável e numa zona de teste. *Prompt (EN):* Run the real deploy against a disposable VPS and a test Cloudflare zone, record the result, and fix whatever the injected tests could not catch (host-key policy, long builds, compose versions).
- **Ticket 10-B: `.env` do projeto não sobe — ABERTO (decisão de desenho):** o operador cria as variáveis de runtime na VPS. *Prompt (EN):* Add an explicit step that writes the project's runtime variables on the VPS from a vault (sops/age) instead of copying `.env`.
- **Ticket 10-C: a etapa 6 do orquestrador `/pure` só roda `ops plan` (não implanta) — ABERTO (decisão de segurança):** deploy real mexe na VPS e no DNS do usuário, então continua sendo um passo explícito (`ops deploy --real`). *Prompt (EN):* Offer an opt-in `--deploy` flag on `/pure` that runs `ops deploy --real` after the final audit.
