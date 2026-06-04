#!/bin/bash
PROJECT_DIR="/usr/share/mailspoof"
PYTHON3="/usr/bin/python3"
VENV_DIR="$PROJECT_DIR/venv"

if [[ ! -d "$VENV_DIR" ]]; then
    "$PYTHON3" -m venv "$VENV_DIR" || {
        echo "[!] Failed to create venv. Install python3-venv:"
        echo "    sudo apt install python3-venv"
        echo "    sudo dnf install python3-virtualenv"
        echo "    sudo pacman -S python-virtualenv"
        exit 1
    }
    "$VENV_DIR/bin/pip" install --upgrade pip >/dev/null 2>&1
    "$VENV_DIR/bin/pip" install -r "$PROJECT_DIR/requirements.txt" >/dev/null 2>&1
fi

exec "$VENV_DIR/bin/python" "$PROJECT_DIR/mailspoof" "$@"
