# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — AIDD-OPS: ROTAÇÃO DE SEGREDOS EFÊMEROS (ZERO CLOUD LOCK-IN)
=============================================================================
Automação de geração e rotação determinística de credenciais efêmeras
(JWT secret, credenciais de banco, webhook signing keys) via Docker Secrets
ou volumes em memória (/run/secrets), em conformidade estrita com a
Lei #6 (Zero Cloud Lock-in / Supremacia Agnóstica).

Uso:
  python tools/aidd-ops/scripts/rotate_secrets.py --secrets-dir PATH [--keys KEY1,KEY2]
  python tools/aidd-ops/scripts/rotate_secrets.py --check --secrets-dir PATH
"""

import argparse
import json
import os
import secrets
import stat
import sys
from datetime import datetime, timezone
from typing import Dict, List, Optional


SECRETS_PADRAO = [
    "jwt_secret",
    "db_password",
    "webhook_signing_secret",
]


def gerar_segredo_criptografico(tipo: str) -> str:
    """Gera entropia criptográfica segura baseada no tipo de segredo."""
    if tipo == "db_password":
        # Senha alfanumérica segura com caracteres especiais seguros para URLs
        return secrets.token_urlsafe(32)
    # 64 bytes de entropia para chaves HMAC/JWT
    return secrets.token_hex(64)


def rotacionar_segredos(
    secrets_dir: str,
    keys: Optional[List[str]] = None,
    backup_antigo: bool = True
) -> Dict[str, any]:
    """
    Rotaciona os arquivos de segredos no diretório especificado (/run/secrets ou .secrets/).
    Garante permissões 0600 em sistemas Unix e persiste metadata de auditoria.
    """
    os.makedirs(secrets_dir, exist_ok=True)
    target_keys = keys or SECRETS_PADRAO
    resultado = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "rotacionados": [],
        "secrets_dir": os.path.abspath(secrets_dir),
    }

    for key in target_keys:
        secret_file = os.path.join(secrets_dir, f"{key}.txt")
        novo_valor = gerar_segredo_criptografico(key)

        # Se existir e backup solicitado, salva versão anterior
        if os.path.isfile(secret_file) and backup_antigo:
            backup_file = os.path.join(secrets_dir, f"{key}.prev")
            try:
                if os.path.isfile(backup_file):
                    os.remove(backup_file)
                os.rename(secret_file, backup_file)
            except OSError:
                pass

        # Grava o novo segredo
        with open(secret_file, "w", encoding="utf-8") as f:
            f.write(novo_valor)

        # Em sistemas Unix, restringe para leitura/escrita do proprietário (0600)
        if hasattr(os, "chmod") and sys.platform != "win32":
            try:
                os.chmod(secret_file, stat.S_IRUSR | stat.S_IWUSR)
            except OSError:
                pass

        resultado["rotacionados"].append(key)

    # Grava manifesto de auditoria de rotação
    audit_file = os.path.join(secrets_dir, "rotation_audit.json")
    with open(audit_file, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2)

    return resultado


def verificar_integridade_segredos(secrets_dir: str, keys: Optional[List[str]] = None) -> bool:
    """Verifica se todos os segredos exigidos existem e não estão vazios."""
    target_keys = keys or SECRETS_PADRAO
    if not os.path.isdir(secrets_dir):
        return False

    for key in target_keys:
        secret_file = os.path.join(secrets_dir, f"{key}.txt")
        if not os.path.isfile(secret_file):
            return False
        if os.path.getsize(secret_file) < 16:
            return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Rotação de Segredos Efêmeros (aidd-ops)")
    parser.add_argument("--secrets-dir", default=".secrets", help="Diretório de segredos (/run/secrets ou .secrets)")
    parser.add_argument("--keys", default="", help="Lista separada por vírgula de segredos a rotacionar")
    parser.add_argument("--check", action="store_true", help="Apenas verifica a presença e integridade dos segredos")
    args = parser.parse_args()

    keys = [k.strip() for k in args.keys.split(",") if k.strip()] or None

    if args.check:
        valido = verificar_integridade_segredos(args.secrets_dir, keys)
        if valido:
            print(f"[OK] Todos os segredos em '{args.secrets_dir}' estao presentes e integros.")
            return 0
        else:
            print(f"[ERRO] Segredos ausentes ou invalidos em '{args.secrets_dir}'.")
            return 1

    res = rotacionar_segredos(args.secrets_dir, keys)
    print(f"[OK] Segredos rotacionados com sucesso em '{res['secrets_dir']}':")
    for k in res["rotacionados"]:
        print(f"  - {k}.txt")
    return 0


if __name__ == "__main__":
    sys.exit(main())
