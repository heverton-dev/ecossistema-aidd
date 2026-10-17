"""
G_TEMPLATE_TANSTACK_OFFLINE — Quality Gate do template canônico TanStack Offline.

Verifica:
  1. Ausência de pacotes de lock-in proprietário no package.json
  2. Presença de AdminShell.tsx e MobileShell.tsx (casca dupla)
  3. sync-queue.ts com menção a HMAC (fila assinada)
  4. template-manifest.json presente

Uso: python gates/G_TEMPLATE_TANSTACK_OFFLINE.py [pasta_do_template]
     Sai com 0 (OK) ou 1 (falha).
"""
import json
import sys
from pathlib import Path

LOCK_IN = {"lovable-auth", "supabase", "firebase", "clerk", "auth0", "next-auth"}

QUARTETO_ROUTES = {"/api", "/webhook", "/mcp", "/docs"}


def falha(msg: str) -> None:
    print(f"[GATE REPROVADO] {msg}", file=sys.stderr)
    sys.exit(1)


def main(pasta: Path) -> None:
    # 1. package.json — sem lock-in
    pkg_path = pasta / "package.json"
    if not pkg_path.exists():
        falha("package.json ausente")
    pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
    deps = set(pkg.get("dependencies", {}).keys()) | set(pkg.get("devDependencies", {}).keys())
    encontrados = deps & LOCK_IN
    if encontrados:
        falha(f"pacotes de lock-in encontrados: {sorted(encontrados)}")

    # 2. template-manifest.json presente
    if not (pasta / "template-manifest.json").exists():
        falha("template-manifest.json ausente")

    # 3. Casca dupla: AdminShell.tsx e MobileShell.tsx
    components = pasta / "src" / "components"
    for shell in ("AdminShell.tsx", "MobileShell.tsx"):
        if not (components / shell).exists():
            falha(f"componente ausente: src/components/{shell}")

    # 4. sync-queue.ts com HMAC
    sync_queue = pasta / "src" / "lib" / "offline" / "sync-queue.ts"
    if not sync_queue.exists():
        falha("src/lib/offline/sync-queue.ts ausente")
    conteudo = sync_queue.read_text(encoding="utf-8").lower()
    if "hmac" not in conteudo:
        falha("sync-queue.ts não menciona HMAC — fila não está assinada")

    print("[GATE OK] template-tanstack-offline conforme (lock-in=0, shells=2, HMAC=sim)")


if __name__ == "__main__":
    raiz = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    main(raiz)
