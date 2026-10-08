"""Funções comuns dos scripts da skill aidd-9router (leitura do .env, chamadas HTTP, Orca)."""
import json
import os
import re
import urllib.error
import urllib.request
import uuid
from pathlib import Path

PADRAO_COMBOS = {"opus": "code-pro", "sonnet": "code-fast", "haiku": "code-tests", "fable": "code-free"}
TODOS_COMBOS = ["code-fast", "code-pro", "code-free", "task-micro", "code-tests"]
LIMITES_COMBOS = {
    "code-fast": {"context": 1000000, "output": 65536},
    "code-pro": {"context": 1000000, "output": 65536},
    "code-free": {"context": 1000000, "output": 65536},
    "task-micro": {"context": 1000000, "output": 32000},
    "code-tests": {"context": 1000000, "output": 65536},
}
PROVEDOR = "aidd9r"
MARCADOR_DESLIGADO = Path.home() / ".aidd" / "9router-desligado"
INFLACAO_9ROUTER = 2000


def achar_env():
    """Primeiro .env subindo a partir da pasta atual; depois a partir deste script."""
    for pasta in [Path.cwd(), *Path.cwd().parents, *Path(__file__).resolve().parents]:
        env = pasta / ".env"
        if env.is_file():
            return env
    return None


def ler_env(nome, padrao=""):
    if os.environ.get(nome):
        return os.environ[nome]
    env = achar_env()
    if env:
        m = re.search(rf'^{nome}=["\']?([^"\'\r\n]*)', env.read_text(encoding="utf-8"), re.M)
        if m and m.group(1).strip():
            return m.group(1).strip()
    return padrao


def gateway():
    return (ler_env("NINEROUTER_URL") or "http://localhost:20128").rstrip("/")


def mapa_combos():
    return {nivel: ler_env(f"NINEROUTER_{nivel.upper()}") or combo for nivel, combo in PADRAO_COMBOS.items()}


def chat(modelo, prompt, max_tokens=300, chave=None, economizador=False, timeout=180, url=None):
    """POST /v1/chat/completions sem streaming. Devolve (status_http, json_ou_texto)."""
    cab = {"Content-Type": "application/json"}
    chave = ler_env("NINEROUTER_KEY") if chave is None else chave
    if chave:
        cab["Authorization"] = f"Bearer {chave}"
    if not economizador:
        cab["X-9Router-Token-Saver"] = "off"
    corpo = json.dumps({"model": modelo, "stream": False, "max_tokens": max_tokens,
                        "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request(f"{url or gateway()}/v1/chat/completions", corpo, cab)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:300].decode("utf-8", "replace")
    except Exception as e:  # rede, timeout
        return 0, f"{type(e).__name__}: {e}"


def orca_rpc(metodo, params=None):
    """Chama o runtime local do Orca pelo named pipe (mesmo caminho da CLI). Devolve o JSON da resposta."""
    rt = json.loads((Path(os.path.expandvars(r"%APPDATA%")) / "orca" / "orca-runtime.json").read_text(encoding="utf-8"))
    pipe = next(t["endpoint"] for t in rt["transports"] if t["kind"] == "named-pipe")
    msg = {"id": str(uuid.uuid4()), "authToken": rt["authToken"], "method": metodo, "params": params}
    with open(pipe, "r+b", buffering=0) as f:
        f.write((json.dumps(msg) + "\n").encode())
        buf = b""
        while b"\n" not in buf:
            parte = f.read(65536)
            if not parte:
                break
            buf += parte
    return json.loads(buf.split(b"\n")[0])
