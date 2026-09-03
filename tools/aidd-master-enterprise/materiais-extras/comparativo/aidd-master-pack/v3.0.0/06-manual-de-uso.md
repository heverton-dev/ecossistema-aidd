# Manual de Uso — AIDD Master Pack v3.0.0

> **Versão documentada:** `v3.0.0` (tag `v3.0.0`, commit `0916eceb65572a3c486bb03cd824f57901d0f0b1`).
> Este manual descreve exclusivamente o comportamento real do código nesta tag. Não presume recursos de tags posteriores (v4.x/v5.x).

---

## 1. O Que É o AIDD Master Pack Nesta Versão

É um pacote de scripts Python e templates para provisionar rapidamente pequenos sistemas web modulares (back-end REST + front-end SPA em HTML/JS puro + banco SQLite/Postgres), pensado para ser operado dentro de um "Harness" de IA (Claude Code e ferramentas similares), mas cujos scripts também podem ser rodados diretamente por linha de comando, sem IA nenhuma.

Nesta tag, o pacote entrega:
- Um CLI (`scripts/aidd.py`) com os comandos `init`, `add-module`, `test`, `audit`, `deploy`, `status`.
- Um gerador de projeto novo (`scripts/provision_project.py`).
- Um gerador de módulo CRUD (`scripts/add_module.py`).
- Três gates de qualidade mecânicos (`templates/gates/`).
- Um "núcleo" reaproveitável de banco de dados, EventBus, OpenAPI/Swagger e Webhooks (`templates/v2/`).
- Seis projetos de exemplo já montados em `examples/`, prontos para servir de referência.

---

## 2. Pré-Requisitos

- **Git** instalado (para clonar o repositório e trocar de tag).
- **Python 3.10+** (o código usa apenas biblioteca padrão para os scripts de scaffolding; `psycopg2` só é necessário se você optar por Postgres em vez de SQLite).
- **`pytest`** instalado, se quiser rodar `aidd.py test unit` (não faz parte da biblioteca padrão do Python).
- **`locust`** instalado, se quiser rodar `aidd.py test load`.
- **Docker e Docker Compose**, se quiser usar `aidd.py deploy docker` (ver ressalva na seção 7).

Nenhum desses requisitos é verificado ou instalado automaticamente por esta tag — não há script de bootstrap/setup.

---

## 3. Obtendo o Código Nesta Versão Específica

```bash
git clone https://github.com/heverton-dev/aidd-master-pack.git
cd aidd-master-pack
git checkout v3.0.0
```

Após o `checkout`, a árvore de arquivos ficará "presa" no estado exato da v3.0.0 (HEAD destacado). Se quiser apenas explorar sem afetar seu clone principal, você também pode extrair um snapshot isolado com `git archive v3.0.0 | tar -x -C <pasta-destino>`.

---

## 4. Estrutura de Diretórios Desta Tag

```
aidd-master-pack/               (raiz na tag v3.0.0)
├── README.md                   # Descreve o pacote como "v2.0" (não foi atualizado nesta tag)
├── SKILL.md                    # Definição da skill "aidd-master-pack" para uso em Harness de IA
├── LICENSE                     # MIT
├── scripts/
│   ├── aidd.py                 # CLI principal
│   ├── provision_project.py    # Gerador de projeto novo
│   └── add_module.py           # Gerador de módulo CRUD
├── templates/
│   ├── gates/                  # G_SEGREDOS.py, G_QUALIDADE.py, G_HARNESS_COMPAT.py
│   ├── rules/                  # 4 arquivos .md de diretrizes (camadas, regras de ouro, design, segurança)
│   └── v2/                     # Núcleo reaproveitável: database.py, events.py, openapi.py,
│                                #   webhooks.py, locustfile.py, Dockerfile, docker-compose.yml, deploy.sh
└── examples/                   # 6 projetos de demonstração já gerados
    ├── catalogo-digital-whatsapp/          (arquitetura legada, com PLANO-EXECUCAO-ESTRUTURADO.json)
    ├── plataforma-de-membros/              (arquitetura legada, com PLANO-EXECUCAO-ESTRUTURADO.json)
    ├── plataforma-modular-assinaturas/     (arquitetura legada, com PLANO-EXECUCAO-ESTRUTURADO.json)
    ├── crm-omnichannel-v2/                 (arquitetura modular V2, sem docs.html)
    ├── crm-omnichannel-v3/                 (Full-CRUD + docs.html "GitBook" em /docs/guia)
    ├── erp-financeiro-v2/                  (arquitetura modular V2, sem docs.html)
    ├── erp-financeiro-v3/                  (Full-CRUD + docs.html "GitBook" em /docs/guia)
    ├── helpdesk-sla-v2/                    (arquitetura modular V2, sem docs.html)
    └── helpdesk-sla-v3/                    (Full-CRUD + docs.html "GitBook" em /docs/guia)
```

---

## 5. Formas de Usar o Pacote

### Opção A — Rodar um exemplo já pronto (forma mais rápida de ver algo funcionando)

```bash
cd examples/erp-financeiro-v3/src
python server.py
```

O servidor sobe em `http://localhost:3002` (a porta é fixa no código de cada exemplo — verifique o valor de `PORT` em `src/server.py` de cada projeto antes de rodar mais de um ao mesmo tempo). Rotas disponíveis nesse exemplo:
- `/` — SPA (tela principal)
- `/api/contas`, `/api/fluxo-caixa`, etc. — API REST
- `/docs` — Swagger UI (requer internet, pois carrega `swagger-ui-dist` de um CDN)
- `/docs/guia` — documentação estilo GitBook (somente em `crm-omnichannel-v3`, `erp-financeiro-v3`, `helpdesk-sla-v3`)

### Opção B — Provisionar um projeto novo do zero

```bash
python scripts/aidd.py init "Minha Plataforma de Cupons"
```

Isso executa `provision_project.provision()`, que monta a estrutura de pastas e copia os arquivos-núcleo. **Atenção:** o destino padrão do projeto novo está fixo no código-fonte (`base_dir` em `scripts/provision_project.py` aponta para um caminho absoluto do Windows do autor original). Se você não estiver nessa máquina, edite esse valor no script antes de rodar, ou chame `provision()` diretamente em Python passando seu próprio `base_dir`.

### Opção C — Adicionar um módulo a um projeto existente

Dentro da pasta do projeto (que já deve ter `scripts/add_module.py` copiado por `init`):

```bash
python scripts/add_module.py cupons "Gerenciador de Cupons de Desconto"
```

Isso cria `src/modules/cupons/{models.py, services.py, routes.py}`, um componente visual em `src/static/components/cupons.html` e um teste em `tests/unit/test_cupons.py`. **Depois disso, é necessário editar manualmente `src/server.py`** para: importar o novo módulo, inicializar seu schema (`init_schema`) e registrar suas rotas — o gerador não faz esse último passo sozinho.

### Opção D — Rodar os testes

```bash
python scripts/aidd.py test unit    # roda pytest -v
python scripts/aidd.py test load    # roda locust headless por 5s com 10 usuários simulados
python scripts/aidd.py test all     # roda os dois
```

### Opção E — Auditar qualidade (gates)

```bash
python scripts/aidd.py audit
```

Executa, em ordem, `G_SEGREDOS.py` → `G_QUALIDADE.py` → `G_HARNESS_COMPAT.py`. Qualquer gate que retorne código de saída diferente de zero interrompe o processo com a mensagem `[FAIL] Gate falhou: <arquivo>`. Se todos passarem: `[OK] SUCESSO: Todos os gates foram 100% aprovados (exit 0)!`.

### Opção F — Consultar o status do projeto

```bash
python scripts/aidd.py status
```

Só produz saída útil se existir um arquivo `PLANO-EXECUCAO-ESTRUTURADO.json` na raiz do projeto (ver `plano-de-execucao.md` para o formato). Essa versão não gera esse arquivo automaticamente — ele precisa ser criado manualmente, seguindo o modelo encontrado nos exemplos legados (`examples/plataforma-de-membros/PLANO-EXECUCAO-ESTRUTURADO.json`).

### Opção G — Deploy

```bash
python scripts/aidd.py deploy docker   # docker compose up -d --build
python scripts/aidd.py deploy vps      # apenas instrui a rodar bash deploy.sh no servidor remoto
```

---

## 6. Entregáveis/Resultados Obtidos ao Final do Uso

Ao seguir o fluxo completo (provisionar → adicionar módulos → integrar manualmente ao servidor → testar → auditar → subir), o resultado é:

1. Um servidor HTTP funcional (biblioteca padrão `http.server`, sem framework externo) servindo API REST, SPA e Swagger UI.
2. Um banco SQLite local (ou Postgres, se configurado manualmente) já populado pelo schema dos módulos criados.
3. Testes unitários por módulo, executáveis via `pytest`.
4. Um relatório de aprovação/reprovação dos 3 gates de qualidade no terminal.
5. Opcionalmente, uma página de documentação estilo GitBook em `/docs/guia`, se você a construir manualmente seguindo o padrão visto em `examples/erp-financeiro-v3/src/static/docs.html`.
6. Um contêiner Docker publicável — **desde que você primeiro crie `requirements.txt` e renomeie/ajuste o `Dockerfile` para apontar para `src/server.py` em vez de `src/main.py`**, pois nenhum dos dois arquivos vem pronto nesta tag (ver `analise-tecnica.md`, itens 1 e 2).

---

## 7. Ressalvas Importantes Antes de Usar em Produção

- **Sem `requirements.txt`:** crie um manualmente listando as dependências reais usadas (nenhuma externa é estritamente necessária para SQLite; para Postgres, adicione `psycopg2-binary`; para testes, `pytest` e `locust`).
- **`Dockerfile` aponta para `src/main.py`:** ajuste o `CMD` do `Dockerfile` para `python src/server.py` (ou renomeie seu arquivo de servidor para `main.py`) antes de tentar buildar a imagem.
- **Sem autenticação:** nenhum exemplo desta tag implementa login, JWT ou controle de acesso — todas as rotas REST são públicas por padrão.
- **Swagger UI depende de internet:** a rota `/docs` carrega assets de um CDN externo; em ambiente sem acesso à internet, a página aparecerá em branco.
- **`docs.html` é manual:** se você quiser a documentação estilo GitBook em um projeto novo, terá que copiar e adaptar `src/static/docs.html` de um dos três exemplos que já a possuem, e adicionar a rota `/docs/guia` manualmente no seu `server.py`.
