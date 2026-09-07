# Item 7 — Bootstrap de dependências do produto gerado, por ferramenta (forge não é chamado por nenhuma das outras 4)

> **Escopo:** Entra: decidir e sequenciar como cada ferramenta (`aidd-forge`, `aidd-generator`, `aidd-master`, `aidd-enterprise`, `aidd-ops`) passa a instalar/wire, no que ela **entrega ao usuário final**, as dependências reais que fazem sentido pro produto gerado (ex.: Cookiecutter real pra scaffolding do master/enterprise via Fase 2 já planejada, Alembic, detect-secrets, hadolint/Checkov onde couber). Não entra: reaproveitar o mecanismo de `gates/dependencias_externas.json` + `dependencia-runner` como está — aquele é exclusivamente para dependências do **agente que desenvolve este repo** (code-review-graph, LLMLingua-2, context7, GitHub MCP), nunca embarcadas no produto gerado.
> **Status:** [RASCUNHO — Aguardando Aprovação Humana]
> **Modelo sugerido:** Claude Opus · Antigravity Gemini 3.8 · MiMo mimo-v2.5-pro (decisão de arquitetura entre 4 pipelines distintos)

---

## Contexto já investigado

- Pergunta original do usuário: as 5 ferramentas também deveriam entregar/instalar isso (dependências mapeadas) no que geram, "desde o Forge até o Ops"?
- Investigação real feita em 2026-09-07: **não existe corrente de chamada entre as ferramentas.** `aidd-forge` é 100% standalone — injeta infraestrutura de desenvolvimento-com-IA (subagentes, gates, `AGENTS.md`) em "qualquer projeto", mas nenhuma das outras 4 ferramentas o importa ou invoca. As referências a "aidd-forge" encontradas em `aidd-generator/scripts/core/injector/contrato.py` e nos `materializador.py` de `aidd-master`/`aidd-enterprise` são só uma string num tuple de nomes conhecidos e um comentário de código ("mesmo padrão do aidd-forge") — nunca uma chamada real.
- Cada ferramenta tem seu próprio `materializador.py`/injector duplicado (4 implementações paralelas do mesmo conceito). `pipeline_completo.py` do generator não tem nenhuma fase de bootstrap de dependência do produto.
- Conclusão: forge injeta infraestrutura de **como construir** (governança de IA); o que o usuário pediu é infraestrutura de **o que foi construído** (dependências reais do app gerado). São naturezas diferentes — acoplar os dois no mesmo mecanismo repete a confusão que a distinção dependencia-runner-vs-produto já resolveu para o agente.
- Decisão de arquitetura em aberto: (a) cada ferramenta ganha seu próprio script de bootstrap de dependências do produto, isolado, sem depender do forge; ou (b) as 4 ferramentas passam a chamar o forge como fase 0 real (acoplamento novo, maior risco, toca os 4 pipelines).

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
2. Decisão registrada aqui: opção (a) ou (b) acima, com justificativa.
3. Se (a): 1 protótipo real num só tool (candidato: master ou enterprise, que já têm Fase 2 endereçando scaffolding) antes de replicar nos outros 4.
4. Critério de verificação real: projeto gerado pela ferramenta escolhida sobe com a dependência nova de fato instalada e funcional (não só arquivo copiado) — reproduzir, não assumir.
5. Só depois do protótipo validado, decidir se generaliza pras outras 3 ferramentas ou se cada uma segue caminho próprio.

## Critério de saída

- Decisão de arquitetura ((a) ou (b)) registrada com justificativa.
- Protótipo em 1 ferramenta reproduzido com sucesso real.
- Gates de integridade aprovados.

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
