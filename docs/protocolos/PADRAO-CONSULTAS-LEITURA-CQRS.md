# Manual Canônico: Leitura Otimizada e CQRS para Fatias Verticais

> **Status:** Canônico e Obrigatório  
> **Ecossistema:** AIDD (AI-Driven Development)  
> **Escopo:** Segregação de Responsabilidade entre Comando e Consulta (CQRS) no Monólito Modular VSA  
> **Diretiva de Integridade:** Zero Stubs, Zero Vendor Lock-in, Alta Performance, Projeções Otimizadas.

---

## 1. Visão Geral e Fundamentos do CQRS no VSA

Na Arquitetura por Fatias Verticais (Vertical Slice Architecture - VSA) adotada pelo ecossistema AIDD, as operações do sistema são segregadas em duas categorias de natureza e propósitos fundamentalmente distintos:

1. **Comandos (Commands / Escrita):**
   - Alteram o estado persistente do sistema.
   - Exigem validação estrita de invariantes de negócio, transações ACID e orquestração de Entidades/Agregados via métodos de fábrica seguros (`try_create`).
   - Retornam status de execução (`Result[T, E]`).

2. **Consultas (Queries / Leitura):**
   - Apenas inspecionam o estado sem produzir efeitos colaterais.
   - **Não passam por Entidades de Domínio ou Use Cases de negócio.**
   - O objetivo é extrair dados no formato exato demandado pelo consumidor (UI ou cliente de API), com mínima latência e sem alocações desnecessárias na memória.

```
       [ REQUISIÇÃO CLIENTE ]
                 |
      +----------+----------+
      |                     |
[ COMANDO (POST/PUT) ] [ CONSULTA (GET) ]
      |                     |
  [ Handler ]           [ Handler ]
      |                     |
[ Entidade/Agregado ]       | (sem carregar agregados)
      |                     |
[ Repositório / WAL ]   [ Leitura Direta SQL / WAL ]
                            |
                     [ DTO / Schema Projeção ]
```

---

## 2. Princípios Invioláveis da Camada de Leitura

1. **Proibição de Agregados na Leitura:** É estritamente proibido carregar entidades ou instanciar agregados de negócio para rotas de leitura (queries). Carregar entidades completas apenas para descartar 90% dos campos na serialização gera overhead desnecessário de I/O e CPU.
2. **Projeção em DTO Direta:** A consulta em SQL projeta diretamente nas colunas requeridas pelo DTO (Data Transfer Object) ou Schema de saída.
3. **Leitura Direta SQL em SQLite WAL:** No backend em Python puro do ecossistema, as consultas utilizam conexões dedicadas em modo leitura sobre o banco SQLite em modo Write-Ahead Logging (WAL). O modo WAL permite múltiplos leitores simultâneos sem bloquear gravadores.
4. **Sem Abstrações Burocráticas:** Consultas simples não precisam de camadas intermediárias de repositório; o handler da fatia de leitura pode executar a consulta SQL diretamente contra o banco de dados.

---

## 3. Implementação de Referência no Backend (Python Puro + SQLite WAL)

Abaixo, o padrão canônico para uma fatia vertical de consulta (`features/relatorios/obter_resumo_vendas.py`):

```python
# -*- coding: utf-8 -*-
"""Fatia Vertical de Consulta: Obter Resumo de Vendas."""
from dataclasses import dataclass
from typing import List, Optional
import sqlite3


@dataclass(frozen=True)
class ItemVendaDTO:
    id: str
    cliente_nome: str
    total_centavos: int
    data_iso: str


@dataclass(frozen=True)
class ResumoVendasDTO:
    total_pedidos: int
    valor_total_centavos: int
    ultimos_itens: List[ItemVendaDTO]


def executar_consulta_resumo_vendas(
    db_path: str, limite: int = 10
) -> ResumoVendasDTO:
    """Executa leitura direta SQL otimizada sem carregar agregados ou entidades."""
    # Conexão em modo leitura direta (SQLite WAL)
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # Consulta agregada ultra rápida
        cursor.execute("""
            SELECT 
                COUNT(*) AS total_pedidos,
                COALESCE(SUM(total_centavos), 0) AS valor_total
            FROM pedidos 
            WHERE status = 'CONCLUIDO';
        """)
        agg = cursor.fetchone()

        # Projeção dos últimos itens formatados diretamente para o DTO
        cursor.execute("""
            SELECT id, cliente_nome, total_centavos, criado_em 
            FROM pedidos 
            WHERE status = 'CONCLUIDO' 
            ORDER BY criado_em DESC 
            LIMIT ?;
        """, (limite,))
        rows = cursor.fetchall()

        itens = [
            ItemVendaDTO(
                id=str(r["id"]),
                cliente_nome=str(r["cliente_nome"]),
                total_centavos=int(r["total_centavos"]),
                data_iso=str(r["criado_em"]),
            )
            for r in rows
        ]

        return ResumoVendasDTO(
            total_pedidos=int(agg["total_pedidos"]),
            valor_total_centavos=int(agg["valor_total"]),
            ultimos_itens=itens,
        )
    finally:
        cursor.close()
        conn.close()
```

---

## 4. Contratos de Projeção no Frontend (TypeScript + Next.js)

Na camada frontend (Next.js), o contrato da projeção é consumido diretamente em componentes React com tipagem estrita:

```typescript
// types/resumo-vendas.dto.ts
export interface ItemVendaDTO {
  id: string;
  cliente_nome: string;
  total_centavos: number;
  data_iso: string;
}

export interface ResumoVendasDTO {
  total_pedidos: number;
  valor_total_centavos: number;
  ultimos_itens: ItemVendaDTO[];
}
```

---

## 5. Diretrizes de Performance: SQLite WAL

- **Modo WAL:** Sempre ativar `PRAGMA journal_mode=WAL;` na inicialização do banco de dados.
- **Conexões Read-Only:** Utilizar `mode=ro` na URI SQLite para leituras, evitando bloqueios na thread principal.
- **Mapeamento de Índices:** Todas as colunas presentes em cláusulas `WHERE`, `ORDER BY` ou `JOIN` de consultas frequentes devem possuir índices compostos cobrindo a query (Covering Indexes).
- **Sem N+1 Queries:** Consultas em lote devem agregar dados em uma única query SQL usando `GROUP BY` ou subqueries, eliminando loops de chamadas ao banco.
