# Auditoria de Etapa: Instalação de Dependências (v2, após correção do Ticket 1)

### [RECURSO]: python ecossistema.py dependencia verify (1ª execução, clone novo)
- **Ordem de Execução:** 1º acionamento da ETAPA_02, após o clone da ETAPA_01 (HEAD `89b4facc`).
- **Ação Executada:** `python ecossistema.py dependencia verify` na raiz do clone, com exit code capturado.
- **Entrega / Artefato Gerado:** diagnóstico de 66 dependências declaradas: 42 pendências (15 skills não instaladas, 27 registros de MCP ausentes).
  - *Caminho Exato (100% concluído):* `C:\Users\trcnologia\aidd-logs-verify.txt`
- **Status & Diagnóstico:**
  - *Sucesso:* Sim. A reprovação (exit 1) era o estado esperado de um clone novo.
  - *Falhas / Anomalias:*
    - *Ocorrência:* Nenhuma além do estado inicial.
    - *Localização Exata do Erro:* N/A
  - *Ação Corretiva Cirúrgica:* N/A

### [RECURSO]: python ecossistema.py dependencia bootstrap (1ª execução)
- **Ordem de Execução:** após o `verify` inicial reprovar.
- **Ação Executada:** `python ecossistema.py dependencia bootstrap`, exit code capturado.
- **Entrega / Artefato Gerado:** hook git pre-commit ativado; 14 skills instaladas; 27 registros de MCP.
  - *Caminho Exato (100% concluído):* `FLUXO-PURE\.claude\skills\{agents-sdk,cloudflare,cloudflare-email-service,cloudflare-one,cloudflare-one-migrations,durable-objects,nextjs-on-cloudflare,sandbox-migrate-to-next,sandbox-next,sandbox-stable,turnstile-spin,web-perf,workers-best-practices,wrangler}\`; MCPs em `FLUXO-PURE\.agents\mcp_config.json`, `FLUXO-PURE\.mcp.json`, `FLUXO-PURE\mimocode.jsonc`. Log: `C:\Users\trcnologia\aidd-logs-bootstrap.txt`
- **Status & Diagnóstico:**
  - *Sucesso:* Não. Exit 1: a skill `impeccable` foi instalada, mas o SHA-256 do `SKILL.md` divergiu do fixado no manifesto.
  - *Falhas / Anomalias:*
    - *Ocorrência:* hash esperado `3895765e…2cb27`, obtido `35c88304…d234c`.
    - *Localização Exata do Erro:* `modulos/04-nucleo-compartilhado/contracts/dependencias_externas.json:9`; comparação em `scripts/gestor_dependencias.py:150-162`.
  - *Ação Corretiva Cirúrgica:* diagnóstico e correção no recurso seguinte.

### [RECURSO]: Diagnóstico do Ticket 1 (npm view + instalação isolada de 10 versões do impeccable)
- **Ordem de Execução:** após a falha do bootstrap, seguindo o Ticket 1 (v1).
- **Ação Executada:**
  1. `npm view impeccable versions`: 41 versões publicadas; `latest` = 4.5.2.
  2. Instalação em diretórios temporários (`git init` + `npx -y impeccable@<v> install --providers=claude --scope=project -y`) das versões 4.5.2, 4.5.1, 4.1.0, 4.0.5, 4.0.4, 4.0.3, 4.0.2, 4.0.1, 4.0.0 e 3.6.1, com `sha256sum` do `SKILL.md` de cada uma.
  3. Comparação (`diff`, com `\r` removido) entre o `SKILL.md` do repositório original (`version: 4.3.1`) e o recém-instalado (`version: 4.5.2`).
- **Entrega / Artefato Gerado:** causa-raiz comprovada.
  - *Caminho Exato (100% concluído):* diretórios e logs em `C:\Users\trcnologia\aidd-tmp\t_<versão>\` e `log_<versão>.txt` (fora do projeto).
- **Status & Diagnóstico:**
  - *Sucesso:* Sim.
  - *Falhas / Anomalias:*
    - *Ocorrência:* a hipótese da v1 (o `npx` pegar versão nova por falta de pin) estava **errada**. As 10 versões testadas instalam o mesmo `SKILL.md` (`version: 4.5.2`, hash `35c88304…`). O CLI imprime "Downloading impeccable skills..." e baixa o conteúdo atual de um servidor remoto, ignorando a versão do pacote npm.
    - O hash fixado no manifesto corresponde ao `SKILL.md` **4.3.1** (confirmado: o arquivo do repositório original, normalizado para LF, tem sha256 `3895765e…`). O conteúdo do impeccable evoluiu (4.3.1 → 4.5.2: nova ação `generate`, nova regra sobre símbolos) e o hash ficou defasado.
    - *Localização Exata do Erro:* `modulos/04-nucleo-compartilhado/contracts/dependencias_externas.json:9` (campo `sha256`). Fixar a versão no `instalar` não resolve.
  - *Ação Corretiva Cirúrgica:* atualizar o `sha256` para o do conteúdo atual (recurso seguinte).

### [RECURSO]: Correção do Ticket 1 (edição do manifesto) + bootstrap e verify de confirmação
- **Ordem de Execução:** após o diagnóstico.
- **Ação Executada:**
  1. `sed` substituindo `3895765e…2cb27` por `35c883046117a416ca008ad7cbcda912c728a01f99b9a88130c2f0ab4c8d234c` em `dependencias_externas.json:9`. `git diff --stat`: 1 linha alterada.
  2. `python ecossistema.py dependencia bootstrap` → exit 0.
  3. `python ecossistema.py dependencia verify` → exit 0, "[SUCESSO] Todas as dependencias externas declaradas estao instaladas/registradas." (66 declaradas).
- **Entrega / Artefato Gerado:** manifesto corrigido; ambiente de dependências íntegro.
  - *Caminho Exato (100% concluído):* `FLUXO-PURE\modulos\04-nucleo-compartilhado\contracts\dependencias_externas.json`. Logs: `C:\Users\trcnologia\aidd-logs-bootstrap2.txt`, `C:\Users\trcnologia\aidd-logs-verify3.txt`
- **Status & Diagnóstico:**
  - *Sucesso:* Sim. Exit 0 real, capturado na mesma linha do comando, sem pipe.
  - *Falhas / Anomalias:*
    - *Ocorrência:* Nenhuma.
    - *Localização Exata do Erro:* N/A
  - *Ação Corretiva Cirúrgica:* a correção é só no clone de teste (`FLUXO-PURE`). O repositório original não foi tocado.
  - *Ressalva:* o hash fixado vai defasar de novo quando o upstream do impeccable mudar, porque o instalador sempre baixa o conteúdo atual. Isso é fragilidade do desenho (hash de artefato sem pin real), registrada no Ticket 2.

## TICKETS
### Ticket 1: Hash do impeccable defasado em relação ao conteúdo baixado (Refere-se a Gate de integridade SHA-256 do `dependencia verify`) — RESOLVIDO
- **Falha:** `dependencia verify`/`bootstrap` saíam com exit 1 num clone novo porque o manifesto fixava o hash do `SKILL.md` 4.3.1 e o instalador entrega o 4.5.2.
- **Artefato de Handoff:** `modulos/04-nucleo-compartilhado/contracts/dependencias_externas.json`
- **Requisito TDD (Red):** `python ecossistema.py dependencia verify` após `bootstrap` retornava exit 1 com "hash SHA-256 divergente" para `skill/impeccable` (evidência: `aidd-logs-verify2.txt`).
- **Implementação Técnica:**
  - Comprovado que nenhuma versão do pacote npm reproduz o hash antigo (as 10 testadas instalam o mesmo conteúdo).
  - Atualizado o campo `sha256` (linha 9) para `35c88304…d234c`.
- **Verificação (Green):** `dependencia bootstrap` (exit 0) e `dependencia verify` (exit 0), em `aidd-logs-verify3.txt`.
- **Construtor Prompt (EN):**
  - Update the `sha256` of skill `impeccable` in `modulos/04-nucleo-compartilhado/contracts/dependencias_externas.json:9` to the hash of the currently installed `.claude/skills/impeccable/SKILL.md`.
  - Run `python ecossistema.py dependencia bootstrap` and `python ecossistema.py dependencia verify` and assert both exit 0.

### Ticket 2: Hash fixo de skill sem pin de conteúdo quebra a cada release do upstream (Refere-se a Gate de integridade SHA-256) — ABERTO, NÃO EXECUTADO
- **Falha:** o instalador do `impeccable` baixa o conteúdo atual de um servidor remoto e ignora a versão do npm. Qualquer hash fixado reprova de novo na próxima atualização upstream, e o clone fica bloqueado.
- **Artefato de Handoff:** `scripts/gestor_dependencias.py` (linhas 150-162) e `modulos/04-nucleo-compartilhado/contracts/dependencias_externas.json`
- **Requisito TDD (Red):** teste que simula `SKILL.md` com `version:` diferente da fixada e espera que o `verify` dê um aviso claro com a versão esperada e a obtida, em vez de acusar "artefato pode ter sido adulterado".
- **Implementação Técnica:**
  - Decidir com o usuário entre: (a) fixar também a `version:` esperada no manifesto e distinguir "versão nova" de "adulteração"; (b) hospedar uma cópia verificada da skill dentro do repositório.
- **Verificação (Green):** `pytest` do teste novo com exit 0.
- **Construtor Prompt (EN):**
  - Do not implement before the user chooses option (a) or (b).
  - After approval, add a failing test in the gestor_dependencias test file that feeds a SKILL.md with a different `version:` and asserts the verify message distinguishes version drift from tampering; then implement and run it with exit 0.
