# -*- coding: utf-8 -*-
"""
Teste dos hooks do codebase-memory-mcp
"""
import subprocess
import sys
import os

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def test_cbm_session_start_hook():
    hook = os.path.join(ROOT_DIR, "componentes", "compartilhado", "hooks", "cbm_session_start.py")
    res = subprocess.run([sys.executable, hook], capture_output=True, text=True, timeout=10)
    assert res.returncode == 0
    assert "suppressOutput" in res.stdout

def test_cbm_update_hook():
    hook = os.path.join(ROOT_DIR, "componentes", "compartilhado", "hooks", "cbm_update.py")
    res = subprocess.run([sys.executable, hook], capture_output=True, text=True, timeout=10)
    assert res.returncode == 0
    assert "suppressOutput" in res.stdout
