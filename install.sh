#!/usr/bin/env bash
# Local installer for Financial Calendar on Arch/CachyOS/KDE.

set -euo pipefail

APP_NAME="financial_calendar"
APP_TITLE="Calendario Finanziario"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/.venv"
APPS_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/${APP_NAME}"
DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/${APP_NAME}"
WRAPPER_DIR="${HOME}/.local/bin"
ICON_DIR="${HOME}/.local/share/icons/hicolor/256x256/apps"

echo "=== Installazione ${APP_TITLE} ==="

if ! command -v python3 &>/dev/null; then
    echo "ERRORE: python3 non trovato."
    exit 1
fi

if ! python3 -c "import venv" &>/dev/null; then
    echo "ERRORE: il modulo Python venv non è disponibile."
    exit 1
fi

if [ ! -d "${VENV_DIR}" ]; then
    echo "[1/6] Creazione ambiente virtuale..."
    python3 -m venv "${VENV_DIR}"
else
    echo "[1/6] Ambiente virtuale già presente."
fi

echo "[2/6] Installazione dipendenze..."
"${VENV_DIR}/bin/python" -m pip install --upgrade pip --quiet
"${VENV_DIR}/bin/python" -m pip install -r "${SCRIPT_DIR}/requirements.txt" --quiet

echo "[3/6] Creazione directory XDG..."
mkdir -p "${CONFIG_DIR}" "${DATA_DIR}" "${APPS_DIR}" "${WRAPPER_DIR}" "${ICON_DIR}"

echo "[4/6] Installazione icona..."
ICON_SRC="${SCRIPT_DIR}/assets/icons/financial-calendar.png"
if [ -f "${ICON_SRC}" ]; then
    cp "${ICON_SRC}" "${ICON_DIR}/financial-calendar.png"
fi

echo "[5/6] Creazione launcher..."
WRAPPER_SCRIPT="${WRAPPER_DIR}/financial-calendar"
cat > "${WRAPPER_SCRIPT}" << WRAPPER_CONTENT
#!/usr/bin/env bash
APP_DIR="${SCRIPT_DIR}"
exec "\${APP_DIR}/.venv/bin/python" "\${APP_DIR}/main.py" "\$@"
WRAPPER_CONTENT
chmod +x "${WRAPPER_SCRIPT}"

echo "[6/6] Creazione voce menu..."
DESKTOP_FILE="${APPS_DIR}/${APP_NAME}.desktop"
cat > "${DESKTOP_FILE}" << EOF
[Desktop Entry]
Type=Application
Name=Calendario Finanziario
Comment=Visualizzatore di calendari economici ForexFactory/Faireconomy e FXStreet
Exec=${WRAPPER_SCRIPT}
Icon=financial-calendar
Terminal=false
Categories=Office;Finance;
Keywords=finance;calendar;economic;forex;
StartupNotify=true
EOF

update-desktop-database "${APPS_DIR}" 2>/dev/null || true

echo
echo "Installazione completata."
echo "Avvio: ${WRAPPER_SCRIPT}"
