# -*- coding: utf-8 -*-
"""
Orquestracao multi-estagio de aidd-forge (D10).

Pipeline sequencial deterministico com transicoes de estado persistidas:
  pre-validacao -> injecao -> pos-verificacao
Estado intermediario corrompido (JSON invalido, ordem violada, estagio
desconhecido) aborta o pipeline com exit 1.
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Callable, Dict, List, Mapping, Optional, Union

ESTAGIOS = ("pre_validacao", "injecao", "pos_verificacao")
_ARQUIVO_ESTADO = "ORQUESTRACAO-ESTADO.json"
_MARCADOR = "ORQUESTRACAO-MARCADOR.txt"
_VERSAO_ESTADO = 1
_STATUS_VALIDOS = ("em_execucao", "concluido", "abortado")

PathLike = Union[str, Path]
Handler = Callable[[], int]


class EstadoCorrompidoError(ValueError):
    """Estado intermediario do pipeline invalido ou fora das transicoes permitidas."""


def _carregar_isolamento():
    """Carrega o modulo irmao isolamento.py (guard de escrita D3)."""
    nome = "aidd_forge_isolamento_orquestracao"
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
    """Valida estrito o estado do pipeline; qualquer anormalidade -> EstadoCorrompidoError."""
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
        raise EstadoCorrompidoError("ordem de estagios violada (transicao invalida)")

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
    """Persiste o estado de forma atomica (write tmp + replace)."""
    caminho = Path(caminho)
    tmp = caminho.with_suffix(caminho.suffix + ".tmp")
    tmp.write_text(json.dumps(estado, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, caminho)


def _handlers_padrao(pasta: Path) -> Dict[str, Handler]:
    isolamento = _carregar_isolamento()

    def pre_validacao() -> int:
        return 0 if pasta.is_dir() else 1

    def injecao() -> int:
        isolamento.escrever_com_isolamento(
            repo_root=pasta,
            alvo_relativo=_MARCADOR,
            conteudo="injecao-concluida\n",
            worktree_dir=None,
        )
        return 0

    def pos_verificacao() -> int:
        marcador = pasta / _MARCADOR
        if not marcador.is_file():
            return 1
        return 0 if marcador.read_text(encoding="utf-8") == "injecao-concluida\n" else 1

    return {"pre_validacao": pre_validacao, "injecao": injecao, "pos_verificacao": pos_verificacao}


def executar_pipeline(
    pasta: PathLike,
    handlers: Optional[Mapping[str, Handler]] = None,
) -> int:
    """
    Executa o pipeline sequencial, persistindo apos cada transicao de estado.
    Estado corrompido ou falha de estagio -> exit 1.
    """
    pasta = Path(pasta).resolve()
    if not pasta.is_dir():
        print(f"[aidd-forge] diretorio de trabalho inexistente: {pasta}", file=sys.stderr)
        return 1

    caminho_estado = pasta / _ARQUIVO_ESTADO
    try:
        if caminho_estado.is_file():
            estado = carregar_estado(caminho_estado)
        else:
            estado = novo_estado()
    except EstadoCorrompidoError as exc:
        print(f"[aidd-forge] estado corrompido, pipeline abortado: {exc}", file=sys.stderr)
        return 1

    if estado["status"] == "concluido":
        print("[aidd-forge] pipeline ja concluido.")
        return 0

    mapa_handlers = dict(handlers) if handlers is not None else _handlers_padrao(pasta)
    faltantes = [e for e in ESTAGIOS if e not in mapa_handlers]
    if faltantes:
        print(f"[aidd-forge] handlers ausentes: {faltantes}", file=sys.stderr)
        return 1

    try:
        for estagio in ESTAGIOS[len(estado["concluidos"]):]:
            try:
                codigo = int(mapa_handlers[estagio]())
            except Exception as exc:
                print(f"[aidd-forge] estagio '{estagio}' lancou excecao: {exc}", file=sys.stderr)
                codigo = 1
            if codigo != 0:
                estado["status"] = "abortado"
                salvar_estado(caminho_estado, estado)
                print(f"[aidd-forge] estagio '{estagio}' falhou, pipeline abortado.", file=sys.stderr)
                return 1
            estado["concluidos"].append(estagio)
            salvar_estado(caminho_estado, estado)
    except OSError as exc:
        print(f"[aidd-forge] falha ao persistir estado: {exc}", file=sys.stderr)
        return 1

    estado["status"] = "concluido"
    salvar_estado(caminho_estado, estado)
    print(f"[aidd-forge] pipeline concluido: {', '.join(estado['concluidos'])}")
    return 0


def main(args: Optional[List[str]] = None) -> int:
    """Entrypoint CLI: <pasta_trabalho>. exit 1 em entrada invalida ou aborto."""
    argv = list(sys.argv[1:] if args is None else args)
    if len(argv) != 1:
        print("Uso: orquestracao.py <pasta_trabalho>", file=sys.stderr)
        return 1
    return executar_pipeline(argv[0])


if __name__ == "__main__":
    sys.exit(main())
