# -*- coding: utf-8 -*-
"""
Ticket 13-A: Derivação de bounded contexts a partir da spec.
Verifica que o planner deriva ddd_bounded_contexts, entidades, atributos
e fatias VSA a partir dos contratos tipados e invariantes da spec em vez
de colapsar tudo no módulo genérico 'nucleo/RegistroPrincipal'.
"""
import os
import sys
from pathlib import Path

import pytest

_PLANNER_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PLANNER_DIR not in sys.path:
    sys.path.insert(0, _PLANNER_DIR)

from src.core_planner import intake, planner_engine


def test_extrair_contextos_da_spec(tmp_path):
    spec_md = """# Spec

## 1. Context
Sistema de vendas.

### Visual Direction
- tom: sóbrio
- cor_primaria: #0F766E
- referencias: Linear
- publico: atendentes

## 2. Contracts & Typed Interfaces

```ts
interface Pedido {
    id: string;
    clienteId: string;
    total: number;
    status: "aberto" | "pago" | "cancelado";
}

interface Cliente {
    id: string;
    nome: string;
    email: string;
}
```

## 3. Invariants & Business Rules

1. Todo pedido pertence a exatamente um cliente.
2. O total do pedido é a soma dos itens e nunca é negativo.
3. O email do cliente deve ser único e válido.

## 4. Binary Acceptance Criteria
- GET /pedidos devolve 200.

## 5. Failure & Degradation Modes
- Banco indisponivel.
"""
    intake_dir = tmp_path / ".aidd" / "intake"
    intake_dir.mkdir(parents=True)
    (intake_dir / "spec.md").write_text(spec_md, encoding="utf-8")

    contextos = intake.extrair_contextos_da_spec(str(tmp_path))
    assert len(contextos) == 2
    modulos = [c["modulo"] for c in contextos]
    assert "pedidos" in modulos or "pedido" in modulos
    assert "clientes" in modulos or "cliente" in modulos

    # Verifica entidades e atributos extraídos
    pedido_ctx = next(c for c in contextos if c["modulo"] in ("pedidos", "pedido"))
    assert len(pedido_ctx["entidades"]) >= 1
    ent = pedido_ctx["entidades"][0]
    assert ent["nome"] == "Pedido"
    assert "total" in ent["atributos"]
    assert "status" in ent["atributos"]


def test_gerar_template_plano_com_contextos_spec():
    contextos_spec = [
        {
            "modulo": "pedidos",
            "descricao": "Contexto de Pedidos",
            "entidades": [
                {
                    "nome": "Pedido",
                    "atributos": {"id": "string", "clienteId": "string", "total": "number"},
                    "regras_invariantes": ["Todo pedido pertence a exatamente um cliente."]
                }
            ]
        },
        {
            "modulo": "clientes",
            "descricao": "Contexto de Clientes",
            "entidades": [
                {
                    "nome": "Cliente",
                    "atributos": {"id": "string", "nome": "string", "email": "string"},
                    "regras_invariantes": ["O email do cliente deve ser único."]
                }
            ]
        }
    ]

    plano = planner_engine.gerar_template_plano(
        fluxo_alvo="fluxo_01_generator",
        projeto_nome="Controle de Vendas",
        slug="controle-vendas",
        descricao="Sistema de vendas e pedidos para pequenos comercios",
        dominio="vendas",
        contextos_spec=contextos_spec
    )

    # Não deve ter o 'nucleo' genérico quando a spec define contextos específicos
    modulos = [c["modulo"] for c in plano["ddd_bounded_contexts"]]
    assert "pedidos" in modulos
    assert "clientes" in modulos
    assert "nucleo" not in modulos

    # As fatias VSA do fluxo 01 devem acompanhar os módulos da spec
    fatias = [f["nome"] for f in plano["payload_especifico_fluxo"]["fatias_vsa"]]
    assert "pedidos" in fatias
    assert "clientes" in fatias
    assert "nucleo" not in fatias

    # O plano gerado deve validar perfeitamente contra o schema/validador
    valido, erros = planner_engine.validar_plano(plano)
    assert valido, f"Erros de validação do plano: {erros}"
