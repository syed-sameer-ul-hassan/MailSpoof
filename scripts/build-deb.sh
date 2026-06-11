#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && cd .. && pwd)"
BUILD_DIR="/tmp/mailspoof-deb"
DEB_NAME="mailspoof-v1.2.0.deb"

echo "[+] Cleaning old build..."
rm -rf "$BUILD_DIR"
rm -f "$SCRIPT_DIR/$DEB_NAME"

echo "[+] Preparing build directory..."
mkdir -p "$BUILD_DIR/mailspoof/usr/share/mailspoof"
mkdir -p "$BUILD_DIR/mailspoof/usr/bin"
mkdir -p "$BUILD_DIR/mailspoof/usr/share/applications"
mkdir -p "$BUILD_DIR/mailspoof/usr/share/icons/hicolor/scalable/apps"
mkdir -p "$BUILD_DIR/mailspoof/DEBIAN"

echo "[+] Copying source files..."
cp -r "$SCRIPT_DIR/lib" "$SCRIPT_DIR/assets" "$SCRIPT_DIR/mailspoof" "$SCRIPT_DIR/requirements.txt" "$SCRIPT_DIR/setup.py" "$SCRIPT_DIR/pyproject.toml" "$BUILD_DIR/mailspoof/usr/share/mailspoof/"

echo "[+] Copying desktop entry and icon..."
cp "$SCRIPT_DIR/mailspoof.desktop" "$BUILD_DIR/mailspoof/usr/share/applications/"
cp "$SCRIPT_DIR/assets/icon.svg" "$BUILD_DIR/mailspoof/usr/share/icons/hicolor/scalable/apps/mailspoof.svg"

echo "[+] Removing unwanted files..."
find "$BUILD_DIR/mailspoof/usr/share/mailspoof" -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
find "$BUILD_DIR/mailspoof/usr/share/mailspoof" -type f -name '*.pyc' -delete 2>/dev/null || true
rm -rf "$BUILD_DIR/mailspoof/usr/share/mailspoof/venv" 2>/dev/null || true

echo "[+] Writing control file..."
cat > "$BUILD_DIR/mailspoof/DEBIAN/control" << 'EOF'
Package: mailspoof
Version: 1.2.0
Section: utils
Priority: optional
Architecture: all
Depends: python3, python3-pip
Maintainer: MailSpoof Security Team <support@mailspoof.local>
Description: Professional Email Security Assessment Framework
 MailSpoof is a professional email spoofing and phishing
 simulation framework for authorized penetration testing
 and security awareness training. Built-in SMTP server,
 45+ HTML templates, custom template engine, audit logging,
 SMTP profile management, and report generation.
EOF

cat > "$BUILD_DIR/mailspoof/DEBIAN/postinst" << 'EOF'
#!/bin/bash
PROJECT_DIR="/usr/share/mailspoof"
PYTHON3="/usr/bin/python3"

if [[ ! -f "$PYTHON3" ]]; then
    PYTHON3=$(command -v python3 2>/dev/null || echo "")
fi
if [[ -z "$PYTHON3" ]]; then
    echo "[!] python3 not found."
    exit 1
fi

echo "[*] Installing MailSpoof via pip..."
"$PYTHON3" -m pip install "$PROJECT_DIR" >/dev/null 2>&1 || {
    echo "[!] pip install failed. Trying with --break-system-packages..."
    "$PYTHON3" -m pip install --break-system-packages "$PROJECT_DIR" >/dev/null 2>&1
}

WRAPPER="/usr/bin/mailspoof"
cat > "$WRAPPER" << 'WEOF'
#!/bin/bash
PYTHON3="/usr/bin/python3"
if [[ ! -f "$PYTHON3" ]]; then
    PYTHON3=$(command -v python3 2>/dev/null || echo "")
fi
if [[ -z "$PYTHON3" ]]; then
    echo "[!] python3 not found."
    exit 1
fi
exec "$PYTHON3" -m mailspoof "$@"
WEOF
chmod +x "$WRAPPER"

echo "[+] MailSpoof v1.2.0 installed."
EOF

cat > "$BUILD_DIR/mailspoof/DEBIAN/prerm" << 'EOF'
#!/bin/bash
WRAPPER="/usr/bin/mailspoof"
PYTHON3="/usr/bin/python3"

if [[ ! -f "$PYTHON3" ]]; then
    PYTHON3=$(command -v python3 2>/dev/null || echo "")
fi

if [[ -n "$PYTHON3" ]]; then
    echo "[*] Removing MailSpoof pip package..."
    "$PYTHON3" -m pip uninstall -y mailspoof >/dev/null 2>&1 || true
fi

[[ -f "$WRAPPER" ]] && rm -f "$WRAPPER"
[[ -f "/usr/share/applications/mailspoof.desktop" ]] && rm -f "/usr/share/applications/mailspoof.desktop"
[[ -f "/usr/share/icons/hicolor/scalable/apps/mailspoof.svg" ]] && rm -f "/usr/share/icons/hicolor/scalable/apps/mailspoof.svg"
EOF

chmod +x "$BUILD_DIR/mailspoof/DEBIAN/postinst" "$BUILD_DIR/mailspoof/DEBIAN/prerm"

echo "[+] Building .deb package..."
dpkg-deb --build "$BUILD_DIR/mailspoof" "$SCRIPT_DIR/$DEB_NAME"

echo "[+] Cleaning up..."
rm -rf "$BUILD_DIR"

echo "[+] Done: $SCRIPT_DIR/$DEB_NAME"
