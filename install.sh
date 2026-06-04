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

VENV_DIR="$SCRIPT_DIR/venv"

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

_SED_INPLACE="sed -i"
if [[ "$PLATFORM" == "macos" ]]; then
    _SED_INPLACE="sed -i ''"
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
    echo "      Professional Email Security Assessment v1.0.0"
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
                pkg install -y python python-pip
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
    echo "[+] Creating virtual environment..."
    "$PYTHON" -m venv "$VENV_DIR"

    echo "[+] Installing dependencies..."
    "$VENV_DIR/bin/pip" install --upgrade pip &>/dev/null
    "$VENV_DIR/bin/pip" install -r "$SCRIPT_DIR/requirements.txt"
}

create_wrapper() {
    local target="$1"
    cat > "$target" <<'WRAPPER'
#!/usr/bin/env bash

if [[ -L "$0" ]]; then
    if command -v readlink &>/dev/null; then
        SCRIPT_PATH="$(readlink "$0" 2>/dev/null || echo "$0")"
    else
        SCRIPT_PATH="$0"
    fi
else
    SCRIPT_PATH="$0"
fi

PROJECT_DIR="SCRIPT_DIR_PLACEHOLDER"
VENV_PYTHON="$PROJECT_DIR/venv/bin/python3"

if [[ ! -f "$VENV_PYTHON" ]]; then
    VENV_PYTHON="python3"
fi

exec "$VENV_PYTHON" "$PROJECT_DIR/mailspoof" "$@"
WRAPPER

    $_SED_INPLACE "s|SCRIPT_DIR_PLACEHOLDER|$SCRIPT_DIR|g" "$target"
    chmod +x "$target"
}

install_system_wide() {
    local target="$INSTALL_DIR/mailspoof"
    echo "[+] Installing system-wide to $target ..."
    if [[ "$PLATFORM" == "termux" ]]; then
        mkdir -p "$INSTALL_DIR"
        create_wrapper "$target"
    elif [[ -w "$INSTALL_DIR" ]]; then
        create_wrapper "$target"
    else
        echo "    Need sudo for system-wide install..."
        sudo bash -c "$(declare -f create_wrapper); create_wrapper '$target'"
        sudo $_SED_INPLACE "s|SCRIPT_DIR_PLACEHOLDER|$SCRIPT_DIR|g" "$target"
        sudo chmod +x "$target"
    fi
    echo "[+] Installed: $target"
}

install_user_local() {
    local target="$USER_INSTALL_DIR/mailspoof"
    mkdir -p "$USER_INSTALL_DIR"
    echo "[+] Installing to user bin: $target ..."
    create_wrapper "$target"
    $_SED_INPLACE "s|SCRIPT_DIR_PLACEHOLDER|$SCRIPT_DIR|g" "$target"
    chmod +x "$target"
    echo "[+] Installed: $target"

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
    install_deps
    setup_dirs

    echo ""
    echo "Choose install location:"
    echo "  1) System-wide  ($INSTALL_DIR/mailspoof)  [requires sudo]"
    echo "  2) User only    ($USER_INSTALL_DIR/mailspoof)"
    echo ""
    read -rp "Enter choice [1-2] (default: 2): " choice
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
