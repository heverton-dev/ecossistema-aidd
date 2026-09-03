# Manual de Uso — AIDD Master Pack `v1.0.0`

> **Tag documentada:** `v1.0.0`
> Este manual descreve como obter, instalar e usar especificamente esta versão do pacote, com base no conteúdo real encontrado na tag (não em versões posteriores).

---

## 1. O que é

O AIDD Master Pack v1.0.0 é uma "skill agêntica" — um conjunto de scripts Python e instruções em Markdown pensados para guiar um agente de IA (ou um desenvolvedor humano) na criação rápida de pequenos sistemas web modulares: backend em Python puro, banco de dados SQLite local, e uma interface web simples servida como HTML/JS estático. O próprio pacote se descreve como "Fundação Modular Vertical Slice — Esqueleto Inicial com SQLite WAL, Pytest e Gates Mecânicos".

Não é um framework instalável via `pip install`; é um conjunto de arquivos que se copia para dentro de um projeto ou para uma pasta de "skills" de um agente de IA.

---

## 2. Pré-requisitos

- **Python 3** instalado (os scripts usam apenas a biblioteca padrão, exceto `pytest` e, opcionalmente, `psycopg2` para PostgreSQL).
- **`pytest`** disponível no ambiente, para rodar os testes automatizados (`pip install pytest`).
- **`locust`** disponível, apenas se for usar o teste de carga (`pip install locust`).
- **Docker e Docker Compose**, apenas se for usar o deploy via container.
- **Git**, para clonar o repositório.

> Nota: nenhum `requirements.txt` acompanha o pacote nesta tag — as dependências acima precisam ser instaladas manualmente pelo usuário.

---

## 3. Obtendo o código desta versão específica

```bash
git clone https://github.com/heverton-dev/aidd-master-pack.git
cd aidd-master-pack
git checkout v1.0.0
```

Após o checkout, a raiz do repositório deve conter:

```
aidd-master-pack/
├── scripts/
│   ├── aidd.py
│   ├── add_module.py
│   └── provision_project.py
├── templates/
│   ├── gates/          (G_QUALIDADE.py, G_SEGREDOS.py, G_HARNESS_COMPAT.py)
│   ├── rules/           (01_layers.md, 02_golden_rules.md, 03_impeccable.md, 04_security.md)
│   └── v2/               (database.py, events.py, openapi.py, webhooks.py, Dockerfile, docker-compose.yml, deploy.sh, locustfile.py, shared/)
├── examples/            (12 projetos de referência já gerados)
├── LICENSE              (MIT)
├── README.md
└── SKILL.md
```

---

## 4. Instalação/Setup

Esta versão não possui um instalador. Existem duas formas de uso:

### 4.1 Uso direto dentro de um projeto único
Copie manualmente `scripts/` e `templates/` para dentro do projeto onde deseja trabalhar, e rode os comandos a partir da raiz desse projeto.

### 4.2 Uso como "skill" compartilhada entre vários projetos (forma esperada pelos próprios scripts)
`provision_project.py` procura, por padrão, os arquivos-fonte em `~/.agents/skills/aidd-master-pack/` (isto é, `C:\Users\<usuario>\.agents\skills\aidd-master-pack\` no Windows). Para usar dessa forma:

```bash
# Windows (exemplo)
mkdir "%USERPROFILE%\.agents\skills\aidd-master-pack"
xcopy /E /I scripts "%USERPROFILE%\.agents\skills\aidd-master-pack\scripts"
xcopy /E /I templates "%USERPROFILE%\.agents\skills\aidd-master-pack\templates"
```

> **Atenção:** o destino padrão de novos projetos criados por `provision_project.py` também é hard-coded no script (`C:\Users\trcnologia\orca\workspaces\PROJETOS Criados com IA` na versão original) — antes de usar em outra máquina, é necessário abrir `scripts/provision_project.py` e ajustar o parâmetro `base_dir` da função `provision()` para um caminho válido no seu ambiente.

---

## 5. Comandos disponíveis

Todos os comandos são executados via `python scripts/aidd.py <comando>` (rodado de dentro da pasta do projeto de destino, após provisionado):

| Comando | Uso | O que faz |
| :--- | :--- | :--- |
| `init` | `python scripts/aidd.py init "<descrição do projeto>"` | Cria a estrutura de pastas do projeto novo e copia o Shared Kernel. |
| `add-module` | `python scripts/aidd.py add-module <nome> [-d "<descrição>"]` | Gera uma fatia vertical (model/service/routes/UI/teste) para um novo domínio de negócio. |
| `test` | `python scripts/aidd.py test [unit\|load\|e2e\|all]` | Roda os testes automatizados (`unit` = pytest; `load` = Locust headless; `e2e` listado mas sem implementação). |
| `audit` | `python scripts/aidd.py audit` | Roda os 3 gates mecânicos em sequência (segredos, sintaxe, compatibilidade). |
| `deploy` | `python scripts/aidd.py deploy [docker\|vps\|vercel]` | `docker` sobe via `docker compose`; `vps` apenas instrui rodar `deploy.sh` manualmente; `vercel` não tem efeito. |
| `status` | `python scripts/aidd.py status` | Mostra nome/status do projeto (lendo `PLANO-EXECUCAO-ESTRUTURADO.json`, se existir) e lista os módulos ativos. |

---

## 6. Passo a passo de uso típico

1. **Provisionar o projeto:**
   ```bash
   python scripts/aidd.py init "catálogo de produtos com pedido via WhatsApp"
   ```
   Isso cria a pasta do projeto (nomeada a partir de um *slug* das 3 primeiras palavras da descrição) com o Shared Kernel já copiado.

2. **Entrar na pasta gerada** e, para cada domínio de negócio necessário, gerar um módulo:
   ```bash
   python scripts/add_module.py produtos
   python scripts/add_module.py pedidos
   ```

3. **Editar manualmente** os arquivos gerados (`models.py`, `services.py`, `routes.py`) para incluir as regras de negócio reais (campos adicionais, validações, integrações), e conectar cada novo módulo ao `src/server.py` do projeto (esse fio de ligação **não é automático** — precisa ser feito à mão, seguindo o padrão visto nos projetos de `examples/`).

4. **Rodar os testes:**
   ```bash
   python scripts/aidd.py test unit
   ```

5. **Rodar a auditoria de qualidade:**
   ```bash
   python scripts/aidd.py audit
   ```

6. **Subir localmente com Docker** (é necessário criar manualmente um `requirements.txt` na raiz do projeto antes, pois o `Dockerfile` do kernel espera esse arquivo e ele não é gerado automaticamente):
   ```bash
   python scripts/aidd.py deploy docker
   ```

7. **Acessar o resultado** em `http://localhost:3000` (porta padrão usada nos projetos de exemplo).

---

## 7. Entregáveis obtidos ao final

Ao completar o fluxo acima, o resultado é:

- Uma aplicação Python rodando com `http.server` da biblioteca padrão (sem framework web externo), servindo páginas HTML estáticas e rotas JSON.
- Um banco de dados SQLite local, em modo WAL, com uma tabela por módulo criado.
- Um documento OpenAPI básico (`openapi.json`) e uma página de documentação Swagger (dependente de CDN externo para os estilos/scripts).
- Testes unitários (`pytest`) cobrindo as operações básicas de cada módulo gerado.
- Um relatório textual de auditoria impresso no terminal (não em arquivo) confirmando ausência de segredos óbvios e sintaxe válida.
- Opcionalmente, um contêiner Docker rodando a aplicação localmente, ou os arquivos necessários (`Dockerfile`, `docker-compose.yml`, `deploy.sh`) para publicá-la manualmente em uma VPS.

---

## 8. O que este manual não cobre (porque não existe em `v1.0.0`)

Comandos como `plan`, `compose`, `heal`, `bench`, integração com MCP, geração de `SPEC-ARQUITETURA.md`, sincronização automática de regras entre múltiplas IDEs, e deploy automatizado em nuvem (Vercel, Kubernetes) **não existem nesta tag** e não devem ser esperados ao seguir este manual. Para esses recursos, é necessário usar uma tag posterior do repositório (`v2.0.0` em diante).
