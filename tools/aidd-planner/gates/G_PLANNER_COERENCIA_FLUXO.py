# -*- coding: utf-8 -*-
"""
G_PLANNER_COERENCIA_FLUXO — Valida a coerência do payload específico com o fluxo alvo selecionado.

Verifica:
  1. Coerência entre meta.fluxo_alvo e payload_especifico_fluxo
  2. Validação profunda dos campos específicos:
     - Fluxo 01 (generator): fatias_vsa e casos_teste_tdd presentes e estruturados
     - Fluxo 02 (factory): ferramentas_opensource e fatias_integracao presentes e estruturados
     - Fluxo 03 (bridge): diretorio_lowcode e mapeamento_banco presentes e estruturados
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
        print(f"[G_PLANNER_COERENCIA_FLUXO] ERRO: Arquivo de plano não encontrado: '{caminho}'", file=sys.stderr)
        return 1

    try:
        with open(caminho, "r", encoding="utf-8") as f:
            plano = json.load(f)
    except Exception as exc:
        print(f"[G_PLANNER_COERENCIA_FLUXO] ERRO: Falha ao ler JSON: {exc}", file=sys.stderr)
        return 1

    fluxo = plano.get("meta", {}).get("fluxo_alvo")
    payload = plano.get("payload_especifico_fluxo")
    if not isinstance(payload, dict):
        print("[G_PLANNER_COERENCIA_FLUXO] FALHA: 'payload_especifico_fluxo' ausente ou inválido.", file=sys.stderr)
        return 1

    erros = []
    if fluxo == "fluxo_01_generator":
        fatias = payload.get("fatias_vsa", [])
        if not isinstance(fatias, list) or len(fatias) == 0:
            erros.append("Fluxo 01 exige lista 'fatias_vsa' com pelo menos 1 fatia vertical.")
        else:
            for idx, fatia in enumerate(fatias):
                if not fatia.get("nome"):
                    erros.append(f"fatias_vsa[{idx}] sem nome.")
                if not fatia.get("endpoints") or not isinstance(fatia.get("endpoints"), list):
                    erros.append(f"fatias_vsa[{idx}] sem lista de endpoints.")

        casos_tdd = payload.get("casos_teste_tdd", [])
        if not isinstance(casos_tdd, list) or len(casos_tdd) == 0:
            erros.append("Fluxo 01 exige 'casos_teste_tdd' para orientar o ciclo Red-Green.")
        else:
            for idx, tdd in enumerate(casos_tdd):
                if not tdd.get("nome") or not tdd.get("red_expectation") or not tdd.get("green_assertion"):
                    erros.append(f"casos_teste_tdd[{idx}] incompleto (exige nome, red_expectation e green_assertion).")

    elif fluxo == "fluxo_02_factory":
        ferramentas = payload.get("ferramentas_opensource", [])
        if not isinstance(ferramentas, list) or len(ferramentas) == 0:
            erros.append("Fluxo 02 exige 'ferramentas_opensource' com catálogo de serviços.")
        else:
            for idx, f in enumerate(ferramentas):
                if not f.get("nome") or not f.get("imagem_docker"):
                    erros.append(f"ferramentas_opensource[{idx}] sem nome ou imagem_docker.")

        integracao = payload.get("fatias_integracao", [])
        if not isinstance(integracao, list) or len(integracao) == 0:
            erros.append("Fluxo 02 exige 'fatias_integracao' para o gateway VSA.")

    elif fluxo == "fluxo_03_bridge":
        if not payload.get("diretorio_lowcode"):
            erros.append("Fluxo 03 exige 'diretorio_lowcode'.")
        mapeamento = payload.get("mapeamento_banco", [])
        if not isinstance(mapeamento, list) or len(mapeamento) == 0:
            erros.append("Fluxo 03 exige 'mapeamento_banco' para desacoplamento de banco.")

    else:
        erros.append(f"Fluxo desconhecido ou não suportado: '{fluxo}'.")

    if erros:
        print(f"[G_PLANNER_COERENCIA_FLUXO] FALHA: {len(erros)} inconsistência(s) de fluxo:", file=sys.stderr)
        for e in erros:
            print(f"  [X] {e}", file=sys.stderr)
        return 1

    print(f"[G_PLANNER_COERENCIA_FLUXO] PASS: Payload do {fluxo} 100% coerente e validado.")
    return 0


if __name__ == "__main__":
    alvo = sys.argv[1] if len(sys.argv) > 1 else "."
    sys.exit(main(alvo))
