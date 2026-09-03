# 03. Ciclo de Vida de uma Fatia Vertical

> **Framework:** AIDD Master Enterprise  
> **Conceito:** O percurso completo de concepção, modelagem, persistência, mensageria e evolução de um módulo de domínio.

---

## 1. Anatomia de uma Fatia Vertical

Cada módulo adicionado ao sistema reside isolado em `src/modules/<nome_modulo>/`:

```
src/modules/<nome_modulo>/
├── __init__.py          # Exportações públicas da fatia
├── models.py            # Entidades puras e Tipagem (Dataclasses)
├── services.py          # Regras de Negócio e Casos de Uso (Result Monad)
└── routes.py            # Endpoints HTTP REST (OpenAPI 3.1 & JWT Guard)
```

E sua suíte de testes unitários dedicada em:
```
tests/unit/test_<nome_modulo>.py
```

---

## 2. As Etapas do Ciclo de Vida

```
  1. Criação Atômica
         │
         ▼
  2. Inicialização DDL & Migrações
         │
         ▼
  3. Transação Atômica + Outbox Pattern
         │
         ▼
  4. Publicação no EventBus
         │
         ▼
  5. Exposição HTTP & Servidor MCP
         │
         ▼
  6. Auditoria Contínua via Gates
```

### 1. Criação Atômica da Fatia
* Criada via comando CLI: `python scripts/aidd.py add-module <nome>` ou via subagente com Context-Purge `python scripts/aidd.py compose-orca <nome>`.
* Criação física imediata da estrutura de diretórios e arquivos mínimos sem acoplar com os módulos vizinhos.

### 2. Inicialização DDL e Idempotência de Migrações
* A tabela do módulo (`mod_<nome>`) é criada com constraints completas:
  - `id INTEGER PRIMARY KEY AUTOINCREMENT` (ou `SERIAL` no PostgreSQL).
  - `criado_em`, `atualizado_em` (ISO 8601).
  - `deletado_em` (Soft-Delete padronizado).
  - `status TEXT DEFAULT 'ativo'`.
* Registro idempotente na tabela interna de controle `_schema_migrations` prevenindo reaplicação de DDLs.

### 3. Transação com Garantia Transacional (Outbox Pattern)
* Quando uma entidade é criada ou alterada, a gravação de banco e o evento de domínio são gravados na **mesma transação ACID**:
  ```python
  with db.get_connection() as conn:
      cur = conn.execute("INSERT INTO mod_pedido ...")
      db.enqueue_outbox_event(conn, "pedido_criado", {"id": cur.lastrowid})
      conn.commit()
  ```
* Isso impede a clássica inconsistência distribuída (onde o banco comita, mas o disparo do evento falha).

### 4. Publicação Assíncrona no EventBus
* O `OutboxWorker` em background processa os eventos pendentes da tabela `_outbox_events` e os envia ao `EventBus`.
* Outros módulos que tenham assinado o evento reagem de forma 100% desacoplada:
  ```python
  from core.events import EventBus

  def ao_receber_pedido(evento):
      # Notifica faturamento sem importar o módulo de pedidos
      ...

  EventBus.subscribe("pedido_criado", ao_receber_pedido)
  ```

### 5. Exposição em Múltiplos Protocolos (REST e MCP)
* **REST / OpenAPI 3.1:** A rota é registrada automaticamente no Swagger Studio (`/docs`).
* **Model Context Protocol (`/mcp`):** A fatia gera ferramentas automáticas (`mod_<nome>_criar`, `mod_<nome>_listar`, `mod_<nome>_obter`) para que IAs como Claude, Cursor e Antigravity possam manipular o módulo via JSON-RPC 2.0.

### 6. Descarte e Soft-Delete
* Nenhuma entidade de negócio é destruída fisicamente no banco com `DELETE` destrutivo.
* A exclusão ocorre via atualização de `deletado_em = now()`, mantendo trilha de auditoria e rastreabilidade total (WORM Audit Chain).
