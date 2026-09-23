# -*- coding: utf-8 -*-
"""
AIDD-Melhoria CLI entrypoint and fallback interface.
Provides deterministic CLI processing for aidd-melhoria manifests and subcommands.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


def find_repo_root(start_path: Optional[Path] = None) -> Path:
    current = (start_path or Path(__file__)).resolve()
    candidates = [current] + list(current.parents)
    for parent in candidates:
        if (parent / "ecossistema.py").is_file():
            return parent
    return Path(__file__).resolve().parents[4]


REPO_ROOT = find_repo_root()
SCRIPTS_DIR = REPO_ROOT / "scripts"
SKILL_DIR = REPO_ROOT / ".agents" / "skills" / "aidd-melhoria" / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

try:
    from isolamento import validar_caminho_escrita, SandboxViolationError
except ImportError:
    try:
        from .isolamento import validar_caminho_escrita, SandboxViolationError
    except ImportError:
        def validar_caminho_escrita(caminho: Any, repo_root: Any, worktree_dir: Any = None) -> bool:
            return True


def gerar_handoff(
    handoff_path: Path,
    status: str,
    codigo_saida: int,
    manifesto: Optional[str] = None,
    detalhes: Optional[Dict[str, Any]] = None,
    erro: Optional[str] = None,
) -> None:
    """Emits structured handoff JSON file."""
    dados: Dict[str, Any] = {
        "ferramenta": "aidd-melhoria",
        "status": status,
        "codigo_saida": codigo_saida,
    }
    if manifesto:
        dados["manifesto"] = str(manifesto)
    if detalhes:
        dados["detalhes"] = detalhes
    if erro:
        dados["erro"] = str(erro)

    try:
        handoff_path.write_text(json.dumps(dados, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception as exc:
        sys.stderr.write(f"[AVISO] Falha ao gravar handoff em {handoff_path}: {exc}\n")


def processar_manifesto(
    manifest_path: str | Path,
    repo_root: Optional[Path] = None,
    handoff_path: Optional[Path] = None,
) -> int:
    root = (repo_root or REPO_ROOT).resolve()
    caminho_manifest = Path(manifest_path).resolve()
    handoff_dest = handoff_path or (root / "handoff-melhoria.json")

    if not caminho_manifest.is_file():
        msg_erro = f"Manifesto não encontrado: {caminho_manifest}"
        print(f"[ERRO] {msg_erro}")
        gerar_handoff(handoff_dest, "FALHA", 1, manifesto=str(caminho_manifest), erro=msg_erro)
        return 1

    try:
        conteudo = caminho_manifest.read_text(encoding="utf-8")
        dados = json.loads(conteudo)
    except Exception as exc:
        msg_erro = f"Falha ao decodificar JSON do manifesto: {exc}"
        print(f"[ERRO] {msg_erro}")
        gerar_handoff(handoff_dest, "FALHA", 1, manifesto=str(caminho_manifest), erro=msg_erro)
        return 1

    if not isinstance(dados, dict):
        msg_erro = "Manifesto inválido: JSON raiz deve ser um objeto/dicionário."
        print(f"[ERRO] {msg_erro}")
        gerar_handoff(handoff_dest, "FALHA", 1, manifesto=str(caminho_manifest), erro=msg_erro)
        return 1

    manifest_dados = dados.get("relatorio", dados)
    if not isinstance(manifest_dados, dict):
        msg_erro = "Envelope 'relatorio' inválido no manifesto."
        print(f"[ERRO] {msg_erro}")
        gerar_handoff(handoff_dest, "FALHA", 1, manifesto=str(caminho_manifest), erro=msg_erro)
        return 1

    pedido = manifest_dados.get("pedido")
    if not pedido:
        msg_erro = "Campo obrigatório 'pedido' ausente no manifesto."
        print(f"[ERRO] {msg_erro}")
        gerar_handoff(handoff_dest, "FALHA", 1, manifesto=str(caminho_manifest), erro=msg_erro)
        return 1

    destino_base = root / "docs" / "melhorias"
    try:
        validar_caminho_escrita(destino_base / "dummy_check.tmp", repo_root=root)
    except SandboxViolationError as exc:
        msg_erro = f"Violação de sandbox ao validar destino: {exc}"
        print(f"[ERRO] {msg_erro}")
        gerar_handoff(handoff_dest, "FALHA", 1, manifesto=str(caminho_manifest), erro=msg_erro)
        return 1

    try:
        import gerenciador_melhorias as gm
    except ImportError:
        msg_erro = "Módulo 'gerenciador_melhorias' não pôde ser importado."
        print(f"[ERRO] {msg_erro}")
        gerar_handoff(handoff_dest, "FALHA", 1, manifesto=str(caminho_manifest), erro=msg_erro)
        return 1

    itens_avaliados = manifest_dados.get("itens_avaliados") or []
    if isinstance(itens_avaliados, list) and itens_avaliados and isinstance(itens_avaliados[0], dict):
        itens_formatados = []
        for item_dict in itens_avaliados:
            item_nome = item_dict.get("item", "")
            item_status = item_dict.get("status", "nao-feito")
            item_just = item_dict.get("justificativa", "Sem justificativa")
            itens_formatados.append(f"{item_nome}::{item_status}::{item_just}")
        itens_avaliados = itens_formatados

    codigo_resultado = gm.cmd_init(
        pedido=pedido,
        nome=manifest_dados.get("nome"),
        nota_atual=manifest_dados.get("nota_atual"),
        evidencia=manifest_dados.get("evidencia"),
        resumo=manifest_dados.get("resumo"),
        achados=manifest_dados.get("achados") or [],
        riscos=manifest_dados.get("riscos") or [],
        recomendacao=manifest_dados.get("recomendacao"),
        destino_base=destino_base,
        plano_existente=manifest_dados.get("plano_existente"),
        item_relacionado=manifest_dados.get("item") or manifest_dados.get("item_relacionado"),
        itens_avaliados=itens_avaliados,
        sobrescrever=True,
    )

    if codigo_resultado == 0:
        detalhes = {
            "pedido": pedido,
            "nome": manifest_dados.get("nome"),
            "nota_atual": manifest_dados.get("nota_atual"),
            "destino_base": str(destino_base),
        }
        gerar_handoff(handoff_dest, "SUCESSO", 0, manifesto=str(caminho_manifest), detalhes=detalhes)
        print("[SUCESSO] Processamento concluído com sucesso.")
        return 0
    else:
        msg_erro = f"Falha na geração do relatório de melhoria (exit code {codigo_resultado})."
        gerar_handoff(handoff_dest, "FALHA", codigo_resultado, manifesto=str(caminho_manifest), erro=msg_erro)
        return codigo_resultado


def main(args: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="CLI Fallback e Interface Componentizada para aidd-melhoria")
    parser.add_argument("--manifest", help="Caminho do arquivo de manifesto JSON de entrada")
    parser.add_argument("--handoff", default=None, help="Caminho do arquivo de handoff a ser emitido")

    parsed, unknown = parser.parse_known_args(args)

    if parsed.manifest:
        return processar_manifesto(parsed.manifest, handoff_path=Path(parsed.handoff) if parsed.handoff else None)

    import gerenciador_melhorias as gm
    old_argv = sys.argv[:]
    try:
        sys.argv = [sys.argv[0]] + (args if args is not None else sys.argv[1:])
        gm.main()
        return 0
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 0
    finally:
        sys.argv = old_argv


if __name__ == "__main__":
    sys.exit(main())
