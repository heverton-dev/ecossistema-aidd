# -*- coding: utf-8 -*-
"""
scripts/fila_ciclos.py — um ciclo pesado por vez, com aviso ao terminar.

Em 30/09/2026 até 4 ciclos 4F rodavam juntos numa máquina de 16 GB: cada suíte de
3 min passava de 20, e a falta de memória derrubou processos. Esta fila:
  - usa uma trava em arquivo (.aidd/fila-ciclos.lock: pid, ciclo, início); o segundo
    ciclo espera, avisando de tempos em tempos, em vez de rodar em paralelo;
  - libera trava órfã (processo dono já morreu);
  - no fim, com sucesso ou falha, grava secoes/medicoes/ultimo-ciclo.json e dispara
    um aviso local do sistema, para ninguém precisar "voltar daqui a 30 minutos".
"""

import contextlib
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

TRAVA = Path(".aidd") / "fila-ciclos.lock"
ULTIMO_CICLO = Path("secoes") / "medicoes" / "ultimo-ciclo.json"


def processo_vivo(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        # os.kill(pid, 0) no Windows não é consulta: 0 == CTRL_C_EVENT. Consulta via Win32.
        import ctypes
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
        if not handle:
            return False
        try:
            codigo = ctypes.c_ulong()
            kernel32.GetExitCodeProcess(handle, ctypes.byref(codigo))
            return codigo.value == 259  # STILL_ACTIVE
        finally:
            kernel32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _ler_trava(caminho: Path):
    try:
        return json.loads(caminho.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def adquirir(ciclo: str, raiz: Path, intervalo_s: float = 30.0, avisar=print, timeout_s=None) -> Path:
    """Bloqueia até a trava ficar livre e a toma para `ciclo`. Devolve o caminho da trava."""
    caminho = Path(raiz) / TRAVA
    caminho.parent.mkdir(parents=True, exist_ok=True)
    inicio = time.monotonic()
    anunciado = None
    while True:
        try:
            fd = os.open(caminho, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            dono = _ler_trava(caminho)
            if dono is None or not processo_vivo(int(dono.get("pid", 0))):
                avisar(f"[FILA] Trava órfã de '{(dono or {}).get('ciclo', '?')}' liberada (processo encerrado).")
                with contextlib.suppress(FileNotFoundError):
                    caminho.unlink()
                continue
            if timeout_s is not None and time.monotonic() - inicio > timeout_s:
                raise TimeoutError(f"fila ocupada por '{dono.get('ciclo')}' há mais de {timeout_s}s")
            if anunciado != dono.get("ciclo"):
                avisar(f"[FILA] Aguardando '{dono.get('ciclo')}' (pid {dono.get('pid')}, desde {dono.get('inicio')}) "
                       f"terminar: um ciclo pesado por vez.")
                anunciado = dono.get("ciclo")
            time.sleep(intervalo_s)
            continue
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump({"pid": os.getpid(), "ciclo": ciclo,
                       "inicio": datetime.now(timezone.utc).isoformat(timespec="seconds")}, f)
        return caminho


def notificar(titulo: str, mensagem: str) -> bool:
    """Aviso local do sistema; devolve False (e só imprime) quando não há como avisar."""
    comando = None
    if os.name == "nt":
        script = ("Add-Type -AssemblyName System.Windows.Forms;"
                  "$n=New-Object System.Windows.Forms.NotifyIcon;$n.Icon=[System.Drawing.SystemIcons]::Information;"
                  f"$n.Visible=$true;$n.ShowBalloonTip(10000,'{titulo}','{mensagem}',"
                  "[System.Windows.Forms.ToolTipIcon]::Info);Start-Sleep 10;$n.Dispose()")
        comando = ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", script]
    elif sys.platform == "darwin" and shutil.which("osascript"):
        comando = ["osascript", "-e", f'display notification "{mensagem}" with title "{titulo}"']
    elif shutil.which("notify-send"):
        comando = ["notify-send", titulo, mensagem]
    print(f"[AVISO] {titulo}: {mensagem}")
    if not comando:
        return False
    try:
        subprocess.Popen(comando, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except OSError:
        return False


def liberar(ciclo: str, resultado: str, raiz: Path, notificador=notificar) -> None:
    """Solta a trava (só se for deste processo), grava o resultado e avisa."""
    caminho = Path(raiz) / TRAVA
    dono = _ler_trava(caminho)
    if dono and int(dono.get("pid", 0)) == os.getpid():
        with contextlib.suppress(FileNotFoundError):
            caminho.unlink()
    registro = Path(raiz) / ULTIMO_CICLO
    registro.parent.mkdir(parents=True, exist_ok=True)
    registro.write_text(json.dumps({"ciclo": ciclo, "resultado": resultado,
                                    "fim": datetime.now(timezone.utc).isoformat(timespec="seconds")},
                                   ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    notificador(f"Ciclo {resultado}", f"{ciclo} terminou: {resultado}.")


@contextlib.contextmanager
def ciclo_pesado(ciclo: str, raiz: Path, **kwargs):
    """Com a trava do ciclo; no fim (inclusive por sys.exit ou erro) libera e avisa."""
    notificador = kwargs.pop("notificador", notificar)
    adquirir(ciclo, raiz, **kwargs)
    resultado = "reprovado"
    try:
        yield
        resultado = "concluido"
    except SystemExit as saida:
        resultado = "concluido" if saida.code in (0, None) else "reprovado"
        raise
    finally:
        liberar(ciclo, resultado, raiz, notificador)
