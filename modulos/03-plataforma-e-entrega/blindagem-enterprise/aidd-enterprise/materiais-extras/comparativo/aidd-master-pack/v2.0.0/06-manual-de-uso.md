# Manual de Uso — AIDD Master Pack v2.0.0

> **Versão documentada:** tag `v2.0.0` do repositório `heverton-dev/aidd-master-pack`.
> Este manual descreve exclusivamente o comportamento do código presente nessa tag específica (commit `e78ab8c`), obtido via `git archive v2.0.0` e inspecionado isoladamente. Comandos e recursos de versões posteriores (v3+, v4+, v5+) **não** estão incluídos aqui.

---

## 1. O Que É

O **AIDD Master Pack v2.0.0** é um conjunto de scripts Python e templates que ajuda a gerar rapidamente o esqueleto de um projeto de software com **arquitetura modular** — banco de dados dual (SQLite para desenvolvimento, PostgreSQL para produção), geração de especificação OpenAPI 3.0 a partir das rotas registradas, testes de carga com Locust, e arquivos prontos para empacotar o projeto em Docker.

Ele **não** é um framework web completo (não inclui Flask/FastAPI) nem gera, sozinho, um servidor HTTP funcional — ver a seção "Limitações Conhecidas desta Versão" antes de prosseguir.

---

## 2. Obtendo o Código Nesta Versão

Clone o repositório e mude para a tag `v2.0.0`:

```bash
git clone https://github.com/heverton-dev/aidd-master-pack.git
cd aidd-master-pack
git checkout v2.0.0
```

Após o `checkout`, o repositório fica no estado "detached HEAD" apontando exatamente para o conteúdo desta tag — que é diferente do conteúdo atual da branch `main` (que já está em uma versão muito mais recente, v5.x).

Estrutura de arquivos que você deve encontrar após o checkout:

```
aidd-master-pack/
├── LICENSE
├── README.md
├── SKILL.md
├── scripts/
│   ├── add_module.py
│   └── provision_project.py
├── templates/
│   ├── gates/
│   │   ├── G_HARNESS_COMPAT.py
│   │   ├── G_QUALIDADE.py
│   │   └── G_SEGREDOS.py
│   └── v2/
│       ├── database.py
│       ├── events.py
│       ├── openapi.py
│       ├── Dockerfile
│       ├── docker-compose.yml
│       ├── deploy.sh
│       └── locustfile.py
└── examples/
    ├── catalogo-digital-whatsapp/
    ├── plataforma-de-membros/
    └── plataforma-modular-assinaturas/   (único exemplo no padrão v2.0 completo)
```

---

## 3. Pré-requisitos

- **Python 3.10+** (o `README.md` da tag declara compatibilidade 3.10+; os templates usam sintaxe simples compatível também com 3.11).
- `pytest` instalado, se quiser rodar os testes unitários gerados (`pip install pytest`).
- `psycopg2-binary` instalado **somente** se for usar PostgreSQL em vez de SQLite (`pip install psycopg2-binary`) — sem isso, `Database.get_connection()` lança `RuntimeError` ao tentar conectar em um `DATABASE_URL` postgres.
- `locust` instalado, se quiser rodar o teste de carga (`pip install locust`).
- Docker e Docker Compose, se for empacotar o projeto em contêiner — mas veja a limitação sobre `requirements.txt`/`src/main.py` abaixo antes de tentar.

---

## 4. Instalação/Setup como Skill Local (opcional, necessário para `provision_project.py`)

O script `scripts/provision_project.py` desta tag foi escrito para copiar templates a partir de uma pasta "hub" fixa no computador do usuário:

```
~/.agents/skills/aidd-master-pack/templates/v2/
~/.agents/skills/aidd-master-pack/templates/gates/
~/.agents/skills/aidd-master-pack/scripts/add_module.py
```

Para que o provisionamento copie corretamente `database.py`, `events.py`, `openapi.py`, `Dockerfile`, `docker-compose.yml`, `deploy.sh`, `locustfile.py` e os 3 gates, essa pasta hub precisa existir com os arquivos do repositório clonado dentro dela (por exemplo, copiando manualmente a pasta `templates/` e `scripts/` do repositório clonado para dentro de `~/.agents/skills/aidd-master-pack/`). Se a pasta hub não existir, o script roda sem erro fatal, mas **pula silenciosamente** as cópias que dependem dela (`if os.path.exists(...)`).

Além disso, o script tenta chamar `orca repo add --path <projeto>` para registrar o projeto na ferramenta ORCA — se o comando `orca` não estiver instalado, a chamada falha e é ignorada (`except: pass`), sem impedir a continuação.

---

## 5. Passo a Passo de Uso

### 5.1 Criar um projeto modular novo

```bash
python scripts/provision_project.py "Minha Plataforma Modular de Assinaturas"
```

Isso cria uma pasta de projeto (por padrão, dentro de `C:\Users\<usuario>\orca\workspaces\PROJETOS Criados com IA\proj_<slug>` — caminho fixo no código-fonte desta tag; ajuste manualmente o script se seu ambiente for diferente) contendo a estrutura descrita na seção 2 do documento `ciclo-de-vida.md`.

### 5.2 Adicionar módulos de domínio

Dentro da pasta do projeto recém-criado:

```bash
python scripts/add_module.py cupons "Gerenciador de Cupons de Desconto"
python scripts/add_module.py afiliados "Programa de Afiliados"
```

Cada chamada gera, para o módulo indicado: `models.py`, `services.py`, `routes.py`, um componente visual HTML e um teste unitário — repita para cada área de negócio necessária.

### 5.3 Rodar os testes unitários gerados

```bash
pytest
```

### 5.4 Rodar os 3 gates de qualidade mecânica

```bash
python scripts/gates/G_QUALIDADE.py
python scripts/gates/G_SEGREDOS.py
python scripts/gates/G_HARNESS_COMPAT.py
```

### 5.5 Rodar o teste de carga (opcional, requer edição manual)

```bash
locust -f tests/load/locustfile.py
```

O arquivo padrão testa rotas genéricas (`/`, `/api/produtos`, `/docs`) — edite-o para apontar para as rotas reais dos módulos que você criou (`/api/cupons`, `/api/afiliados`, etc.).

### 5.6 Empacotar e subir com Docker

```bash
docker compose up -d
```

**Atenção:** para este comando funcionar de fato, você precisará criar manualmente dois arquivos que esta versão não gera:
1. Um `requirements.txt` na raiz do projeto (o `Dockerfile` faz `COPY requirements.txt .`, mas nenhum script desta tag cria esse arquivo).
2. Um `src/main.py` que importe cada módulo, registre suas rotas via `RouteRegistry`, sirva `/openapi.json` e `/docs`, e efetivamente escute a porta 3000 (o `Dockerfile` roda `CMD ["python", "src/main.py"]`, mas esse arquivo não é gerado automaticamente por nenhum script da tag).

### 5.7 Deploy em VPS

```bash
bash deploy.sh
```

Esse script faz `git pull origin main`, `docker compose down`, `docker compose build --no-cache` e `docker compose up -d` — pressupõe que você já está executando dentro de uma VPS (ex.: Hetzner ou Contabo) com Docker instalado, repositório git configurado e as pendências da seção 5.6 já resolvidas.

---

## 6. Entregáveis/Resultados Obtidos ao Final do Fluxo

Ao seguir os passos 5.1 a 5.4, você obtém:

- Uma estrutura de pastas modular (`src/core`, `src/modules/<cada módulo>`, `src/static/components`).
- Um banco de dados SQLite local (arquivo `.db`, modo WAL) pronto para uso, com uma tabela por módulo.
- Testes unitários passando para cada módulo criado.
- Um relatório de sintaxe limpo e uma varredura de segredos sem alertas (assumindo que os gates passem).
- Documentos `AGENTS.md`/`CLAUDE.md`/`GEMINI.md`/`.cursorrules` com as regras do projeto para uso por assistentes de IA.
- Um `PLANO-EXECUCAO-ESTRUTURADO.json` com o resumo declarativo do projeto (ver `plano-de-execucao.md` para detalhes sobre suas limitações).

Você **não** obtém, apenas com os passos acima, uma aplicação web rodando e acessível — isso exige o trabalho manual adicional descrito na seção 5.6.

---

## 7. Limitações Conhecidas desta Versão (Resumo)

Para uma análise técnica completa, ver `analise-tecnica.md` e `matriz-de-qualidade.md` nesta mesma pasta. Resumidamente:

- Não gera `src/main.py`/servidor HTTP.
- Não gera `requirements.txt`.
- `provision_project.py` tem caminho de destino fixo no código, pensado para o ambiente original do autor.
- Apenas 3 gates mecânicos, um deles (`G_HARNESS_COMPAT`) não verifica nada de fato.
- Nenhum gate executa os testes automaticamente.
- O manifesto de plano de execução não é atualizado conforme o projeto evolui.
- Dos exemplos incluídos na tag, apenas um (`plataforma-modular-assinaturas`) segue de fato a arquitetura v2.0 descrita neste manual.
