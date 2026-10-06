# Manual de Uso — AIDD Master Pack v4.2.0

> **Versão documentada:** tag `v4.2.0` do repositório `heverton-dev/aidd-master-pack`.
> Este manual descreve exclusivamente os comandos e comportamentos existentes nesta tag, verificados no código-fonte real (não na versão atual do HEAD, que é v5.1.0 e tem comandos e gates adicionais).

---

## 1. O que é o AIDD Master Pack v4.2.0

É um pacote de automação em Python (sem dependências externas obrigatórias) que gera a estrutura inicial de sistemas web modulares — bancos de dados, regras de negócio (CRUD), rotas de API documentadas em OpenAPI, comunicação entre módulos via eventos, webhooks assinados por HMAC e, opcionalmente, um servidor de integração com IA (MCP). Ele também traz "gates" (inspeções automáticas) que verificam sintaxe, vazamento de segredos e — quando acionado manualmente — segurança OWASP.

---

## 2. Pré-requisitos

- **Python 3** instalado e acessível via `python` no terminal.
- **Git** instalado (para clonar o repositório e para o `git init` automático que os scripts executam em novos projetos).
- Opcional, dependendo do que for usar:
  - `pytest` (para `aidd.py test unit`).
  - `locust` (para `aidd.py test load`).
  - `Docker` e `docker compose` (para `aidd.py deploy docker`).
  - `psycopg2-binary` (somente se optar por PostgreSQL em vez do SQLite padrão).

---

## 3. Obtendo o código-fonte desta versão exata

```bash
git clone https://github.com/heverton-dev/aidd-master-pack.git
cd aidd-master-pack
git checkout v4.2.0
```

Depois do `checkout`, o repositório fica no estado exato da tag `v4.2.0` (`HEAD` destacado). A partir daqui, todos os comandos deste manual assumem que o terminal está dentro dessa pasta, salvo indicação contrária.

---

## 4. Duas formas de usar o pacote

O código desta tag tem **dois mecanismos de provisionamento diferentes**, com pré-requisitos distintos. É importante escolher o correto para evitar erro de "arquivo não encontrado".

### 4.1. Modo recomendado a partir do clone: `compose_suite.py`

Este script localiza os templates de forma relativa a si mesmo, então funciona diretamente de dentro da pasta clonada, sem instalação adicional:

```bash
python scripts/compose_suite.py <pasta_destino> <nome_da_suite> [modulo1] [modulo2] ...
```

Exemplo prático:

```bash
python scripts/compose_suite.py ../minha-suite "Suite Comercial" crm erp helpdesk
```

Isso cria a pasta `../minha-suite` com a estrutura `src/core`, `src/shared/ui`, `src/static`, `src/modules` e `tests`, e copia para dentro dela os arquivos do "shared kernel" (`database.py`, `events.py`, `webhooks.py`, `security.py`, `openapi.py`) e do motor de feedback visual (`shared/ui`). Os nomes de módulo passados na linha de comando (`crm`, `erp`, `helpdesk`) são apenas rótulos nesta etapa — a criação efetiva de cada módulo com CRUD é feita depois, com `add_module.py` (seção 5).

### 4.2. Modo `aidd.py init` — requer instalação prévia como "skill"

```bash
python scripts/aidd.py init "descrição do projeto"
```

Este comando chama `provision_project.py`, que busca os templates em um caminho fixo do usuário: `~/.agents/skills/aidd-master-pack/templates/...`. **Se o pacote não estiver copiado para esse caminho**, a cópia de arquivos do "shared kernel" e dos gates simplesmente não ocorre (o script verifica `os.path.exists` antes de copiar e segue em frente silenciosamente se não encontrar). Além disso, o destino do novo projeto por padrão é uma pasta fixa do Windows (`C:\Users\trcnologia\orca\workspaces\PROJETOS Criados com IA`), que só faz sentido na máquina original do autor do pacote — em qualquer outra máquina, é necessário editar `scripts/provision_project.py` (parâmetro `base_dir`) antes de usar este modo.

**Recomendação prática:** para a maioria dos usuários que apenas clonaram o repositório, use o modo 4.1 (`compose_suite.py`). O modo 4.2 só é vantajoso se o pacote já estiver instalado como skill compartilhada de um agente de IA.

---

## 5. Adicionando módulos de negócio (`add_module.py`)

De dentro da pasta do projeto já criado (seja pelo modo 4.1 ou 4.2), rode:

```bash
cd ../minha-suite
python scripts/add_module.py <nome_do_modulo>
```

Exemplo:

```bash
python scripts/add_module.py faturamento
```

Isso gera, dentro de `src/modules/faturamento/`:
- `models.py` — cria a tabela `mod_faturamento` no SQLite (colunas: `id`, `titulo`, `dados_json`, `ativo`, `criado_em`).
- `services.py` — classe `FaturamentoService` com os métodos `listar()`, `criar()` e `deletar()`. **Atenção:** não há método de atualização (`update`) gerado automaticamente nesta versão.
- `routes.py` — expõe `GET /api/faturamento`, `POST /api/faturamento` e `POST /api/faturamento/deletar`.
- Um componente HTML de cartão em `src/static/components/faturamento.html`.
- Um teste unitário em `tests/unit/test_faturamento.py`, cobrindo criar → listar → deletar.

Repita o comando para cada módulo de negócio que o sistema precisar.

---

## 6. Rodando o sistema localmente

Os projetos de exemplo desta tag sobem via:

```bash
python src/server.py
```

Nos exemplos completos (como `logistica-hub-v4`), o servidor abre na porta `3000` e expõe:
- A aplicação web em `http://localhost:3000`
- Documentação interativa da API (Swagger Studio) em `http://localhost:3000/docs`
- Um guia oficial de uso em `http://localhost:3000/docs/guia`
- Nos dois exemplos que já incluem o servidor MCP configurado manualmente (`enterprise-suite-v4` e `logistica-hub-v4`), um portal de integração com IA em `http://localhost:3000/mcp`

Em projetos gerados apenas pelo scaffolding básico (`compose_suite.py` + `add_module.py`, sem os exemplos prontos), é necessário escrever o próprio `src/server.py` amarrando o `RouteRegistry`, o `Database` e as rotas de cada módulo — o esqueleto entrega as peças, mas não um `server.py` genérico pronto para uso automático fora dos exemplos.

---

## 7. Testando

```bash
python scripts/aidd.py test unit    # roda pytest -v em tests/unit/
python scripts/aidd.py test load    # roda locust headless: 10 usuários, 2/s, por 5 segundos
python scripts/aidd.py test all     # roda unit + load em sequência
```

O tipo `e2e` é aceito pelo comando, mas não executa nenhuma ação nesta versão (não há implementação para ele no código).

---

## 8. Auditando qualidade e segurança

```bash
python scripts/aidd.py audit
```

Este comando roda, em sequência, três inspeções automáticas e para no primeiro erro encontrado:
1. `G_SEGREDOS.py` — procura chaves/segredos hardcoded (por regex e por entropia de Shannon).
2. `G_QUALIDADE.py` — compila todos os arquivos `.py` e falha se houver erro de sintaxe.
3. `G_HARNESS_COMPAT.py` — checagem de compatibilidade (sempre aprova nesta versão).

Para a auditoria de segurança mais completa (headers OWASP, JWT, SQL Injection, Nginx, Docker, WAL, OpenAPI), é preciso rodar manualmente, pois ela **não** faz parte do comando `audit` nesta tag:

```bash
python scripts/gates/G_SEGURANCA.py
```

Se o gate de segurança não existir dentro da pasta `scripts/gates/` do seu projeto (ele só é copiado automaticamente para 2 dos exemplos oficiais), copie manualmente o arquivo `scripts/gates/G_SEGURANCA.py` do pacote-mestre para dentro de `<seu_projeto>/scripts/gates/` antes de executá-lo.

---

## 9. Publicando (deploy)

```bash
python scripts/aidd.py deploy docker   # roda: docker compose up -d --build
python scripts/aidd.py deploy vps      # imprime instrução para rodar "bash deploy.sh" no servidor
```

O alvo `vercel` é aceito como opção de linha de comando, mas não possui nenhuma lógica de integração real nesta tag — apenas imprime uma mensagem genérica de conclusão.

---

## 10. Consultando o status do projeto

```bash
python scripts/aidd.py status
```

Mostra o nome, a versão e o status registrados em `PLANO-EXECUCAO-ESTRUTURADO.json` (se esse arquivo tiver sido criado manualmente na raiz do projeto — nesta versão ele não é gerado automaticamente por nenhum comando) e lista os módulos encontrados em `src/modules/`.

---

## 11. O que você obtém ao final

Seguindo os passos acima, o resultado é:

- Um projeto Python autocontido, sem necessidade de Node.js/build front-end.
- Banco de dados SQLite local (modo WAL) com uma tabela por módulo criado.
- API REST documentada dinamicamente em OpenAPI 3.1, navegável via Swagger Studio.
- Comunicação entre módulos via eventos internos (`EventBus`) e, quando configurado, notificações externas via Webhooks assinados com HMAC-SHA256.
- Um relatório de auditoria impresso no terminal (não um arquivo) toda vez que `aidd.py audit` ou `G_SEGURANCA.py` são executados, indicando aprovação ou pontos de falha.
- Arquivos prontos de infraestrutura (`Dockerfile`, `docker-compose.yml`, `deploy.sh`) para publicar o sistema.

---

## 12. Antes de considerar isso pronto para produção

Consulte `analise-tecnica.md` e `matriz-de-qualidade.md`, nesta mesma pasta, para as limitações reais desta tag — em especial: CRUD gerado sem operação de atualização, gate de segurança não integrado ao fluxo automático de auditoria, e servidor MCP que precisa ser escrito manualmente por projeto.
