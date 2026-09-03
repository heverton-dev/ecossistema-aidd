#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Entrypoint do Aplicativo Web Local
web_app.py — aidd-project-generator
"""

import sys
import webbrowser
import threading
import time
from pathlib import Path

# Adiciona raiz ao path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from web.app import app

if __name__ == '__main__':
    porta = 5000
    url = f"http://localhost:{porta}"

    def _abrir_navegador():
        time.sleep(1.2)
        try:
            webbrowser.open(url)
        except Exception:
            pass

    # Dispara abertura automática do navegador em background
    threading.Thread(target=_abrir_navegador, daemon=True).start()

    print("\n" + "=" * 70)
    print("  🚀 AIDD PROJECT GENERATOR — INTERFACE WEB LOCAL")
    print(f"  🌐 Servidor ativo em: {url}")
    print("  💡 Pressione CTRL+C nesta janela para encerrar o servidor.")
    print("=" * 70 + "\n")

    app.run(host='127.0.0.1', port=porta, debug=False)
