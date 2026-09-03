# Camada Servicos — Regras de Logica de Negocio

> **Escopo:** Toda logica de negocio em `services.py` dos modulos (`src/modules/<dominio>/`).
> **Referencia:** `templates/core/result.py`, `templates/core/events.py`, `templates/core/circuit_breaker.py`, `templates/core/saga.py`.

---

## 1. Result Monad Pattern (Obrigatorio)

Nenhuma excecao de negocio deve escapar de um metodo de servico. Usar exclusivamente `Result.ok()` / `Result.fail()`:

```python
from src.core.result import Result

class ClienteService:
    def criar(self, dados: dict) -> Result:
        if not dados.get("nome"):
            return Result.fail("Nome e obrigatorio", codigo="VALIDACAO_CAMPO")
        
        with self.db.get_connection() as conn:
            conn.execute("INSERT INTO clientes (nome, email) VALUES (?, ?)", ...)
            self.db.enqueue_outbox_event(conn, "cliente.criado", {"id": id, ...})
            conn.commit()
        
        return Result.ok(valor={"id": id, "nome": dados["nome"]})
```

- `Result.ok(valor={...})` para sucesso.
- `Result.fail(erro="...", codigo="...")` para falha de negocio.
- Codigos de erro padronizados: `VALIDACAO_CAMPO`, `NAO_ENCONTRADO`, `CONFLITO`, `ERRO_EXTERNO`.
- `Result.to_dict()` para serializacao em respostas HTTP e MCP.
- Excecoes sao permitidas apenas para erros de infraestrutura (conexao, timeout).

---

## 2. Circuit Breaker para Chamadas Externas

Toda chamada a servicos externos (APIs, webhooks, Redis, filas) DEVE ser protegida por Circuit Breaker:

```python
from src.core.circuit_breaker import CircuitBreaker

breaker = CircuitBreaker(name="payment_api", failure_threshold=5, timeout=60)

def chamar_gateway_pagamento(payload):
    return breaker.call(requests.post, "https://api.payments.com/charge", json=payload)
```

- Estados: `CLOSED` (normal) -> `OPEN` (fast-fail) -> `HALF_OPEN` (teste).
- `failure_threshold=5` como padrao (configuravel por servico).
- `timeout=60` segundos antes de tentar `HALF_OPEN`.
- Quando `OPEN`, retornar `Result.fail("Servico temporariamente indisponivel", codigo="CIRCUIT_OPEN")`.
- Logar toda transicao de estado para observabilidade.

---

## 3. EventBus para Comunicacao Cross-Module

A comunicacao entre modulos e EXCLUSIVAMENTE via EventBus. Nunca import direto:

```python
# CORRETO: modulo CRM publica evento
self.event_bus.emit("lead.ganho", {"lead_id": lead_id, "valor": 5000}, origin_module="crm")

# INCORRETO: import direto de outro modulo
from src.modules.erp.services import FinanceiroService  # PROIBIDO
```

- Todo evento DEVE conter: `event_id`, `event_name`, `origin_module`, `timestamp`.
- Nomes de eventos: `<modulo>.<entidade>.<acao>` (ex: `crm.lead.criado`, `erp.conta.paga`).
- Handlers de eventos DEVEM ser idempotentes (processar duas vezes nao causa efeito colateral).
- Usar `db.enqueue_outbox_event()` para garantir entrega via Transactional Outbox.

---

## 4. Zero Acoplamento Direto entre Modulos

Regras estritas de isolamento:

| Permitido | Proibido |
|-----------|----------|
| `event_bus.emit("modulo.evento", data)` | `from src.modules.X.services import ...` |
| `event_bus.on("modulo.evento", handler)` | `from src.modules.X.models import ...` |
| Contratos de evento no `shared/events/contracts.py` | SQL direto em tabelas de outro modulo |
| Chamada HTTP via API interna com Circuit Breaker | Acesso direto a `db` de outro modulo |

- Cada modulo DEVE funcionar isoladamente (testavel sem outros modulos).
- Dados de outro modulo obtidos via: (a) evento com dados suficientes, ou (b) chamada a API do modulo.
- `shared/events/contracts.py` define os schemas de eventos como contrato compartilhado.

---

## 5. Saga Pattern para Transacoes Distribuidas

Operacoes que envolvem multiplos modulos DEVEM usar Saga Orchestration:

```python
from src.core.saga import SagaOrchestrator, SagaStep

saga = SagaOrchestrator(steps=[
    SagaStep(
        name="reservar_estoque",
        execute=lambda ctx: estoque_service.reservar(ctx["pedido"]),
        compensate=lambda ctx: estoque_service.liberar(ctx["pedido"])
    ),
    SagaStep(
        name="processar_pagamento",
        execute=lambda ctx: pagamento_service.cobrar(ctx["pedido"]),
        compensate=lambda ctx: pagamento_service.estornar(ctx["pedido"])
    ),
    SagaStep(
        name="confirmar_pedido",
        execute=lambda ctx: pedido_service.confirmar(ctx["pedido"]),
        compensate=lambda ctx: pedido_service.cancelar(ctx["pedido"])
    ),
])

resultado = saga.run({"pedido": pedido_data})
```

- Cada `SagaStep` tem `execute` (acao) e `compensate` (rollback).
- Em caso de falha, compensacoes sao executadas em ordem reversa.
- `saga_id` rastreavel em todos os logs e eventos.
- Sagas longas (>30s) DEVEM persistir estado no banco via tabela `_saga_state`.

---

## 6. Estrutura Padrao de um Service

```python
class ModuloService:
    def __init__(self, db, event_bus):
        self.db = db
        self.event_bus = event_bus

    def criar(self, dados: dict) -> Result:
        """Cria entidade com validacao, persistencia e evento."""
        # 1. Validacao
        # 2. Persistencia + Outbox Event
        # 3. Return Result.ok()

    def listar(self, filtros: dict = None) -> Result:
        """Lista com paginacao e filtros opcionais."""

    def buscar_por_id(self, id: str) -> Result:
        """Busca por ID com tratamento de nao encontrado."""

    def atualizar(self, id: str, dados: dict) -> Result:
        """Atualiza com validacao de conflito."""

    def deletar(self, id: str) -> Result:
        """Soft delete (deletado_em) ou hard delete."""
```

- Todo service recebe `db` e `event_bus` via injecao de dependencia.
- Metodos CRUD padronizados: `criar`, `listar`, `buscar_por_id`, `atualizar`, `deletar`.
- Campos de auditoria obrigatorios: `criado_em`, `atualizado_em`, `deletado_em`.

---

## 7. Validacao de Entrada

- Validacao DEVE ocorrer antes de qualquer operacao de persistencia.
- Usar `Result.fail()` com codigo especifico para cada tipo de erro.
- Campos obrigatorios verificados com `if not dados.get("campo")`.
- Tipos validados: strings nao vazias, numeros positivos, emails com formato valido.
- NUNCA confiar em dados do usuario — sanitizar e validar tudo.

---

## Checklist de Auditoria Servicos

| # | Criterio | Gate |
|---|----------|------|
| 1 | Todo metodo retorna `Result.ok()` ou `Result.fail()` | G_CONTRACTS |
| 2 | Circuit Breaker em toda chamada externa | G_SEGURANCA |
| 3 | Zero imports cruzados entre modulos | G_ESTRUTURA |
| 4 | EventBus para comunicacao cross-module | G_CONTRACTS |
| 5 | Outbox event na mesma transacao da mutacao | G_TESTES |
| 6 | Handlers idempotentes | G_TESTES |
| 7 | Saga com compensacao para transacoes distribuidas | G_QUALIDADE |
| 8 | Campos de auditoria em toda entidade | G_ESTRUTURA |
| 9 | Validacao de entrada antes de persistencia | G_SEGURANCA |
