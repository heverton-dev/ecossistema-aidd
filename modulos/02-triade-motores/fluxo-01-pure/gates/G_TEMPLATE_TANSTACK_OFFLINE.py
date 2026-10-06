#!/usr/bin/env python3
"""
G_TEMPLATE_TANSTACK_OFFLINE.py
Quality Gate determinístico que valida a integridade do template canônico TanStack Offline.
Regido pelas Leis #1, #6, #10 e #11 do Ecossistema AIDD.
"""

import json
import os
import sys
from pathlib import Path


def verificar_template(caminho_template: str) -> None:
    print(f"[{__file__}] Auditando template TanStack Offline em: {caminho_template}")
    base = Path(caminho_template)

    if not base.exists() or not base.is_dir():
        print(f"EXIT 1: Diretório do template não encontrado: {caminho_template}")
        sys.exit(1)

    falhas = []

    # 1. Validação do Manifesto
    manifest_path = base / "template-manifest.json"
    if not manifest_path.exists():
        falhas.append("Arquivo 'template-manifest.json' ausente.")
    else:
        try:
            dados = json.loads(manifest_path.read_text(encoding="utf-8"))
            if not dados.get("padrao_ouro"):
                falhas.append("Manifesto não define 'padrao_ouro: true'.")
            quarteto = dados.get("quarteto_sine_qua_non", {})
            for r in ["/api", "/webhook", "/mcp", "/docs"]:
                if r not in quarteto.values():
                    falhas.append(f"Manifesto não mapeia o estúdio '{r}' do Quarteto.")
        except Exception as e:
            falhas.append(f"Erro ao ler template-manifest.json: {e}")

    # 2. Ausência de Lock-in (Lei #6)
    pkg_path = base / "package.json"
    if not pkg_path.exists():
        falhas.append("Arquivo 'package.json' ausente.")
    else:
        conteudo_pkg = pkg_path.read_text(encoding="utf-8")
        if "@lovable.dev" in conteudo_pkg:
            falhas.append("Violação da Lei #6: detectada dependência com '@lovable.dev'.")
        if "@tanstack/react-router" not in conteudo_pkg:
            falhas.append("Falta a dependência canônica '@tanstack/react-router'.")

    # 3. Design Tokens OKLCH & Impeccable
    design_path = base / "DESIGN.md"
    if not design_path.exists():
        falhas.append("Arquivo 'DESIGN.md' ausente.")
    else:
        conteudo_design = design_path.read_text(encoding="utf-8")
        if "oklch(" not in conteudo_design:
            falhas.append("DESIGN.md não utiliza o padrão de cores moderno 'oklch'.")

    # 4. Casca Dupla Responsiva
    admin_shell = base / "src" / "components" / "AdminShell.tsx"
    mobile_shell = base / "src" / "components" / "MobileShell.tsx"
    use_mobile = base / "src" / "hooks" / "use-mobile.tsx"

    for f_path, nome in [(admin_shell, "AdminShell.tsx"), (mobile_shell, "MobileShell.tsx"), (use_mobile, "use-mobile.tsx")]:
        if not f_path.exists():
            falhas.append(f"Componente obrigatório '{nome}' ausente.")

    # 5. Quarteto Sine Qua Non na casca (Lei #10)
    if admin_shell.exists():
        conteudo_shell = admin_shell.read_text(encoding="utf-8")
        for rota in ["/api", "/webhook", "/mcp", "/docs"]:
            if f'to="{rota}"' not in conteudo_shell and f"to='{rota}'" not in conteudo_shell:
                falhas.append(f"AdminShell não possui link de navegação para '{rota}'.")

    # 6. Camada Offline e HMAC SHA-256
    sync_queue = base / "src" / "lib" / "offline" / "sync-queue.ts"
    seguranca = base / "src" / "lib" / "seguranca.ts"
    pwa = base / "src" / "lib" / "pwa.ts"

    for f_path, nome in [(sync_queue, "sync-queue.ts"), (seguranca, "seguranca.ts"), (pwa, "pwa.ts")]:
        if not f_path.exists():
            falhas.append(f"Módulo offline obrigatório '{nome}' ausente.")

    if seguranca.exists():
        conteudo_seg = seguranca.read_text(encoding="utf-8")
        if "HMAC" not in conteudo_seg or "SHA-256" not in conteudo_seg:
            falhas.append("Módulo de segurança não implementa HMAC SHA-256.")

    if falhas:
        print("EXIT 1: O Quality Gate reprovou o template com as seguintes violações:")
        for falha in falhas:
            print(f" - {falha}")
        return 1

    print("EXIT 0: Template TanStack Offline aprovado com 100% de conformidade canônica.")
    return 0


if __name__ == "__main__":
    caminho = sys.argv[1] if len(sys.argv) > 1 else "componentes/compartilhado/templates/frontend-tanstack"
    sys.exit(verificar_template(caminho))
