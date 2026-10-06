# Plano de Execução — AIDD Master Pack v4.2.0

> **Tag analisada:** `v4.2.0`.
> Este documento descreve o real papel do arquivo `PLANO-EXECUCAO-ESTRUTURADO.json` nesta tag específica — que é bem diferente do papel formal que esse manifesto assume em versões posteriores do framework.

---

## 1. Declaração explícita: nesta tag, o manifesto NÃO é gerado por nenhum script

Foi feita uma busca por toda a árvore `scripts/` e `templates/` da tag `v4.2.0` pelo texto `PLANO-EXECUCAO`. O único resultado encontrado está em `scripts/aidd.py`, dentro da função `cmd_status()`:

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

Ou seja: `python scripts/aidd.py status` **lê** o arquivo `PLANO-EXECUCAO-ESTRUTURADO.json` se ele já existir no diretório do projeto, e imprime nome, versão e status. Nenhum outro script desta tag (`provision_project.py`, `add_module.py`, `compose_suite.py`) **cria** ou **escreve** esse arquivo. Não existe, nesta versão, um comando `aidd.py plan` (esse comando só aparece em versões posteriores do framework).

### Evidência empírica: o arquivo é manual e inconsistente entre projetos

Dos 13 projetos em `examples/`, apenas **5** contêm `PLANO-EXECUCAO-ESTRUTURADO.json`: `catalogo-digital-v3`, `catalogo-digital-whatsapp`, `plataforma-de-membros`, `plataforma-membros-v3` e `plataforma-modular-assinaturas`. Os outros 8 exemplos (incluindo os dois "flagship", `enterprise-suite-v4` e `logistica-hub-v4`) não têm o arquivo.

Além disso, comparando o conteúdo entre exemplos que possuem o arquivo, a estrutura **não é uniforme** — o que é o sinal mais forte de que ele foi escrito manualmente (por um humano ou por uma sessão de IA ad hoc), e não produzido por um gerador determinístico com schema fixo:

**Exemplo 1 — `examples/catalogo-digital-v3/PLANO-EXECUCAO-ESTRUTURADO.json`:**
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
    { "id": "fase-01-analise", "nome": "Analise e Modelagem de Contratos", "status": "PENDENTE",
      "mesa_orca": "mesa-analise", "expected_outputs": ["docs/ARQUITETURA.md"] },
    { "id": "fase-02-implementacao", "nome": "Implementacao do Core Determinístico", "status": "PENDENTE",
      "mesa_orca": "mesa-dev", "expected_outputs": ["src/main.py"] },
    { "id": "fase-03-validacao", "nome": "Auditoria de Gates e Testes Finais", "status": "PENDENTE",
      "mesa_orca": "mesa-qa", "expected_outputs": ["tests/"] }
  ]
}
```
Note que este exemplo **não tem** o campo `projeto.versao` (que `cmd_status()` tenta ler) e usa `mesa_orca` em cada fase.

**Exemplo 2 — `examples/plataforma-modular-assinaturas/PLANO-EXECUCAO-ESTRUTURADO.json`:**
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
  "fases": [
    { "id": "fase-01-core-setup", "nome": "Configuracao do Core, Dual Database e EventBus", "status": "CONCLUIDO",
      "expected_outputs": ["src/core/database.py", "src/core/events.py", "src/core/openapi.py"] },
    { "id": "fase-02-modulos-iniciais", "nome": "Criacao dos Modulos de Dominio", "status": "PENDENTE",
      "expected_outputs": ["src/modules/"] },
    { "id": "fase-03-infra-e-deploy", "nome": "Empacotamento Docker, Deploy Script e Testes de Carga", "status": "CONCLUIDO",
      "expected_outputs": ["Dockerfile", "docker-compose.yml", "deploy.sh", "tests/load/locustfile.py"] }
  ]
}
```
Este segundo exemplo já tem `projeto.versao`, um array `modulos_instalados` inexistente no primeiro exemplo, e nenhuma fase usa `mesa_orca` — em vez disso, os `status` de fase já aparecem como `"CONCLUIDO"`.

---

## 2. O que os campos que aparecem (na prática) significam

Combinando os dois exemplos acima, os campos observáveis são:

| Campo | Presente em todos os exemplos? | Significado observado |
| :--- | :---: | :--- |
| `projeto.nome` | Sim | Nome/slug do projeto. |
| `projeto.descricao` | Sim | Descrição textual livre do que o projeto faz. |
| `projeto.versao` | Não (ausente em `catalogo-digital-v3`) | Versão semântica livre, sem relação obrigatória com a versão do AIDD Master Pack. |
| `projeto.arquitetura` | Sim (texto livre, valores diferentes por exemplo: `"AIDD 4 Camadas"`, `"AIDD Modular Data-Driven"`) | Rótulo descritivo do estilo arquitetural escolhido. |
| `projeto.status` | Sim | String livre (`"INICIALIZADO"` nos exemplos vistos) — é o único campo que `cmd_status()` de fato imprime. |
| `projeto.zero_api_key_mode` / `dual_database` / `openapi_swagger` / `docker_ready` | Não (aparecem só em alguns exemplos) | Flags booleanas ad hoc descrevendo capacidades específicas daquele projeto — não fazem parte de um schema fixo. |
| `modulos_instalados` | Não (só em `plataforma-modular-assinaturas`) | Lista de slugs de módulos já criados. |
| `fases[].id` / `.nome` / `.status` | Sim | Identificador, nome e status textual (`PENDENTE`/`CONCLUIDO`) de uma etapa do plano. |
| `fases[].mesa_orca` | Não (só em `catalogo-digital-v3`) | Referência a uma "mesa" de trabalho do ORCA (ambiente de agentes) responsável pela fase — conceito específico de orquestração multiagente, não usado em todos os exemplos. |
| `fases[].expected_outputs` | Sim | Lista de caminhos de arquivo esperados como resultado da fase. |

---

## 3. Como o planejamento de execução realmente funciona nesta versão

Como não existe geração automática do manifesto nesta tag, o "planejamento de execução" da v4.2.0 acontece de outra forma, através dos próprios comandos determinísticos:

1. **Planejamento implícito via composição de módulos:** ao rodar `python scripts/compose_suite.py <destino> <suite> crm erp helpdesk logistica`, a lista de módulos passada na linha de comando **é** o plano — não existe uma etapa intermediária de aprovação de um JSON antes da geração de código.
2. **Planejamento incremental via `add-module`:** cada chamada a `python scripts/add_module.py <nome>` adiciona uma fatia vertical de cada vez; o "plano" emerge da sequência de comandos executados pelo operador, não de um documento único revisado previamente.
3. **Acompanhamento pós-hoc via `status`:** depois que módulos já existem em `src/modules/`, `python scripts/aidd.py status` lista os diretórios encontrados — funcionando como um "retrato do que já foi construído", não como um roteiro do que ainda falta construir.
4. **`PLANO-EXECUCAO-ESTRUTURADO.json`, quando presente, é documentação de apoio** — provavelmente escrita manualmente (ou por uma sessão de IA fora do fluxo dos scripts) para dar contexto de fases/mesas de trabalho em um ambiente de orquestração multiagente (ORCA), mas seu conteúdo não é validado, versionado ou atualizado automaticamente por nenhuma rotina desta tag.

**Conclusão:** nesta tag, o manifesto de plano de execução existe como *convenção informal de nomenclatura de arquivo* (mesmo nome, `PLANO-EXECUCAO-ESTRUTURADO.json`, reconhecido por `cmd_status()`), mas ainda **não é** um contrato formal gerado e mantido automaticamente pelo framework — isso viria a se consolidar em versões posteriores, com um comando dedicado de planejamento e um schema estável (ver o arquivo homônimo no HEAD atual do repositório, que já inclui `gates_qualidade`, lista estruturada de `modulos` com rotas e eventos, e é gerado por um comando explícito).
