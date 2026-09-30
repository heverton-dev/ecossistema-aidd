# -*- coding: utf-8 -*-
"""
Analisador de Grafo DAG e Detector de Ciclos para aidd-tickets (Ticket 4 / D8 / DoD 3).
Implementa o algoritmo de ordenação topológica de Kahn para garantir que não haja
dependências circulares (deadlocks) entre os tickets de implementação.
"""

from __future__ import annotations

from collections import defaultdict, deque
from typing import List, Dict, Any, Tuple


def ordenar_topologicamente_kahn(tickets: List[Dict[str, Any]]) -> Tuple[bool, List[str], str]:
    """
    Ordena tickets topologicamente respeitando 'blocked_by'.
    Retorna (valido, ordem_ids, mensagem_erro).
    Se houver ciclo, retorna (False, [], "Ciclo de dependência detectado...").
    """
    grau_entrada = defaultdict(int)
    adjacencia = defaultdict(list)
    todos_ids = set()

    for t in tickets:
        tid = t["id"]
        todos_ids.add(tid)
        if tid not in grau_entrada:
            grau_entrada[tid] = 0

    for t in tickets:
        tid = t["id"]
        bloqueadores = t.get("blocked_by", [])
        for blocker in bloqueadores:
            if blocker in todos_ids:
                adjacencia[blocker].append(tid)
                grau_entrada[tid] += 1

    # Fila com nós com grau de entrada zero (podem executar imediatamente)
    fila = deque([tid for tid in todos_ids if grau_entrada[tid] == 0])
    ordem = []

    while fila:
        u = fila.popleft()
        ordem.append(u)
        for v in adjacencia[u]:
            grau_entrada[v] -= 1
            if grau_entrada[v] == 0:
                fila.append(v)

    if len(ordem) != len(todos_ids):
        nos_em_ciclo = [tid for tid in todos_ids if tid not in ordem]
        return False, [], f"Ciclo de dependência detectado (deadlock) envolvendo tickets: {', '.join(sorted(nos_em_ciclo))}"

    return True, ordem, ""
