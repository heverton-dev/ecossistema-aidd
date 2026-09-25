# -*- coding: utf-8 -*-
"""
AIDD-Diagnose Módulo de Output Consolidado e Handoff Estruturado (D15 / Ticket 8).

Provê:
1. Construção do envelope canônico `handoff-diagnose.json` (schema 1.0.0) para
   SUCESSO, SUCESSO_FALLBACK e FALHA, com diagnóstico consolidado: causa-raiz,
   arquivos alterados, teste de regressão, status do Quality Gate `G_aidd_diagnose`
   e próxima ferramenta sugerida (`aidd-tdd` ou `aidd-handoff`).
2. Assinatura determinística do payload canônico (chaves ordenadas, sem o campo
   'assinatura'):
   - `sha256`: selo de integridade (detecta adulteração, não prova autoria);
   - `hmac-sha256`: autenticidade, quando a variável AIDD_HANDOFF_CHAVE estiver definida.
3. Gravação atômica (arquivo temporário + os.replace) — nunca deixa handoff parcial.
4. Persistência do estado entre fases em `sessao.json` (contrato do Ticket 1):
   a emissão registra fase_atual=5, fases_completadas, status, próxima ferramenta,
   caminho do handoff e data de emissão — os dados não passam só pela conversa (D10).
5. Verificação e consumo: `transicionar_fase` só libera diagnose -> próxima
   ferramenta com handoff presente, íntegro, assinado, status SUCESSO/exit 0 e
   artefatos inalterados.

Reaproveita (DRY) os primitivos determinísticos de
`.agents/skills/aidd-melhoria/scripts/handoff.py` (sha256 de arquivo, payload
canônico e cálculo de assinatura), com fallback local idêntico para garantir
independência total do módulo (Zero Stubs).
"""

from __future__ import annotations

import datetime
import hashlib
import hmac
import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Union

VERSAO_SCHEMA = "1.0.0"
FERRAMENTA = "aidd-diagnose"
FASE_ATUAL = "diagnose"
FERRAMENTAS_PROXIMAS: tuple = ("aidd-tdd", "aidd-handoff")
VAR_CHAVE = "AIDD_HANDOFF_CHAVE"
ESCOPO_ASSINATURA = "payload-canonico-sem-assinatura"
STATUS_VALIDOS = ("SUCESSO", "SUCESSO_FALLBACK", "FALHA")
NOME_ARQUIVO_HANDOFF = "handoff-diagnose.json"
NOME_GATE = "G_aidd_diagnose"
FASE_FINAL = 5

# Prefixo em ordem da diagnose -> distribuição dos ramos (aidd-tdd | aidd-handoff).
_TODAS_FASES = list(range(1, FASE_FINAL + 1))

# Reuso DRY: primitivos de assinatura/hash do handoff de aidd-melhoria.
# Carregado sob nome de módulo próprio ('handoff' já ocupa sys.modules: o próprio
# aidd-diagnose/scripts/handoff.py), evitando auto-referência recursiva.
_MELHORIA_HANDOFF: Any = None
_NOME_MODULO_MELHORIA = "aidd_melhoria_handoff_dry"
_src_melhoria = (
    Path(__file__).resolve().parents[3] / "aidd-melhoria" / "scripts" / "handoff.py"
)
if _src_melhoria.is_file():
    try:
        _spec = importlib.util.spec_from_file_location(_NOME_MODULO_MELHORIA, _src_melhoria)
        if _spec is not None and _spec.loader is not None:
            _modulo_melhoria = importlib.util.module_from_spec(_spec)
            sys.modules[_NOME_MODULO_MELHORIA] = _modulo_melhoria
            _spec.loader.exec_module(_modulo_melhoria)
            _MELHORIA_HANDOFF = _modulo_melhoria
    except (ImportError, OSError, TypeError):  # pragma: no cover - fallback garantido
        _MELHORIA_HANDOFF = None


def _encontrar_raiz_repo(start_path: Optional[Union[Path, str]] = None) -> Path:
    """Encontra a raiz do repositório procurando por ecossistema.py."""
    atual = (Path(start_path) if start_path else Path(__file__)).resolve()
    for parent in [atual, *atual.parents]:
        if (parent / "ecossistema.py").is_file():
            return parent
    return atual.parents[4]


def sha256_arquivo(caminho: Union[Path, str]) -> str:
    """Reuso de aidd-melhoria quando disponível; fallback local determinístico."""
    if _MELHORIA_HANDOFF is not None and hasattr(_MELHORIA_HANDOFF, "sha256_arquivo"):
        return _MELHORIA_HANDOFF.sha256_arquivo(caminho)
    digest = hashlib.sha256()
    with open(caminho, "rb") as fh:
        for bloco in iter(lambda: fh.read(65536), b""):
            digest.update(bloco)
    return digest.hexdigest()


def _payload_canonico(dados: Dict[str, Any]) -> bytes:
    """Reuso de aidd-melhoria quando disponível; fallback local determinístico."""
    if _MELHORIA_HANDOFF is not None and hasattr(_MELHORIA_HANDOFF, "_payload_canonico"):
        return _MELHORIA_HANDOFF._payload_canonico(dados)
    sem_assinatura = {k: v for k, v in dados.items() if k != "assinatura"}
    return json.dumps(
        sem_assinatura, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")


def _calcular_assinatura(dados: Dict[str, Any], chave: Optional[str]) -> Dict[str, str]:
    """Reuso de aidd-melhoria quando disponível; fallback local determinístico."""
    if _MELHORIA_HANDOFF is not None and hasattr(_MELHORIA_HANDOFF, "_calcular_assinatura"):
        return _MELHORIA_HANDOFF._calcular_assinatura(dados, chave)
    payload = _payload_canonico(dados)
    if chave:
        valor = hmac.new(chave.encode("utf-8"), payload, hashlib.sha256).hexdigest()
        algoritmo = "hmac-sha256"
    else:
        valor = hashlib.sha256(payload).hexdigest()
        algoritmo = "sha256"
    return {"algoritmo": algoritmo, "escopo": ESCOPO_ASSINATURA, "valor": valor}


def _caminho_relativo(caminho: Union[Path, str], base: Union[Path, str]) -> str:
    try:
        return Path(caminho).resolve().relative_to(Path(base).resolve()).as_posix()
    except ValueError:
        return str(Path(caminho).resolve())


def localizar_ultima_sessao(repo_root: Union[Path, str]) -> Optional[Path]:
    """Última sessão de diagnose (Ticket 1). Fonte única: cli.localizar_ultima_sessao."""
    nome = "aidd_diagnose_cli"
    cli = sys.modules.get(nome)
    if cli is None:
        spec = importlib.util.spec_from_file_location(nome, str(Path(__file__).resolve().parent / "cli.py"))
        cli = importlib.util.module_from_spec(spec)
        sys.modules[nome] = cli
        spec.loader.exec_module(cli)
    return cli.localizar_ultima_sessao(Path(repo_root))


def persistir_sessao(
    sessao_path: Union[Path, str], atualizacoes: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Persiste o estado da diagnose entre fases em sessao.json (Ticket 1).
    Atualiza o JSON existente (sintoma, data_inicio, fase_atual, fases_completadas)
    com os novos campos de emissão, em escrita atômica (tmp + os.replace).
    """
    sessao = Path(sessao_path)
    if sessao.is_file():
        dados = json.loads(sessao.read_text(encoding="utf-8"))
    else:
        dados = {}
    if not isinstance(dados, dict):
        raise ValueError(f"sessao.json com raiz inválida (esperado objeto): {sessao}")
    dados.update(atualizacoes)
    sessao.parent.mkdir(parents=True, exist_ok=True)
    temporario = sessao.with_name(sessao.name + ".tmp")
    temporario.write_text(
        json.dumps(dados, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    os.replace(temporario, sessao)
    return dados


def construir_handoff(
    status: str,
    codigo_saida: int,
    repo_root: Union[Path, str],
    causa_raiz: str,
    arquivos_alterados: Iterable[Union[Path, str]],
    teste_regressao: Union[Path, str],
    gate_status: str,
    proxima_ferramenta: Optional[str],
    sessao_dir: Optional[Union[Path, str]] = None,
    detalhes: Optional[Dict[str, Any]] = None,
    erro: Optional[str] = None,
    artefatos: Optional[Iterable[Union[Path, str]]] = None,
) -> Dict[str, Any]:
    """Monta o envelope canônico assinado do diagnóstico consolidado (D15)."""
    if status not in STATUS_VALIDOS:
        raise ValueError(
            f"Status de handoff inválido: {status!r}. Esperado um de {STATUS_VALIDOS}."
        )
    base = Path(repo_root)
    liberada = status == "SUCESSO" and codigo_saida == 0

    if not causa_raiz or not str(causa_raiz).strip():
        raise ValueError("causa_raiz é obrigatória para emitir handoff-diagnose.json.")
    arquivos = [Path(a) for a in arquivos_alterados]
    if not arquivos:
        raise ValueError("arquivos_alterados deve conter ao menos um caminho.")
    if not str(teste_regressao).strip():
        raise ValueError("teste_regressao é obrigatório para emitir handoff-diagnose.json.")
    if not gate_status or not str(gate_status).strip():
        raise ValueError("gate_status é obrigatório (status do G_aidd_diagnose).")

    if liberada:
        if proxima_ferramenta not in FERRAMENTAS_PROXIMAS:
            raise ValueError(
                f"Diagnóstico SUCESSO exige 'proxima_ferramenta' em {FERRAMENTAS_PROXIMAS}; "
                f"recebido {proxima_ferramenta!r}."
            )
        proxima_fase = proxima_ferramenta
    else:
        proxima_fase = None
        if proxima_ferramenta not in (None,) + FERRAMENTAS_PROXIMAS:
            raise ValueError(
                f"proxima_ferramenta inválida: {proxima_ferramenta!r}. "
                f"Esperado uma de {FERRAMENTAS_PROXIMAS} ou None."
            )

    arquivos_relativos = [_caminho_relativo(a, base) for a in arquivos]
    dados: Dict[str, Any] = {
        "versao_schema": VERSAO_SCHEMA,
        "ferramenta": FERRAMENTA,
        "status": status,
        "codigo_saida": codigo_saida,
        "emitido_em": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "sessao": _caminho_relativo(Path(sessao_dir), base) if sessao_dir else None,
        "transicao": {
            "fase_atual": FASE_ATUAL,
            "proxima_fase": proxima_fase,
            "liberada": liberada,
            "requer_aprovacao_humana": True,
        },
        "diagnose": {
            "causa_raiz": str(causa_raiz),
            "arquivos_alterados": arquivos_relativos,
            "teste_regressao": _caminho_relativo(Path(teste_regressao), base),
            "gate": NOME_GATE,
            "gate_status": str(gate_status),
        },
        "proxima_ferramenta": proxima_ferramenta,
        "artefatos": [
            {"caminho": _caminho_relativo(a, base), "sha256": sha256_arquivo(a)}
            for a in (artefatos or arquivos + [Path(teste_regressao)])
        ],
    }
    if detalhes:
        dados["detalhes"] = detalhes
    if erro:
        dados["erro"] = str(erro)

    dados["assinatura"] = _calcular_assinatura(dados, os.environ.get(VAR_CHAVE))
    return dados


def emitir_handoff(
    sessao_dir: Optional[Union[Path, str]] = None,
    handoff_path: Optional[Union[Path, str]] = None,
    repo_root: Optional[Union[Path, str]] = None,
    status: str = "SUCESSO",
    codigo_saida: int = 0,
    causa_raiz: Optional[str] = None,
    arquivos_alterados: Optional[Iterable[Union[Path, str]]] = None,
    teste_regressao: Optional[Union[Path, str]] = None,
    gate_status: str = "APROVADO",
    proxima_ferramenta: Optional[str] = None,
    detalhes: Optional[Dict[str, Any]] = None,
    erro: Optional[str] = None,
    artefatos: Optional[Iterable[Union[Path, str]]] = None,
) -> Dict[str, Any]:
    """
    Constrói, assina e grava atomicamente docs/diagnosticos/<data>_<slug>/handoff-diagnose.json.
    Ao final, persiste o estado da emissão em sessao.json (Ticket 1).
    Retorna o envelope gravado.
    """
    base = Path(repo_root) if repo_root else _encontrar_raiz_repo()
    if sessao_dir is None:
        sessao_dir = localizar_ultima_sessao(base)
    if sessao_dir is not None:
        sessao_dir = Path(sessao_dir)

    if handoff_path is None:
        if sessao_dir is None:
            raise ValueError(
                "Não foi possível determinar a sessão: informe --sessao-dir ou "
                "--repo-root com docs/diagnosticos/<data>_<slug>/."
            )
        handoff_path = sessao_dir / NOME_ARQUIVO_HANDOFF

    destino = Path(handoff_path)
    dados = construir_handoff(
        status=status,
        codigo_saida=codigo_saida,
        repo_root=base,
        causa_raiz=causa_raiz or "",
        arquivos_alterados=arquivos_alterados or [],
        teste_regressao=teste_regressao or "",
        gate_status=gate_status,
        proxima_ferramenta=proxima_ferramenta,
        sessao_dir=sessao_dir,
        detalhes=detalhes,
        erro=erro,
        artefatos=artefatos,
    )

    destino.parent.mkdir(parents=True, exist_ok=True)
    temporario = destino.with_name(destino.name + ".tmp")
    temporario.write_text(
        json.dumps(dados, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    os.replace(temporario, destino)

    if sessao_dir is not None:
        sessao_path = sessao_dir / "sessao.json"
        if sessao_path.is_file():
            persistir_sessao(
                sessao_path,
                {
                    "fase_atual": FASE_FINAL,
                    "fases_completadas": _TODAS_FASES,
                    "status": dados["status"],
                    "proxima_ferramenta": dados["proxima_ferramenta"],
                    "handoff": _caminho_relativo(destino, base),
                    "emitido_em": dados["emitido_em"],
                },
            )
    return dados


def verificar_handoff(
    handoff_path: Union[Path, str],
    repo_root: Optional[Union[Path, str]] = None,
) -> List[str]:
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

    erros: List[str] = []

    for campo in (
        "versao_schema",
        "ferramenta",
        "status",
        "codigo_saida",
        "emitido_em",
        "transicao",
        "diagnose",
        "artefatos",
        "assinatura",
    ):
        if campo not in dados:
            erros.append(f"Campo obrigatório ausente: {campo}")
    if dados.get("versao_schema") != VERSAO_SCHEMA:
        erros.append(
            f"versao_schema inesperado: {dados.get('versao_schema')!r} (esperado {VERSAO_SCHEMA!r})."
        )
    if dados.get("ferramenta") != FERRAMENTA:
        erros.append(
            f"Ferramenta inesperada: {dados.get('ferramenta')!r} (esperado {FERRAMENTA!r})."
        )
    if dados.get("status") not in STATUS_VALIDOS:
        erros.append(f"Status inválido: {dados.get('status')!r}.")

    diagnostico = dados.get("diagnose")
    if not isinstance(diagnostico, dict):
        erros.append("Campo 'diagnose' ausente ou inválido (esperado objeto).")
    else:
        for campo_diag in ("causa_raiz", "arquivos_alterados", "teste_regressao", "gate", "gate_status"):
            if not diagnostico.get(campo_diag):
                erros.append(f"Campo obrigatório ausente em diagnose: {campo_diag}")
        if diagnostico.get("gate") != NOME_GATE:
            erros.append(
                f"Gate de diagnose inesperado: {diagnostico.get('gate')!r} (esperado {NOME_GATE!r})."
            )
        if not isinstance(diagnostico.get("arquivos_alterados"), list) or not diagnostico.get("arquivos_alterados"):
            erros.append("diagnose.arquivos_alterados deve ser uma lista não vazia.")

    proxima_ferramenta = dados.get("proxima_ferramenta")
    liberada_esperada = dados.get("status") == "SUCESSO" and dados.get("codigo_saida") == 0
    if liberada_esperada and proxima_ferramenta not in FERRAMENTAS_PROXIMAS:
        erros.append(
            f"Transição incoerente: SUCESSO sem próxima ferramenta válida "
            f"({proxima_ferramenta!r} ≠ {FERRAMENTAS_PROXIMAS})."
        )
    elif not liberada_esperada and proxima_ferramenta not in (None,) + FERRAMENTAS_PROXIMAS:
        erros.append(f"proxima_ferramenta inválida: {proxima_ferramenta!r}.")

    transicao = dados.get("transicao")
    if not isinstance(transicao, dict):
        erros.append("Campo 'transicao' ausente ou inválido (esperado objeto).")
    else:
        if transicao.get("liberada") != liberada_esperada:
            erros.append(
                f"Transição incoerente: liberada={transicao.get('liberada')} com status "
                f"{dados.get('status')} e codigo_saida {dados.get('codigo_saida')}."
            )
        if liberada_esperada and transicao.get("proxima_fase") != proxima_ferramenta:
            erros.append(
                "Transição incoerente: proxima_fase não corresponde à próxima ferramenta."
            )
        if not liberada_esperada and transicao.get("proxima_fase") is not None:
            erros.append("Transição incoerente: FALHA/não-SUCESSO não pode direcionar próxima fase.")

    assinatura = dados.get("assinatura")
    if not isinstance(assinatura, dict) or "valor" not in assinatura:
        erros.append("Campo 'assinatura' ausente ou inválido.")
    else:
        chave = os.environ.get(VAR_CHAVE)
        if assinatura.get("algoritmo") == "hmac-sha256" and not chave:
            erros.append(f"Handoff assinado com hmac-sha256, mas a chave {VAR_CHAVE} não está definida.")
        chave_efetiva = chave if assinatura.get("algoritmo") == "hmac-sha256" else None
        esperado = _calcular_assinatura(dados, chave_efetiva)
        if not hmac.compare_digest(esperado["valor"], assinatura.get("valor", "")):
            erros.append("Assinatura inválida: payload do handoff foi alterado após a emissão.")

    base = Path(repo_root) if repo_root else caminho.parent
    for artefato in dados.get("artefatos", []):
        if not isinstance(artefato, dict) or not artefato.get("caminho"):
            erros.append("Artefato inválido: esperado objeto com 'caminho' e 'sha256'.")
            continue
        alvo = Path(artefato["caminho"])
        alvo = alvo if alvo.is_absolute() else base / alvo
        if not alvo.is_file():
            erros.append(f"Artefato não encontrado: {artefato['caminho']}")
        elif sha256_arquivo(alvo) != artefato.get("sha256"):
            erros.append(
                f"Artefato com sha256 divergente (alterado após o handoff): {artefato['caminho']}"
            )
    return erros


def transicionar_fase(
    handoff_path: Union[Path, str],
    repo_root: Optional[Union[Path, str]] = None,
) -> Dict[str, Any]:
    """
    Ponto de consumo do orquestrador: decide se diagnose -> próxima ferramenta
    (aidd-tdd | aidd-handoff) pode avançar.
    """
    erros = verificar_handoff(handoff_path, repo_root=repo_root)
    proxima_fase = None
    if not erros:
        dados = json.loads(Path(handoff_path).read_text(encoding="utf-8"))
        if not dados["transicao"]["liberada"]:
            motivo = dados.get("erro") or dados["status"]
            erros.append(f"Transição bloqueada: status {dados['status']} ({motivo}).")
        elif not dados["diagnose"].get("arquivos_alterados"):
            erros.append("Transição bloqueada: diagnóstico sem arquivos alterados registrados.")
        else:
            proxima_fase = dados["transicao"]["proxima_fase"]
    if erros:
        return {"liberada": False, "proxima_fase": None, "erros": erros}
    return {"liberada": True, "proxima_fase": proxima_fase, "erros": []}


def _cmd_emitir(args: Any) -> int:
    base = Path(args.repo_root) if args.repo_root else _encontrar_raiz_repo()
    sessao_dir = Path(args.sessao_dir) if args.sessao_dir else localizar_ultima_sessao(base)
    artefatos = (
        [p.strip() for p in args.artefatos.split(",") if p.strip()]
        if args.artefatos else None
    )
    proxima = args.proxima_ferramenta or None
    try:
        dados = emitir_handoff(
            sessao_dir=sessao_dir,
            handoff_path=args.handoff,
            repo_root=base,
            status=args.status,
            codigo_saida=args.codigo_saida,
            causa_raiz=args.causa_raiz,
            arquivos_alterados=[
                p.strip() for p in args.arquivos_alterados.split(",") if p.strip()
            ],
            teste_regressao=args.teste_regressao,
            gate_status=args.gate_status,
            proxima_ferramenta=proxima,
            erro=args.erro,
            artefatos=artefatos,
        )
    except ValueError as exc:
        print(f"[ERRO] {exc}")
        return 1
    print(
        f"[OK] handoff-diagnose.json emitido (status={dados['status']}, "
        f"liberada={dados['transicao']['liberada']}, próxima={dados['proxima_ferramenta']})."
    )
    return 0


def _cmd_transicionar(args: Any) -> int:
    base = Path(args.repo_root) if args.repo_root else _encontrar_raiz_repo()
    if args.handoff:
        caminho = Path(args.handoff)
    else:
        sessao = localizar_ultima_sessao(base)
        caminho = sessao / NOME_ARQUIVO_HANDOFF if sessao else base / NOME_ARQUIVO_HANDOFF
    resultado = transicionar_fase(caminho, repo_root=base)
    if resultado["liberada"]:
        print(
            f"[OK] Transição liberada para '{resultado['proxima_fase']}' "
            "(requer aprovação humana)."
        )
        return 0
    print("[REPROVADO] Transição bloqueada.")
    for erro in resultado["erros"]:
        print(f"  - {erro}")
    return 1


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse_parser()
    parsed = parser.parse_args(argv)
    if not parsed.comando:
        parser.print_help()
        return 1
    if parsed.comando == "emitir":
        return _cmd_emitir(parsed)
    if parsed.comando == "transicionar":
        return _cmd_transicionar(parsed)
    parser.print_help()
    return 1


def argparse_parser():
    """Aplica argparse de forma determinística (isolado para testabilidade)."""
    import argparse

    parser = argparse.ArgumentParser(
        prog="python .agents/skills/aidd-diagnose/scripts/handoff.py",
        description=(
            "Output Consolidado e Handoff Estruturado do aidd-diagnose (D15/Ticket 8): "
            "emite e verifica handoff-diagnose.json."
        ),
    )
    sub = parser.add_subparsers(dest="comando", help="Comandos disponíveis")

    p_emitir = sub.add_parser("emitir", help="Emite docs/diagnosticos/<data>_<slug>/handoff-diagnose.json")
    p_emitir.add_argument("--sessao-dir", default=None, help="Diretório da sessão (default: última em docs/diagnosticos)")
    p_emitir.add_argument("--handoff", default=None, help="Caminho de saída do handoff")
    p_emitir.add_argument("--repo-root", default=None, help="Raiz do repositório")
    p_emitir.add_argument("--causa-raiz", required=True, help="Causa-raiz do diagnóstico")
    p_emitir.add_argument("--arquivos-alterados", required=True, help="Caminhos separados por vírgula")
    p_emitir.add_argument("--teste-regressao", required=True, help="Caminho do teste de regressão")
    p_emitir.add_argument("--gate-status", default="APROVADO", help="Status do G_aidd_diagnose")
    p_emitir.add_argument("--proxima-ferramenta", default=None, choices=list(FERRAMENTAS_PROXIMAS), help="Próxima ferramenta (aidd-tdd ou aidd-handoff)")
    p_emitir.add_argument("--status", default="SUCESSO", choices=list(STATUS_VALIDOS))
    p_emitir.add_argument("--codigo-saida", type=int, default=0)
    p_emitir.add_argument("--erro", default=None)
    p_emitir.add_argument("--artefatos", default=None, help="Caminhos separados por vírgula (default: arquivos alterados + teste de regressão)")

    p_trans = sub.add_parser("transicionar", help="Decide a liberação diagnose -> próxima ferramenta")
    p_trans.add_argument("--handoff", default=None, help="Caminho do handoff (default: última sessão)")
    p_trans.add_argument("--repo-root", default=None, help="Raiz do repositório")
    return parser


if __name__ == "__main__":
    sys.exit(main())