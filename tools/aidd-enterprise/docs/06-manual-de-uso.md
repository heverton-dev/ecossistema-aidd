# 06. Manual de Uso Universal: Do Iniciante ao Especialista

> **Framework:** AIDD Master Enterprise  
> **Público-Alvo:** Este manual foi escrito para ser compreendido por **qualquer pessoa**: desde quem nunca programou na vida até PhDs em Engenharia Agêntica.

---

# 🟢 PARTE 1: Guia para Quem Não É de Tecnologia (Iniciantes)

Se você não sabe o que é código, terminal, banco de dados ou API, **esta seção foi feita sob medida para você**.

---

## 1. O que é o AIDD Master Enterprise? (A Analogia da Construtora)

Imagine que construir um software antigamente era como construir uma casa inteira sozinho, tijolo por tijolo: você precisava aprender a fazer o cimento, passar os canos de água, instalar a fiação elétrica e pintar cada parede. Se você errasse um cano, a casa alagava.

O **AIDD Master** é como uma **Construtora de Alta Tecnologia com Robôs Especialistas**:
* Você não precisa saber como funciona a fiação elétrica.
* Você apenas chega para a equipe e diz: *"Quero uma casa com 3 quartos, sala e cozinha"*.
* Os robôs montam toda a estrutura com blocos perfeitos, testam se a água e a energia estão funcionando sem vazamentos e entregam a chave pronta na sua mão.

---

## 2. Como Usar em 3 Passos Rápidos (Sem Tocar em Código)

Você só precisa conversar com a sua ferramenta de IA (Claude, Antigravity, Cursor, etc.):

### Passo 1: Diga o que você quer construir
No campo de mensagem do chat, use o comando rápido `/compose` seguido dos setores que o seu sistema terá.

**Exemplos da vida real:**
* Para uma **Clínica Médica**:  
  `/compose pacientes agendamentos prontuarios financeiro`
* Para uma **Loja / Comércio**:  
  `/compose produtos clientes vendas estoque`
* Para uma **Oficina Mecânica**:  
  `/compose veiculos clientes ordens_de_servico orcamentos`
* Ou simplesmente digite em **português normal**:  
  *"Crie um sistema para gerenciar minha escola com alunos, turmas e mensalidades."*

### Passo 2: A ferramenta trabalha para você
* A inteligência artificial vai criar cada parte do seu sistema em segundos.
* Ela fará verificações de segurança para garantir que ninguém consiga invadir ou roubar dados.
* Ela rodará mais de 150 testes automáticos para ter certeza de que tudo funciona antes de entregar.

### Passo 3: Abra o seu sistema no navegador
Ao final, ela ligará o sistema e informará um endereço de internet local (um link azul):  
👉 **`http://localhost:8000`**

Basta clicar no link! Uma tela visual bonita aparecerá no seu navegador, com botões para você cadastrar, listar, editar e excluir informações, funcionando imediatamente no seu computador.

---

## 3. Glossário Simplificado (Traduzindo o "Techniquês")

| Termo que os técnicos usam | O que significa em português claro? |
| :--- | :--- |
| **Fatia Vertical (Module)** | Uma pasta organizada que cuida de um setor do seu negócio (ex: a pasta de "Clientes" ou a de "Vendas"). |
| **Banco de Dados (SQLite/Postgres)** | O caderno digital seguro onde todas as informações cadastradas ficam salvas para nunca se perderem. |
| **Quality Gates (Portões de Qualidade)** | Fiscais digitais rigorosos que barram o sistema se houver qualquer erro ou risco de falha. |
| **Auto-Healing (Auto-Cura)** | Se um fiscal encontrar um erro simples (como um texto fora de ordem), a ferramenta conserta sozinha e tenta de novo. |
| **OpenAPI / Swagger (`/docs`)** | Uma página mágica que lista todas as ações que o seu sistema sabe fazer, permitindo testá-las clicando em botões. |
| **MCP Server (`/mcp`)** | Um "tradutor" que permite que robôs de IA conversem diretamente com o seu sistema. |

---

# 🔵 PARTE 2: Guia Avançado para Desenvolvedores e Engenheiros

Se você é engenheiro de software, arquiteto de soluções ou pesquisador de IA, esta seção detalha os contratos, flags de CLI, schemas e mecanismos do runtime.

---

## 1. Interface de Linha de Comando (`scripts/aidd.py`)

### Diagnóstico de Ambiente (`setup`)
```bash
python scripts/aidd.py setup
```
* **Fleet Auto-Discovery:** Escaneia binários no `$PATH` (`claude`, `agy`, `codex`, `gemini`, `opencode`, `mimocode`, `ollama`).
* Validação de runtime Python 3.10+, SQLite com suporte a WAL e injeção de dependências.

### Composição Efêmera com Context-Purge (`compose-orca`)
```bash
python scripts/aidd.py compose-orca crm erp billing helpdesk --dir ./app_suite
```
* Spawna subprocessos isolados por módulo via `SubagentEngine`.
* Limite cognitivo de ~1.200 tokens de prompt por subagente.
* Context-Purge imediato após gravação em disco para evitar contaminação cross-slice.
* Emissão de manifesto estruturado `COMPOSE-ORCA-MANIFEST.json`.

### Composição Determinística Tradicional (`compose`)
```bash
python scripts/aidd.py compose --suite "Enterprise Hub" --db postgres crm erp logistica
```
* `--db sqlite`: SQLite com `PRAGMA journal_mode=WAL` e `busy_timeout=5000`.
* `--db postgres`: PostgreSQL / Supabase com connection pooling e proxy de dialeto (`?` ➔ `%s`).

### Adição de Fatia Atômica (`add-module`)
```bash
python scripts/aidd.py add-module faturamento
```
* Scaffold de `models.py` (Dataclasses), `services.py` (Result Monad), `routes.py` (OpenAPI 3.1) e `test_faturamento.py` (Full CRUD BDD).

---

## 2. Orquestração e Execução dos 10 Quality Gates

Para validar o sistema antes de qualquer release de produção:

```bash
# Execução sequencial com Auto-Healing:
python scripts/run_all.py

# Ou execução de gates individuais:
python scripts/gates/G_ARQUITETURA.py    # Linter AST de Bounded Context (Zero cross-imports)
python scripts/gates/G_PERFORMANCE.py    # Latência p99 < 200ms, RSS < 512MB, N+1 detection
python scripts/gates/G_SEGURANCA.py      # OWASP, JWT HS256 e auditoria CVE via pip-audit
python -m pytest tests/ -v               # Suíte unitária completa (158 testes)
```

---

## 3. Protocolos de Integração e Portais do Servidor

Inicie o servidor de aplicação:
```bash
python src/server.py
```

### Portais Nativos Ativos:
1. **Super-App SPA (`/`):** Front-end responsivo em Tailwind CSS e design corporativo Impeccable (4px scrollbars, zero emojis na UI).
2. **Swagger Studio OpenAPI 3.1 (`/docs`):** Documentação viva compatível com Swagger UI e Bearer JWT Auth.
3. **Servidor MCP JSON-RPC 2.0 (`/mcp`):** Exposição nativa de ferramentas para agentes de IA:
   * Métodos: `mod_<modulo>_listar`, `mod_<modulo>_criar`, `mod_<modulo>_obter`, `mod_<modulo>_atualizar`, `mod_<modulo>_deletar`.
4. **Webhook Configuration Studio (`/webhooks`):** Gerenciador de dispatchers assíncronos com assinatura digital HMAC SHA-256 no header `X-Signature-SHA256`.
