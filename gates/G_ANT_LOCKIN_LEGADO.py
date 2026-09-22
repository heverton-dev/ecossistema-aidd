#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
G_ANT_LOCKIN_LEGADO.py — Quality Gate Determinístico (ISSUE-USA-0008 / Lei #1 + #13).

Varre entrega/legado por resíduo lovable|supabase|firebase e dirs `.lovable/`,
`supabase/`. Nunca apaga (Lei #7). Allowlist: lockin-allowlist.txt (Lei #8).

Exit 0: limpo (ou só allowlist) / módulo presente.
Exit 1: resíduo sem allowlist, ou módulo/fecho ausentes.
"""

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Entregas reais sob a raiz (pastas com README-USUARIO) + legados irmãos.
CANDIDATOS_EXCLUSOS = {
    ".git", ".venv", "venv", "node_modules", "__pycache__",
    "tools", "gates", "core", "componentes", "scripts",
    "docs", "tests", "testes", "dist", ".worktrees",
    ".claude", ".agents", ".mimocode", ".opencode", ".gemini",
    ".cursor", ".codebuddy", ".skills", ".hooks", ".github",
}


def _alvos_entrega() -> list[Path]:
    alvos = []
    # Só pastas com README-USUARIO (entrega real de app) — package.json
    # sozinho pega harness e falso-positivo (ISSUE-USA-0008).
    if (ROOT / "README-USUARIO.md").is_file():
        alvos.append(ROOT)
    for filho in sorted(ROOT.iterdir()):
        if not filho.is_dir() or filho.name in CANDIDATOS_EXCLUSOS:
            continue
        if (filho / "README-USUARIO.md").is_file():
            alvos.append(filho)
    return alvos


def verificar_modulo() -> list[str]:
    erros = []
    gen = ROOT / "core" / "anti_lockin.py"
    if not gen.is_file():
        erros.append("core/anti_lockin.py ausente")
    else:
        t = gen.read_text(encoding="utf-8", errors="ignore")
        if "varredura" not in t or "supabase" not in t.lower():
            erros.append("core/anti_lockin.py incompleto (varredura/padrao supabase)")
    orc = ROOT / "scripts" / "orquestrador_sincrono.py"
    if orc.is_file():
        ot = orc.read_text(encoding="utf-8", errors="ignore")
        # Wire no fecho: ao menos import ou chamada
        if "anti_lockin" not in ot and "varredura" not in ot:
            erros.append("orquestrador_sincrono nao chama a varredura anti-lock-in no fecho")
    return erros


def verificar_entregas() -> list[str]:
    erros = []
    try:
        from core.anti_lockin import possui_sujeira, varredura
    except ImportError as exc:
        return [f"import core.anti_lockin: {exc}"]
    for alvo in _alvos_entrega():
        r = varredura(alvo)
        if possui_sujeira(r):
            resumo = (r["dirs"] + r["hits"])[:5]
            erros.append(f"{alvo.name}: resíduo lock-in {resumo}")
    return erros


def main() -> int:
    erros = verificar_modulo() + verificar_entregas()
    if erros:
        print("=" * 70)
        print("VIOLACAO [G_ANT_LOCKIN_LEGADO]: resíduo de fornecedor ou varredura ausente!")
        print("Registre em lockin-allowlist.txt se for intencional (Lei #8).")
        print("=" * 70)
        for e in erros:
            print(f"- {e}")
        print(f"TOTAL VIOLATIONS: {len(erros)}")
        return 1
    print("[OK] G_ANT_LOCKIN_LEGADO: varredura determinística ativa; sem resíduo fora da allowlist.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
