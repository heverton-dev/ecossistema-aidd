"""
Bateria TDD para G_TEMPLATE_TANSTACK_OFFLINE.py — prova que o gate morde (Lei #13).
Red: fixtures quebradas devem retornar exit 1.
Green: template real deve retornar exit 0.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

GATE = Path(__file__).parent.parent / "componentes" / "compartilhado" / "gates" / "G_TEMPLATE_TANSTACK_OFFLINE.py"
TEMPLATE_REAL = Path(__file__).parent.parent / "componentes" / "compartilhado" / "templates" / "frontend-tanstack"


def rodar_gate(pasta: Path) -> int:
    r = subprocess.run(
        [sys.executable, str(GATE), str(pasta)],
        capture_output=True,
    )
    return r.returncode


def test_gate_morde_pacote_proprietario(tmp_path):
    """exit 1 se package.json contém pacote de lock-in (lovable-auth)."""
    (tmp_path / "package.json").write_text(
        json.dumps({"dependencies": {"lovable-auth": "^1.0.0", "@tanstack/react-router": "^1.0.0"}}),
        encoding="utf-8",
    )
    (tmp_path / "template-manifest.json").write_text("{}", encoding="utf-8")
    shells = tmp_path / "src" / "components"
    shells.mkdir(parents=True)
    (shells / "AdminShell.tsx").write_text("export default function AdminShell() {}", encoding="utf-8")
    (shells / "MobileShell.tsx").write_text("export default function MobileShell() {}", encoding="utf-8")
    offline = tmp_path / "src" / "lib" / "offline"
    offline.mkdir(parents=True)
    (offline / "sync-queue.ts").write_text("// hmac", encoding="utf-8")
    assert rodar_gate(tmp_path) == 1


def test_gate_morde_sem_shells(tmp_path):
    """exit 1 se AdminShell.tsx ou MobileShell.tsx ausentes."""
    (tmp_path / "package.json").write_text(
        json.dumps({"dependencies": {"@tanstack/react-router": "^1.0.0"}}),
        encoding="utf-8",
    )
    (tmp_path / "template-manifest.json").write_text("{}", encoding="utf-8")
    # sem src/components
    offline = tmp_path / "src" / "lib" / "offline"
    offline.mkdir(parents=True)
    (offline / "sync-queue.ts").write_text("// hmac", encoding="utf-8")
    assert rodar_gate(tmp_path) == 1


def test_gate_morde_sem_hmac(tmp_path):
    """exit 1 se sync-queue.ts não menciona hmac."""
    (tmp_path / "package.json").write_text(
        json.dumps({"dependencies": {"@tanstack/react-router": "^1.0.0"}}),
        encoding="utf-8",
    )
    (tmp_path / "template-manifest.json").write_text("{}", encoding="utf-8")
    shells = tmp_path / "src" / "components"
    shells.mkdir(parents=True)
    (shells / "AdminShell.tsx").write_text("export default function AdminShell() {}", encoding="utf-8")
    (shells / "MobileShell.tsx").write_text("export default function MobileShell() {}", encoding="utf-8")
    offline = tmp_path / "src" / "lib" / "offline"
    offline.mkdir(parents=True)
    (offline / "sync-queue.ts").write_text("// sem assinatura", encoding="utf-8")
    assert rodar_gate(tmp_path) == 1


def test_gate_passa_template_real():
    """exit 0 no template canônico real."""
    assert rodar_gate(TEMPLATE_REAL) == 0
