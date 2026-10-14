# Especificação — Controle de Pedidos

## 1. Context & Explicit Non-Goals

Sistema web para pequenos comércios lançarem e acompanharem pedidos de clientes.
Non-goals: pagamento online, emissão fiscal, aplicativo nativo.

### Visual Direction
- tom: sóbrio e profissional
- cor_primaria: #0F766E
- referencias: Linear, Stripe
- publico: atendentes de pequenos comércios

## 2. Contracts & Typed Interfaces

```ts
interface Pedido { id: string; clienteId: string; total: number; status: "aberto" | "pago" | "cancelado" }
```

## 3. Invariants & Business Rules

1. Todo pedido pertence a exatamente um cliente.
2. O total do pedido é a soma dos itens e nunca é negativo.

## 4. Binary Acceptance Criteria

- `GET /pedidos/{id}` devolve HTTP 404 quando o id não existe.
- `pytest` termina com exit code 0.
- `POST /pedidos` com total negativo devolve HTTP 422.

## 5. Failure & Degradation Modes

- Banco indisponível: a API devolve HTTP 503 e o frontend mostra a tela de erro.
