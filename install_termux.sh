#!/usr/bin/env bash

set -e

REPO_URL="https://github.com/syed-sameer-ul-hassan/MailSpoof.git"

if [[ -f "mailspoof" && -d "lib" ]]; then
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
else
    CLONE_DIR="$HOME/.mailspoof/repo"
    echo "[*] Cloning MailSpoof repository..."
    rm -rf "$CLONE_DIR"
    mkdir -p "$CLONE_DIR"
    git clone "$REPO_URL" "$CLONE_DIR"
    cd "$CLONE_DIR"
    SCRIPT_DIR="$CLONE_DIR"
fi

print_banner() {
    echo ""
    echo "  ▄▄███▄▄     ▄██████  ██ ▄█   ▄███████    ▄█████▄  ▄█████▄  ▄█████▄   ▄███████"
    echo " ██▀▀██▀▀█▄   ██   ██  ▄█ ██   ██    ██   ██    ██ ██    ██ ██    ██   ██    ██"
    echo " ██  ██  ██   ██   ██  ██ ██   ██    █▀   ██    ██ ██    ██ ██    ██   ██    █▀"
    echo " ██  ██  ██   ██   ██  ██ ██   ██         ██    ██ ██    ██ ██    ██  ▄██▄▄"
    echo " ██  ██  ██ ▀████████  ██ ██   ▀████████ ▀███████▀ ██    ██ ██    ██ ▀▀██▀▀"
    echo " ██  ██  ██   ██   ██  ██ ██          ██   ██      ██    ██ ██    ██   ██"
    echo " ██  ██  ██   ██   ██  ██ ██▌  ▄      ██   ██      ██    ██ ██    ██   ██"
    echo " ▀█  ██  █▀   ██   █▀  █▀ ███▄ ▄███████▀  ▄███▀    ▀█████▀   ▀█████▀   ███"
    echo "                                  ."
    echo ""
    echo "      Professional Email Security Assessment v1.2.0"
    echo "      Platform: Termux"
    echo ""
}

install_system_packages() {
    echo "[*] Checking Termux dependencies..."
    pkg update -y
    pkg install -y python git
}

check_python() {
    if command -v python &>/dev/null; then
        PYTHON=python
    else
        echo "[!] Python is required but not installed."
        exit 1
    fi
    echo "[+] Found Python: $PYTHON ($($PYTHON --version))"
}

setup_dirs() {
    echo "[+] Creating config directories..."
    mkdir -p "$HOME/.mailspoof/templates"
    mkdir -p "$HOME/.mailspoof/reports"
}

install_mailspoof() {
    echo "[+] Installing MailSpoof via pip..."
    local pip_flags=""
    if "$PYTHON" -m pip help install 2>/dev/null | grep -q "break-system-packages"; then
        pip_flags="--break-system-packages"
    fi
    (cd "$SCRIPT_DIR" && "$PYTHON" -m pip install --upgrade pip $pip_flags && "$PYTHON" -m pip install $pip_flags .)
    echo "[+] Installed MailSpoof in Termux environment"
}

main() {
    print_banner
    install_system_packages
    check_python
    setup_dirs
    install_mailspoof

    echo ""
    echo "         [+] Termux Installation Complete!"
    echo ""
    echo "  Commands:"
    echo "    mailspoof              Start interactive spoofing"
    echo "    mailspoof list         List templates"
    echo "    mailspoof start        Start server + send"
    echo "    mailspoof create       Create custom template"
    echo "    mailspoof uninstall    Remove MailSpoof"
    echo "    mailspoof help         Show all commands"
    echo ""
    echo "  Custom templates folder: ~/.mailspoof/templates/"
    echo ""
}

main "$@"
