# -*- coding: utf-8 -*-
"""
Ticket 9 (skills-pocock ciclo-01, D11): template.sh do aidd-wizard rodado em bash real.

Teste de comportamento: carrega a biblioteca do template (tudo acima do marcador STAGES)
num bash de verdade e exercita write_env, ask_secret e open_url. Pula só se não houver
bash utilizável (Git Bash / bash nativo); o launcher do WSL (System32/WindowsApps) não
serve porque não enxerga os caminhos temporários do Windows.

Limite honesto: sem pseudo-terminal no Windows, "não ecoa" é provado pela saída do
processo (o valor digitado nunca aparece) + pelo uso de `read -rs`; o eco do terminal
em si não é observável aqui.
"""
import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = ROOT / "componentes" / "compartilhado" / "skills" / "aidd-wizard"
TEMPLATE = SKILL_DIR / "template.sh"
MARCADOR = "# STAGES:"


def _bash():
    candidatos = []
    achado = shutil.which("bash")
    if achado:
        candidatos.append(achado)
    candidatos += [
        r"C:\Program Files\Git\usr\bin\bash.exe",
        r"C:\Program Files\Git\bin\bash.exe",
        "/bin/bash",
        "/usr/bin/bash",
    ]
    for c in candidatos:
        baixo = c.lower()
        if "system32" in baixo or "windowsapps" in baixo:
            continue
        if os.path.isfile(c):
            return c
    return None


BASH = _bash()
precisa_bash = pytest.mark.skipif(BASH is None, reason="bash (Git Bash ou nativo) ausente no PATH")


def _posix(p: Path) -> str:
    return p.as_posix()


def _posix_path_entry(p: Path) -> str:
    """Entrada de PATH para bash: 'C:/x' vira '/c/x' (o ':' do drive quebraria o PATH)."""
    s = p.as_posix()
    if len(s) > 1 and s[1] == ":":
        s = "/" + s[0].lower() + s[2:]
    return s


def _biblioteca(tmp_path: Path) -> Path:
    texto = TEMPLATE.read_text(encoding="utf-8")
    assert MARCADOR in texto, "template sem marcador STAGES"
    lib = texto[: texto.index(MARCADOR)]
    destino = tmp_path / "lib.sh"
    destino.write_bytes(lib.encode("utf-8"))
    return destino


def _rodar(script: str, cwd: Path, entrada: str = "", env_extra=None):
    env = dict(os.environ)
    env.update(env_extra or {})
    return subprocess.run(
        [BASH, "-c", script],
        cwd=str(cwd),
        input=entrada.encode("utf-8"),
        capture_output=True,
        env=env,
        timeout=60,
    )


def test_template_e_skill_existem():
    assert TEMPLATE.is_file(), f"template ausente: {TEMPLATE}"
    assert (SKILL_DIR / "SKILL.md").is_file(), "SKILL.md do aidd-wizard ausente"


@precisa_bash
def test_bash_n_passa():
    r = subprocess.run([BASH, "-n", _posix(TEMPLATE)], capture_output=True, timeout=60)
    assert r.returncode == 0, r.stderr.decode("utf-8", "replace")


@precisa_bash
def test_write_env_idempotente(tmp_path):
    lib = _biblioteca(tmp_path)
    env_file = tmp_path / ".env"
    env_file.write_bytes(b"OUTRA=1\n")
    r = _rodar(
        f'source "{_posix(lib)}"; ENV_FILE="{_posix(env_file)}"; '
        'write_env API_KEY primeiro; write_env API_KEY segundo',
        tmp_path,
    )
    assert r.returncode == 0, r.stderr.decode("utf-8", "replace")
    linhas = env_file.read_text(encoding="utf-8").splitlines()
    assert [l for l in linhas if l.startswith("API_KEY=")] == ["API_KEY=segundo"]
    assert "OUTRA=1" in linhas


@precisa_bash
def test_entrada_oculta_nao_ecoa_e_captura(tmp_path):
    lib = _biblioteca(tmp_path)
    digitado = "valor-oculto-XYZ"
    r = _rodar(
        f'source "{_posix(lib)}"; ENV_FILE="{_posix(tmp_path / ".env")}"; '
        'ask_secret VALOR "Cole o valor:"; printf "len=%s\n" "${#VALOR}"',
        tmp_path,
        entrada=digitado + "\n",
    )
    assert r.returncode == 0, r.stderr.decode("utf-8", "replace")
    saida = (r.stdout + r.stderr).decode("utf-8", "replace")
    assert digitado not in saida, "ask_secret imprimiu o valor digitado"
    assert f"len={len(digitado)}" in saida, "ask_secret não capturou o valor"
    corpo = TEMPLATE.read_text(encoding="utf-8")
    inicio = corpo.index("ask_secret() {")
    assert "read -rs" in corpo[inicio : corpo.index("\n}", inicio)]


@precisa_bash
def test_open_url_no_git_bash_usa_cmd_start(tmp_path):
    lib = _biblioteca(tmp_path)
    falso = tmp_path / "bin"
    falso.mkdir()
    registro = tmp_path / "cmd_args.txt"
    cmd = falso / "cmd.exe"
    cmd.write_bytes(f'#!/bin/sh\nprintf "%s|" "$@" > "{_posix(registro)}"\n'.encode("utf-8"))
    r = _rodar(
        f'chmod +x "{_posix(cmd)}"; export PATH="{_posix_path_entry(falso)}:/usr/bin:/bin"; OSTYPE=msys; '
        f'source "{_posix(lib)}"; open_url "https://example.com/painel"',
        tmp_path,
    )
    assert r.returncode == 0, r.stderr.decode("utf-8", "replace")
    assert registro.is_file(), "open_url não chamou cmd.exe no Git Bash"
    args = registro.read_text(encoding="utf-8")
    assert "start" in args and "https://example.com/painel" in args
