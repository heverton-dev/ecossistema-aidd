# Item 7 — Bootstrap de dependências do produto gerado, por ferramenta (forge não é chamado por nenhuma das outras 4)

> **Escopo:** Entra: decidir e sequenciar como cada ferramenta (`aidd-forge`, `aidd-generator`, `aidd-master`, `aidd-enterprise`, `aidd-ops`) passa a instalar/wire, no que ela **entrega ao usuário final**, as dependências reais que fazem sentido pro produto gerado (ex.: Cookiecutter real pra scaffolding do master/enterprise via Fase 2 já planejada, Alembic, detect-secrets, hadolint/Checkov onde couber). Não entra: reaproveitar o mecanismo de `gates/dependencias_externas.json` + `dependencia-runner` como está — aquele é exclusivamente para dependências do **agente que desenvolve este repo** (code-review-graph, LLMLingua-2, context7, GitHub MCP), nunca embarcadas no produto gerado.
> **Status:** [PROTÓTIPO GENERALIZADO PARA aidd-enterprise EM 2026-09-08 — aprovado pelo usuário; aidd-generator e aidd-ops seguem fora de escopo desta decisão]
> **Modelo sugerido:** Claude Opus · Antigravity Gemini 3.8 · MiMo mimo-v2.5-pro (decisão de arquitetura entre 4 pipelines distintos)

---

## Contexto já investigado

- Pergunta original do usuário: as 5 ferramentas também deveriam entregar/instalar isso (dependências mapeadas) no que geram, "desde o Forge até o Ops"?
- Investigação real feita em 2026-09-07: **não existe corrente de chamada entre as ferramentas.** `aidd-forge` é 100% standalone — injeta infraestrutura de desenvolvimento-com-IA (subagentes, gates, `AGENTS.md`) em "qualquer projeto", mas nenhuma das outras 4 ferramentas o importa ou invoca. As referências a "aidd-forge" encontradas em `aidd-generator/scripts/core/injector/contrato.py` e nos `materializador.py` de `aidd-master`/`aidd-enterprise` são só uma string num tuple de nomes conhecidos e um comentário de código ("mesmo padrão do aidd-forge") — nunca uma chamada real.
- Cada ferramenta tem seu próprio `materializador.py`/injector duplicado (4 implementações paralelas do mesmo conceito). `pipeline_completo.py` do generator não tem nenhuma fase de bootstrap de dependência do produto.
- Conclusão: forge injeta infraestrutura de **como construir** (governança de IA); o que o usuário pediu é infraestrutura de **o que foi construído** (dependências reais do app gerado). São naturezas diferentes — acoplar os dois no mesmo mecanismo repete a confusão que a distinção dependencia-runner-vs-produto já resolveu para o agente.
- Decisão de arquitetura em aberto: (a) cada ferramenta ganha seu próprio script de bootstrap de dependências do produto, isolado, sem depender do forge; ou (b) as 4 ferramentas passam a chamar o forge como fase 0 real (acoplamento novo, maior risco, toca os 4 pipelines).

## Decisão registrada (2026-09-07)

**Opção escolhida: (a) — cada ferramenta mantém seu próprio bootstrap de dependências do produto, sem depender do forge.**

Justificativa, ancorada no levantamento concreto acima:

1. **Forge não tem o que contribuir aqui.** Confirmado por investigação real (não suposição): `aidd-forge` não gera produto para usuário final — não escreve `requirements.txt`/manifest em nenhum alvo, só injeta infraestrutura de desenvolvimento-com-IA (subagentes, gates, `AGENTS.md`). Chamá-lo como "fase 0" (opção b) forçaria o forge a aprender a inspecionar templates alheios (`templates/core/security.py`, `events.py`, etc.) de 4 ferramentas que ele nunca conheceu — inversão de responsabilidade, não reaproveitamento.
2. **O ponto de geração do manifesto já existe e já é local a cada ferramenta.** `compose_suite.py:1833-1841` e `provision_project.py:84-86` (aidd-master/aidd-enterprise), e `05_criador.py:772-776` (aidd-generator) já são os únicos lugares que escrevem `requirements.txt` no produto. A correção real é fechar o gap ali — no ponto que já tem acesso direto aos templates/módulos que vão ser copiados — não introduzir uma chamada de rede/processo extra a uma ferramenta externa (forge) que teria que redescobrir essa mesma informação.
3. **Risco e raio de explosão.** (b) tocaria os 4 pipelines simultaneamente para resolver um problema que, na prática, é uma lacuna pontual (`requirements.txt` hardcoded e incompleto) em cada motor. (a) permite corrigir e reproduzir uma ferramenta por vez, isolado, sem acoplar o sucesso de uma à disponibilidade/versão do forge.
4. **Consistência com a distinção já estabelecida no ecossistema.** O próprio mecanismo `gates/dependencias_externas.json` + `dependencia-runner` já separa "dependência do agente que desenvolve este repo" de "dependência do produto gerado". Fazer o forge (ferramenta de desenvolvimento-com-IA) prover dependências de runtime do produto gerado reintroduziria a mesma confusão de camadas que aquela separação resolveu.

## Protótipo real — aidd-master, motor `compose_suite.py` (2026-09-07)

**Achado concreto que motivou o alvo do protótipo:** todo produto composto via `compose_suite.py` tem o `src/server.py` gerado com as rotas de SSO Corporativo (OAuth2/OIDC + PKCE) sempre registradas (`compose_suite.py`, bloco `SERVER_TEMPLATE`, rotas `/api/auth/oauth/login` e `/api/auth/oauth/callback`), que chamam `OIDCService.validate_id_token` (`templates/core/security.py:167-185`). Esse método faz `import jwt` (PyJWT) e usa `jwt.algorithms.RSAAlgorithm` (que depende de `cryptography`) para validar o `id_token` via JWKS/RS256. Porém o `requirements.txt` gerado em `compose_suite.py:1833-1838` **nunca** declarava `pyjwt`/`cryptography` — só `pytest`, `mutmut`, `requests`, e `psycopg2-binary` quando `--db postgres`. Resultado real: qualquer empresa que configure as variáveis `OIDC_*` (SSO já documentado como "Zero Fricção" no próprio server gerado) recebe `RuntimeError("PyJWT não instalado...")` em produção, porque a dependência nunca foi instalada — não é hipotético, é o comportamento do código hoje.

**Correção aplicada:** `compose_suite.py` passa a incluir `pyjwt>=2.8.0` e `cryptography>=42.0.0` de forma incondicional no `requirements.txt` gerado (a rota SSO é sempre registrada em todo produto, então a dependência é sempre real, não condicional como `psycopg2-binary`).

**Reprodução real (antes/depois), script em `docs/relatorios/`:**
- **Antes:** gerado projeto de teste em pasta temporária isolada (`compose_suite.py <tmp> "TesteBootstrap" vendas --db sqlite`) com o código original; `requirements.txt` resultante **não** contém `pyjwt`/`cryptography`; instalando esse `requirements.txt` num venv limpo e chamando `OIDCService.validate_id_token(...)` com um `id_token` RS256 real (assinado on-the-fly com uma chave RSA gerada via `cryptography`) levanta `RuntimeError: PyJWT não instalado...` — falha real, reproduzida, não suposta.
- **Depois:** mesmo fluxo com a correção aplicada; `requirements.txt` agora contém `pyjwt>=2.8.0` e `cryptography>=42.0.0`; `pip install -r requirements.txt` num venv limpo instala as duas dependências; chamar `OIDCService.validate_id_token(...)` com o mesmo `id_token`/JWKS forjados retorna as claims decodificadas corretamente — a dependência está de fato instalada e funcional, não só um arquivo copiado.

Evidência completa (comandos, saídas de `pip install`, script de reprodução) em `docs/relatorios/item-7-prototipo-compose-suite-jwt.md`.

## Levantamento concreto por ferramenta (investigação real, 2026-09-07)

> Item 1 da Definição de Pronto abaixo — concluído. Cada linha verificada em código real (arquivo:linha), não suposição.

| Ferramenta | Gera produto pro usuário final? | Dependência de produto hoje | Achado |
|---|---|---|---|
| **aidd-forge** | Não — só infraestrutura de desenvolvimento-com-IA (gates stdlib puro, skills, hooks git, `AGENTS.md`). Nenhum `requirements.txt`/manifest gravado no alvo. | N/A | **Fora de escopo deste item.** Forge não gera produto — não há onde embarcar dependência de produto. |
| **aidd-master / aidd-enterprise** | Sim | Zero declarada — `templates/core/security.py` e `templates/v2/security.py` (idênticos nos dois) são JWT hand-rolled via `hmac`/`hashlib`/`base64`, CSP como string literal; `database.py` usa `sqlite3` cru; RLS do enterprise reescreve SQL via regex (`_rewrite_insert`/`_rewrite_select`). Nenhum `requirements.txt` existe dentro de `templates/core/` ou `templates/v2/`. Dockerfile gerado (`templates/core/Dockerfile:9,25`) segue sem `RUN pip install`. `add_module.py`/`compose_suite.py` não usam Jinja2/Cookiecutter, só string/`.format`. | Maior espaço de ganho: qualquer dependência real adicionada (SQLAlchemy, secure.py, Cookiecutter) entra num produto que hoje não declara nenhuma. |
| **aidd-generator** | Sim | `requirements.txt` gerado na Fase 5 (`05_criador.py:772-776`) grava só `requests>=2.31.0`, fixo, e nunca é atualizado pela Fase 8 mesmo quando o LLM gera código usando FastAPI/uvicorn/etc. MCP é JSON-RPC implementado na mão — docstring do próprio scaffold admite "sem SDK mcp, que não está em requirements.txt" (`scaffolds.py:139-145`). CORS inseguro do relatório de auditoria vem de código gerado pelo LLM (prompt), não de template fixo. | **Achado novo (fora do NIH doc):** o `requirements.txt` entregue está sistematicamente dessincronizado do código real gerado — bug de correção, candidato a item novo no plano tático, não decisão deste item estratégico. |
| **aidd-ops** | Sim (infra rodando numa VPS) | Traefik só roteia o próprio dashboard (`templates/infra/traefik/docker-compose.yml:37-41`) — Twenty/Chatwoot/Cal.com usam `ports:` diretos, sem labels. Porta 3000 ainda colide entre os 3 (`twenty/docker-compose.yml:27`, `chatwoot/docker-compose.yml:24`, `calcom/docker-compose.yml:23`). SSH hardening manual via `paramiko` (`ssh_runner.py:29-35,114-118`), sem Ansible. Zero traço de Coolify/CapRover/Dokku no código. Cofre de credenciais 100% inexistente (só o plano em `docs/planos/a-fazer/03-evolucao-aidd-ops-fase-completa/`). | Os 2 bugs críticos do relatório de auditoria original (porta duplicada, Traefik subutilizado) **persistem sem correção** até hoje. |

## Definição de Pronto

1. ~~Levantamento concreto, por ferramenta, do que faria sentido embarcar no produto gerado~~ — feito, ver tabela acima. `aidd-forge` sai do escopo de execução deste item (nada a embarcar); o trabalho real recai sobre master/enterprise, generator e ops.
2. ~~Decisão registrada aqui: opção (a) ou (b) acima, com justificativa.~~ — feito, ver "Decisão registrada (2026-09-07)" acima: opção (a).
3. ~~Se (a): 1 protótipo real num só tool~~ — feito em `aidd-master`/`compose_suite.py` (ver "Protótipo real" acima).
4. ~~Critério de verificação real: projeto gerado pela ferramenta escolhida sobe com a dependência nova de fato instalada e funcional (não só arquivo copiado) — reproduzir, não assumir.~~ — feito: `pip install` real em venv limpo + validação de um `id_token` RS256 genuíno via `OIDCService.validate_id_token`, antes (falha real) e depois (sucesso real). Detalhes em `docs/relatorios/item-7-prototipo-compose-suite-jwt.md`.
5. **`aidd-enterprise` — CONCLUÍDO (2026-09-08):** aprovado pelo usuário e reproduzido. `tools/aidd-enterprise/scripts/compose_suite.py` já gerava `requirements.txt` com `pyjwt>=2.8.0` e `cryptography>=42.0.0` incondicionais (mesma dependência real, mesma rota `OIDCService.validate_id_token` em `templates/core/security.py` e `templates/v2/security.py`) — a correção já estava presente no código, faltava só a reprodução real que confirma que funciona. Reprodução: projeto gerado em pasta temporária isolada (`compose_suite.py <tmp> TesteJWT vendas --db sqlite`); `requirements.txt` resultante contém as duas dependências; `pip install -r requirements.txt` num venv limpo instala ambas; chamada real a `OIDCService.validate_id_token(...)` com um `id_token` RS256 genuíno (assinado on-the-fly com chave RSA gerada via `cryptography`, JWKS correspondente) decodifica as claims corretamente (`sub`, `aud`, `iss`, `email`) — sucesso real, não suposto.
   - **Fora de escopo, mantido assim (sem mudança):** `aidd-generator` (gap já documentado como item novo — `requirements.txt` dessincronizado, problema diferente, não uma variação deste mesmo bug) e `aidd-ops` (não gera manifesto de dependência de linguagem — infra via docker-compose; decisão de bootstrap ali é de outra natureza). Generalizar a correção do PyJWT pra esses dois não faz sentido: não é o mesmo bug.

## Critério de saída

- ~~Decisão de arquitetura ((a) ou (b)) registrada com justificativa.~~ Feito — opção (a).
- ~~Protótipo em 1 ferramenta reproduzido com sucesso real.~~ Feito — `aidd-master`/`compose_suite.py`, PyJWT/cryptography.
- Gates de integridade aprovados — `tools/aidd-master`: 215 passed/4 skipped/0 failed (pytest) + `python scripts/aidd.py audit`, ver `docs/relatorios/item-7-prototipo-compose-suite-jwt.md` para o resultado completo. Gate global `python ecossistema.py audit` tem falhas pré-existentes e não relacionadas em `aidd-generator`/`aidd-ops` (fora do escopo deste item).
- ~~Aguardando aprovação humana explícita antes de generalizar a correção.~~ Aprovado pelo usuário em 2026-09-08 ("pode aprovar o item 5, pode seguir"), nesta sessão.
- ~~Generalização para `aidd-enterprise` reproduzida com sucesso real.~~ Feito — ver item 5 acima.
- **Concluído para o escopo aprovado.** `aidd-generator` e `aidd-ops` permanecem deliberadamente fora — não são o mesmo bug, exigem itens próprios se algum dia priorizados.

## Prompt de Execução (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Você vai implementar o Item 7: Bootstrap de dependências do produto gerado, por ferramenta (forge não é chamado por nenhuma das outras 4).
Siga rigorosamente a Definição de Pronto acima.
Não invente aprovações e mantenha as regras do monorepo.
```

## Prompt de Execução — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 7: Bootstrap of the generated product's own dependencies, per tool (forge is not called by any of the other 4).
Strictly follow the Definition of Done above.
Do not fabricate approvals and maintain monorepo governance rules.
```
