# -*- coding: utf-8 -*-
"""
AIDD-Melhoria Módulo de Output Consolidado e Handoff Estruturado (D15 / Ticket 8).
Provê:
1. Construção do envelope canônico `handoff-melhoria.json` (schema 1.0.0) para SUCESSO,
   SUCESSO_FALLBACK e FALHA, com lista de artefatos e sha256 de cada um.
2. Assinatura determinística do payload canônico (chaves ordenadas, sem o campo 'assinatura'):
   - `sha256`: selo de integridade (detecta adulteração, não prova autoria);
   - `hmac-sha256`: autenticidade, quando a variável AIDD_HANDOFF_CHAVE estiver definida.
3. Gravação atômica (arquivo temporário + os.replace) — nunca deixa handoff parcial.
4. Verificação e consumo pelo orquestrador: `transicionar_fase` só libera melhoria -> plan
   com handoff presente, íntegro, assinado, status SUCESSO e artefatos inalterados.
"""

from __future__ import annotations

import datetime
import hashlib
import hmac
import json
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Union

VERSAO_SCHEMA = "1.0.0"
FERRAMENTA = "aidd-melhoria"
FASE_ATUAL = "melhoria"
PROXIMA_FASE = "plan"
VAR_CHAVE = "AIDD_HANDOFF_CHAVE"
ESCOPO_ASSINATURA = "payload-canonico-sem-assinatura"
STATUS_VALIDOS = ("SUCESSO", "SUCESSO_FALLBACK", "FALHA")
NOME_SCHEMA = "handoff-melhoria.schema.json"


def _localizar_schema() -> Optional[Path]:
    for pasta in Path(__file__).resolve().parents:
        candidato = pasta / "componentes" / "compartilhado" / "specs" / NOME_SCHEMA
        if candidato.is_file():
            return candidato
    return None


def sha256_arquivo(caminho: Union[Path, str]) -> str:
    digest = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(65536), b""):
            digest.update(bloco)
    return digest.hexdigest()


def _payload_canonico(dados: Dict[str, Any]) -> bytes:
    sem_assinatura = {k: v for k, v in dados.items() if k != "assinatura"}
    return json.dumps(sem_assinatura, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def _calcular_assinatura(dados: Dict[str, Any], chave: Optional[str]) -> Dict[str, str]:
    payload = _payload_canonico(dados)
    if chave:
        valor = hmac.new(chave.encode("utf-8"), payload, hashlib.sha256).hexdigest()
        algoritmo = "hmac-sha256"
    else:
        valor = hashlib.sha256(payload).hexdigest()
        algoritmo = "sha256"
    return {"algoritmo": algoritmo, "escopo": ESCOPO_ASSINATURA, "valor": valor}


def _caminho_relativo(caminho: Path, base: Path) -> str:
    try:
        return caminho.resolve().relative_to(base.resolve()).as_posix()
    except ValueError:
        return str(caminho.resolve())


def construir_handoff(
    status: str,
    codigo_saida: int,
    repo_root: Union[Path, str],
    manifesto: Optional[str] = None,
    detalhes: Optional[Dict[str, Any]] = None,
    erro: Optional[str] = None,
    artefatos: Optional[Iterable[Union[Path, str]]] = None,
) -> Dict[str, Any]:
    """Monta o envelope canônico assinado. Só SUCESSO com exit 0 libera a próxima fase."""
    if status not in STATUS_VALIDOS:
        raise ValueError(f"Status de handoff inválido: {status!r}. Esperado um de {STATUS_VALIDOS}.")

    base = Path(repo_root)
    liberada = status == "SUCESSO" and codigo_saida == 0
    dados: Dict[str, Any] = {
        "versao_schema": VERSAO_SCHEMA,
        "ferramenta": FERRAMENTA,
        "status": status,
        "codigo_saida": codigo_saida,
        "emitido_em": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "transicao": {
            "fase_atual": FASE_ATUAL,
            "proxima_fase": PROXIMA_FASE if liberada else None,
            "liberada": liberada,
            "requer_aprovacao_humana": True,
        },
        "artefatos": [
            {"caminho": _caminho_relativo(Path(a), base), "sha256": sha256_arquivo(a)}
            for a in (artefatos or [])
        ],
    }
    if manifesto:
        dados["manifesto"] = str(manifesto)
    if detalhes:
        dados["detalhes"] = detalhes
    if erro:
        dados["erro"] = str(erro)

    dados["assinatura"] = _calcular_assinatura(dados, os.environ.get(VAR_CHAVE))
    return dados


def emitir_handoff(handoff_path: Union[Path, str], **kwargs: Any) -> Dict[str, Any]:
    """Constrói, assina e grava atomicamente o handoff. Retorna o envelope gravado."""
    destino = Path(handoff_path)
    dados = construir_handoff(**kwargs)
    destino.parent.mkdir(parents=True, exist_ok=True)
    temporario = destino.with_name(destino.name + ".tmp")
    temporario.write_text(json.dumps(dados, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(temporario, destino)
    return dados


def _validar_schema(dados: Dict[str, Any]) -> List[str]:
    caminho_schema = _localizar_schema()
    if caminho_schema is None:
        return [f"Schema canônico {NOME_SCHEMA} não encontrado."]
    try:
        import jsonschema
    except ImportError:
        return ["Biblioteca 'jsonschema' não instalada no ambiente Python."]
    schema = json.loads(caminho_schema.read_text(encoding="utf-8"))
    erros = []
    for err in jsonschema.Draft7Validator(schema).iter_errors(dados):
        local = " -> ".join(str(p) for p in err.absolute_path) or "raiz"
        erros.append(f"Schema [{local}]: {err.message}")
    return erros


def verificar_handoff(handoff_path: Union[Path, str], repo_root: Optional[Union[Path, str]] = None) -> List[str]:
    """Retorna a lista de violações do handoff (vazia = íntegro). Não julga o status."""
    caminho = Path(handoff_path)
    if not caminho.is_file():
        return [f"Handoff ausente: {caminho}"]
    try:
        dados = json.loads(caminho.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return [f"Handoff com JSON inválido: {exc}"]
    if not isinstance(dados, dict):
        return ["Handoff inválido: JSON raiz deve ser um objeto."]

    erros = _validar_schema(dados)
    if erros:
        return erros

    assinatura = dados["assinatura"]
    chave = os.environ.get(VAR_CHAVE)
    if assinatura["algoritmo"] == "hmac-sha256" and not chave:
        return [f"Handoff assinado com hmac-sha256, mas a chave {VAR_CHAVE} não está definida."]
    esperado = _calcular_assinatura(dados, chave if assinatura["algoritmo"] == "hmac-sha256" else None)
    if not hmac.compare_digest(esperado["valor"], assinatura["valor"]):
        erros.append("Assinatura inválida: payload do handoff foi alterado após a emissão.")

    transicao = dados["transicao"]
    deveria_liberar = dados["status"] == "SUCESSO" and dados["codigo_saida"] == 0
    if transicao["liberada"] != deveria_liberar:
        erros.append(
            f"Transição incoerente: liberada={transicao['liberada']} com status "
            f"{dados['status']} e codigo_saida {dados['codigo_saida']}."
        )
    if transicao["liberada"] != (transicao["proxima_fase"] == PROXIMA_FASE):
        erros.append("Transição incoerente: proxima_fase não corresponde a 'liberada'.")

    base = Path(repo_root) if repo_root else caminho.parent
    for artefato in dados["artefatos"]:
        alvo = Path(artefato["caminho"])
        alvo = alvo if alvo.is_absolute() else base / alvo
        if not alvo.is_file():
            erros.append(f"Artefato não encontrado: {artefato['caminho']}")
        elif sha256_arquivo(alvo) != artefato["sha256"]:
            erros.append(f"Artefato com sha256 divergente (alterado após o handoff): {artefato['caminho']}")
    return erros


def transicionar_fase(handoff_path: Union[Path, str], repo_root: Optional[Union[Path, str]] = None) -> Dict[str, Any]:
    """Ponto de consumo do orquestrador: decide se melhoria -> plan pode avançar."""
    erros = verificar_handoff(handoff_path, repo_root=repo_root)
    if not erros:
        dados = json.loads(Path(handoff_path).read_text(encoding="utf-8"))
        if not dados["transicao"]["liberada"]:
            motivo = dados.get("erro") or "sem liberação para a próxima fase"
            erros.append(f"Transição bloqueada: status {dados['status']} ({motivo}).")
        elif not dados["artefatos"]:
            erros.append("Transição bloqueada: handoff de SUCESSO sem artefatos consolidados.")
    if erros:
        return {"liberada": False, "proxima_fase": None, "erros": erros}
    return {"liberada": True, "proxima_fase": PROXIMA_FASE, "erros": []}
