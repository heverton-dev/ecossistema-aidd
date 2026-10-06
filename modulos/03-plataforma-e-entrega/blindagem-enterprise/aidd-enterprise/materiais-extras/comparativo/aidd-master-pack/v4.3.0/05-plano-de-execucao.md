# Manifesto de Plano de Execução — AIDD Master Pack `v4.3.0`

> **Tag analisada:** `v4.3.0`
> **Conclusão principal, verificada por busca em todo o snapshot da tag (`grep -r "PLANO-EXECUCAO-ESTRUTURADO"`):** esta versão **não possui nenhum script que gere** o arquivo `PLANO-EXECUCAO-ESTRUTURADO.json`. Ele é apenas **lido opcionalmente** por um comando, e aparece de forma **não padronizada** em alguns dos projetos de exemplo — provavelmente criado manualmente ou por um processo de orquestração externo ao pacote (referências a "mesa-orca" do ambiente ORCA), não por este código-fonte.

---

## 1. Onde o arquivo é mencionado no código desta tag

Apenas em `scripts/aidd.py`, dentro de `cmd_status()`:

```python
def cmd_status(args):
    print("[AIDD STATUS] Inspecionando saude do projeto modular...")
    import json
    if os.path.exists("PLANO-EXECUCAO-ESTRUTURADO.json"):
        with open("PLANO-EXECUCAO-ESTRUTURADO.json", "r", encoding="utf-8") as f:
            plano = json.load(f)
        print(f"Projeto: {plano.get('projeto', {}).get('nome')} (v{plano.get('projeto', {}).get('versao')})")
        print(f"Status: {plano.get('projeto', {}).get('status')}")
        ...
```

Ou seja: o comando `python scripts/aidd.py status` **tenta ler** esse arquivo *se ele existir* no diretório corrente, mas nenhuma rotina de `compose_suite.py`, `add_module.py` ou `provision_project.py` o escreve. Não há `open(..., "w")` para esse nome de arquivo em lugar nenhum do pacote.

## 2. O que existe nos projetos de exemplo (evidência empírica)

Dos 9 projetos em `examples/`, apenas **5** contêm um `PLANO-EXECUCAO-ESTRUTURADO.json` na raiz — e o esquema de campos **não é consistente entre eles**, o que reforça que não há um gerador único e determinístico por trás deles:

**`examples/catalogo-digital-v3/PLANO-EXECUCAO-ESTRUTURADO.json`** (o mais simples, com 3 fases fixas de um pipeline de orquestração externo):
```json
{
  "projeto": {
    "nome": "catalogo-digital-e",
    "descricao": "Catalogo Digital e Loja com Checkout WhatsApp e Painel Admin",
    "arquitetura": "AIDD 4 Camadas",
    "zero_api_key_mode": true,
    "status": "INICIALIZADO"
  },
  "fases": [
    { "id": "fase-01-analise", "nome": "Analise e Modelagem de Contratos", "status": "PENDENTE", "mesa_orca": "mesa-analise", "expected_outputs": ["docs/ARQUITETURA.md"] },
    { "id": "fase-02-implementacao", "nome": "Implementacao do Core Determinístico", "status": "PENDENTE", "mesa_orca": "mesa-dev", "expected_outputs": ["src/main.py"] },
    { "id": "fase-03-validacao", "nome": "Auditoria de Gates e Testes Finais", "status": "PENDENTE", "mesa_orca": "mesa-qa", "expected_outputs": ["tests/"] }
  ]
}
```
Note: não há campo `versao` — se `aidd.py status` fosse rodado neste projeto, imprimiria literalmente `"(vNone)"`.

**`examples/plataforma-modular-assinaturas/PLANO-EXECUCAO-ESTRUTURADO.json`** (esquema diferente, com campos extras que não aparecem no exemplo anterior):
```json
{
  "projeto": {
    "nome": "plataforma-de-assinaturas",
    "descricao": "Plataforma de Assinaturas e Cursos Modular",
    "versao": "2.0.0",
    "arquitetura": "AIDD Modular Data-Driven",
    "dual_database": true,
    "openapi_swagger": true,
    "docker_ready": true,
    "status": "INICIALIZADO"
  },
  "modulos_instalados": ["core"],
  "fases": [ ... ]
}
```

Os outros 3 exemplos (`catalogo-digital-whatsapp`, `plataforma-de-membros`, `plataforma-membros-v3`) seguem variações próprias do mesmo padrão geral (`projeto` + `fases[]`), mas com campos e granularidade diferentes. Os 4 exemplos restantes (`enterprise-suite-v4`, `logistica-hub-v4`, `crm-omnichannel-v2/v3`, `erp-financeiro-v2/v3`, `helpdesk-sla-v2/v3`) **não possuem esse arquivo**, apesar de serem os exemplos mais completos e funcionais do pacote (com `src/core/mcp_server.py` e servidores plenamente operacionais).

## 3. Por que o arquivo existe mesmo sem gerador — a pista nas regras

`templates/rules/02_golden_rules.md` (Regra 3 das "3 Regras de Ouro Anti-Estouro de Tokens") diz:

> "Reinicie sessões usando o Plano JSON (retoma estado com ~500 tokens)."

Isso indica que, nesta versão, o `PLANO-EXECUCAO-ESTRUTURADO.json` é um **artefato esperado pela metodologia de trabalho** (para o agente de IA reconstruir contexto de sessão rapidamente), mas sua **criação é responsabilidade do agente/operador humano no momento da orquestração** (via ambiente ORCA, mencionado em `AGENTS.md` dos exemplos: *"Mesas de Trabalho (ORCA Worktrees): Despache tarefas pesadas via `orca worktree create`"*) — não uma responsabilidade do código Python deste pacote. Os campos `mesa_orca: "mesa-analise"`, `"mesa-dev"`, `"mesa-qa"` referenciam esse processo de orquestração externo.

## 4. Como o planejamento de execução funciona de fato nesta versão

Sem um gerador determinístico do manifesto, o planejamento na v4.3.0 acontece por meio de:
1. **Comandos sequenciais da CLI** (`aidd.py init` → `add-module` → `audit` → `test` → `deploy`), cada um imprimindo seu próprio progresso no terminal — não há um arquivo único de estado de pipeline.
2. **Regras textuais em Markdown** (`templates/rules/*.md` e o `AGENTS.md`/`CLAUDE.md`/`GEMINI.md`/`.cursorrules` copiados para cada projeto de exemplo) que orientam o agente de IA sobre a ordem de trabalho (ciclo `impl → test → validate → verify`, mencionado em `AGENTS.md`), mas sem checagem automática de conformidade.
3. **`aidd.py status`** como único ponto de leitura de um plano, funcionando apenas quando alguém (tipicamente o agente de orquestração ORCA) já colocou manualmente um `PLANO-EXECUCAO-ESTRUTURADO.json` no diretório.

## 5. Contraste rápido com a série v5 (apenas para referência, sem aprofundar)
Nas tags mais recentes da linha v5, o arquivo `PLANO-EXECUCAO-ESTRUTURADO.json` passa a ter um **esquema fixo e documentado**, com blocos `projeto` (incluindo `versao`, `slug`, `framework`, `criado_em`), `arquitetura` (padrão, comunicação, documentação, webhooks, mcp, persistência, design system), `modulos[]` (com `rotas`, `eventos`, `testes` por módulo) e `gates_qualidade[]` (listando os 6-7 gates aplicáveis) — e passa a ser gerado automaticamente como parte do fluxo `aidd.py plan`/`apply`. Essa padronização **não existe** na v4.3.0.
