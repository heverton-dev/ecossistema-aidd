# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — Geração do Par de Chaves Ed25519 do Manifesto Canônico
=============================================================================
Gera (uma única vez, ou após rotação explícita) o par de chaves Ed25519 usado
para assinar/verificar o manifesto canônico CAPABILITIES.json do Injetor
Universal (item 'manifest-assinado-ed25519-componentes-enterprise',
PLAN-0018 fase 05 — seguranca-zero-trust).

Saída:
  chaves/manifesto/ed25519_public.json  — chave pública (versionada no git)
  chaves/manifesto/ed25519_private.pem  — chave privada (NUNCA versionada;
                                            '*.pem' já está no .gitignore raiz)

Uso:
  python scripts/gerar_chave_manifesto.py                 # gera (falha se já existir)
  python scripts/gerar_chave_manifesto.py --sobrescrever   # regenera (invalida assinaturas antigas)
"""

import argparse
import os
import sys

_ROOT = os.path.dirname(os.path.abspath(__file__))
_ECOSSISTEMA_ROOT = os.path.dirname(_ROOT)
_SRC_CORE = os.path.join(_ECOSSISTEMA_ROOT, "componentes", "compartilhado", "src-core")
if _SRC_CORE not in sys.path:
    sys.path.insert(0, _SRC_CORE)

from assinatura_manifesto import salvar_par_chaves  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sobrescrever", action="store_true", help="Regenera o par mesmo se já existir.")
    args = parser.parse_args()

    resultado = salvar_par_chaves(ecossistema_root=_ECOSSISTEMA_ROOT, sobrescrever=args.sobrescrever)
    if not resultado.sucesso:
        print(f"[FAIL] {resultado.codigo}: {resultado.erro}")
        return 1

    print("[OK] Par de chaves Ed25519 gerado com sucesso:")
    print(f"  - Chave pública (versionar no git): {resultado.valor['chave_publica']}")
    print(f"  - Chave privada (NUNCA versionar):  {resultado.valor['chave_privada']}")
    print("\nLembrete: qualquer manifesto CAPABILITIES.json assinado com a chave")
    print("privada anterior perde a validade após uma regeneração (--sobrescrever).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
