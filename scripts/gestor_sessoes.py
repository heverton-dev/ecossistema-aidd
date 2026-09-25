# -*- coding: utf-8 -*-
"""
=============================================================================
GESTOR DETERMINÍSTICO DE SESSÕES AGÊNTICAS (AIDD-SESSAO)
=============================================================================
Gerencia o registro e consulta de IDs de sessões agênticas entre harnesses.
Persiste em JSON estruturado (secoes/historico_sessoes.json) e espelho Markdown.

Conforme Leis #1 (Determinismo), #3 (Persistência Estruturada), #5 (Zero Stubs),
#6 (Agnóstico) e #13 (Prova que Morde).
=============================================================================
"""

import argparse
import datetime
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any

DEFAULT_JSON_PATH = "secoes/historico_sessoes.json"
DEFAULT_MD_PATH = "secoes/INDICE-SESSOES.md"


def carregar_historico(caminho_json: str) -> Dict[str, Any]:
    """Carrega o histórico de sessões do arquivo JSON."""
    caminho = Path(caminho_json)
    if not caminho.exists():
        return {
            "versao": "1.0",
            "atualizado_em": datetime.datetime.now().isoformat(),
            "total_sessoes": 0,
            "sessoes": []
        }
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            dados = json.load(f)
            if not isinstance(dados, dict) or "sessoes" not in dados:
                raise ValueError("Estrutura JSON inválida: chave 'sessoes' ausente.")
            return dados
    except Exception as exc:
        raise ValueError(f"Falha ao carregar arquivo de sessões '{caminho_json}': {exc}")


def salvar_historico(dados: Dict[str, Any], caminho_json: str, gerar_md: bool = True, caminho_md: str = DEFAULT_MD_PATH) -> None:
    """Salva os dados de histórico atomicamente no JSON e atualiza o espelho Markdown."""
    caminho = Path(caminho_json)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    
    dados["total_sessoes"] = len(dados.get("sessoes", []))
    dados["atualizado_em"] = datetime.datetime.now().isoformat()

    # Gravação atômica em JSON
    tmp_file = caminho.with_suffix(".tmp")
    with open(tmp_file, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)
    tmp_file.replace(caminho)

    if gerar_md:
        atualizar_espelho_markdown(dados, caminho_md)


def atualizar_espelho_markdown(dados: Dict[str, Any], caminho_md: str) -> None:
    """Gera um índice legível em Markdown a partir dos dados consolidados."""
    caminho = Path(caminho_md)
    caminho.parent.mkdir(parents=True, exist_ok=True)

    linhas = [
        "# 📑 Índice Canônico de Sessões Agênticas — Ecossistema AIDD",
        "",
        f"> **Total de Sessões Registradas:** {dados.get('total_sessoes', 0)}  ",
        f"> **Última Atualização:** {dados.get('atualizado_em', 'N/D')}",
        "",
        "| Data / Hora | Harness | Modelo | Conversation ID | Objetivo / Título | Workspace |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |",
    ]

    for s in reversed(dados.get("sessoes", [])):
        sess_id = s.get("id", "N/D")
        dt = s.get("registrado_em", "N/D")
        harness = s.get("harness", "desconhecido")
        modelo = s.get("modelo", "N/D")
        titulo = s.get("titulo", "Sem descrição").replace("|", "-")
        ws = s.get("workspace", ".").replace("\\", "/")
        
        # Link para o ID se houver transcript local conhecido
        transcript_path = s.get("transcript_path")
        if transcript_path and os.path.exists(transcript_path):
            id_link = f"[`{sess_id[:8]}...`](file:///{Path(transcript_path).as_posix()})"
        else:
            id_link = f"`{sess_id}`"

        linhas.append(f"| {dt} | `{harness}` | `{modelo}` | {id_link} | {titulo} | `{ws}` |")

    linhas.append("")
    with open(caminho, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas))


def registrar_sessao(
    session_id: str,
    harness: str = "antigravity",
    modelo: str = "auto",
    titulo: str = "Sessão Agêntica",
    workspace: Optional[str] = None,
    transcript_path: Optional[str] = None,
    caminho_json: str = DEFAULT_JSON_PATH,
    gerar_md: bool = True,
    caminho_md: str = DEFAULT_MD_PATH
) -> Dict[str, Any]:
    """Registra uma nova sessão de forma idempotente (atualiza se o ID já existir)."""
    if not session_id or not session_id.strip():
        raise ValueError("O parâmetro 'session_id' é obrigatório e não pode ser vazio.")

    session_id = session_id.strip()
    dados = carregar_historico(caminho_json)
    sessoes: List[Dict[str, Any]] = dados.setdefault("sessoes", [])

    # Verificar se ID já existe para atualizar
    existente = next((s for s in sessoes if s.get("id") == session_id), None)
    timestamp_agora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    registro = {
        "id": session_id,
        "registrado_em": timestamp_agora,
        "harness": harness or "desconhecido",
        "modelo": modelo or "N/D",
        "titulo": titulo or "Sessão Agêntica",
        "workspace": workspace or str(Path.cwd()),
        "transcript_path": transcript_path or ""
    }

    if existente:
        existente.update(registro)
        existente["atualizado_em"] = timestamp_agora
    else:
        sessoes.append(registro)

    salvar_historico(dados, caminho_json, gerar_md=gerar_md, caminho_md=caminho_md)
    return registro


def listar_sessoes(caminho_json: str = DEFAULT_JSON_PATH) -> List[Dict[str, Any]]:
    """Lista todas as sessões registradas."""
    dados = carregar_historico(caminho_json)
    return dados.get("sessoes", [])


def buscar_sessao(termo: str, caminho_json: str = DEFAULT_JSON_PATH) -> List[Dict[str, Any]]:
    """Busca sessões por ID parcial, título ou harness."""
    termo_lower = termo.lower()
    sessoes = listar_sessoes(caminho_json)
    return [
        s for s in sessoes
        if termo_lower in s.get("id", "").lower()
        or termo_lower in s.get("titulo", "").lower()
        or termo_lower in s.get("harness", "").lower()
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gestor_sessoes.py",
        description="Gestor determinístico de registro e busca de IDs de sessões agênticas."
    )
    subparsers = parser.add_subparsers(dest="acao", required=True)

    # Subcomando: registrar
    reg = subparsers.add_parser("registrar", help="Registra uma nova sessão ou atualiza existente.")
    reg.add_argument("--id", required=True, help="ID único da conversa / sessão.")
    reg.add_argument("--harness", default="antigravity", help="Nome do harness (antigravity, claude, etc).")
    reg.add_argument("--modelo", default="auto", help="Nome ou identificador do LLM em uso.")
    reg.add_argument("--titulo", default="Sessão Agêntica", help="Título descritivo ou objetivo da sessão.")
    reg.add_argument("--workspace", default=None, help="Diretório do workspace da sessão.")
    reg.add_argument("--transcript", default=None, help="Caminho do arquivo de logs/transcripts.")
    reg.add_argument("--arquivo", default=DEFAULT_JSON_PATH, help="Caminho do JSON de persistência.")
    reg.add_argument("--no-md", action="store_true", help="Desativa geração do espelho Markdown.")

    # Subcomando: listar
    lis = subparsers.add_parser("listar", help="Lista todas as sessões registradas.")
    lis.add_argument("--arquivo", default=DEFAULT_JSON_PATH, help="Caminho do JSON de persistência.")
    lis.add_argument("--json", action="store_true", help="Exibe resultado em JSON puro.")

    # Subcomando: buscar
    bus = subparsers.add_parser("buscar", help="Busca sessões por ID, título ou harness.")
    bus.add_argument("termo", help="Termo para busca.")
    bus.add_argument("--arquivo", default=DEFAULT_JSON_PATH, help="Caminho do JSON de persistência.")
    bus.add_argument("--json", action="store_true", help="Exibe resultado em JSON puro.")

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.acao == "registrar":
            reg = registrar_sessao(
                session_id=args.id,
                harness=args.harness,
                modelo=args.modelo,
                titulo=args.titulo,
                workspace=args.workspace,
                transcript_path=args.transcript,
                caminho_json=args.arquivo,
                gerar_md=not args.no_md
            )
            print(f"[OK] Sessão registrada com sucesso:")
            print(f"     ID:        {reg['id']}")
            print(f"     Harness:   {reg['harness']} | Modelo: {reg['modelo']}")
            print(f"     Título:    {reg['titulo']}")
            print(f"     Arquivo:   {args.arquivo}")
            return 0

        elif args.acao == "listar":
            sessoes = listar_sessoes(args.arquivo)
            if args.json:
                print(json.dumps(sessoes, indent=2, ensure_ascii=False))
            else:
                print(f"\nTotal de sessões registradas: {len(sessoes)}")
                print("-" * 80)
                for s in sessoes:
                    print(f"[{s['registrado_em']}] {s['id']} | {s['harness']} | {s['titulo']}")
            return 0

        elif args.acao == "buscar":
            encontradas = buscar_sessao(args.termo, args.arquivo)
            if args.json:
                print(json.dumps(encontradas, indent=2, ensure_ascii=False))
            else:
                print(f"\nResultados encontrados para '{args.termo}': {len(encontradas)}")
                print("-" * 80)
                for s in encontradas:
                    print(f"[{s['registrado_em']}] {s['id']} | {s['harness']} | {s['titulo']}")
            return 0

    except Exception as exc:
        print(f"[ERRO] {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
