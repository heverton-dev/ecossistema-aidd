"""Módulo do Almoxarifado Único do AIDD Forge (D15 / DoD 5).

Guarda e distribui peças do ecossistema a partir de componentes/compartilhado/CATALOGO.json.
Nenhuma ferramenta guarda cópia; o forge entrega sob demanda para projetos e recusa
gravar dentro de 'tools/'.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any


def _encontrar_raiz(raiz: str | Path | None = None) -> Path:
    """Encontra deterministicamente a raiz do repositório contendo CATALOGO.json."""
    if raiz is not None:
        candidato = Path(raiz).resolve()
        if (candidato / "componentes" / "compartilhado" / "CATALOGO.json").is_file():
            return candidato
        return candidato

    # Tenta subindo a partir deste arquivo (aidd_forge/core/almoxarifado.py -> 4 níveis acima)
    arquivo_atual = Path(__file__).resolve()
    for parent in arquivo_atual.parents:
        if (parent / "componentes" / "compartilhado" / "CATALOGO.json").is_file():
            return parent
        if (parent / "ecossistema.py").is_file():
            return parent

    # Fallback: tentar a partir do diretório de trabalho atual
    cwd = Path.cwd().resolve()
    for parent in (cwd, *cwd.parents):
        if (parent / "componentes" / "compartilhado" / "CATALOGO.json").is_file():
            return parent
        if (parent / "ecossistema.py").is_file():
            return parent

    return cwd


def carregar_catalogo(raiz: str | Path | None = None) -> dict[str, Any]:
    """Carrega o arquivo CATALOGO.json do almoxarifado."""
    root = _encontrar_raiz(raiz)
    catalogo_path = root / "componentes" / "compartilhado" / "CATALOGO.json"
    if not catalogo_path.is_file():
        raise FileNotFoundError(
            f"Catálogo do almoxarifado não encontrado em '{catalogo_path}'."
        )
    return json.loads(catalogo_path.read_text(encoding="utf-8"))


def _buscar_peca(nome: str, catalogo: dict[str, Any]) -> dict[str, Any]:
    """Busca os metadados de uma peça pelo nome no catálogo."""
    pecas = catalogo.get("pecas", [])
    for peca in pecas:
        if peca.get("nome") == nome:
            return peca
    raise ValueError(
        f"Peça '{nome}' não encontrada no catálogo do almoxarifado (CATALOGO.json)."
    )


def caminho_peca(nome: str, raiz: str | Path | None = None) -> Path:
    """Retorna o caminho em disco de uma peça do almoxarifado (apenas leitura, sem cópia)."""
    root = _encontrar_raiz(raiz)
    catalogo = carregar_catalogo(root)
    peca = _buscar_peca(nome, catalogo)

    caminho_rel = peca.get("caminho")
    if not caminho_rel:
        raise ValueError(f"Peça '{nome}' não tem caminho definido no catálogo.")

    caminho_abs = (root / caminho_rel).resolve()
    if not caminho_abs.is_file():
        raise FileNotFoundError(
            f"Arquivo da peça '{nome}' não encontrado no disco: '{caminho_abs}'."
        )

    return caminho_abs


def _calcular_sha256(caminho: Path) -> str:
    """Calcula o hash sha256 de um arquivo."""
    hasher = hashlib.sha256()
    with open(caminho, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def obter_peca(
    nome: str,
    destino: str | Path,
    raiz: str | Path | None = None,
    manter_estrutura: bool = False,
) -> Path:
    """Copia uma peça do almoxarifado para a pasta do projeto e verifica o sha256.

    Regras:
    - Recusa expressamente qualquer destino dentro da pasta 'tools/'.
    - Verifica a integridade do sha256 contra o catálogo oficial.
    """
    root = _encontrar_raiz(raiz)
    catalogo = carregar_catalogo(root)
    peca = _buscar_peca(nome, catalogo)

    dest_path = Path(destino).resolve()

    # Validação de segurança arquitetural: proibido gravar em 'tools/'
    tools_repo = (root / "tools").resolve()
    if (
        any(part.lower() == "tools" for part in dest_path.parts)
        or dest_path == tools_repo
        or tools_repo in dest_path.parents
    ):
        raise ValueError(
            f"Destino inválido '{destino}': proibido gravar dentro de 'tools/'. "
            "O almoxarifado entrega peças exclusivamente para pastas de projetos."
        )

    origem = caminho_peca(nome, raiz=root)

    # Determina arquivo de destino final
    if dest_path.is_dir() or str(destino).endswith(("/", "\\")) or not dest_path.suffix:
        if manter_estrutura:
            arquivo_destino = dest_path / nome
        else:
            arquivo_destino = dest_path / origem.name
    else:
        arquivo_destino = dest_path

    arquivo_destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(origem, arquivo_destino)

    # Verificação de integridade via sha256
    hash_calculado = _calcular_sha256(arquivo_destino)
    hash_esperado = peca.get("sha256", "")
    if hash_esperado.startswith("sha256-"):
        hash_esperado = hash_esperado.split("sha256-", 1)[1]

    if hash_esperado and hash_calculado != hash_esperado:
        if arquivo_destino.exists():
            arquivo_destino.unlink()
        raise ValueError(
            f"Integridade violada para '{nome}': hash esperado '{hash_esperado}', "
            f"calculado '{hash_calculado}'."
        )

    return arquivo_destino
