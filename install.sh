#!/usr/bin/env bash
# Local installer for Financial Calendar.

set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_DIR="${SCRIPT_DIR}/.venv"

echo "=== Installazione Calendario Finanziario ==="

if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
    echo "ERRORE: ${PYTHON_BIN} non trovato."
    exit 1
fi

if ! "${PYTHON_BIN}" - <<'PY'
import sys
raise SystemExit(0 if sys.version_info >= (3, 12) else 1)
PY
then
    echo "ERRORE: è richiesto Python 3.12 o superiore."
    exit 1
fi

if ! "${PYTHON_BIN}" -c "import venv" >/dev/null 2>&1; then
    echo "ERRORE: il modulo Python venv non è disponibile."
    exit 1
fi

if [ -x "${VENV_DIR}/bin/python" ]; then
    if ! "${VENV_DIR}/bin/python" - <<'PY' >/dev/null 2>&1
import sys
raise SystemExit(0 if sys.prefix != sys.base_prefix and sys.version_info >= (3, 12) else 1)
PY
    then
        echo "[1/3] Ambiente virtuale non valido: ricreazione..."
        rm -rf "${VENV_DIR}"
    fi
fi

if [ ! -x "${VENV_DIR}/bin/python" ]; then
    echo "[1/3] Creazione ambiente virtuale..."
    "${PYTHON_BIN}" -m venv "${VENV_DIR}"
else
    echo "[1/3] Ambiente virtuale valido già presente."
fi

echo "[2/3] Installazione dipendenze..."
"${VENV_DIR}/bin/python" -m pip install --upgrade pip
"${VENV_DIR}/bin/python" -m pip install -r "${SCRIPT_DIR}/requirements.txt"

echo "[3/3] Verifica runtime critico..."
if ! "${VENV_DIR}/bin/python" - <<'PY'
import requests
from PySide6.QtCore import qVersion
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineWidgets import QWebEngineView

assert requests.__version__
assert qVersion()
assert QWebChannel
assert QWebEngineView
PY
then
    echo "ERRORE: verifica degli import critici fallita."
    exit 1
fi

echo
echo "Installazione completata."
echo "Avvio: .venv/bin/python main.py"
