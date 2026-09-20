#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hook de Enforcement da Regra Canônica #7 (Zero Subagentes Headless / Anti-Concorrência).
Intercepta chamadas a ferramentas de subagentes (Task, Agent, invoke_subagent)
e bloqueia lançamentos concorrentes ou paralelos não autorizados explicitamente
pelo usuário humano.

Regras de Interceptação:
1. Lançamento Paralelo em Batch: Mais de 1 subagente solicitado na mesma chamada
   sem confirmação explícita é estritamente BLOQUEADO.
2. Lançamento Concorrente em Runtime: Tentativa de iniciar um subagente enquanto outro
   já está registrado como ativo sem confirmação explícita é estritamente BLOQUEADA.
3. Caminho Legítimo: Chamadas com confirmação explícita (campo `user_confirmed`: true,
   `explicit_confirm`: true, argumento `--confirmed` ou env `AIDD_SUBAGENT_CONFIRMED=1`)
   são PERMITIDAS.

Retorno:
  - Exit 0: Permitido (execução sequencial ou autorizada explicitamente).
  - Exit 2 (ou 1 em CLI direto): Bloqueado com mensagem detalhada de violação no stderr.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

for stream in (sys.stdin, sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


HOOK_DIR = Path(__file__).resolve().parent
DEFAULT_LOCK_PATH = Path(os.environ.get("AIDD_SUBAGENT_LOCK_FILE", HOOK_DIR / "subagent_active.lock"))
LOCK_TTL_SECONDS = 300  # 5 minutos para expiração de agentes órfãos


def is_process_alive(pid: int) -> bool:
    """Verifica se o processo com o pid informado ainda existe no SO de forma agnóstica."""
    if pid <= 0:
        return False
    try:
        if sys.platform == "win32":
            import ctypes
            kernel32 = ctypes.windll.kernel32
            SYNCHRONIZE = 0x00100000
            process = kernel32.OpenProcess(SYNCHRONIZE, False, pid)
            if process != 0:
                kernel32.CloseHandle(process)
                return True
            return False
        else:
            os.kill(pid, 0)
            return True
    except (OSError, PermissionError, AttributeError):
        return False


def checar_confirmacao_explicita(payload: Dict[str, Any], cli_confirmed: bool) -> bool:
    """Verifica se a confirmação explícita do usuário foi fornecida."""
    if cli_confirmed:
        return True
    if os.environ.get("AIDD_SUBAGENT_CONFIRMED", "").strip() in ("1", "true", "True", "yes"):
        return True

    # Checar no payload
    if payload.get("user_confirmed") is True or payload.get("explicit_confirm") is True:
        return True

    tool_input = payload.get("tool_input", {})
    if isinstance(tool_input, dict):
        if tool_input.get("user_confirmed") is True or tool_input.get("explicit_confirm") is True:
            return True
        if tool_input.get("confirmed") is True:
            return True

    return False


def detectar_paralelismo_no_payload(payload: Dict[str, Any]) -> Tuple[bool, str]:
    """Detecta se o payload solicita múltiplos subagentes em paralelo."""
    tool_input = payload.get("tool_input", {})
    if not isinstance(tool_input, dict):
        return False, ""

    # Caso 1: Array de subagentes com len > 1
    subagents = tool_input.get("subagents") or tool_input.get("Subagents")
    if isinstance(subagents, list) and len(subagents) > 1:
        return True, f"Tentativa de disparar {len(subagents)} subagentes em lote paralelo na mesma chamada."

    # Caso 2: Flag explícita de paralelismo não autorizado
    if tool_input.get("parallel") is True:
        return True, "Tentativa de execução paralela marcada via flag 'parallel: true'."

    return False, ""


def checar_concorrencia_ativa(lock_path: Path, current_pid: int) -> Tuple[bool, str]:
    """Verifica se há outro subagente ativo registrado no lockfile."""
    if not lock_path.exists():
        return False, ""

    try:
        conteudo = json.loads(lock_path.read_text(encoding="utf-8"))
        active_pid = conteudo.get("pid")
        ts = conteudo.get("timestamp", 0)
        agente_nome = conteudo.get("agent_name", "subagente-desconhecido")

        agora = time.time()
        # Se expirou por TTL, ignora lock antigo
        if agora - ts > LOCK_TTL_SECONDS:
            try:
                lock_path.unlink()
            except OSError:
                pass
            return False, ""

        # Se o processo registrado não estiver mais vivo, libera lock
        if active_pid and not is_process_alive(active_pid):
            try:
                lock_path.unlink()
            except OSError:
                pass
            return False, ""

        # Se o lock pertence ao próprio processo atual, permite prosseguir
        if active_pid == current_pid:
            return False, ""

        return True, f"Subagente '{agente_nome}' (PID {active_pid}) ja esta em execucao ativa."
    except Exception:
        return False, ""


def registrar_subagente_ativo(lock_path: Path, pid: int, agent_name: str) -> None:
    """Registra subagente ativo no lockfile."""
    dados = {
        "pid": pid,
        "agent_name": agent_name,
        "timestamp": time.time(),
    }
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text(json.dumps(dados, indent=2), encoding="utf-8")


def liberar_subagente_ativo(lock_path: Path) -> None:
    """Remove o lockfile de subagente ativo."""
    if lock_path.exists():
        try:
            lock_path.unlink()
        except OSError:
            pass


def interceptar(
    payload: Dict[str, Any],
    lock_path: Path = DEFAULT_LOCK_PATH,
    cli_confirmed: bool = False,
    register_on_success: bool = True,
    current_pid: Optional[int] = None,
) -> Tuple[int, str]:
    """
    Avalia a chamada de subagente.
    Retorna (código_de_saída, mensagem).
    0 = Permitido
    2 = Bloqueado (convenção Claude Code PreToolUse)
    """
    if current_pid is None:
        current_pid = os.getpid()

    is_confirmed = checar_confirmacao_explicita(payload, cli_confirmed)

    # 1. Verificar paralelismo na chamada
    eh_paralelo, motivo_paralelo = detectar_paralelismo_no_payload(payload)
    if eh_paralelo and not is_confirmed:
        msg = (
            f"[BLOQUEIO G_ZERO_HEADLESS] Lançamento de subagentes em paralelo bloqueado!\n"
            f"  Motivo: {motivo_paralelo}\n"
            f"  Violação: Lei Canônica #7 (Zero Subagentes Headless / Concorrência Silenciosa).\n"
            f"  Ação Requerida: Exija confirmação humana explícita do operador antes de disparar agentes paralelos."
        )
        return 2, msg

    # 2. Verificar concorrência em runtime com agente já ativo
    eh_concorrente, motivo_concorrente = checar_concorrencia_ativa(lock_path, current_pid)
    if eh_concorrente and not is_confirmed:
        msg = (
            f"[BLOQUEIO G_ZERO_HEADLESS] Lançamento concorrente de subagente bloqueado!\n"
            f"  Motivo: {motivo_concorrente}\n"
            f"  Violação: Lei Canônica #7 (Execuções estritamente sequenciais e interativas).\n"
            f"  Ação Requerida: Aguarde a finalização do subagente ativo ou obtenha confirmação humana explícita."
        )
        return 2, msg

    # 3. Lançamento Permitido
    if is_confirmed:
        msg_permissao = "[PERMITIDO] Lançamento de subagente autorizado com confirmação explícita do usuário."
    else:
        msg_permissao = "[PERMITIDO] Lançamento sequencial e interativo autorizado."

    if register_on_success:
        tool_name = payload.get("tool_name", "subagent")
        registrar_subagente_ativo(lock_path, current_pid, tool_name)

    return 0, msg_permissao


def main() -> int:
    parser = argparse.ArgumentParser(description="Hook de proteção anti-headless e anti-concorrência de subagentes.")
    parser.add_argument("--tool", default="Task", help="Nome da ferramenta (ex: Task, Agent, invoke_subagent)")
    parser.add_argument("--input", default="{}", help="Payload JSON da ferramenta")
    parser.add_argument("--confirmed", action="store_true", help="Sinaliza confirmação humana explícita")
    parser.add_argument("--lock-file", default=None, help="Caminho alternativo para o arquivo de lock")
    parser.add_argument("--release-lock", action="store_true", help="Libera o lockfile ativo")
    parser.add_argument("--exit-code-on-block", type=int, default=2, help="Código de saída em caso de bloqueio (padrão: 2)")

    args = parser.parse_args()

    lock_path = Path(args.lock_file) if args.lock_file else DEFAULT_LOCK_PATH

    if args.release_lock:
        liberar_subagente_ativo(lock_path)
        print("[OK] Lock de subagente liberado com sucesso.")
        return 0

    # Determinar payload
    payload: Dict[str, Any] = {}
    if not sys.stdin.isatty():
        try:
            stdin_data = sys.stdin.read().strip()
            if stdin_data:
                payload = json.loads(stdin_data)
        except Exception:
            pass

    if not payload:
        try:
            parsed_input = json.loads(args.input)
        except Exception:
            parsed_input = {}
        payload = {
            "tool_name": args.tool,
            "tool_input": parsed_input,
        }

    exit_code, msg = interceptar(
        payload=payload,
        lock_path=lock_path,
        cli_confirmed=args.confirmed,
        register_on_success=True,
    )

    if exit_code != 0:
        sys.stderr.write(msg + "\n")
        # Retorna o código configurado (ex: 2 para Claude Code, ou custom)
        return args.exit_code_on_block if args.exit_code_on_block != 2 else exit_code
    else:
        print(msg)
        return 0


if __name__ == "__main__":
    sys.exit(main())
