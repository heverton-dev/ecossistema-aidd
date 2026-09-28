# Manual Canônico: DDD Tático e Invariantes no Monólito VSA

> **Status:** Canônico e Obrigatório  
> **Ecossistema:** AIDD (AI-Driven Development)  
> **Escopo:** Modelagem de Domínio Tático em Arquitetura por Fatias Verticais (VSA)  
> **Diretiva de Integridade:** Zero Stubs, Zero Vendor Lock-in, Tipagem Estrita, Invariantes Rígidas.

---

## 1. Visão Geral e Princípios Fundamentais

No ecossistema AIDD, a camada de domínio reside no coração das fatias verticais (Vertical Slice Architecture - VSA) e na camada compartilhada do monólito modular. O design tático guiado por domínio (Domain-Driven Design - DDD) é aplicado com foco na **defesa irrestrita de invariantes** de negócio e na **erradicação de estados ilegais representáveis**.

### Princípios Invioláveis

1. **Invariantes na Criação (Never-Invalid Principle):** Nenhuma entidade ou objeto de valor pode existir em estado inválido na memória da aplicação. A instanciação direta é privada ou restrita; a criação pública ocorre exclusivamente via métodos de fábrica seguros (`try_create` / `tryCreate`).
2. **Result Pattern em Vez de Exceções de Fluxo:** Erros de validação e violações de regras de negócio são valores de retorno esperados (`Result[T, E]`), e não exceções que desviam silenciosamente o fluxo de execução.
3. **Zero Vendor Lock-in no Domínio:** A camada de domínio é construída em linguagem pura (Pure Python / Pure TypeScript). É estritamente proibido acoplar entidades a ORMs (SQLAlchemy, Prisma, TypeORM), frameworks web (FastAPI, Express, NestJS) ou SDKs proprietários de provedores em nuvem.
4. **Alinhamento com Vertical Slice Architecture (VSA):** Cada fatia vertical (comando ou consulta) orquestra entidades e objetos de valor de forma coesa e independente, sem gerar camadas horizontais burocráticas ou acoplamento indireto entre módulos.

---

## 2. Objetos de Valor (Value Objects)

Um **Objeto de Valor (Value Object)** representa um elemento de domínio cuja identidade é determinada exclusivamente pelo conjunto de seus atributos e não por um identificador persistente.

### Características Canônicas

- **Imutabilidade Absoluta:** Uma vez instanciado, seus valores nunca podem ser alterados.
- **Auto-validação na Criação:** Suas regras intrínsecas são garantidas no momento da criação.
- **Igualdade por Valor:** Dois objetos com os mesmos valores de atributo são rigorosamente iguais e intercambiáveis.
- **Comportamento Rico:** Possui métodos puros que realizam cálculos ou transformações, gerando novas instâncias.

---

## 3. Entidades e Agregados com `try_create`

Uma **Entidade** possui uma identidade estável ao longo do tempo e de seu ciclo de vida. Um **Agregado** é um cluster de entidades e objetos de valor com um limite explícito de consistência transacional, governado por uma **Raiz de Agregado (Aggregate Root)**.

### O Padrão `try_create`

Para assegurar que nenhuma entidade nasça em estado inválido, o construtor padrão não é exposto para validações complexas. Em seu lugar, adota-se o método de fábrica seguro:

- **Assinatura:** `try_create(...) -> Result[Entidade, ErroDominio]` (Python) ou `tryCreate(...) -> Result<Entidade, ErroDominio>` (TypeScript).
- **Sem Efeitos Colaterais:** A fábrica valida todos os parâmetros e dependências de invariantes antes de alocar e retornar a instância encapsulada em um resultado de sucesso (`Ok`).
- **Mutações Protegidas:** Qualquer transição de estado interna da entidade é executada por métodos que também validam as invariantes pós-condição e retornam `Result`.

---

## 4. O Padrão Result (Result Pattern)

O padrão Result formaliza a dualidade determinística de uma operação que pode produzir um sucesso tipado ou uma falha de domínio tipada:

$$\text{Result}\langle T, E \rangle = \text{Ok}(T) \cup \text{Err}(E)$$

### Vantagens no Monólito VSA

- **Transparência Total de Contrato:** O chamador é explicitamente obrigado pelo sistema de tipos a tratar cenários de sucesso e falha.
- **Previsibilidade Operacional:** Elimina a necessidade de blocos `try/catch` para regras de negócio normais, reservando exceções exclusivamente para falhas catastróficas de infraestrutura (falha de rede, disco indisponível).
- **Composabilidade:** Facilita pipelines de execução sequenciais (`map`, `and_then`) dentro do Handler da fatia vertical.

---

## 5. Integração com Vertical Slice Architecture (VSA)

Na arquitetura por fatias verticais, cada feature vive em um diretório autocontido contendo seu Handler, Contrato (Request/Response) e Ponto de Integração.

```
fatias/
└── realizar_pagamento/
    ├── handler.py           # Orquestrador da fatia (Command Handler)
    ├── dto.py               # Contratos de entrada e saída
    ├── endpoint.py          # Adaptador HTTP / RPC
    └── domain/ (opcional)   # Entidades ou VOs específicos desta fatia
```

### Regras de Coexistência VSA + DDD

1. **Fatias Operam Como Orquestradores:** O Handler recebe o DTO de entrada, chama a fábrica `try_create` das entidades necessárias, invoca a operação de negócio e delega a persistência ao repositório ou adaptador de infraestrutura.
2. **Entidades Reutilizáveis no Domínio Compartilhado:** Entidades centrais do domínio e invariantes transversais residem em `compartilhado/dominio/`, sendo consumidas pelas fatias sem violar fronteiras modulares.
3. **Mapeamento Explícito nos Limites:** DTOs de entrada são mapeados para Objetos de Valor e Entidades; estados de Entidades são convertidos para DTOs de resposta. Nenhuma entidade de domínio vaza diretamente para o contrato público da API.

---

## 6. Zero Vendor Lock-in na Prática

A camada de domínio tático deve permanecer agnóstica a fornecedores e tecnologias externas:

| Camada | Permitido | Estritamente Proibido |
| :--- | :--- | :--- |
| **Domínio (Entities & VOs)** | Python puro (`dataclasses`, `typing`), TypeScript puro | SQLAlchemy, Pydantic (como modelo de domínio), Prisma, TypeORM, decorators de ORM |
| **Erros de Domínio** | Classes de dados simples, Enums | HTTPExceptions, dependências de status HTTP |
| **Persistência** | Interfaces/Portas puras (`Protocol`, `interface`) | Repositórios concretos acoplados a vendors |

A persistência é uma preocupação de infraestrutura. Os mapeadores de infraestrutura convertem o estado puro das entidades para esquemas relacionais ou documentos, garantindo que o núcleo permaneça imune a trocas de banco de dados ou frameworks.

---

## 7. Implementação Completa em Python

Abaixo encontra-se a implementação canônica, tipada e sem dependências externas em Python puro:

```python
from __future__ import annotations
from dataclasses import dataclass
from typing import Generic, TypeVar, Optional, List
import re

T = TypeVar("T")
E = TypeVar("E")


@dataclass(frozen=True)
class Result(Generic[T, E]):
    """Implementação canônica pura do padrão Result em Python."""
    _value: Optional[T]
    _error: Optional[E]
    _is_success: bool

    @classmethod
    def ok(cls, value: T) -> Result[T, E]:
        return cls(_value=value, _error=None, _is_success=True)

    @classmethod
    def fail(cls, error: E) -> Result[T, E]:
        return cls(_value=None, _error=error, _is_success=False)

    @property
    def is_ok(self) -> bool:
        return self._is_success

    @property
    def is_err(self) -> bool:
        return not self._is_success

    def value(self) -> T:
        if not self._is_success:
            raise ValueError(f"Não é possível obter valor de um Result.fail: {self._error}")
        return self._value  # type: ignore[return-value]

    def error(self) -> E:
        if self._is_success:
            raise ValueError("Não é possível obter erro de um Result.ok")
        return self._error  # type: ignore[return-value]


@dataclass(frozen=True)
class Dinheiro:
    """Value Object imutável que representa quantia monetária."""
    centavos: int
    moeda: str

    @classmethod
    def try_create(cls, valor_decimal: float, moeda: str = "BRL") -> Result[Dinheiro, str]:
        if valor_decimal < 0:
            return Result.fail("O valor monetário não pode ser negativo")
        if not moeda or len(moeda.strip()) != 3:
            return Result.fail("A moeda deve conter exatamente 3 caracteres ISO")
        
        centavos = int(round(valor_decimal * 100))
        return Result.ok(cls(centavos=centavos, moeda=moeda.upper().strip()))

    def somar(self, outro: Dinheiro) -> Result[Dinheiro, str]:
        if self.moeda != outro.moeda:
            return Result.fail(f"Moedas incompatíveis: {self.moeda} e {outro.moeda}")
        return Result.ok(Dinheiro(centavos=self.centavos + outro.centavos, moeda=self.moeda))


@dataclass
class ItemPedido:
    """Entidade filha pertencente ao agregado Pedido."""
    item_id: str
    nome_produto: str
    subtotal: Dinheiro


class Pedido:
    """Entidade raiz de agregado com proteção estrita de invariantes via try_create."""

    def __init__(self, pedido_id: str, cliente_id: str, itens: List[ItemPedido], total: Dinheiro):
        self._pedido_id = pedido_id
        self._cliente_id = cliente_id
        self._itens = list(itens)
        self._total = total
        self._status = "RASCUNHO"

    @classmethod
    def try_create(cls, pedido_id: str, cliente_id: str, itens_iniciais: List[ItemPedido]) -> Result[Pedido, str]:
        if not pedido_id or not pedido_id.strip():
            return Result.fail("Identificador do pedido é obrigatório")
        if not cliente_id or not cliente_id.strip():
            return Result.fail("Identificador do cliente é obrigatório")
        if not itens_iniciais:
            return Result.fail("O pedido deve possuir ao menos um item inicial")

        moeda_base = itens_iniciais[0].subtotal.moeda
        total_centavos = 0
        for item in itens_iniciais:
            if item.subtotal.moeda != moeda_base:
                return Result.fail("Todos os itens do pedido devem possuir a mesma moeda")
            total_centavos += item.subtotal.centavos

        total_vo = Dinheiro(centavos=total_centavos, moeda=moeda_base)
        instancia = cls(pedido_id.strip(), cliente_id.strip(), itens_iniciais, total_vo)
        return Result.ok(instancia)

    @property
    def id(self) -> str:
        return self._pedido_id

    @property
    def total(self) -> Dinheiro:
        return self._total

    @property
    def status(self) -> str:
        return self._status

    def adicionar_item(self, item: ItemPedido) -> Result[bool, str]:
        if self._status != "RASCUNHO":
            return Result.fail("Não é permitido adicionar itens a um pedido já finalizado")
        if item.subtotal.moeda != self._total.moeda:
            return Result.fail("Moeda do item diverge da moeda do pedido")

        self._itens.append(item)
        self._total = Dinheiro(centavos=self._total.centavos + item.subtotal.centavos, moeda=self._total.moeda)
        return Result.ok(True)
```

---

## 8. Implementação Completa em TypeScript

Abaixo encontra-se a implementação correspondente em TypeScript com tipagem estrita e imutabilidade estrutural:

```typescript
export type Result<T, E> =
  | { readonly success: true; readonly data: T }
  | { readonly success: false; readonly error: E };

export const Result = {
  ok<T, E = never>(data: T): Result<T, E> {
    return { success: true, data };
  },
  fail<E, T = never>(error: E): Result<T, E> {
    return { success: false, error };
  }
};

export class Email {
  readonly valor: string;

  private constructor(valor: string) {
    this.valor = valor;
  }

  static tryCreate(raw: string): Result<Email, string> {
    if (!raw || typeof raw !== "string") {
      return Result.fail("Endereço de e-mail é obrigatório");
    }
    const limpo = raw.trim().toLowerCase();
    const regexEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!regexEmail.test(limpo)) {
      return Result.fail(`Formato de e-mail inválido: ${raw}`);
    }
    return Result.ok(new Email(limpo));
  }

  equals(outro: Email): boolean {
    return this.valor === outro.valor;
  }
}

export interface UsuarioProps {
  readonly id: string;
  readonly nome: string;
  readonly email: Email;
  readonly ativo: boolean;
}

export class Usuario {
  readonly id: string;
  private _nome: string;
  private _email: Email;
  private _ativo: boolean;

  private constructor(props: UsuarioProps) {
    this.id = props.id;
    this._nome = props.nome;
    this._email = props.email;
    this._ativo = props.ativo;
  }

  static tryCreate(id: string, nome: string, email: Email): Result<Usuario, string> {
    if (!id || id.trim().length === 0) {
      return Result.fail("Identificador único de usuário é obrigatório");
    }
    if (!nome || nome.trim().length < 3) {
      return Result.fail("Nome deve conter no mínimo 3 caracteres");
    }
    return Result.ok(
      new Usuario({
        id: id.trim(),
        nome: nome.trim(),
        email,
        ativo: true
      })
    );
  }

  get nome(): string {
    return this._nome;
  }

  get email(): Email {
    return this._email;
  }

  get ativo(): boolean {
    return this._ativo;
  }

  desativar(): Result<boolean, string> {
    if (!this._ativo) {
      return Result.fail("Usuário já se encontra inativo");
    }
    this._ativo = false;
    return Result.ok(true);
  }
}
```

---

## 9. Matriz de Conformidade e Auditoria

Toda fatia vertical e componente de domínio do ecossistema AIDD passa pela validação determinística de portões de qualidade:

| Requisito Canônico | Validação Automatizada | Consequência da Violação |
| :--- | :--- | :--- |
| **Defesa de Invariantes** | Construtores privados ou protegidos; presença de `try_create` | Rejeição no Portão de Qualidade |
| **Result Pattern** | Ausência de `raise` de regras de negócio em métodos de domínio | Bloqueio em CI e auditoria estática |
| **Isolamento de Fornecedor** | Proibição de imports de ORMs ou frameworks no módulo `dominio/` | Reprovação por `G_COMPONENTE_AGNOSTICO` |
| **Coesão VSA** | Resolução atômica de fatias sem acoplamento horizontal direto | Verificação por barreira de junção VSA |
