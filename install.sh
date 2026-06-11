#!/usr/bin/env bash

set -e

REPO_URL="https://github.com/syed-sameer-ul-hassan/MailSpoof.git"
PROJECT_NAME="MailSpoof"

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

PLATFORM="linux"
DISTRO="unknown"
INSTALL_DIR="/usr/local/bin"
USER_INSTALL_DIR="$HOME/.local/bin"

detect_platform() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        PLATFORM="macos"
        INSTALL_DIR="/usr/local/bin"
        USER_INSTALL_DIR="$HOME/.local/bin"
    elif [[ -n "$TERMUX_VERSION" ]] || [[ "$PREFIX" == *"termux"* ]]; then
        PLATFORM="termux"
        INSTALL_DIR="$PREFIX/bin"
        USER_INSTALL_DIR="$HOME/.local/bin"
    else
        if [[ -f /etc/os-release ]]; then
            . /etc/os-release
            DISTRO="$ID"
        elif command -v lsb_release &>/dev/null; then
            DISTRO=$(lsb_release -is | tr '[:upper:]' '[:lower:]')
        fi
    fi
}

install_shortcut() {
    local scope="$1"
    local icon_src="$SCRIPT_DIR/assets/icon.svg"
    local desktop_src="$SCRIPT_DIR/mailspoof.desktop"

    if [[ "$PLATFORM" == "macos" ]] || [[ "$PLATFORM" == "termux" ]]; then
        echo "[~] Skipping launcher install (not supported on $PLATFORM)."
        return
    fi

    if [[ ! -f "$icon_src" ]] || [[ ! -f "$desktop_src" ]]; then
        echo "[~] Skipping launcher install (icon or desktop file missing)."
        return
    fi

    if [[ "$scope" == "system" ]]; then
        local icon_dest="/usr/share/icons/hicolor/scalable/apps/mailspoof.svg"
        local desktop_dest="/usr/share/applications/mailspoof.desktop"
        echo "[+] Installing launcher (system)..."
        if [[ $(id -u) -eq 0 ]]; then
            install -Dm644 "$icon_src" "$icon_dest"
            install -Dm644 "$desktop_src" "$desktop_dest"
        else
            sudo install -Dm644 "$icon_src" "$icon_dest"
            sudo install -Dm644 "$desktop_src" "$desktop_dest"
        fi
    else
        local icon_dest="$HOME/.local/share/icons/hicolor/scalable/apps/mailspoof.svg"
        local desktop_dest="$HOME/.local/share/applications/mailspoof.desktop"
        echo "[+] Installing launcher (user)..."
        install -Dm644 "$icon_src" "$icon_dest"
        install -Dm644 "$desktop_src" "$desktop_dest"
    fi
}


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
    echo "      Platform: $PLATFORM"
    [[ "$PLATFORM" == "linux" ]] && echo "      Distro:   $DISTRO"
    echo ""
}

install_system_packages() {
    echo "[*] Checking system dependencies..."

    local has_python=false
    local has_venv=false
    local has_pip=false

    if command -v python3 &>/dev/null; then
        has_python=true
    elif command -v python &>/dev/null; then
        has_python=true
    fi

    if python3 -m venv --help &>/dev/null 2>&1; then
        has_venv=true
    fi

    if command -v pip3 &>/dev/null || command -v pip &>/dev/null; then
        has_pip=true
    fi

    if [[ "$has_python" == true && "$has_venv" == true && "$has_pip" == true ]]; then
        echo "[+] All system dependencies satisfied."
        return
    fi

    echo "[*] Installing system dependencies for: $DISTRO"

    case "$DISTRO" in
        debian|ubuntu|linuxmint|pop|elementary|zorin|kali|parrot)
            echo "    Using apt..."
            sudo apt-get update
            sudo apt-get install -y python3 python3-venv python3-pip
            ;;
        fedora|rhel|centos|rocky|almalinux)
            echo "    Using dnf..."
            if command -v dnf &>/dev/null; then
                sudo dnf install -y python3 python3-pip python3-virtualenv
            else
                sudo yum install -y python3 python3-pip python3-virtualenv
            fi
            ;;
        arch|manjaro|endeavouros|garuda)
            echo "    Using pacman..."
            sudo pacman -Syu --noconfirm python python-pip python-virtualenv
            ;;
        opensuse*|suse*)
            echo "    Using zypper..."
            sudo zypper install -y python3 python3-pip python3-virtualenv
            ;;
        alpine)
            echo "    Using apk..."
            sudo apk add python3 py3-pip py3-virtualenv
            ;;
        *)
            if [[ "$PLATFORM" == "macos" ]]; then
                if command -v brew &>/dev/null; then
                    echo "    Using Homebrew..."
                    brew install python3
                else
                    echo "[!] Homebrew not found. Install it from https://brew.sh"
                    exit 1
                fi
            elif [[ "$PLATFORM" == "termux" ]]; then
                echo "    Using pkg..."
                pkg install -y python
            else
                echo "[!] Unknown distro: $DISTRO"
                echo "    Please install manually: python3, python3-venv (or python3-virtualenv), python3-pip"
                exit 1
            fi
            ;;
    esac
}

check_python() {
    if command -v python3 &>/dev/null; then
        PYTHON=python3
    elif command -v python &>/dev/null; then
        PYTHON=python
    else
        echo "[!] Python 3 is required but not installed."
        echo "    Auto-install failed. Please install Python 3 manually."
        exit 1
    fi
    echo "[+] Found Python: $PYTHON ($($PYTHON --version))"
}

install_deps() {
    echo "[+] Installing MailSpoof via pip..."
    local scope="$1"
    
    local pip_flags=""
    if "$PYTHON" -m pip help install 2>/dev/null | grep -q "break-system-packages"; then
        pip_flags="--break-system-packages"
    fi

    if [[ "$scope" == "system" ]]; then
        if [[ $(id -u) -eq 0 ]] || [[ "$PLATFORM" == "termux" ]] || [[ "$PLATFORM" == "macos" ]]; then
            (cd "$SCRIPT_DIR" && "$PYTHON" -m pip install --upgrade pip $pip_flags && "$PYTHON" -m pip install $pip_flags .)
        else
            (cd "$SCRIPT_DIR" && sudo "$PYTHON" -m pip install --upgrade pip $pip_flags && sudo "$PYTHON" -m pip install $pip_flags .)
        fi
    else
        (cd "$SCRIPT_DIR" && "$PYTHON" -m pip install --upgrade pip $pip_flags && "$PYTHON" -m pip install --user $pip_flags .)
    fi
}

install_system_wide() {
    echo "[+] Installing system-wide via pip..."
    install_deps "system"
    install_shortcut "system"
    echo "[+] Installed system-wide"
}

install_user_local() {
    mkdir -p "$USER_INSTALL_DIR"
    echo "[+] Installing to user site-packages and bin (~/.local/bin)..."
    install_deps "user"
    install_shortcut "user"
    echo "[+] Installed to user environment"

    if [[ ":$PATH:" != *":$USER_INSTALL_DIR:"* ]]; then
        echo ""
        echo "[!] IMPORTANT: Add this line to your ~/.bashrc or ~/.zshrc:"
        echo "    export PATH=\"\$HOME/.local/bin:\$PATH\""
        echo "    Then run:  source ~/.bashrc"
        echo ""
    fi
}

setup_dirs() {
    echo "[+] Creating config directories..."
    mkdir -p "$HOME/.mailspoof/templates"
    mkdir -p "$HOME/.mailspoof/reports"
}

main() {
    detect_platform
    print_banner
    install_system_packages
    check_python
    setup_dirs

    echo ""
    echo "Choose install location:"
    if [[ "$PLATFORM" == "macos" ]] || [[ "$PLATFORM" == "termux" ]]; then
        echo "  1) System-wide  ($INSTALL_DIR/mailspoof)"
    else
        echo "  1) System-wide  ($INSTALL_DIR/mailspoof)  [requires sudo]"
    fi
    echo "  2) User only    ($USER_INSTALL_DIR/mailspoof)"
    echo ""
    if [ -t 0 ]; then
        read -rp "Enter choice [1-2] (default: 2): " choice || choice=2
    elif [ -c /dev/tty ]; then
        read -rp "Enter choice [1-2] (default: 2): " choice </dev/tty || choice=2
    else
        choice=2
    fi
    choice=${choice:-2}

    if [[ "$choice" == "1" ]]; then
        install_system_wide
    else
        install_user_local
    fi

    echo ""
    echo ""
    echo "  ▄▄███▄▄     ▄██████  ██ ▄█   ▄███████    ▄█████▄  ▄█████▄  ▄█████▄   ▄███████"
    echo " ██▀▀██▀▀█▄   ██   ██  ▄█ ██   ██    ██   ██    ██ ██    ██ ██    ██   ██    ██"
    echo " ██  ██  ██   ██   ██  ██ ██   ██    █▀   ██    ██ ██    ██ ██    ██   ██    █▀"
    echo " ██  ██  ██   ██   ██  ██ ██   ██         ██    ██ ██    ██ ██    ██  ▄██▄▄"
    echo " ██  ██  ██ ▀████████  ██ ██   ▀████████ ▀███████▀ ██    ██ ██    ██ ▀▀██▀▀"
    echo " ██  ██  ██   ██   ██  ██ ██          ██   ██      ██    ██ ██    ██   ██"
    echo " ██  ██  ██   ██   ██  ██ ██▌  ▄      ██   ██      ██    ██ ██    ██   ██"
    echo " ▀█  ██  █▀   ██   █▀  █▀ ███▄ ▄███████▀  ▄███▀    ▀█████▀   ▀█████▀   ███"
    echo "                                  "
    echo ""
    echo "         [+] Installation Complete!"
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
