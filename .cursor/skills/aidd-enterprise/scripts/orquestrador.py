# -*- coding: utf-8 -*-
"""
Orquestracao multi-estagio de aidd-enterprise (D10).

Pipeline estrito e sequencial com transicoes de estado persistidas no arquivo
de sessao estruturado ORQUESTRADOR-ESTADO.json:
  prevalidacao -> snapshot -> injecao -> verificacao -> handoff
Estado intermediario corrompido, prevalidacao pulada, estagio desconhecido ou
falha de estagio aborta o pipeline com exit 1.
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Callable, Dict, List, Mapping, Optional, Union

ESTAGIOS = ("prevalidacao", "snapshot", "injecao", "verificacao", "handoff")
_ARQUIVO_ESTADO = "ORQUESTRADOR-ESTADO.json"
_ARQUIVO_SNAPSHOT = "ORQUESTRADOR-SNAPSHOT.json"
_MARCADOR = "ORQUESTRADOR-MARCADOR.txt"
_ARQUIVO_HANDOFF = "HANDOFF-ENTERPRISE.json"
_VERSAO_ESTADO = 1
_STATUS_VALIDOS = ("em_execucao", "concluido", "abortado")

PathLike = Union[str, Path]
Handler = Callable[[], int]


class EstadoCorrompidoError(ValueError):
    """Estado intermediario do pipeline invalido ou fora das transicoes permitidas."""


def _carregar_isolamento():
    """Carrega o modulo irmao isolamento.py (guard de escrita D3)."""
    nome = "aidd_enterprise_isolamento_orquestrador"
    if nome in sys.modules:
        return sys.modules[nome]
    spec = importlib.util.spec_from_file_location(nome, str(Path(__file__).resolve().parent / "isolamento.py"))
    modulo = importlib.util.module_from_spec(spec)
    sys.modules[nome] = modulo
    spec.loader.exec_module(modulo)
    return modulo


def novo_estado() -> dict:
    return {"versao": _VERSAO_ESTADO, "concluidos": [], "status": "em_execucao"}


def validar_estado(estado: object) -> dict:
    """Valida estrito o estado da sessao; qualquer anormalidade -> EstadoCorrompidoError."""
    if not isinstance(estado, dict):
        raise EstadoCorrompidoError("estado deve ser um objeto JSON")

    if estado.get("versao") != _VERSAO_ESTADO:
        raise EstadoCorrompidoError(f"versao de estado desconhecida: {estado.get('versao')!r}")

    desconhecidas = set(estado) - {"versao", "concluidos", "status"}
    if desconhecidas:
        raise EstadoCorrompidoError(f"campos de estado desconhecidos: {sorted(desconhecidas)}")

    concluidos = estado.get("concluidos")
    if not isinstance(concluidos, list) or any(not isinstance(c, str) for c in concluidos):
        raise EstadoCorrompidoError("'concluidos' deve ser lista de strings")

    for item in concluidos:
        if item not in ESTAGIOS:
            raise EstadoCorrompidoError(f"estagio desconhecido no estado: {item!r}")
    if concluidos != list(ESTAGIOS[: len(concluidos)]):
        raise EstadoCorrompidoError("ordem de estagios violada (prevalidacao pulada ou fase fora de ordem)")

    status = estado.get("status")
    if status not in _STATUS_VALIDOS:
        raise EstadoCorrompidoError(f"status desconhecido: {status!r}")
    if status == "concluido" and concluidos != list(ESTAGIOS):
        raise EstadoCorrompidoError("status 'concluido' exige todos os estagios concluidos")
    if status == "abortado" and len(concluidos) >= len(ESTAGIOS):
        raise EstadoCorrompidoError("status 'abortado' incompativel com pipeline completo")

    return {"versao": _VERSAO_ESTADO, "concluidos": list(concluidos), "status": status}


def carregar_estado(caminho: PathLike) -> dict:
    """Le e valida o estado persistido; arquivo corrompido -> EstadoCorrompidoError."""
    try:
        texto = Path(caminho).read_text(encoding="utf-8")
        dados = json.loads(texto)
    except (OSError, ValueError) as exc:
        raise EstadoCorrompidoError(f"arquivo de estado corrompido: {exc}") from exc
    return validar_estado(dados)


def salvar_estado(caminho: PathLike, estado: dict) -> None:
    """Persiste o estado da sessao de forma atomica (write tmp + replace)."""
    caminho = Path(caminho)
    tmp = caminho.with_suffix(caminho.suffix + ".tmp")
    tmp.write_text(json.dumps(estado, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, caminho)


def _handlers_padrao(pasta: Path) -> Dict[str, Handler]:
    isolamento = _carregar_isolamento()

    def prevalidacao() -> int:
        return 0 if pasta.is_dir() else 1

    def snapshot() -> int:
        isolamento.escrever_com_isolamento(
            repo_root=pasta,
            alvo_relativo=_ARQUIVO_SNAPSHOT,
            conteudo=json.dumps(
                {"estagios": list(ESTAGIOS), "origem": str(pasta), "snapshot_de": "prevalidacao"},
                indent=2,
                sort_keys=True,
            )
            + "\n",
            caminhos_permitidos=[_ARQUIVO_SNAPSHOT],
            worktree_dir=None,
        )
        return 0

    def injecao() -> int:
        isolamento.escrever_com_isolamento(
            repo_root=pasta,
            alvo_relativo=_MARCADOR,
            conteudo="injecao-concluida\n",
            caminhos_permitidos=[_MARCADOR],
            worktree_dir=None,
        )
        return 0

    def verificacao() -> int:
        snapshot = pasta / _ARQUIVO_SNAPSHOT
        marcador = pasta / _MARCADOR
        if not snapshot.is_file() or not marcador.is_file():
            return 1
        if marcador.read_text(encoding="utf-8") != "injecao-concluida\n":
            return 1
        try:
            dados = json.loads(snapshot.read_text(encoding="utf-8"))
        except ValueError:
            return 1
        return 0 if dados.get("estagios") == list(ESTAGIOS) else 1

    def handoff() -> int:
        if not (pasta / _MARCADOR).is_file() or not (pasta / _ARQUIVO_SNAPSHOT).is_file():
            return 1
        isolamento.escrever_com_isolamento(
            repo_root=pasta,
            alvo_relativo=_ARQUIVO_HANDOFF,
            conteudo=json.dumps(
                {"versao": 1, "estagios": list(ESTAGIOS), "status": "pronto"},
                indent=2,
                sort_keys=True,
            )
            + "\n",
            caminhos_permitidos=[_ARQUIVO_HANDOFF],
            worktree_dir=None,
        )
        return 0

    return {
        "prevalidacao": prevalidacao,
        "snapshot": snapshot,
        "injecao": injecao,
        "verificacao": verificacao,
        "handoff": handoff,
    }


def executar_pipeline(
    pasta: PathLike,
    handlers: Optional[Mapping[str, Handler]] = None,
) -> int:
    """
    Executa o pipeline estrito, persistindo apos cada transicao de estado.
    Estado corrompido, prevalidacao pulada ou falha de estagio -> exit 1.
    """
    pasta = Path(pasta).resolve()
    if not pasta.is_dir():
        print(f"[aidd-enterprise] diretorio de trabalho inexistente: {pasta}", file=sys.stderr)
        return 1

    caminho_estado = pasta / _ARQUIVO_ESTADO
    try:
        if caminho_estado.is_file():
            estado = carregar_estado(caminho_estado)
        else:
            estado = novo_estado()
    except EstadoCorrompidoError as exc:
        print(f"[aidd-enterprise] estado corrompido, pipeline abortado: {exc}", file=sys.stderr)
        return 1

    if estado["status"] == "concluido":
        print("[aidd-enterprise] pipeline ja concluido.")
        return 0

    mapa_handlers = dict(handlers) if handlers is not None else _handlers_padrao(pasta)
    faltantes = [e for e in ESTAGIOS if e not in mapa_handlers]
    if faltantes:
        print(f"[aidd-enterprise] handlers ausentes: {faltantes}", file=sys.stderr)
        return 1

    try:
        for estagio in ESTAGIOS[len(estado["concluidos"]):]:
            try:
                codigo = int(mapa_handlers[estagio]())
            except Exception as exc:
                print(f"[aidd-enterprise] estagio '{estagio}' lancou excecao: {exc}", file=sys.stderr)
                codigo = 1
            if codigo != 0:
                estado["status"] = "abortado"
                salvar_estado(caminho_estado, estado)
                print(f"[aidd-enterprise] estagio '{estagio}' falhou, pipeline abortado.", file=sys.stderr)
                return 1
            estado["concluidos"].append(estagio)
            salvar_estado(caminho_estado, estado)
    except OSError as exc:
        print(f"[aidd-enterprise] falha ao persistir estado: {exc}", file=sys.stderr)
        return 1

    estado["status"] = "concluido"
    salvar_estado(caminho_estado, estado)
    print(f"[aidd-enterprise] pipeline concluido: {', '.join(estado['concluidos'])}")
    return 0


def main(args: Optional[List[str]] = None) -> int:
    """Entrypoint CLI: <pasta_trabalho>. exit 1 em entrada invalida ou aborto."""
    argv = list(sys.argv[1:] if args is None else args)
    if len(argv) != 1:
        print("Uso: orquestrador.py <pasta_trabalho>", file=sys.stderr)
        return 1
    return executar_pipeline(argv[0])


if __name__ == "__main__":
    sys.exit(main())
