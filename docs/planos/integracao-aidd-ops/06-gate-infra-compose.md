# Pacote 6 — Gate `G_INFRA_COMPOSE.py` (Gap 3 da proposta)

> **Status:** Concluído (100% testado e integrado)
> **Gap original coberto:** Gap 3 (§8.2 da proposta) — "Quality Gate de Docker e Redes".
> **Natureza:** gate 100% estático e offline — mesma classe dos 6 gates já existentes, sem efeito colateral em sistemas reais.

---

## Diagnóstico

Os 6 gates atuais (`gates/G_*.py`) auditam código Python, segredos, compatibilidade multi-harness e drift estrutural — nenhum audita arquivos de orquestração Docker ou topologia de banco **dentro do escopo de `tools/aidd-ops/` e seus templates de infraestrutura** (este gate não audita os `docker-compose.yml` já existentes em `tools/aidd-master/templates/`, `tools/aidd-enterprise/templates/` ou `.../materiais-extras/examples/` — esses ficam fora de escopo por decisão deliberada, para não invadir as 4 ferramentas já homologadas). Este gate fecha a lacuna dentro do seu escopo, e por ser puramente estático (roda `docker compose config`, que só valida sintaxe, sem subir nada), pode entrar na bateria síncrona de `python ecossistema.py audit`.

**Correção aplicada após auditoria real (verificação independente):**
- **Dependência de ambiente não tratada, corrigida.** Testei ao vivo: `docker compose config` roda sem precisar do daemon acessível (confirmado com `DOCKER_HOST` inalcançável, ainda retorna exit 0/YAML renderizado) — a alegação "puramente estático" está correta. Mas o binário `docker` em si precisa estar instalado e no PATH, e isso **nunca é verificado hoje por nenhum dos 6 gates existentes** (seria o primeiro a depender de um binário externo). Testado ao vivo: chamar um binário inexistente via `subprocess.run` sem tratamento lança `FileNotFoundError` não capturada — isso quebraria `python ecossistema.py audit` com traceback cru em qualquer máquina sem Docker, em vez de reprovar com mensagem `[FALHA]` limpa no mesmo padrão dos outros gates. Corrigido abaixo com checagem explícita via `shutil.which("docker")`.
- **Nome de arquivo corrigido:** o artefato real que o Pacote 3 produz é `PLANO-INFRAESTRUTURA.json` (arquivo único por execução, gravado no diretório de saída escolhido pelo usuário via `--pasta`), não um padrão `plano-infra-*.json` que não existe. Além disso, como esse arquivo é efêmero e por-execução (nunca commitado, nunca em caminho fixo do repositório), a checagem "todo banco do plano tem entrada no script" só faz sentido contra um `PLANO-INFRAESTRUTURA.json` **estático e versionado**, um por template canônico de nicho (Pacote 8) — não contra uma execução de teste qualquer do usuário. Corrigido abaixo para deixar isso explícito.
- **Caminho de templates corrigido:** `componentes/templates/infra/` foi corrigido no Pacote 8 para `tools/aidd-ops/templates/infra/<bloco>/` (templates de infra não passam por `components sync` multi-harness) — este gate precisa apontar para o mesmo caminho corrigido, não para o antigo.

---

## Definição de Pronto

1. `gates/G_INFRA_COMPOSE.py` criado seguindo o mesmo estilo dos gates existentes (ler `gates/G_HARNESS_COMPAT.py` primeiro como referência de estrutura/retorno).
2. **Checagem de pré-requisito de ambiente, antes de qualquer outra validação:** `shutil.which("docker")` — se `None`, o gate reprova com `Result`/mensagem estruturada e honesta (ex.: "Docker não encontrado no PATH — este gate exige Docker instalado para validar sintaxe de compose"), nunca deixa uma exceção não tratada propagar como traceback cru. Documentar isso explicitamente como um novo tipo de pré-requisito de ambiente para `python ecossistema.py audit` (até agora 100% Python-only, sem dependência de binário externo).
3. Validações mínimas, todas estáticas (só depois do item 2 confirmar Docker disponível):
   - `docker compose config` sem erro de sintaxe para todo `docker-compose.yml` gerado/versionado em `tools/aidd-ops/` ou em `tools/aidd-ops/templates/infra/<bloco>/` (templates canônicos, Pacote 8).
   - Colisão de portas externas: nenhum `docker-compose.yml` do catálogo pode expor a mesma porta de host duas vezes.
   - Script de inicialização do PostgreSQL centralizado (`init-multiple-databases.sh`, quando presente) validado sintaticamente (`bash -n`) e conferido contra a lista de bancos lógicos declarada num `PLANO-INFRAESTRUTURA.json` **estático e versionado, um por template canônico de nicho** (não contra uma execução de teste do usuário) — todo banco listado deve ter uma entrada correspondente de criação no script, e vice-versa.
   - Toda variável de ambiente sensível referenciada em um `docker-compose.yml` (`${VAR}`) precisa ter definição correspondente no `.env.example` do mesmo diretório — sem valor hardcoded no compose.
4. Gate registrado em `ecossistema.py audit` (`cmd_audit`), como 7º gate raiz, documentado em `AGENTS.md §4`.
5. Testes automatizados (`gates/test_g_infra_compose.py`): um `docker-compose.yml` sintaticamente inválido forjado precisa reprovar; um com colisão de porta forjada precisa reprovar; um caso são precisa passar; **um caso simulando Docker ausente do PATH precisa reprovar com mensagem estruturada, nunca com traceback**. Mesmo padrão de prova dos gates existentes (`gates/test_g_cli_help_consistencia.py` como referência).

---

## Prompt de Execução

> Copie o bloco abaixo integralmente para o agente executor. Autocontido — não pressupõe que ele viu esta conversa.

```
Você vai criar um gate determinístico novo, gates/G_INFRA_COMPOSE.py,
cobrindo o Gap 3 identificado em
"docs/features/PLANO ARQUITETURAL NOVA FEATURE AIDD-OPS.md §8.2":
validação estática de arquivos docker-compose.yml e do script de
inicialização do PostgreSQL centralizado. Este gate é 100% estático e
offline — não sobe nenhum contêiner real, só valida sintaxe/estrutura.

DEFINIÇÃO DE PRONTO:

1. Leia gates/G_HARNESS_COMPAT.py e gates/G_DRIFT_NUCLEO_COMPARTILHADO.py
   primeiro para seguir o mesmo estilo de estrutura, retorno (exit
   0/1) e formato de mensagem de erro dos gates existentes.

2. Checagem de pré-requisito de ambiente, ANTES de qualquer outra
   validação: `shutil.which("docker")` — se `None`, o gate reprova com
   mensagem estruturada e honesta (ex.: "Docker não encontrado no PATH
   — este gate exige Docker instalado para validar sintaxe de compose"),
   nunca deixa uma exceção não tratada propagar como traceback cru.
   Documente isso como um novo tipo de pré-requisito de ambiente para
   `python ecossistema.py audit` (até agora 100% Python-only).

3. Implemente as checagens, todas via subprocess/parsing estático, sem
   subir nenhum contêiner (só depois do item 2 confirmar Docker
   disponível):
   a. `docker compose config` para todo docker-compose.yml sob
      tools/aidd-ops/ ou tools/aidd-ops/templates/infra/<bloco>/
      (templates canônicos, Pacote 8) — reprova se sair código de erro.
   b. Parseie as portas de host expostas (seção `ports:`) e reprove se
      houver colisão dentro do mesmo arquivo compose.
   c. Se existir um script init-multiple-databases.sh no escopo, valide
      com `bash -n` (sintaxe) e confira que todo banco lógico citado num
      `PLANO-INFRAESTRUTURA.json` ESTÁTICO E VERSIONADO, um por template
      canônico de nicho (não contra uma execução de teste do usuário —
      esse arquivo é efêmero, por execução, nunca em caminho fixo do
      repositório) tem uma linha de criação correspondente no script.
   d. Para toda variável ${VAR} referenciada em um docker-compose.yml,
      confirme que existe VAR= no .env.example do mesmo diretório, sem
      valor default sensível hardcoded no próprio compose.

4. Registre o gate em ecossistema.py (cmd_audit) como 7º gate raiz,
   documente em AGENTS.md §4 no mesmo formato dos 6 existentes.

5. Escreva gates/test_g_infra_compose.py: fixtures com um compose
   sintaticamente quebrado, um com colisão de porta forjada, um são
   (deve passar), um caso de variável sem .env.example correspondente, e
   **um caso simulando Docker ausente do PATH, confirmando reprovação
   com mensagem estruturada, nunca traceback.**

6. Rode `python ecossistema.py audit` (7 gates agora) e confirme exit 0
   sem regressão nos 6 gates existentes.

REGRAS DE ESCOPO — NÃO FAÇA: não suba nenhum contêiner Docker real (nem
para teste — use fixtures estáticas); não toque nos outros 6 gates além
de registrar o novo em cmd_audit; não faça git commit/push sem aprovação.

ENTREGÁVEL: código do gate, testes, output real de
`python ecossistema.py audit` e de `pytest gates/`.
```

---

## Critério de validação

`python ecossistema.py audit` exit 0 com 7 gates; `pytest gates/test_g_infra_compose.py` 100% passando, incluindo os casos forjados de reprovação.

---

## Veredito da Execução (Auditoria Real)

- **Status:** APROVADO (100% dos critérios de aceite atingidos).
- **Gate Implementado:** `gates/G_INFRA_COMPOSE.py` cobrindo 100% estático (sem subir contêineres):
  - Pré-requisito de ambiente: `shutil.which("docker")` verificado no início, falhando limpo com mensagem estruturada (sem traceback) se ausente.
  - Validação de 7 arquivos `docker-compose.yml` (`authentik`, `calcom`, `chatwoot`, `gateway`, `postgres`, `traefik`, `twenty`) via `docker compose config` com interpolação mock baseada nos arquivos `.env.example`.
  - Correção de sintaxe YAML no template do `postgres` (adicionadas aspas na variável com dois-pontos embutido).
  - Validação estrita de colisão de portas no host (bloco `ports:`).
  - Validação de variáveis de ambiente: variáveis referenciadas devem constar no `.env.example` local.
  - Validação de `init-multiple-databases.sh` via `bash -n` e conferência contra os 5 planos canônicos de nichos em `tools/aidd-ops/templates/infra/nichos/*.json`.
- **Registro no Ecossistema:**
  - Registrado em `ecossistema.py` (`cmd_audit`) como 7º gate raiz.
  - Documentado formalmente em `AGENTS.md §4`.
- **Suíte de Testes:** `gates/test_g_infra_compose.py` criado com 6 testes unitários verdes (incluindo teste com mock de Docker ausente, colisão de portas e variáveis faltantes).
- **Validação Global:** `python ecossistema.py audit` rodou com 7 gates em sequência, todos 100% aprovados (exit 0). `pytest gates/` (27 testes) e `pytest tools/aidd-ops/tests/` (39 testes) todos verdes (66 testes no monorepo).

## Prompt de Execução — English version

```
You are going to create a new deterministic gate,
gates/G_INFRA_COMPOSE.py, covering Gap 3 identified in
"docs/features/PLANO ARQUITETURAL NOVA FEATURE AIDD-OPS.md §8.2": static
validation of docker-compose.yml files and of the centralized PostgreSQL
initialization script. This gate is 100% static and offline — it never
spins up a real container, it only validates syntax/structure.

DEFINITION OF DONE:

1. Read gates/G_HARNESS_COMPAT.py and
   gates/G_DRIFT_NUCLEO_COMPARTILHADO.py first to follow the same
   structure/return style and error-message format as the existing
   gates.

2. Environment-prerequisite check, BEFORE any other validation:
   `shutil.which("docker")` — if `None`, the gate fails with a
   structured, honest message (e.g. "Docker not found on PATH — this
   gate requires Docker to validate compose syntax"), never letting an
   unhandled exception propagate as a raw traceback. Document this
   explicitly as a new kind of environment prerequisite for
   `python ecossistema.py audit` (100% Python-only until now, no
   external binary dependency).

3. Implement the checks, all via subprocess/static parsing, without
   spinning up any container (only after step 2 confirms Docker is
   available):
   a. `docker compose config` for every docker-compose.yml under
      tools/aidd-ops/ or tools/aidd-ops/templates/infra/<block>/
      (canonical templates, Package 8) — fail if it exits with an error
      code.
   b. Parse the exposed host ports (the `ports:` section) and fail if
      there is a collision within the same compose file.
   c. If an init-multiple-databases.sh script exists in scope, validate
      it with `bash -n` (syntax) and confirm that every logical
      database cited in a STATIC, VERSIONED PLANO-INFRAESTRUTURA.json,
      one per canonical niche template (not against a user's ad-hoc
      test run — that file is ephemeral, per-run, never at a fixed
      repo path) has a matching creation line in the script.
   d. For every ${VAR} referenced in a docker-compose.yml, confirm a
      matching VAR= exists in the same directory's .env.example, with
      no sensitive default value hardcoded in the compose file itself.

4. Register the gate in ecossistema.py (cmd_audit) as the 7th root
   gate, document it in AGENTS.md §4 in the same format as the existing
   6.

5. Write gates/test_g_infra_compose.py: fixtures with a syntactically
   broken compose, one with a forged port collision, a healthy one
   (must pass), a case of a variable missing its .env.example
   counterpart, and **a case simulating Docker missing from PATH,
   confirming a structured failure message, never a raw traceback.**

6. Run `python ecossistema.py audit` (7 gates now) and confirm exit 0
   with no regression in the 6 existing gates.

SCOPE RULES — DO NOT: spin up any real Docker container (not even for
testing — use static fixtures); touch the other 6 gates beyond
registering the new one in cmd_audit; `git commit`/`git push` without
approval.

DELIVERABLE: gate code, tests, real output of
`python ecossistema.py audit` and of `pytest gates/`.
```
