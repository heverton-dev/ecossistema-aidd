# Padrão Arquitetural: VSA Light-Lane (Query Slices)

> **Status:** Homologado Canônico  
> **Camada:** Software Architecture & Vertical Slice Architecture (VSA)  
> **Referência:** Monólito Modular AIDD (Padrão CTT)

---

## 1. Princípio Arquitetural (CQRS Pragmático)

Na Vertical Slice Architecture (VSA), cada funcionalidade é uma fatia vertical autônoma. Entretanto, operações de **Escrita (Commands)** e operações de **Leitura (Queries)** possuem naturezas fundamentalmente distintas:

| Dimensão | Command Slices (Mutação) | Query Slices / Light-Lane (Leitura) |
| :--- | :--- | :--- |
| **Operação** | INSERT, UPDATE, DELETE, Side-effects | SELECT, Lookups, Agregações, Filtros |
| **Mecanismo** | Railway Oriented (`Result[Ok, Err]`) estrito | Retorno direto de DTOs / Schemas Pydantic |
| **Transacionalidade**| Transações com lock e rollback | Conexões read-only ou queries parametrizadas |
| **Caching** | Invalidação de cache | `ReadModelCache` (Stale-While-Revalidate) |
| **Overhead** | Completo (Command, Handler, Domain Rules) | Mínimo (Query Function direta -> DTO) |

---

## 2. A Via Rápida (Light-Lane)

Para evitar a proliferação desnecessária de arquivos e boilerplate em consultas simples (como listar opções, ler perfis ou consultar dados cadastrais), adota-se a **Light-Lane**:

1. **Eliminação de Domain Services Ociosos:** Uma consulta read-only que apenas projeta dados do banco para o cliente não necessita de um Domain Service intermediário.
2. **DTOs Diretos:** Repositórios ou handlers de leitura retornam schemas de apresentação diretamente a partir de SQL parametrizado (`SELECT ... WHERE ...`), sem construir entidades de domínio complexas.
3. **Resiliência e Cache:** Consultas de alto throughput utilizam o `ReadModelCache` nativo (`src/core/cqrs.py`), assegurando resposta em submilissegundos com revalidação assíncrona em background.

---

## 3. Exemplo Prático de Implementação

### Estrutura de uma Fatia com Light-Lane:
```text
src/features/catalogo/
├── commands/               # Mutações (Railway estrito)
│   ├── criar_produto.py
│   └── atualizar_preco.py
├── queries/                # Light-Lane (Consultas diretas)
│   ├── listar_produtos.py  # QuerySlice direta -> Lista de DTOs
│   └── obter_detalhe.py
└── router.py               # Endpoints REST e MCP
```

### Código de uma Query Slice (`queries/listar_produtos.py`):
```python
from typing import list
from pydantic import BaseModel
from src.core.cqrs import QuerySlice, read_model
from src.core.database import get_db

class ProdutoDTO(BaseModel):
    id: str
    nome: str
    preco: float

def listar_produtos_query(categoria: str | None = None) -> list[ProdutoDTO]:
    cache_key = f"produtos:cat:{categoria or 'todos'}"
    
    def _fetch():
        with get_db() as db:
            if categoria:
                rows = db.execute("SELECT id, nome, preco FROM produtos WHERE categoria = ?", (categoria,)).fetchall()
            else:
                rows = db.execute("SELECT id, nome, preco FROM produtos").fetchall()
            return [ProdutoDTO(id=r[0], nome=r[1], preco=r[2]) for r in rows]

    return QuerySlice.execute_query(_fetch, cache_key=cache_key, ttl=60)
```

---

## 4. Invariantes de Governança

1. **Zero Queries Não Parametrizadas:** Toda query Light-Lane DEVE usar queries parametrizadas (anti-SQL Injection).
2. **Isolamento VSA Preservado:** Uma Query Slice jamais importa repositórios ou queries de outra fatia.
3. **Imutabilidade de DTO:** DTOs de leitura são estritamente para visualização e contratos OpenAPI/MCP.
