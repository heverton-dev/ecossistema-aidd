import ctypes
from ctypes import wintypes
import time

class STARTUPINFOW(ctypes.Structure):
    _fields_ = [
        ('cb', wintypes.DWORD),
        ('lpReserved', wintypes.LPWSTR),
        ('lpDesktop', wintypes.LPWSTR),
        ('lpTitle', wintypes.LPWSTR),
        ('dwX', wintypes.DWORD),
        ('dwY', wintypes.DWORD),
        ('dwXSize', wintypes.DWORD),
        ('dwYSize', wintypes.DWORD),
        ('dwXCountChars', wintypes.DWORD),
        ('dwYCountChars', wintypes.DWORD),
        ('dwFillAttribute', wintypes.DWORD),
        ('dwFlags', wintypes.DWORD),
        ('wShowWindow', wintypes.WORD),
        ('cbReserved2', wintypes.WORD),
        ('lpReserved2', ctypes.c_void_p),
        ('hStdInput', wintypes.HANDLE),
        ('hStdOutput', wintypes.HANDLE),
        ('hStdError', wintypes.HANDLE),
    ]

class PROCESS_INFORMATION(ctypes.Structure):
    _fields_ = [
        ('hProcess', wintypes.HANDLE),
        ('hThread', wintypes.HANDLE),
        ('dwProcessId', wintypes.DWORD),
        ('dwThreadId', wintypes.DWORD),
    ]

def main():
    si = STARTUPINFOW()
    si.cb = ctypes.sizeof(STARTUPINFOW)
    si.lpDesktop = "WinSta0\\Default"
    si.dwFlags = 1  # STARTF_USESHOWWINDOW
    si.wShowWindow = 5  # SW_SHOW

    pi = PROCESS_INFORMATION()

    cmd = (
        'cmd.exe /k "'
        'title AIDD_TTY_EFEMERO_POPUP && '
        'color 0B && '
        'echo ============================================================ && '
        'echo   AIDD ECOSSISTEMA - TTY EFEMERO POP-UP AO VIVO NO MONITOR   && '
        'echo ============================================================ && '
        'echo. && '
        'echo Este e o terminal nativo onde o agente roda e imprime tudo! && '
        'agy --version && '
        'echo. && '
        'echo Pressione qualquer tecla ou feche a janela quando ver... && '
        'pause > nul"'
    )

    kernel32 = ctypes.windll.kernel32
    res = kernel32.CreateProcessW(
        None,
        cmd,
        None,
        None,
        False,
        0x00000010,  # CREATE_NEW_CONSOLE
        None,
        None,
        ctypes.byref(si),
        ctypes.byref(pi)
    )

    print("CreateProcessW:", bool(res), "PID:", pi.dwProcessId)
    kernel32.CloseHandle(pi.hProcess)
    kernel32.CloseHandle(pi.hThread)

if __name__ == "__main__":
    main()
