# -*- coding: utf-8 -*-
"""Use Case: deploy — preparação de deploy Docker/VPS."""

import os
import subprocess


def cmd_deploy(args):
    alvo = getattr(args, "alvo", "docker") or "docker"
    print(f"🚀 [AIDD DEPLOY] Preparando deploy para: {alvo}...")
    if alvo == "docker":
        subprocess.run(["docker", "compose", "up", "-d", "--build"])
    elif alvo == "vps":
        if os.path.exists("deploy.sh"):
            print("Execute no seu servidor de produção: bash deploy.sh")
    print(f"✨ [OK] Instruções de deploy para {alvo} processadas.")