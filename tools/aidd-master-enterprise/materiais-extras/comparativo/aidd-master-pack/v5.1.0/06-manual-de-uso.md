# Manual de Uso — AIDD Master Pack (tag v5.1.0)

> **Versão documentada:** `v5.1.0`
> **Repositório oficial:** `https://github.com/heverton-dev/aidd-master-pack`
> Todos os comandos abaixo foram verificados diretamente no código-fonte extraído da tag `v5.1.0` (`scripts/aidd.py`, `README.md`, `SKILL.md`, `FIRE_TEST_MULTI_HARNESS.md`).

---

## 1. O que é o AIDD Master Pack v5.1.0

O AIDD Master Pack v5.1.0 é um framework de engenharia agêntica que gera, de forma automatizada, suítes de software empresariais completas — com back-end, front-end, documentação de API, conectividade para IA (MCP) e uma bateria de checagens de qualidade obrigatórias. Ele funciona como uma CLI Python (`scripts/aidd.py`) que pode ser usada tanto por um desenvolvedor humano diretamente no terminal quanto por um agente de IA (Claude, Cursor, etc.) operando em nome do usuário.

Principais entregas desta versão:
- Arquitetura em fatias verticais isoladas (Clean Architecture) por domínio de negócio.
- Persistência em SQLite (modo WAL) com adapter opcional para PostgreSQL.
- Documentação de API viva (Swagger/OpenAPI 3.1) e servidor MCP (JSON-RPC 2.0) para IAs.
- Interface web própria (SPA offline-first, sem dependência de build/Node).
- 7 Quality Gates automáticos que bloqueiam a entrega de código incompleto ou inseguro.

## 2. Pré-requisitos

- Python 3 instalado no sistema.
- Git instalado.
- Acesso à internet apenas para o clone inicial (a execução do framework em si não depende de chaves de API pagas — "zero API key mode").
- Opcional: Docker, caso deseje usar os scripts de deploy/containerização já incluídos nos exemplos.

## 3. Passo 1 — Obtendo o código-fonte da tag v5.1.0

Clone o repositório e mude explicitamente para a tag `v5.1.0` (não para o branch `main`, que pode conter mudanças posteriores a este release):

```bash
git clone https://github.com/heverton-dev/aidd-master-pack.git
cd aidd-master-pack
git checkout v5.1.0
```

Após esse passo, o diretório local estará exatamente no estado do release `v5.1.0`, incluindo os scripts, templates, gates e exemplos descritos neste manual.

## 4. Passo 2 — Instalação e diagnóstico do ambiente

Execute o diagnóstico automático, que verifica dependências e prepara o ambiente (instala pacotes como `pytest`, `behave`, `pyjwt`, `psycopg2`, conforme necessário):

```bash
python scripts/aidd.py setup
```

Esse comando também detecta automaticamente se o projeto será operado em modo SQLite local (padrão, sem configuração adicional) ou PostgreSQL remoto (caso variáveis de conexão sejam fornecidas).

## 5. Passo 3 — Criando um projeto (três formas possíveis)

### Opção A — Pedir em linguagem natural (recomendado para não-programadores)

```bash
python scripts/aidd.py "Criar sistema financeiro multi-tenant com CRM e ERP"
```

A ferramenta interpreta o pedido, gera uma especificação arquitetural (`SPEC-ARQUITETURA.md`) e um manifesto de plano (`PLANO-EXECUCAO-ESTRUTURADO.json`) para revisão antes de construir qualquer coisa.

### Opção B — Comando declarativo direto (para quem já sabe os módulos desejados)

```bash
python scripts/aidd.py compose ./meu-projeto "Suite Financeira" crm erp --db sqlite
```

Isso compõe imediatamente uma suíte com os módulos `crm` e `erp` dentro da pasta `./meu-projeto`, usando SQLite como banco (`--db postgres` é a alternativa para PostgreSQL).

### Opção C — Adicionar um módulo a um projeto já existente

```bash
python scripts/aidd.py add-module cobranca --dir ./meu-projeto
```

### Fluxo completo recomendado (planejar → aprovar → aplicar)

```bash
# 1. Gera a especificação e o plano, sem construir nada ainda
python scripts/aidd.py plan "Crie um CRM e ERP de faturamento"

# 2. Após revisar e aprovar o plano gerado, executa a construção de fato
python scripts/aidd.py apply --dir ./app_crm-erp-faturamento-suite
```

## 6. Passo 4 — Validando a qualidade do projeto gerado

Execute a suíte de testes unitários:

```bash
python scripts/aidd.py test --dir ./app_crm-erp-faturamento-suite
```

Execute os 7 Quality Gates e gere o relatório de auditoria factual:

```bash
python scripts/aidd.py audit --report --dir ./app_crm-erp-faturamento-suite
```

Este comando falha (`exit` diferente de 0) caso qualquer um dos gates a seguir reprove o projeto: `G_ESTRUTURA`, `G_QUALIDADE`, `G_TESTES`, `G_CONTRACTS`, `G_SEGREDOS`, `G_HARNESS_COMPAT`, `G_SEGURANCA`.

## 7. Passo 5 — Recursos opcionais avançados

```bash
# Benchmark de carga e concorrência (SQLite WAL / EventBus)
python scripts/aidd.py bench -n 100 --dir ./app_crm-erp-faturamento-suite

# Gerar infraestrutura como código (Terraform AWS + Helm Chart Kubernetes)
python scripts/aidd.py scaffold-infra --dir ./app_crm-erp-faturamento-suite

# Exportar um front-end Next.js/TypeScript tipado, a partir do contrato OpenAPI já gerado
python scripts/aidd.py export-frontend --dir ./app_crm-erp-faturamento-suite --stack nextjs

# Rodar o refinador de regras de negócio via testes de comportamento (BDD/Gherkin)
python scripts/aidd.py refine-module <modulo> --spec <feature>

# Auto-remediação determinística de módulos com inconsistências
python scripts/aidd.py heal --dir ./app_crm-erp-faturamento-suite

# Consultar o status/integridade atual do projeto e do manifesto de plano
python scripts/aidd.py status --dir ./app_crm-erp-faturamento-suite
```

## 8. Passo 6 — Rodando o sistema gerado

```bash
python ./app_crm-erp-faturamento-suite/src/server.py
```

Com o servidor no ar, os seguintes portais ficam disponíveis (endereço padrão `localhost:3000`, salvo configuração diferente):

| Portal | Endereço | O que é |
| :--- | :--- | :--- |
| Aplicação (Super-App) | `http://localhost:3000/` | Tela de uso do sistema (CRUD, KPIs, dark mode) |
| Documentação da API | `http://localhost:3000/docs` | Swagger Studio, documentação interativa (OpenAPI 3.1) |
| Webhooks | `http://localhost:3000/webhooks` | Painel de eventos/webhooks assinados (HMAC SHA-256) |
| Conexão para IA | `http://localhost:3000/mcp` | Endpoint MCP JSON-RPC 2.0, para uso por assistentes de IA |
| Métricas | `http://localhost:3000/metrics` | Telemetria Prometheus, se o projeto incluir esse módulo |

## 9. O que você recebe ao final (entregáveis)

Ao concluir o processo, o projeto gerado contém, entre outros artefatos:

- `src/server.py` — servidor HTTP do sistema.
- `src/core/` — kernel compartilhado (banco de dados, segurança, eventos, jobs, métricas, etc.).
- `src/modules/<modulo>/` — cada domínio de negócio como uma fatia vertical completa (modelos, serviços, rotas e testes).
- `tests/unit/` — testes automatizados de cada módulo.
- `frontend/` — aplicação Next.js/TypeScript, apenas se `export-frontend` foi executado.
- `infra/terraform/` e `infra/helm/` — arquivos de infraestrutura como código, apenas se `scaffold-infra` foi executado.
- `RELATORIO-AUDITORIA.json` — relatório com o resultado da auditoria dos 7 Quality Gates e o score de segurança obtido.
- `PLANO-EXECUCAO-ESTRUTURADO.json` — manifesto com o histórico de fases executadas e gates aprovados em cada uma (ver `plano-de-execucao.md` para detalhes de estrutura).

## 10. Observações importantes desta tag específica

- Use sempre `git checkout v5.1.0` após o clone caso queira reproduzir exatamente o comportamento descrito neste manual — o branch `main` do repositório pode conter funcionalidades adicionadas após este release (por exemplo, mudanças na lógica de Row-Level Security e testes de fuzzing contínuo de APIs) que **não fazem parte** da v5.1.0.
- O modo padrão de banco é SQLite (zero configuração); PostgreSQL é suportado via `--db postgres`, mas exige que o adapter correspondente esteja configurado no ambiente.
- A ferramenta foi desenhada para operar em "zero API key mode": não é necessário possuir chaves de serviços de IA pagos para que o processo de geração e os Quality Gates funcionem.
- Recomenda-se sempre executar `audit --report` antes de considerar qualquer projeto gerado como "pronto para uso", pois é essa etapa que garante a ausência de código incompleto, segredos expostos ou falhas de segurança básicas.
