# Manual de Uso — AIDD Master Pack, versão v4.1.0

> **Tag documentada:** `v4.1.0` (commit `1daf757031e891b3874b6acd1aa2096d10bb61fa`, 31/08/2026)
> Este manual descreve exclusivamente o que existe no snapshot desta tag. Comandos, gates ou arquivos que só existem em tags posteriores (v4.2.0+) **não** estão descritos aqui.

---

## 1. O Que É Esta Versão do Projeto

O **AIDD Master Pack v4.1.0** é um framework de automação para gerar sistemas web modulares (monólitos com "fatias verticais" independentes por domínio de negócio — ex.: CRM, ERP, Helpdesk). Ele é distribuído como uma pasta de scripts Python, templates de código e regras em Markdown, pensada para ser usada tanto por desenvolvedores quanto por assistentes de IA (Claude, Cursor, etc.) que automatizam a criação de projetos.

Nesta tag específica, o diferencial introduzido em relação à versão anterior (`v4.0.1`) foi um **pacote de infraestrutura de produção**: Dockerfile, docker-compose com Nginx (SSL/HTTPS, HTTP/2, limitação de requisições) e uma camada de autenticação JWT (HS256).

---

## 2. Pré-requisitos

- **Python 3** instalado (o `Dockerfile` desta tag usa `python:3.12-slim`; os exemplos mais antigos usam `python:3.11-slim` — qualquer Python 3.11+ funciona para rodar os scripts localmente).
- **Git** instalado.
- **Docker e Docker Compose** (opcional, apenas se for usar o fluxo de deploy em contêiner).
- **OpenSSL** disponível no PATH (opcional, usado pelo gerador de certificado SSL; se ausente, um certificado de teste "dummy" é criado como alternativa — ver Seção 6).
- **pytest** e, opcionalmente, **locust** instalados via `pip`, caso deseje rodar os testes automatizados (`python scripts/aidd.py test`).

---

## 3. Obtendo o Código Nesta Tag Específica

```bash
# 1. Clonar o repositório
git clone https://github.com/heverton-dev/aidd-master-pack.git

# 2. Entrar na pasta do repositório
cd aidd-master-pack

# 3. Fazer checkout exatamente na tag v4.1.0
git checkout v4.1.0
```

Após o `checkout`, o repositório fica em modo "detached HEAD" apontando para o snapshot exato da tag `v4.1.0` — ou seja, exatamente o conteúdo documentado neste manual, e não o HEAD atual do projeto (que já está em versões mais recentes, como v5.1.0).

Para conferir que o checkout deu certo:

```bash
git log -1 --oneline
# Deve mostrar: 1daf757 feat(v4): Producao em Alta Escala: ...
```

---

## 4. Estrutura do Pacote Nesta Tag

```
aidd-master-pack/                 (na tag v4.1.0)
├── LICENSE
├── README.md
├── SKILL.md                       # Descrição da skill para agentes de IA
├── scripts/
│   ├── aidd.py                    # CLI principal (init, add-module, test, audit, deploy, status)
│   ├── add_module.py              # Gerador de módulos (fatias verticais) com CRD
│   ├── compose_suite.py           # Copiador do Shared Kernel para suítes cross-project
│   └── provision_project.py       # Provisionamento inicial de um novo projeto
├── templates/
│   ├── gates/                     # G_QUALIDADE.py, G_SEGREDOS.py, G_HARNESS_COMPAT.py
│   ├── rules/                     # 01_layers, 02_golden_rules, 03_impeccable,
│   │                               # 04_cross_project, 04_security, 05_production_vps (.md)
│   └── v2/                        # Shared Kernel: database.py, events.py, openapi.py,
│                                   # security.py, webhooks.py, Dockerfile, docker-compose.yml,
│                                   # nginx/ (config + gerador de SSL), shared/ (UI de feedback)
└── examples/                      # 13 projetos de referência já construídos
    ├── enterprise-suite-v4/       # (com o novo pacote Docker+Nginx+SSL desta tag)
    ├── logistica-hub-v4/          # (com o novo pacote Docker+Nginx+SSL desta tag)
    ├── crm-omnichannel-v2/, crm-omnichannel-v3/
    ├── erp-financeiro-v2/, erp-financeiro-v3/
    ├── helpdesk-sla-v2/, helpdesk-sla-v3/
    ├── catalogo-digital-v3/, catalogo-digital-whatsapp/
    └── plataforma-de-membros/, plataforma-membros-v3/, plataforma-modular-assinaturas/
```

**Nota de instalação importante:** os scripts `provision_project.py` e `compose_suite.py` foram escritos para funcionar melhor quando o pacote está instalado globalmente como uma "skill" de agente de IA, no caminho `~/.agents/skills/aidd-master-pack/`. Um clone isolado, sem esse passo de instalação global, ainda permite explorar os exemplos e rodar os gates/testes dentro de cada exemplo, mas o comando `aidd.py init` pode não copiar corretamente o Shared Kernel para um projeto novo se esse caminho global não existir no seu computador.

---

## 5. Explorando os Projetos de Exemplo Já Prontos

A forma mais rápida de ver a versão v4.1.0 funcionando é rodar um dos 13 exemplos inclusos:

```bash
cd examples/logistica-hub-v4
python src/server.py
```

Depois, no navegador:
- **Aplicação Web:** `http://localhost:3000`
- **Swagger Studio (documentação interativa das rotas):** `http://localhost:3000/docs`
- **Portal MCP (para conexão com agentes de IA como Claude Desktop/Cursor):** `http://localhost:3000/mcp`

Os exemplos `enterprise-suite-v4` e `logistica-hub-v4` são os únicos, nesta tag, que já incluem o pacote completo de produção (Docker + Nginx + SSL + JWT) descrito na Seção 6.

---

## 6. Colocando um Projeto em Produção (Docker + Nginx + SSL)

Este é o fluxo de deploy novo, introduzido especificamente nesta tag `v4.1.0`, documentado em `templates/rules/05_production_vps.md`:

```bash
# 1. Dentro da pasta do projeto (ex.: examples/enterprise-suite-v4)
cd examples/enterprise-suite-v4

# 2. Gerar os certificados SSL (autoassinados, válidos para teste/staging)
python nginx/ssl/generate_ssl.py

# 3. Subir os contêineres (aplicação + Nginx) em segundo plano
docker compose up -d --build

# 4. Verificar se os serviços subiram corretamente
docker compose ps
docker compose logs -f
```

Após isso, o serviço fica acessível via `https://localhost` (ou o domínio configurado), com:
- Redirecionamento automático de HTTP (porta 80) para HTTPS (porta 443).
- Limitação de 100 requisições por segundo por IP (com pico de até 50 requisições extras).
- Autenticação via token JWT (`Authorization: Bearer <token>`), obtida em `POST /api/auth/login`.

**Antes de usar em produção real:**
1. **Troque a chave secreta do JWT.** O `docker-compose.yml` de exemplo já vem com um valor de `JWT_SECRET_KEY` escrito no arquivo — substitua-o por um valor único e mantenha-o fora do controle de versão.
2. **Substitua o certificado SSL autoassinado** por um certificado emitido por uma autoridade confiável (por exemplo, via Certbot/Let's Encrypt), se o sistema for exposto publicamente com um domínio próprio — o gerador desta tag só cria certificados de teste.
3. **Defina `ALLOW_ANONYMOUS=0`** (já é o padrão no `Dockerfile`) para impedir acesso sem autenticação.

---

## 7. Criando um Projeto Novo do Zero

```bash
# Cria um novo projeto (nome/descrição livre) usando o CLI principal
python scripts/aidd.py init "Sistema de agendamento de consultas"
```

Isso provisiona a estrutura básica de pastas (`src/core`, `src/shared`, `src/modules`, `tests/`, `scripts/gates`), copia o Shared Kernel e os gates de qualidade, e inicializa um repositório Git dentro do novo projeto.

### 7.1 Adicionando um módulo (fatia vertical) ao projeto

```bash
python scripts/aidd.py add-module clientes --descricao "Cadastro de clientes"
```

Isso gera automaticamente, dentro do projeto: o schema de banco de dados do módulo, o serviço com as operações de **criar**, **listar** e **apagar** (não gera "atualizar" automaticamente — essa parte precisa ser escrita manualmente), as rotas de API correspondentes, um componente visual básico e um teste automatizado.

### 7.2 Compondo uma suíte com múltiplos domínios (cross-project)

```bash
python scripts/compose_suite.py ./minha-suite "Minha Suíte" crm erp helpdesk
```

Isso copia o Shared Kernel (banco de dados, eventos, webhooks, segurança, rotas) para a pasta de destino. **Atenção:** este comando não gera automaticamente o código específico de cada domínio listado (`crm`, `erp`, `helpdesk`) — a criação do código de negócio de cada domínio ainda precisa ser feita com `add-module` ou manualmente.

---

## 8. Validando a Qualidade do Código (Gates)

```bash
python scripts/aidd.py audit
```

Executa, em sequência, os 3 fiscais automáticos desta tag:
1. `G_SEGREDOS.py` — bloqueia se encontrar senhas/chaves/tokens no código.
2. `G_QUALIDADE.py` — bloqueia se houver erro de sintaxe em qualquer arquivo Python.
3. `G_HARNESS_COMPAT.py` — sempre passa (não faz verificação real nesta versão).

Se qualquer gate falhar, o processo é interrompido e o script informa qual gate falhou.

---

## 9. Rodando os Testes

```bash
# Testes unitários (pytest)
python scripts/aidd.py test unit

# Teste de carga rápido (Locust, 5 segundos, 10 usuários simulados)
python scripts/aidd.py test load

# Ambos
python scripts/aidd.py test all
```

---

## 10. Consultando o Status do Projeto

```bash
python scripts/aidd.py status
```

Se um arquivo `PLANO-EXECUCAO-ESTRUTURADO.json` existir na raiz do projeto, o comando exibe o nome, a versão e o status registrados nele. Nesta versão, esse arquivo **não é criado automaticamente** por nenhum comando — ele precisa ser escrito manualmente (ou por um agente de IA durante o planejamento) para que essa parte do `status` mostre informação útil. Independentemente disso, o comando sempre lista os módulos existentes na pasta `src/modules`.

---

## 11. Resultados e Entregáveis Obtidos ao Final do Uso

Ao final de um ciclo completo de uso desta versão (criar projeto → adicionar módulos → validar → testar → publicar), o que se obtém é:

1. **Um projeto de código-fonte completo**, organizado em fatias verticais por domínio, com banco de dados SQLite (ou PostgreSQL, se configurado), pronto para rodar localmente com `python src/server.py`.
2. **Uma aplicação web funcional** na porta 3000 (ou a porta configurada), com criação/listagem/exclusão de registros por módulo, feedback visual (toasts) e sem diálogos nativos do sistema operacional.
3. **Documentação de API viva** em `/docs` (Swagger Studio), permitindo testar cada rota diretamente pelo navegador.
4. **Um canal `/mcp`** para que agentes de IA operem o sistema programaticamente (nos exemplos que implementam essa camada manualmente).
5. **Um relatório de aprovação dos 3 gates de qualidade** (`aidd.py audit`), indicando ausência de segredos vazados e ausência de erros de sintaxe.
6. **Opcionalmente, um pacote de produção pronto para deploy** (Dockerfile + docker-compose + Nginx com SSL/rate limiting + autenticação JWT) — a principal novidade entregue por esta tag específica — publicável em qualquer VPS (DigitalOcean, AWS, Hetzner, Oracle, etc.) com os comandos descritos na Seção 6.

---

## 12. Limitações Conhecidas Desta Versão (Resumo Rápido)

- Geração automática de módulo não inclui operação de "atualizar" (CRUD incompleto no gerador).
- EventBus é síncrono, em memória, sem persistência de eventos.
- Webhooks não têm assinatura HMAC, apesar de a documentação mencionar isso.
- Certificado SSL padrão é autoassinado (não é confiável publicamente sem substituição).
- Apenas 2 dos 13 exemplos inclusos já vêm com o novo pacote de produção Docker+Nginx+SSL.
- O gate `G_HARNESS_COMPAT` não faz nenhuma verificação real nesta versão.

Para uma análise técnica mais detalhada dessas e de outras limitações, consulte o relatório `analise-tecnica.md` nesta mesma pasta.
