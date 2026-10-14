# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — REFERÊNCIAS DE UI DO PLANNER (Mobbin ou spec)
=============================================================================
Monta `referencias-ui.json` do projeto a partir da direção visual da spec:

  - origem `mobbin_api`: uma consulta descritiva POR TELA (ancorada nos apps de referência da spec),
    modo `standard`, resultado em cache por hash (`.aidd/cache/mobbin/`), tokens agregados das telas;
  - origem `mcp`: o harness, que é quem usa o MCP oficial do Mobbin, grava
    `.aidd/intake/referencias-mcp.json` (telas e fluxos); o planner só valida e registra;
  - origem `spec`: sem Mobbin (caminho 3), ou quando ele falha. A queda NUNCA é silenciosa: o aviso vai
    para stderr e para o arquivo.

Guarda só tokens derivados e links (`mobbin_url`, id): nunca as imagens, nem as URLs delas (expiram em
~30 dias e o direito de uso das imagens não está documentado pelo Mobbin).
=============================================================================
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

ARQUIVO_REFERENCIAS = "referencias-ui.json"
CACHE_DIR = Path(".aidd") / "cache" / "mobbin"
ARQUIVO_MCP = Path(".aidd") / "intake" / "referencias-mcp.json"
TIPOS_DE_TELA = ("dashboard overview", "data table list", "create form")
DIREITOS = ("Guardados apenas tokens derivados e links do Mobbin; as imagens não são armazenadas. "
            "Uso das imagens sujeito aos termos do Mobbin (não documentados na API).")
LIMITE_POR_CONSULTA = 6
TELAS_PARA_TOKENS = 6


def consultas_da_spec(direcao: Dict[str, Any], dominio: str) -> List[str]:
    """Uma consulta descritiva por tela, ancorada nos apps de referência da spec (o app citado restringe a busca)."""
    apps = list(direcao.get("referencias") or [])[:2]
    consultas: List[str] = []
    for app in apps:
        for tipo in TIPOS_DE_TELA:
            consultas.append(f"{app} {tipo}"[:500])
    consultas.append(f"{dominio} {direcao.get('publico', '')} dashboard".strip()[:500])
    consultas.append(f"{dominio} management table list"[:500])
    vistas: List[str] = []
    for c in consultas:
        if c not in vistas:
            vistas.append(c)
    return vistas


def _chave_cache(query: str, plataforma: str, modo: str, limite: int) -> str:
    return hashlib.sha256(f"{query}|{plataforma}|{modo}|{limite}".encode("utf-8")).hexdigest()


def _buscar_com_cache(pasta: str, query: str, buscar: Callable[..., Dict[str, Any]],
                      plataforma: str = "web", modo: str = "standard", limite: int = LIMITE_POR_CONSULTA) -> Dict[str, Any]:
    destino = Path(pasta) / CACHE_DIR / f"{_chave_cache(query, plataforma, modo, limite)}.json"
    if destino.is_file():
        try:
            return json.loads(destino.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            pass  # cache corrompido: refaz a consulta
    resposta = buscar(query, platform=plataforma, mode=modo, limit=limite)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(resposta, ensure_ascii=False), encoding="utf-8", newline="\n")
    return resposta


def _gravar(pasta: str, dados: Dict[str, Any]) -> None:
    (Path(pasta) / ARQUIVO_REFERENCIAS).write_text(
        json.dumps(dados, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def _base(origem: str, direcao: Dict[str, Any], dominio: str, aviso: Optional[str] = None) -> Dict[str, Any]:
    dados: Dict[str, Any] = {
        "versao": 1,
        "origem": origem,
        "gerado_em": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "dominio": dominio,
        "direcao_visual": direcao,
        "direitos": DIREITOS,
    }
    if aviso:
        dados["aviso"] = aviso
    return dados


def _importar_extrator():
    raiz = next((p for p in Path(__file__).resolve().parents if (p / "ecossistema.py").is_file()), None)
    if raiz is not None and str(raiz) not in sys.path:
        sys.path.insert(0, str(raiz))
    from componentes.compartilhado.mcps.mobbin_mcp import token_extractor
    return token_extractor


def _cair_na_spec(pasta, direcao, dominio, aviso) -> Dict[str, Any]:
    print(f"[AVISO] Referências de UI vêm da spec, não do Mobbin: {aviso}", file=sys.stderr)
    dados = _base("spec", direcao, dominio, aviso)
    _gravar(pasta, dados)
    return dados


def montar_referencias(
    pasta: str,
    direcao: Dict[str, Any],
    dominio: str,
    buscar: Optional[Callable[..., Dict[str, Any]]] = None,
    baixar: Optional[Callable[[str], bytes]] = None,
    usar_mobbin: bool = True,
    origem_mcp: bool = False,
) -> Dict[str, Any]:
    """Grava `referencias-ui.json` e devolve o dicionário gravado (`origem`: mobbin_api | mcp | spec)."""
    if origem_mcp:
        arquivo = Path(pasta) / ARQUIVO_MCP
        if not arquivo.is_file():
            return _cair_na_spec(pasta, direcao, dominio,
                                 f"o caminho MCP escolhido não tem {ARQUIVO_MCP.as_posix()} (o harness grava as "
                                 f"telas e fluxos do Mobbin ali).")
        try:
            entrada = json.loads(arquivo.read_text(encoding="utf-8"))
        except (OSError, ValueError) as erro:
            return _cair_na_spec(pasta, direcao, dominio, f"{ARQUIVO_MCP.as_posix()} ilegível ({type(erro).__name__}).")
        dados = _base("mcp", direcao, dominio)
        dados["telas"] = [{"id": t.get("id"), "app_name": t.get("app_name"), "mobbin_url": t.get("mobbin_url")}
                          for t in entrada.get("telas", [])]
        dados["fluxos"] = [{"id": f.get("id"), "name": f.get("name"), "app_name": f.get("app_name"),
                            "screen_count": f.get("screen_count")} for f in entrada.get("fluxos", [])]
        _gravar(pasta, dados)
        return dados

    if not usar_mobbin:
        dados = _base("spec", direcao, dominio)
        _gravar(pasta, dados)
        return dados

    if buscar is None:
        from .mobbin_client import executar_busca as buscar  # noqa: F811
    from .mobbin_client import MobbinError

    consultas = consultas_da_spec(direcao, dominio)
    telas_por_id: Dict[str, Dict[str, Any]] = {}
    registro_consultas = []
    try:
        for query in consultas:
            resposta = _buscar_com_cache(pasta, query, buscar)
            ids = []
            for tela in resposta.get("screens", []):
                if tela.get("id") and tela["id"] not in telas_por_id:
                    telas_por_id[tela["id"]] = tela
                ids.append(tela.get("id"))
            registro_consultas.append({"query": query, "modo": "standard", "ids": ids})
    except (MobbinError, ValueError) as erro:
        return _cair_na_spec(pasta, direcao, dominio, str(erro))

    if not telas_por_id:
        return _cair_na_spec(pasta, direcao, dominio, "o Mobbin não devolveu nenhuma tela para as consultas da spec.")

    extrator = _importar_extrator()
    escolhidas = list(telas_por_id.values())[:TELAS_PARA_TOKENS]
    tokens = extrator.extrair_tokens_de_telas(escolhidas, baixar=baixar)
    dados = _base("mobbin_api", direcao, dominio)
    dados["consultas"] = registro_consultas
    dados["telas"] = [{"id": t.get("id"), "app_name": t.get("app_name"), "platform": t.get("platform"),
                       "mobbin_url": t.get("mobbin_url")} for t in telas_por_id.values()]
    dados["tokens"] = {"cores": tokens["cores"], "arquetipo_layout": tokens.get("arquetipo_layout"),
                       "telas_analisadas": tokens.get("telas_analisadas"),
                       "nao_extraido_da_imagem": tokens.get("nao_extraido_da_imagem")}
    _gravar(pasta, dados)
    return dados
