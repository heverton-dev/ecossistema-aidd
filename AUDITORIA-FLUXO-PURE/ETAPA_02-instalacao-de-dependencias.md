# Auditoria de Etapa: Instalação de Dependências

### [RECURSO]: python ecossistema.py dependencia verify
- **Ordem de Execução:** 1º acionamento da ETAPA_02, logo após o clone da ETAPA_01 (HEAD `89b4facc`).
- **Ação Executada:** `python ecossistema.py dependencia verify` na raiz do clone, saída redirecionada a arquivo, exit code capturado.
- **Entrega / Artefato Gerado:** diagnóstico de 66 dependências declaradas.
  - *Caminho Exato (100% concluído):* log bruto em `C:\Users\trcnologia\aidd-logs-verify.txt`
- **Status & Diagnóstico:**
  - *Sucesso:* Sim (o diagnóstico foi produzido) — o `verify` reprovou como esperado num clone novo: exit 1, 42 pendências (15 skills não instaladas, 27 registros de MCP ausentes).
  - *Falhas / Anomalias:*
    - *Ocorrência:* Nenhuma além do estado inicial esperado.
    - *Localização Exata do Erro:* N/A
  - *Ação Corretiva Cirúrgica:* acionado o `bootstrap` (recurso abaixo).

### [RECURSO]: python ecossistema.py dependencia bootstrap
- **Ordem de Execução:** logo após o `verify` reprovar (exit 1).
- **Ação Executada:** `python ecossistema.py dependencia bootstrap`, saída em arquivo, exit code capturado. Em seguida, novo `verify`.
- **Entrega / Artefato Gerado:** hook git pre-commit de auto-sync ativado; 14 skills instaladas; 27 registros de MCP feitos.
  - *Caminho Exato (100% concluído):*
    - Skills: `FLUXO-PURE\.claude\skills\<agents-sdk|cloudflare|cloudflare-email-service|cloudflare-one|cloudflare-one-migrations|durable-objects|nextjs-on-cloudflare|sandbox-migrate-to-next|sandbox-next|sandbox-stable|turnstile-spin|web-perf|workers-best-practices|wrangler>\`
    - MCPs (modificados): `FLUXO-PURE\.agents\mcp_config.json`, `FLUXO-PURE\.mcp.json`, `FLUXO-PURE\mimocode.jsonc`
    - Log bruto: `C:\Users\trcnologia\aidd-logs-bootstrap.txt`
- **Status & Diagnóstico:**
  - *Sucesso:* Não — exit 1 do `bootstrap` e do `verify` seguinte (restou 1 pendência, de 66).
  - *Falhas / Anomalias:*
    - *Ocorrência:* skill `impeccable` instalada via `npx impeccable install` (versão 4.5.2), mas o SHA-256 de `.claude/skills/impeccable/SKILL.md` diverge do fixado no manifesto. O comando de instalação não fixa versão, então o `npx` baixou uma versão mais nova que a do hash fixado. Isso é hipótese, ainda não comprovada: falta saber qual versão gera o hash esperado.
      - Esperado: `3895765e9434400dfc1b30e364be002cf499c1718fb2431e65b907c14ae2cb27`
      - Obtido: `35c883046117a416ca008ad7cbcda912c728a01f99b9a88130c2f0ab4c8d234c`
    - *Localização Exata do Erro:* manifesto `modulos/04-nucleo-compartilhado/contracts/dependencias_externas.json:9` (campo `sha256` da skill `impeccable`); comparação em `scripts/gestor_dependencias.py:150-162`.
  - *Ação Corretiva Cirúrgica:* nenhuma aplicada. Trocar o hash sem saber a causa seria aceitar artefato não verificado; aguarda decisão do usuário.

## TICKETS
### Ticket 1: Hash do impeccable diverge da instalação via npx sem versão fixa (Refere-se a Gate de integridade SHA-256 do `dependencia verify`)
- **Falha:** `dependencia verify`/`bootstrap` saem com exit 1 num clone novo porque o `impeccable` é instalado sem versão fixada e seu `SKILL.md` não bate com o `sha256` do manifesto.
- **Artefato de Handoff:** `modulos/04-nucleo-compartilhado/contracts/dependencias_externas.json`
- **Requisito TDD (Red):** `python ecossistema.py dependencia verify` num clone limpo após `bootstrap` retorna exit 1 com a mensagem "hash SHA-256 divergente" para `skill/impeccable`.
- **Implementação Técnica:**
  - Descobrir a versão do pacote `impeccable` cujo `SKILL.md` tem sha256 `3895765e...2cb27`; se nenhuma reproduzir, decidir com o usuário atualizar o hash fixado.
  - Fixar a versão no campo `instalar` (ex.: `npx impeccable@<versão> install ...`) e manter ou atualizar o `sha256` de acordo.
- **Verificação (Green):** `python ecossistema.py dependencia bootstrap` e depois `python ecossistema.py dependencia verify` com exit 0 num clone limpo.
- **Construtor Prompt (EN):**
  - Find which published version of the `impeccable` npm package produces a `.claude/skills/impeccable/SKILL.md` whose sha256 equals `3895765e9434400dfc1b30e364be002cf499c1718fb2431e65b907c14ae2cb27`.
  - Pin that version in the `instalar` command of `modulos/04-nucleo-compartilhado/contracts/dependencias_externas.json`; if no version matches, stop and ask the user before changing the `sha256`.
  - Run `python ecossistema.py dependencia bootstrap && python ecossistema.py dependencia verify` in a clean clone and assert exit 0.
