# -*- coding: utf-8 -*-
"""
G_PLANNER_SINE_QUA_NON — Valida a conformidade da Lei Inviolável 10 (Quarteto Sine Qua Non Dinâmico).

Verifica:
  1. Presença da chave quarteto_sine_qua_non
  2. Presença e ativação (ativo: true) dos 4 pilares:
     - Swagger Studio: /docs (ou alias legado /swagger)
     - Webhook Studio: /webhooks (ou /api/webhooks)
     - MCP Studio: /mcp (ou /api/mcp)
     - Guia do Utilizador: /docs/guia (ou /guia)
  3. Existência de ferramentas MCP e eventos de Webhooks mapeados no plano
"""
import json
import os
import sys

_PLANNER_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ECOSSISTEMA_ROOT = os.path.dirname(_PLANNER_ROOT)

if _PLANNER_ROOT not in sys.path:
    sys.path.insert(0, _PLANNER_ROOT)
if _ECOSSISTEMA_ROOT not in sys.path:
    sys.path.insert(0, _ECOSSISTEMA_ROOT)


def resolver_caminho_plano(alvo: str) -> str:
    if os.path.isfile(alvo):
        return alvo
    for c in ["PLANNER.json", "PRE-PLANO.json", "planner.json"]:
        p = os.path.join(alvo, c)
        if os.path.isfile(p):
            return p
    return os.path.join(alvo, "PLANNER.json")


def main(alvo_arg: str = ".") -> int:
    caminho = resolver_caminho_plano(alvo_arg)
    if not os.path.isfile(caminho):
        print(f"[G_PLANNER_SINE_QUA_NON] ERRO: Arquivo de plano não encontrado: '{caminho}'", file=sys.stderr)
        return 1

    try:
        with open(caminho, "r", encoding="utf-8") as f:
            plano = json.load(f)
    except Exception as exc:
        print(f"[G_PLANNER_SINE_QUA_NON] ERRO: Falha ao ler JSON: {exc}", file=sys.stderr)
        return 1

    erros = []
    quarteto = plano.get("quarteto_sine_qua_non")
    if not isinstance(quarteto, dict):
        print("[G_PLANNER_SINE_QUA_NON] FALHA: 'quarteto_sine_qua_non' ausente ou inválido.", file=sys.stderr)
        return 1

    pilares = ["swagger", "webhooks", "mcp", "guia"]
    for pilar in pilares:
        cfg = quarteto.get(pilar)
        # Retrocompatibilidade: aceitar chave 'docs' como alias legado para 'guia'
        if pilar == "guia" and not isinstance(cfg, dict) and isinstance(quarteto.get("docs"), dict):
            cfg = quarteto.get("docs")
        if not isinstance(cfg, dict):
            erros.append(f"Pilar '{pilar}' ausente no Quarteto Sine Qua Non.")
            continue
        if cfg.get("ativo") is not True:
            erros.append(f"Pilar '{pilar}' deve possuir 'ativo: true'.")

    # Verificações de robustez dos pilares
    webhooks = quarteto.get("webhooks", {})
    eventos = webhooks.get("eventos_suportados", [])
    if not isinstance(eventos, list) or len(eventos) == 0:
        erros.append("Pilar 'webhooks' deve declarar ao menos 1 evento suportado em 'eventos_suportados'.")

    mcp = quarteto.get("mcp", {})
    ferramentas = mcp.get("ferramentas_expostas", [])
    if not isinstance(ferramentas, list) or len(ferramentas) == 0:
        erros.append("Pilar 'mcp' deve declarar ao menos 1 ferramenta exposta em 'ferramentas_expostas'.")

    guia = quarteto.get("guia") if isinstance(quarteto.get("guia"), dict) else quarteto.get("docs", {})
    if guia.get("guia_usuario") is not True:
        erros.append("Pilar 'guia' deve declarar 'guia_usuario: true'.")

    if erros:
        print(f"[G_PLANNER_SINE_QUA_NON] FALHA: {len(erros)} violação(ões) do Quarteto Sine Qua Non:", file=sys.stderr)
        for e in erros:
            print(f"  [X] {e}", file=sys.stderr)
        return 1

    print(f"[G_PLANNER_SINE_QUA_NON] PASS: Quarteto Sine Qua Non 100% planejado e em conformidade.")
    return 0


if __name__ == "__main__":
    alvo = sys.argv[1] if len(sys.argv) > 1 else "."
    sys.exit(main(alvo))
