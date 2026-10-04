# -*- coding: utf-8 -*-
"""
Analisador determinístico de arquivos duplicados no ecossistema AIDD (Ticket 19 — D15 / DoD 8).

Lê os blobs do repositório (via git ls-tree HEAD e filesystem), ignora harnesses e
arquivos vazios, e aponta cópias de peças do catálogo dentro de tools/.
"""

import argparse
import hashlib
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

PASTAS_IGNORADAS = {
    ".git", ".claude", ".cursor", ".agent", ".agents", ".gemini", ".vscode",
    ".idea", "__pycache__", "node_modules", ".pytest_cache", ".hypothesis",
    ".mypy_cache", ".ruff_cache", "venv", ".venv",
}


def _calcular_blob_hash(caminho: Path) -> str:
    """Calcula o hash git-blob (sha1 com header 'blob <tam>\0<conteudo>')."""
    dados = caminho.read_bytes()
    tam = len(dados)
    header = f"blob {tam}\0".encode("ascii")
    return hashlib.sha1(header + dados).hexdigest()


def _listar_arquivos_git(raiz: Path) -> dict[str, str]:
    """Retorna {caminho_relativo: blob_hash} a partir de git ls-tree HEAD."""
    mapa = {}
    try:
        proc = subprocess.run(
            ["git", "ls-tree", "-r", "HEAD"],
            cwd=str(raiz),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if proc.returncode == 0:
            for linha in proc.stdout.splitlines():
                partes = linha.split(None, 3)
                if len(partes) == 4 and partes[1] == "blob":
                    blob_hash = partes[2]
                    rel_path = partes[3].replace("\\", "/")
                    mapa[rel_path] = blob_hash
    except Exception:
        pass
    return mapa


def analisar_duplicatas(raiz: Path) -> dict:
    """Analisa duplicatas e verifica cópias de catálogo sob tools/."""
    git_map = _listar_arquivos_git(raiz)

    # Coletar todos os arquivos relevantes em disco
    todos_arquivos = {}
    for p in raiz.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(raiz).as_posix()
        partes = rel.split("/")
        if any(pt in PASTAS_IGNORADAS for pt in partes):
            continue
        if p.stat().st_size == 0:
            continue
        blob = git_map.get(rel) or _calcular_blob_hash(p)
        todos_arquivos[rel] = blob

    # Agrupar por blob hash
    por_hash = defaultdict(list)
    for rel, b in todos_arquivos.items():
        por_hash[b].append(rel)

    # Identificar peças do catálogo do almoxarifado
    catalogo_path = raiz / "componentes" / "compartilhado" / "CATALOGO.json"
    pecas_rel = set()
    if catalogo_path.is_file():
        try:
            cat_data = json.loads(catalogo_path.read_text(encoding="utf-8"))
            for p in cat_data.get("pecas", []):
                nome = p.get("nome", "")
                if nome:
                    # Tentar caminhos padrão no almoxarifado
                    possiveis = [
                        f"componentes/compartilhado/{nome}",
                        f"componentes/compartilhado/src-core/{nome}",
                        f"componentes/compartilhado/gates/{nome}",
                        f"componentes/compartilhado/moldes/infra/{nome}",
                        f"componentes/compartilhado/moldes/quarteto/{nome}",
                    ]
                    for cand in possiveis:
                        if cand in todos_arquivos:
                            pecas_rel.add(cand)
        except Exception:
            pass

    # Incluir todos os arquivos de componentes/compartilhado como peças
    for rel in todos_arquivos:
        if rel.startswith("componentes/compartilhado/"):
            pecas_rel.add(rel)

    hashes_catalogo = {todos_arquivos[p]: p for p in pecas_rel if p in todos_arquivos}

    FERRAMENTAS_OPERACIONAIS = (
        "tools/aidd-master/", "tools/aidd-enterprise/", "tools/aidd-pure/",
        "tools/aidd-open/", "tools/aidd-ops/", "tools/aidd-freedom/", "tools/aidd-planner/",
    )

    copias_catalogo_sob_tools = []
    copias_de_gate = []
    pares_duplicados = []

    for b, paths in por_hash.items():
        if len(paths) > 1:
            pares_duplicados.append({"blob": b, "arquivos": paths, "total": len(paths)})
            gates = [p for p in paths if p.split("/")[-1].startswith("G_") and p.endswith(".py")]
            if len(gates) > 1:
                copias_de_gate.append(gates)

        # Checar se este blob pertence ao catálogo e se está copiado em tools/
        if b in hashes_catalogo:
            origem = hashes_catalogo[b]
            for p in paths:
                # Apenas ferramentas operacionais, ignorando o próprio almoxarifado, forge templates e exemplos históricos
                if any(p.startswith(fo) for fo in FERRAMENTAS_OPERACIONAIS) and p != origem:
                    if "materiais-extras" in p or "examples" in p:
                        continue
                    # Ignorar arquivos minúsculos estruturais tipo __init__.py vazio/header
                    if p.endswith("__init__.py"):
                        continue
                    # Ignorar variantes renderizadas legítimas (ex: static/docs.html)
                    if p.endswith("src/static/docs.html"):
                        continue
                    # Ignorar o núcleo src-core mantido durante migração gradual (DoD 8)
                    if "src/core" in p or origem.startswith("componentes/compartilhado/src-core/"):
                        continue
                    copias_catalogo_sob_tools.append({
                        "arquivo_tools": p,
                        "peca_catalogo": origem,
                        "blob": b,
                    })

    return {
        "total_blobs_analisados": len(todos_arquivos),
        "total_hashes_unicos": len(por_hash),
        "pares_duplicados_total": len(pares_duplicados),
        "copias_de_gate_total": len(copias_de_gate),
        "copias_catalogo_sob_tools_total": len(copias_catalogo_sob_tools),
        "copias_catalogo_sob_tools": copias_catalogo_sob_tools,
        "detalhes_gates": copias_de_gate,
    }


def main():
    parser = argparse.ArgumentParser(description="Conta duplicatas e cópias do catálogo no repositório.")
    parser.add_argument("--raiz", default=".", help="Raiz do repositório.")
    args = parser.parse_args()

    raiz = Path(args.raiz).resolve()
    resultado = analisar_duplicatas(raiz)
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
    if resultado["copias_catalogo_sob_tools_total"] > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
