#!/usr/bin/env bash
# ======================================================================
#          AIDD PROJECT GENERATOR — INTERFACE WEB LOCAL
# ======================================================================
# Inicia o servidor Flask em localhost:5000 e abre o navegador.
# Uso: ./iniciar.sh
# ======================================================================

set -euo pipefail

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo -e "${CYAN}======================================================================${NC}"
echo -e "${CYAN}       AIDD PROJECT GENERATOR — INTERFACE WEB LOCAL${NC}"
echo -e "${CYAN}======================================================================${NC}"
echo ""

# [1/3] Detectar Python
echo -e " ${GREEN}[1/3]${NC} Verificando ambiente Python..."

PYTHON_EXE=""

# Prioridade: venv local > python3 > python
if [ -f ".venv/bin/python" ]; then
    PYTHON_EXE=".venv/bin/python"
elif command -v python3 &>/dev/null; then
    PYTHON_EXE="python3"
elif command -v python &>/dev/null; then
    PYTHON_EXE="python"
fi

if [ -z "$PYTHON_EXE" ]; then
    echo -e " ${RED}[ERRO]${NC} Python nao encontrado no sistema."
    echo "        Por favor, instale o Python 3.10+ e tente novamente."
    echo ""
    exit 1
fi

PY_VERSION=$($PYTHON_EXE --version 2>&1)
echo -e " ${GREEN}✓${NC} Python encontrado: $PY_VERSION ($PYTHON_EXE)"

# [2/3] Verificar dependências
echo -e " ${GREEN}[2/3]${NC} Verificando dependências..."

if [ -f "requirements.txt" ]; then
    # Verificar se Flask está instalado
    if ! $PYTHON_EXE -c "import flask" 2>/dev/null; then
        echo -e " ${YELLOW}⚠${NC} Flask nao encontrado. Instalando dependencias..."
        $PYTHON_EXE -m pip install -r requirements.txt --quiet
    fi
fi

echo -e " ${GREEN}✓${NC} Dependencias OK"

# [3/3] Iniciar servidor
echo -e " ${GREEN}[3/3]${NC} Iniciando servidor e abrindo navegador..."
echo ""
echo -e "  A interface abrira automaticamente em: ${CYAN}http://localhost:5000${NC}"
echo -e "  Mantenha este terminal aberto enquanto estiver usando o aplicativo."
echo -e "  (Para encerrar, pressione ${YELLOW}CTRL+C${NC})"
echo ""
echo -e "${CYAN}======================================================================${NC}"
echo ""

# Executa o entrypoint que inicia o Flask e abre o navegador
$PYTHON_EXE web_app.py

echo ""
echo -e " ${YELLOW}[AVISO]${NC} O servidor foi finalizado."
