# Manual de Uso — AIDD Master Pack (tag v4.0.0)

> **Versão documentada:** `v4.0.0` (commit `7c64daa`)
> **Importante:** este manual descreve exclusivamente o comportamento do código nesta tag específica. Comandos, arquivos e recursos de tags posteriores (v4.0.1+, v5.x) não estão incluídos.

---

## 1. O Que É Esta Versão do Projeto

O AIDD Master Pack v4.0.0 é um conjunto de scripts Python (sem dependências externas pesadas — apenas biblioteca padrão) que:
- Provisiona a estrutura inicial de um projeto de software modular (banco SQLite, barramento de eventos em memória, documentação de API básica).
- Permite adicionar "módulos" (fatias verticais de funcionalidade) sob demanda, cada um com seu CRUD mínimo, testes e componente de tela.
- Executa 3 verificações automáticas de qualidade/segurança antes de considerar o código pronto.
- Inclui, como material de referência, 12 projetos de exemplo já montados em `examples/`, demonstrando diferentes estágios de evolução do framework — dois deles (`enterprise-suite-v4` e `logistica-hub-v4`) demonstram manualmente a nova central de documentação de API em 3 colunas ("Swagger Studio") que dá nome a esta tag.

Esta versão **não** é um produto SaaS, não tem instalador gráfico e não exige nenhuma chave de API paga — tudo roda localmente com Python.

---

## 2. Pré-requisitos

- **Python 3.10 ou superior** instalado e disponível no `PATH`.
- **Git** instalado (para clonar o repositório e para o comando `git init` interno do provisionador).
- Opcional: **Docker** e **Docker Compose**, apenas se for usar o comando de deploy via contêiner.
- Opcional: **pytest** e **locust** instalados (`pip install pytest locust`), necessários para os comandos de teste unitário e de carga.
- Sistema operacional: Windows, Linux ou macOS (o framework não usa nenhuma chamada específica de sistema operacional nos scripts principais).

---

## 3. Obtendo o Código Nesta Versão Exata

```bash
git clone https://github.com/heverton-dev/aidd-master-pack.git
cd aidd-master-pack
git checkout v4.0.0
```

Isso deixa a pasta de trabalho exatamente no estado do commit `7c64daa`, com a seguinte estrutura na raiz:

```
aidd-master-pack/
├── LICENSE
├── README.md              # Nesta tag, descreve a v1.0.0 (ver observação abaixo)
├── SKILL.md                # Nesta tag, descreve a v1.0.0 (ver observação abaixo)
├── .gitignore
├── scripts/
│   ├── aidd.py              # Micro-CLI do framework
│   ├── add_module.py        # Gerador de módulos/fatias verticais
│   └── provision_project.py # Gerador do projeto base
├── templates/
│   ├── gates/                # G_SEGREDOS.py, G_QUALIDADE.py, G_HARNESS_COMPAT.py
│   ├── rules/                # Regras de ouro, camadas, design, segurança (Markdown)
│   └── v2/                   # Núcleo copiado para novos projetos (database, events, openapi, webhooks, docker, shared/)
└── examples/                 # 12 projetos de referência já montados
```

> **Observação sobre `README.md`/`SKILL.md`:** nesta tag específica, esses dois arquivos da raiz descrevem a versão 1.0.0 do pacote, não a 4.0.0 — é uma inconsistência real de versionamento do repositório nesta tag (documentada em detalhe em `analise-tecnica.md`). Não use o conteúdo desses dois arquivos como referência do que a v4.0.0 faz; use este manual e o código real dos `scripts/`.

---

## 4. Instalação / Preparação do Ambiente

Não há um passo de "instalação" formal (não é um pacote `pip`). O que existe:

1. Confirme que o Python funciona: `python --version` (precisa ser 3.10+).
2. **Ponto de atenção crítico:** o script `scripts/provision_project.py` lê templates a partir de um caminho fixo do usuário: `~/.agents/skills/aidd-master-pack/templates/v2/` e `~/.agents/skills/aidd-master-pack/scripts/`. Para o comando de criação de projeto (`init`) funcionar corretamente, copie (ou faça symlink) da pasta clonada para esse local:
   - **Linux/macOS:** `mkdir -p ~/.agents/skills/ && cp -r aidd-master-pack ~/.agents/skills/aidd-master-pack`
   - **Windows (PowerShell):** `Copy-Item -Recurse .\aidd-master-pack "$env:USERPROFILE\.agents\skills\aidd-master-pack"`
   Se esse passo for pulado, `provision_project.py` ainda cria a estrutura de pastas, mas **não copia nenhum arquivo-núcleo** (porque as condições `if os.path.exists(...)` simplesmente falham silenciosamente).
3. (Opcional) instale dependências de teste: `pip install pytest locust`.

---

## 5. Como Usar — Comandos Disponíveis

Todos os comandos passam pela micro-CLI `scripts/aidd.py`:

### 5.1. Criar um novo projeto
```bash
python scripts/aidd.py init "Minha Plataforma de Vendas"
```
Cria uma pasta nova em `C:\Users\<usuário>\orca\workspaces\PROJETOS Criados com IA\proj_<slug>` (caminho padrão hardcoded no script — pode ser mudado editando `provision_project.py`, já que a tag não expõe essa opção via linha de comando) contendo a estrutura de pastas, os arquivos-núcleo (`database.py`, `events.py`, `openapi.py`, `webhooks.py`), a pasta `shared/`, arquivos Docker/deploy, os scripts `aidd.py`/`add_module.py` e os 3 gates de qualidade.

### 5.2. Adicionar um módulo de funcionalidade
```bash
cd "<pasta do projeto criado>"
python scripts/aidd.py add-module financeiro
```
Gera `src/modules/financeiro/{models,services,routes}.py`, um componente de tela em `src/static/components/financeiro.html` e um teste em `tests/unit/test_financeiro.py`.

### 5.3. Rodar as verificações de qualidade
```bash
python scripts/aidd.py audit
```
Executa `G_SEGREDOS.py` → `G_QUALIDADE.py` → `G_HARNESS_COMPAT.py` em sequência. Encerra com código de saída 0 apenas se todos passarem.

### 5.4. Rodar os testes
```bash
python scripts/aidd.py test unit   # pytest -v
python scripts/aidd.py test load   # Locust headless, 5s, 10 usuários (exige servidor rodando)
python scripts/aidd.py test all    # os dois
```

### 5.5. Ver o status do projeto
```bash
python scripts/aidd.py status
```
Mostra o nome/versão/status lidos de `PLANO-EXECUCAO-ESTRUTURADO.json` **se esse arquivo existir** no diretório atual (nenhum comando desta tag cria esse arquivo automaticamente — veja `plano-de-execucao.md`) e lista os módulos presentes em `src/modules/`.

### 5.6. Ligar o servidor localmente
Nesta tag, `provision_project.py` não gera um `src/server.py` pronto — esse arquivo precisa ser escrito (pelo usuário ou por um agente de IA seguindo a `SKILL.md`), amarrando os módulos criados às rotas HTTP. Nos 12 projetos de exemplo isso já está feito; para reproduzir localmente um deles:
```bash
cd examples/logistica-hub-v4/src
python server.py
```
Abra no navegador:
- `http://localhost:3000/` — aplicação principal.
- `http://localhost:3000/docs` — documentação de API (Swagger Studio 3-colunas, neste exemplo específico).
- `http://localhost:3000/mcp` — portal do servidor MCP (apenas em `enterprise-suite-v4` e `logistica-hub-v4`).
- `http://localhost:3000/openapi.json` — schema OpenAPI cru.

> **Aviso de compatibilidade:** o exemplo `examples/enterprise-suite-v4/src/server.py`, ao ser executado nesta tag, encerra imediatamente com erro (`TypeError: RouteRegistry.get() got an unexpected keyword argument 'sample_response'`) por uma incompatibilidade entre o servidor e o registrador de rotas dentro do próprio exemplo. Isso foi reproduzido e confirmado ao rodar `python server.py` diretamente no snapshot da tag. O exemplo `logistica-hub-v4` não tem esse problema e inicia normalmente.

### 5.7. Deploy (opcional)
```bash
python scripts/aidd.py deploy docker   # docker compose up -d --build
python scripts/aidd.py deploy vps      # apenas orienta a rodar deploy.sh manualmente no servidor
```

---

## 6. Configuração para Uso com Agentes de IA (MCP)

Nos dois exemplos que possuem `mcp_server.py` (`enterprise-suite-v4`, `logistica-hub-v4`), é possível conectar um assistente de IA compatível com Model Context Protocol (ex.: Claude Desktop) apontando para o servidor local. O próprio exemplo traz um arquivo de referência (`claude_desktop_config.json`) com o formato esperado:
```json
{
  "mcpServers": {
    "aidd-enterprise-suite": {
      "command": "python",
      "args": ["<caminho-absoluto>\\src\\core\\mcp_server.py"],
      "env": { "PYTHONIOENCODING": "utf-8" }
    }
  }
}
```
Basta ajustar o caminho para a sua cópia local do projeto e colar essa entrada no arquivo de configuração de MCP do seu harness de IA.

---

## 7. Resultados/Entregáveis Obtidos ao Final do Uso

Ao seguir o fluxo completo desta tag, o usuário obtém:

1. **Uma pasta de projeto** com banco de dados SQLite (`.db`), pastas de módulos, testes unitários e infraestrutura Docker.
2. **Um relatório de console** do comando `audit`, indicando aprovação ou falha nas 3 checagens mecânicas (nenhum arquivo de relatório é salvo em disco nesta tag — a saída é apenas texto no terminal).
3. **Um servidor HTTP local** (quando `server.py` é escrito/copiado de um exemplo), expondo API REST, documentação interativa e, em 2 dos 12 casos, o portal MCP para agentes de IA.
4. **Nenhum manifesto de plano de execução automático** — se o usuário quiser um documento de acompanhamento de fases, precisa criá-lo manualmente seguindo o formato encontrado em `examples/catalogo-digital-v3/PLANO-EXECUCAO-ESTRUTURADO.json` ou `examples/plataforma-modular-assinaturas/PLANO-EXECUCAO-ESTRUTURADO.json`.
5. **Nenhuma autenticação ativa** nas rotas geradas pelos exemplos desta tag — adequado apenas para uso local/demonstração, não para exposição pública sem trabalho adicional de segurança.

---

## 8. Resumo Rápido de Comandos

| Ação | Comando |
|---|---|
| Clonar nesta versão exata | `git clone ...` + `git checkout v4.0.0` |
| Criar projeto novo | `python scripts/aidd.py init "<descrição>"` |
| Adicionar módulo | `python scripts/aidd.py add-module <nome>` |
| Rodar gates de qualidade | `python scripts/aidd.py audit` |
| Rodar testes | `python scripts/aidd.py test [unit\|load\|all]` |
| Ver status do projeto | `python scripts/aidd.py status` |
| Ligar servidor (se `server.py` existir) | `python src/server.py` |
| Deploy via Docker | `python scripts/aidd.py deploy docker` |
| Deploy via VPS (manual) | `python scripts/aidd.py deploy vps` |
