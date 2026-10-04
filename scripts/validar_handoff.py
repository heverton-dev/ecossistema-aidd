# -*- coding: utf-8 -*-
"""
Validador de contratos de handoff entre etapas do pipeline.
"""
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List


def _calcular_sha256(caminho: Path) -> str:
    h = hashlib.sha256()
    try:
        with open(caminho, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
    except Exception:
        return ""
    return h.hexdigest()


def validar_handoff(handoff_path: str) -> bool:
    try:
        p = Path(handoff_path)
        if not p.exists():
            return False
        with open(p, "r", encoding="utf-8") as f:
            dados = json.load(f)

        # 1. Contrato C1 (forge -> planner)
        if "projeto_dir" in dados and "git" in dados and "leis_e_guardas" in dados:
            git_info = dados.get("git")
            if not isinstance(git_info, dict) or git_info.get("inicializado") is not True:
                return False
            commit_inicial = git_info.get("commit_inicial")
            if not commit_inicial or not isinstance(commit_inicial, str):
                return False
            deps = dados.get("dependencias")
            if not isinstance(deps, list) or not deps:
                return False
            leis = dados.get("leis_e_guardas")
            if not isinstance(leis, list) or not leis:
                return False
            for lei in leis:
                if not isinstance(lei, dict) or not lei.get("sha256") or not lei.get("gate"):
                    return False
            almox = dados.get("almoxarifado")
            if not isinstance(almox, dict) or not almox.get("catalogo_sha256"):
                return False
            return True

        # 2. Contrato C2 (planner -> engine)
        if "fluxo_alvo" in dados and "tickets" in dados and "perfil_app" in dados:
            tickets = dados.get("tickets")
            if not isinstance(tickets, list) or not tickets:
                return False
            for t in tickets:
                if not isinstance(t, dict) or not t.get("ferramenta_destino") or not t.get("id"):
                    return False
            quarteto = dados.get("quarteto_sine_qua_non")
            if not isinstance(quarteto, dict):
                return False
            return True

        # 3. Contrato C3 (engine -> master)
        if "origem_engine" in dados and "slices_geradas" in dados and "testes_executados" in dados:
            slices = dados.get("slices_geradas")
            if not isinstance(slices, list) or not slices:
                return False
            for sl in slices:
                if not isinstance(sl, dict) or not sl.get("caminho_src") or not sl.get("sha256_arvore"):
                    return False
            testes = dados.get("testes_executados")
            if not isinstance(testes, dict) or testes.get("total", 0) <= 0:
                return False
            if testes.get("falharam", 0) != 0:
                return False
            return True

        # 4. Contrato C4 (master -> enterprise)
        if "quarteto" in dados and "servidor_sobe" in dados:
            servidor = dados.get("servidor_sobe")
            if not isinstance(servidor, dict) or not servidor.get("log_subida") or not servidor.get("porta"):
                return False
            quarteto = dados.get("quarteto")
            if not isinstance(quarteto, list) or len(quarteto) < 4:
                return False
            for q in quarteto:
                status = q.get("status_http_medido")
                if not isinstance(status, (int, float)) or status < 200 or status > 399:
                    return False
            return True

        # 5. Contrato C5 (enterprise -> ops)
        if "registry" in dados and "selo_sha256" in dados and "drift" in dados:
            reg = dados.get("registry")
            if not isinstance(reg, dict) or not reg.get("sha256") or not reg.get("caminho"):
                return False
            selo = dados.get("selo_sha256")
            if not isinstance(selo, str) or len(selo) != 64:
                return False
            drift = dados.get("drift")
            if not isinstance(drift, dict) or drift.get("verificado") is not True or drift.get("exit_code") != 0:
                return False
            return True

        # 6. Contrato genérico / teste unitário (Ticket 7)
        servidor_sobe = dados.get("servidor_sobe")
        if servidor_sobe is not True:
            return False

        produzido_por = dados.get("produzido_por")
        projetado_por = dados.get("projetado_por")
        if not produzido_por or not isinstance(produzido_por, str):
            return False
        if not projetado_por or not isinstance(projetado_por, str):
            return False
        if produzido_por != projetado_por:
            return False

        slice_path = dados.get("slice_path")
        if not slice_path:
            return False
        if not Path(slice_path).exists():
            return False

        evidencias = dados.get("evidencias", [])
        if not isinstance(evidencias, list) or not evidencias:
            return False
        for ev in evidencias:
            caminho_ev = ev.get("caminho")
            if not caminho_ev:
                return False
            p_ev = Path(caminho_ev)
            if not p_ev.exists():
                return False
            sha_esperado = ev.get("sha256")
            if not sha_esperado:
                return False
            sha_calculado = _calcular_sha256(p_ev)
            if sha_calculado != sha_esperado:
                return False
            http_status = ev.get("http_status_medido")
            if http_status is None:
                return False
            if not isinstance(http_status, (int, float)):
                return False

        log_erros = dados.get("log_erros", [])
        if log_erros:
            return False

        return True
    except Exception:
        return False


def main():
    if len(sys.argv) < 2:
        print("Uso: validar_handoff.py <caminho_do_handoff.json>", file=sys.stderr)
        sys.exit(2)
    ok = validar_handoff(sys.argv[1])
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
