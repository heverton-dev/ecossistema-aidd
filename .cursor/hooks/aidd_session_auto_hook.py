# -*- coding: utf-8 -*-
"""
AIDD: Hook determinístico de registro de sessão (Zero LLM).
Executado em PreInvocation pelos harnesses compatíveis (Antigravity CLI, Claude, etc).
Registra a sessão ativa em secoes/historico_sessoes.json e secoes/INDICE-SESSOES.md
sem qualquer consumo de tokens de LLM.
"""

import json
import os
import sys
from pathlib import Path


def main():
    try:
        raw_input = ""
        if not sys.stdin.isatty():
            try:
                raw_input = sys.stdin.readline()
            except Exception:
                pass

        payload = {}
        if raw_input and raw_input.strip():
            try:
                payload = json.loads(raw_input)
            except Exception:
                pass

        conv_id = (
            payload.get("conversationId")
            or os.environ.get("CONVERSATION_ID")
            or os.environ.get("ANTIGRAVITY_CONVERSATION_ID")
        )

        if conv_id:
            # Localizar raiz do repositório procurando por ecossistema.py
            current_dir = Path(__file__).resolve().parent
            repo_root = current_dir
            for parent in [current_dir] + list(current_dir.parents):
                if (parent / "ecossistema.py").exists():
                    repo_root = parent
                    break

            if str(repo_root) not in sys.path:
                sys.path.insert(0, str(repo_root))

            from scripts.gestor_sessoes import registrar_sessao

            workspace = None
            ws_paths = payload.get("workspacePaths") or []
            if ws_paths:
                workspace = ws_paths[0]
            else:
                workspace = str(repo_root)

            transcript_path = payload.get("transcriptPath")
            if not transcript_path:
                # Tenta localizar o transcript no caminho padrão do AGY/Antigravity
                user_home = Path.home()
                candidato_transcript = (
                    user_home
                    / ".gemini"
                    / "antigravity-cli"
                    / "brain"
                    / conv_id
                    / ".system_generated"
                    / "logs"
                    / "transcript.jsonl"
                )
                if candidato_transcript.exists():
                    transcript_path = str(candidato_transcript)

            model_name = payload.get("modelName", "auto")

            json_path = repo_root / "secoes" / "historico_sessoes.json"
            md_path = repo_root / "secoes" / "INDICE-SESSOES.md"

            registrar_sessao(
                session_id=conv_id,
                harness="antigravity",
                modelo=model_name,
                titulo="Sessão Ativa (Auto-Registrada)",
                workspace=workspace,
                transcript_path=transcript_path,
                caminho_json=str(json_path),
                gerar_md=True,
                caminho_md=str(md_path)
            )
    except Exception:
        # Falhas silenciosas no hook para nunca abortar o fluxo principal
        pass
    finally:
        # Contrato canônico PreInvocation (Antigravity CLI / AGY)
        sys.stdout.write(json.dumps({}) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()

