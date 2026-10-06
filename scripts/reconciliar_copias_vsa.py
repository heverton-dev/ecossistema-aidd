# -*- coding: utf-8 -*-
"""
Relatório determinístico de divergência entre tools/ e modulos/ (ciclo-03 VSA, Ticket 1).

Para cada ferramenta de tools/aidd-* compara os arquivos versionados com a pasta canônica
em modulos/ (decisão A: modulos/ é a cópia canônica). Ignora CRLF e pastas de cache.
Com --exigir-zero, sai com 1 se houver arquivo divergente ou só em tools/.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

RAIZ_PADRAO = Path(__file__).resolve().parents[1]
SAIDA_PADRAO = "docs/auditoria/modularizacao-vsa/ciclo-03/DIVERGENCIAS-TOOLS-MODULOS.json"

MAPA_CANONICO = {
    "aidd-forge": "modulos/01-governanca-e-qualidade/core/aidd-forge",
    "aidd-planner": "modulos/01-governanca-e-qualidade/core/aidd-planner",
    "aidd-pure": "modulos/02-triade-motores/fluxo-01-pure/core/aidd-pure",
    "aidd-open": "modulos/02-triade-motores/fluxo-02-open/core/aidd-open",
    "aidd-freedom": "modulos/02-triade-motores/fluxo-03-freedom/core/aidd-freedom",
    "aidd-enterprise": "modulos/03-plataforma-e-entrega/blindagem-enterprise/aidd-enterprise",
    "aidd-master": "modulos/03-plataforma-e-entrega/fatiamento-master/aidd-master",
    "aidd-ops": "modulos/03-plataforma-e-entrega/operacoes-ops/aidd-ops",
}

PASTAS_IGNORADAS = {"__pycache__", ".pytest_cache", "node_modules"}
SUFIXOS_IGNORADOS = (".db-wal", ".db-shm", ".pyc")


def _ignorado(rel: str) -> bool:
    partes = rel.split("/")
    return any(p in PASTAS_IGNORADAS for p in partes) or rel.endswith(SUFIXOS_IGNORADOS)


def _arquivos_versionados(raiz: Path, prefixo: str) -> set[str]:
    """Caminhos relativos ao prefixo, vindos do índice do git (tracked)."""
    proc = subprocess.run(
        ["git", "ls-files", "-z", "--", prefixo],
        cwd=str(raiz), capture_output=True, check=True,
    )
    base = prefixo.rstrip("/") + "/"
    arquivos = set()
    for item in proc.stdout.decode("utf-8", errors="replace").split("\0"):
        if item.startswith(base):
            rel = item[len(base):]
            if not _ignorado(rel):
                arquivos.add(rel)
    return arquivos


def _conteudo_normalizado(caminho: Path) -> bytes | None:
    try:
        return caminho.read_bytes().replace(b"\r\n", b"\n")
    except OSError:
        return None


def comparar(raiz: Path) -> dict:
    ferramentas = {}
    for ferramenta, destino in MAPA_CANONICO.items():
        origem = f"tools/{ferramenta}"
        lado_tools = _arquivos_versionados(raiz, origem)
        lado_modulos = _arquivos_versionados(raiz, destino)
        divergentes, identicos = [], 0
        for rel in sorted(lado_tools & lado_modulos):
            if _conteudo_normalizado(raiz / origem / rel) == _conteudo_normalizado(raiz / destino / rel):
                identicos += 1
            else:
                divergentes.append(rel)
        ferramentas[ferramenta] = {
            "origem": origem,
            "destino": destino,
            "identicos": identicos,
            "divergentes": divergentes,
            "so_tools": sorted(lado_tools - lado_modulos),
            "so_modulos": sorted(lado_modulos - lado_tools),
        }
    totais = {
        chave: sum(len(f[chave]) for f in ferramentas.values())
        for chave in ("divergentes", "so_tools", "so_modulos")
    }
    totais["identicos"] = sum(f["identicos"] for f in ferramentas.values())
    return {"ferramentas": ferramentas, "totais": totais}


def _linha_base_anterior(saida: Path):
    try:
        return json.loads(saida.read_text(encoding="utf-8")).get("linha_base_testes_passando")
    except (OSError, ValueError):
        return None


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raiz", default=str(RAIZ_PADRAO))
    parser.add_argument("--saida", default=None, help=f"JSON de saída (padrão: <raiz>/{SAIDA_PADRAO})")
    parser.add_argument("--exigir-zero", action="store_true",
                        help="exit 1 se houver arquivo divergente ou só em tools/")
    parser.add_argument("--linha-base-testes", type=int, default=None,
                        help="total de testes passando na bateria completa (linha de base do ciclo)")
    args = parser.parse_args(argv)

    raiz = Path(args.raiz).resolve()
    saida = Path(args.saida) if args.saida else raiz / SAIDA_PADRAO

    relatorio = comparar(raiz)
    linha_base = args.linha_base_testes if args.linha_base_testes is not None else _linha_base_anterior(saida)
    relatorio["linha_base_testes_passando"] = linha_base

    saida.parent.mkdir(parents=True, exist_ok=True)
    with open(saida, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(relatorio, fh, ensure_ascii=False, indent=2)
        fh.write("\n")

    pendentes = []
    for ferramenta, dados in relatorio["ferramentas"].items():
        for rel in dados["divergentes"]:
            pendentes.append(f"  [DIVERGENTE] {ferramenta}/{rel}")
        for rel in dados["so_tools"]:
            pendentes.append(f"  [SO_TOOLS]   {ferramenta}/{rel}")

    t = relatorio["totais"]
    print(f"[reconciliar] identicos={t['identicos']} divergentes={t['divergentes']} "
          f"so_tools={t['so_tools']} so_modulos={t['so_modulos']} -> {saida}")
    if pendentes:
        print("\n".join(pendentes))
    if args.exigir_zero and pendentes:
        print(f"[FALHA] {len(pendentes)} arquivo(s) sem reconciliar entre tools/ e modulos/.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
