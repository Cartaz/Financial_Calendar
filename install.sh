#!/usr/bin/env bash
# Local installer for Financial Calendar.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_DIR="${SCRIPT_DIR}/.venv"

echo "=== Installazione Calendario Finanziario ==="

if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
    echo "ERRORE: ${PYTHON_BIN} non trovato."
    exit 1
fi

if ! "${PYTHON_BIN}" -c "import venv" >/dev/null 2>&1; then
    echo "ERRORE: il modulo Python venv non è disponibile."
    exit 1
fi

if [ ! -x "${VENV_DIR}/bin/python" ]; then
    echo "[1/2] Creazione ambiente virtuale..."
    "${PYTHON_BIN}" -m venv "${VENV_DIR}"
else
    echo "[1/2] Ambiente virtuale già presente."
fi

echo "[2/2] Installazione dipendenze..."
"${VENV_DIR}/bin/python" -m pip install --upgrade pip
"${VENV_DIR}/bin/python" -m pip install -r "${SCRIPT_DIR}/requirements.txt"

echo
echo "Installazione completata."
echo "Avvio: .venv/bin/python main.py"
