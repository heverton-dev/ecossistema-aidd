# Manifesto de Plano de Execução — AIDD Master Pack v2.0.0

> **Tag analisada:** `v2.0.0`
> **Confirmação:** sim, esta tag já gera um arquivo `PLANO-EXECUCAO-ESTRUTURADO.json` na raiz de cada projeto provisionado. A geração acontece dentro de `scripts/provision_project.py`, na função `provision()`, escrito com `json.dump(plano_data, f, indent=2, ensure_ascii=False)`.
> Evidência: os 3 exemplos da tag (`examples/catalogo-digital-whatsapp`, `examples/plataforma-de-membros`, `examples/plataforma-modular-assinaturas`) cada um contém seu próprio `PLANO-EXECUCAO-ESTRUTURADO.json`, mas em **dois formatos diferentes** (ver seção 3).

---

## 1. Estrutura Real do Manifesto Gerado por `provision_project.py` (formato v2.0)

Este é o formato que a v2.0.0 efetivamente produz quando um projeto passa pelo fluxo novo (`provision_project.py`), confirmado pelo exemplo `examples/plataforma-modular-assinaturas/PLANO-EXECUCAO-ESTRUTURADO.json`:

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
    {
      "id": "fase-01-core-setup",
      "nome": "Configuracao do Core, Dual Database e EventBus",
      "status": "CONCLUIDO",
      "expected_outputs": ["src/core/database.py", "src/core/events.py", "src/core/openapi.py"]
    },
    {
      "id": "fase-02-modulos-iniciais",
      "nome": "Criacao dos Modulos de Dominio",
      "status": "PENDENTE",
      "expected_outputs": ["src/modules/"]
    },
    {
      "id": "fase-03-infra-e-deploy",
      "nome": "Empacotamento Docker, Deploy Script e Testes de Carga",
      "status": "CONCLUIDO",
      "expected_outputs": ["Dockerfile", "docker-compose.yml", "deploy.sh", "tests/load/locustfile.py"]
    }
  ]
}
```

### Campos do bloco `projeto`
| Campo | Tipo | Significado real |
| :--- | :--- | :--- |
| `nome` | string | Slug derivado das 3 primeiras palavras da descrição passada na linha de comando. |
| `descricao` | string | A descrição completa recebida como argumento de `provision_project.py`. |
| `versao` | string | Fixo em `"2.0.0"` — não é lida de nenhum lugar, é uma constante no script. |
| `arquitetura` | string | Fixo em `"AIDD Modular Data-Driven"`. |
| `dual_database` | bool | Sempre `true` — apenas informativo, não verifica se o `DATABASE_URL` de fato aponta para Postgres. |
| `openapi_swagger` | bool | Sempre `true` — apenas informativo, mesmo que nenhum servidor sirva `/docs` de fato (ver `analise-tecnica.md`). |
| `docker_ready` | bool | Sempre `true` — apenas confirma que os arquivos Docker foram copiados, não que a imagem builda com sucesso. |
| `status` | string | Sempre `"INICIALIZADO"` no momento da criação. Não há nenhum outro ponto do código desta tag que atualize esse campo depois. |

### Campos do bloco `fases`
Cada fase tem `id`, `nome`, `status` e `expected_outputs` (lista de caminhos de arquivo esperados).

**Achado importante:** os valores de `status` (`"CONCLUIDO"` para fase-01 e fase-03, `"PENDENTE"` para fase-02) são **strings fixas escritas diretamente no código-fonte** de `provision_project.py` — não resultam de nenhuma checagem real de arquivos no disco nem de execução de gates. Ou seja, o manifesto já "declara sucesso" nas fases 1 e 3 no instante da criação do projeto, antes mesmo de qualquer teste ou gate ter rodado. Isso deve ser lido como um **plano/checklist declarativo**, não como um relatório de auditoria factual.

`modulos_instalados` também é hardcoded como `["core"]` — mesmo que o usuário já tenha rodado `add_module.py` para adicionar módulos reais, este array não é atualizado automaticamente por `add_module.py` (o script de criação de módulos não toca no JSON).

---

## 2. Como o Planejamento de Execução Funciona na Prática (v2.0.0)

1. O manifesto é **gerado uma única vez**, no momento do provisionamento inicial (`provision_project.py`), e reflete apenas o "esqueleto core" (`src/core/*`, Docker, Locust).
2. Não existe nenhum comando ou gate nesta tag que **releia e atualize** o `PLANO-EXECUCAO-ESTRUTURADO.json` depois da criação — nem `add_module.py`, nem os 3 gates mecânicos, tocam nesse arquivo.
3. Consequentemente, o campo `status: "INICIALIZADO"` e a fase `fase-02-modulos-iniciais: "PENDENTE"` tendem a ficar **congelados/desatualizados** assim que o usuário começa a adicionar módulos de domínio com `add_module.py` — o manifesto não acompanha o progresso real do projeto.
4. O propósito prático descrito no `AGENTS.md` gerado (ver Regra de Ouro nº 3) é servir como **ponto de retomada de contexto para um agente de IA**: ao reabrir uma sessão, o agente é instruído a ler este JSON para "lembrar" o estado do projeto sem reprocessar todo o histórico de chat — mas, dado o ponto 3 acima, essa retomada de contexto é baseada em um snapshot estático do momento da criação, não em estado corrente.

---

## 3. Divergência: Nem Todo Exemplo da Tag Usa Este Formato

Os outros dois exemplos incluídos na mesma tag (`catalogo-digital-whatsapp` e `plataforma-de-membros`) têm um `PLANO-EXECUCAO-ESTRUTURADO.json` em **formato antigo, herdado da v1.0** (arquitetura "AIDD 4 Camadas", campo `mesa_orca` por fase, sem os campos `versao`/`dual_database`/`openapi_swagger`/`docker_ready`):

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
    {
      "id": "fase-01-analise",
      "nome": "Analise e Modelagem de Contratos",
      "status": "PENDENTE",
      "mesa_orca": "mesa-analise",
      "expected_outputs": ["docs/ARQUITETURA.md"]
    }
  ]
}
```

Isso confirma que esses dois exemplos **não foram gerados pelo `provision_project.py` desta tag** (ou foram criados antes da v2.0.0 e simplesmente carregados para dentro do repositório junto com a tag), e não devem ser usados como referência do formato "oficial" v2.0.0 do manifesto — o formato oficial e atual é o descrito na Seção 1.
