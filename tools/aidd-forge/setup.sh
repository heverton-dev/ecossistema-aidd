#!/usr/bin/env bash
# Executavel de 1-clique (Linux/Mac): configura o AIDD Forge silenciosamente.
set -uo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
else
    printf "%b\n" "${RED}[aidd-forge] Python nao encontrado no PATH. Instale Python 3.10+ e tente novamente.${NC}"
    exit 1
fi

LOG_FILE="$(mktemp)"

if ! "$PYTHON_BIN" -m aidd_forge.cli init >"$LOG_FILE" 2>&1; then
    printf "%b\n" "${RED}[aidd-forge] Nao foi possivel configurar o projeto automaticamente.${NC}"
    echo "[aidd-forge] Detalhes em: $LOG_FILE"
    exit 1
fi

cat "$LOG_FILE"
printf "%b\n" "${GREEN}[OK] AIDD Forge configurado com sucesso neste projeto.${NC}"
rm -f "$LOG_FILE"
exit 0
