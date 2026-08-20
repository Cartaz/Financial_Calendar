#!/usr/bin/env bash
# Script di installazione locale per Calendario Finanziario
# Conforme alle specifiche Freedesktop.org e XDG
# Progettato per CachyOS / Arch Linux (PEP 668 compliant)
# Compatibile con bash e fish (non usa source/activate)

set -euo pipefail

APP_NAME="financial_calendar"
APP_TITLE="Calendario Finanziario"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/.venv"
APPS_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"

echo "=== Installazione ${APP_TITLE} ==="
echo ""

# Verifica che python3 sia disponibile
if ! command -v python3 &>/dev/null; then
    echo "ERRORE: python3 non trovato. Installa con: sudo pacman -S python"
    exit 1
fi

# Verifica che python-venv sia disponibile (su Arch serve un pacchetto separato)
if python3 -c "import venv" &>/dev/null; then
    :  # OK
else
    echo "ERRORE: modulo venv non disponibile."
    echo "Installa con: sudo pacman -Sy && sudo pacman -S python-virtualenv"
    echo "Oppure: sudo pacman -S python-venv"
    exit 1
fi

# Crea ambiente virtuale se non esiste
if [ ! -d "${VENV_DIR}" ]; then
    echo "[1/7] Creazione ambiente virtuale Python..."
    python3 -m venv "${VENV_DIR}"
else
    echo "[1/7] Ambiente virtuale già esistente, salto creazione."
fi

# Installa dipendenze usando pip direttamente dal venv
# (non usa source/activate per compatibilità con fish shell)
echo "[2/7] Installazione dipendenze nell'ambiente virtuale..."
"${VENV_DIR}/bin/pip" install --upgrade pip --quiet
"${VENV_DIR}/bin/pip" install -r "${SCRIPT_DIR}/requirements.txt" --quiet

# Verifica installazione PySide6
if "${VENV_DIR}/bin/python" -c "import PySide6" 2>/dev/null; then
    echo "      PySide6 installato correttamente."
else
    echo "      ATTENZIONE: PySide6 non installato! Prova manualmente:"
    echo "      ${VENV_DIR}/bin/pip install PySide6"
fi

# Crea directory XDG
echo "[3/7] Creazione directory configurazione..."
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/${APP_NAME}"
DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/${APP_NAME}"
mkdir -p "${CONFIG_DIR}" "${DATA_DIR}"

# Installa l'icona dell'applicazione nella directory XDG icons
# (necessaria per il file .desktop e il menu KDE)
echo "[4/7] Installazione icona applicazione..."
ICON_DIR="${HOME}/.local/share/icons/hicolor/256x256/apps"
mkdir -p "${ICON_DIR}"
ICON_SRC="${SCRIPT_DIR}/assets/icons/financial-calendar.png"
if [ -f "${ICON_SRC}" ]; then
    cp "${ICON_SRC}" "${ICON_DIR}/financial-calendar.png"
    echo "      Icona installata in ${ICON_DIR}/financial-calendar.png"
else
    echo "      ATTENZIONE: icona non trovata in ${ICON_SRC}"
fi

# Crea uno script wrapper in ~/.local/bin/ (senza spazi nel percorso).
# Il file .desktop non gestisce gli spazi nel campo Exec, quindi
# usiamo un wrapper con il percorso completo dell'app hardcoded.
echo "[5/7] Creazione script di avvio..."
WRAPPER_DIR="${HOME}/.local/bin"
mkdir -p "${WRAPPER_DIR}"
WRAPPER_SCRIPT="${WRAPPER_DIR}/financial-calendar"

# Hardcode il percorso dell'app nel wrapper per robustezza
cat > "${WRAPPER_SCRIPT}" << WRAPPER_CONTENT
#!/usr/bin/env bash
# Wrapper per Calendario Finanziario — generato da install.sh
# Non modificare a mano; riesegui install.sh se sposti l'app.
APP_DIR="${SCRIPT_DIR}"
exec "\${APP_DIR}/.venv/bin/python" "\${APP_DIR}/main.py" "\$@"
WRAPPER_CONTENT

chmod +x "${WRAPPER_SCRIPT}"

# Pulisce eventuali file .desktop orfani di versioni precedenti.
# Cerca tutti i .desktop che puntano a "Calendario Finanziario" e li
# rimuove, così rimane solo quello nuovo creato qui sotto.
echo "[6/7] Pulizia vecchie voci menu..."
DESKTOP_FILE="${APPS_DIR}/${APP_NAME}.desktop"
mkdir -p "${APPS_DIR}"

ORPHAN_COUNT=0
for dsk in "${APPS_DIR}"/*.desktop; do
    [ -f "$dsk" ] || continue
    # Cerca .desktop che contengono il nome dell'app ma NON sono quello corretto
    if grep -qi "Calendario Finanziario" "$dsk" 2>/dev/null; then
        if [ "$(realpath "$dsk" 2>/dev/null || echo "$dsk")" != "$(realpath "${DESKTOP_FILE}" 2>/dev/null || echo "${DESKTOP_FILE}")" ]; then
            echo "      Rimosso vecchio: $(basename "$dsk")"
            rm -f "$dsk"
            ORPHAN_COUNT=$((ORPHAN_COUNT + 1))
        fi
    fi
done
if [ "${ORPHAN_COUNT}" -eq 0 ]; then
    echo "      Nessun file .desktop orfano trovato."
fi

# Crea file .desktop per KDE
echo "[7/7] Creazione voce menu applicazioni..."

# Usa lo script wrapper nel campo Exec (percorso senza spazi)
cat > "${DESKTOP_FILE}" << EOF
[Desktop Entry]
Type=Application
Name=Calendario Finanziario
Comment=Visualizzatore di calendari economici IG e FXStreet
Exec=${WRAPPER_SCRIPT} %f
Icon=financial-calendar
Terminal=false
Categories=Office;Finance;
Keywords=finance;calendar;economic;forex;
StartupNotify=true
EOF

update-desktop-database ~/.local/share/applications/ 2>/dev/null || true

echo ""
echo "=== Installazione completata! ==="
echo ""
echo "Per avviare l'applicazione:"
echo "  ${WRAPPER_SCRIPT}"
echo ""
echo "Oppure dalla directory dell'app:"
echo "  ${VENV_DIR}/bin/python ${SCRIPT_DIR}/main.py"
echo ""
echo "Oppure cerca 'Calendario Finanziario' nel menu KDE."
echo ""
echo "Per aggiornare le dipendenze:"
echo "  ${VENV_DIR}/bin/pip install -r ${SCRIPT_DIR}/requirements.txt"
echo ""
echo "Per disinstallare:"
echo "  rm -rf ${SCRIPT_DIR} ${DESKTOP_FILE} ${WRAPPER_SCRIPT}"
echo "  rm -rf ${CONFIG_DIR} ${DATA_DIR}"
echo "  rm -f ${ICON_DIR}/financial-calendar.png"
