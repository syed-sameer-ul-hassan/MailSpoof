#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && cd .. && pwd)"
BUILD_DIR="/tmp/mailspoof-deb"
DEB_NAME="mailspoof-v1.0.0.deb"

echo "[+] Cleaning old build..."
rm -rf "$BUILD_DIR"
rm -f "$SCRIPT_DIR/$DEB_NAME"

echo "[+] Preparing build directory..."
mkdir -p "$BUILD_DIR/mailspoof/usr/share/mailspoof"
mkdir -p "$BUILD_DIR/mailspoof/usr/bin"
mkdir -p "$BUILD_DIR/mailspoof/DEBIAN"

echo "[+] Copying source files..."
cp -r "$SCRIPT_DIR/lib" "$SCRIPT_DIR/templates" "$SCRIPT_DIR/mailspoof" "$SCRIPT_DIR/requirements.txt" "$BUILD_DIR/mailspoof/usr/share/mailspoof/"

echo "[+] Removing unwanted files..."
find "$BUILD_DIR/mailspoof/usr/share/mailspoof" -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
find "$BUILD_DIR/mailspoof/usr/share/mailspoof" -type f -name '*.pyc' -delete 2>/dev/null || true
rm -rf "$BUILD_DIR/mailspoof/usr/share/mailspoof/venv" 2>/dev/null || true

echo "[+] Writing control file..."
cat > "$BUILD_DIR/mailspoof/DEBIAN/control" << 'EOF'
Package: mailspoof
Version: 1.0.0
Section: utils
Priority: optional
Architecture: all
Depends: python3, python3-venv
Maintainer: MailSpoof Security Team <support@mailspoof.local>
Description: Professional Email Security Assessment Framework
 MailSpoof is a modular email spoofing assessment tool for
 authorized penetration testing and security research.
EOF

cat > "$BUILD_DIR/mailspoof/DEBIAN/postinst" << 'EOF'
#!/bin/bash
PROJECT_DIR="/usr/share/mailspoof"
VENV_DIR="$PROJECT_DIR/venv"
PYTHON3="/usr/bin/python3"

if [[ ! -f "$PYTHON3" ]]; then
    PYTHON3=$(command -v python3 2>/dev/null || echo "")
fi
if [[ -z "$PYTHON3" ]]; then
    echo "[!] python3 not found."
    exit 1
fi

"$PYTHON3" -m venv "$VENV_DIR" || exit 1
"$VENV_DIR/bin/pip" install --upgrade pip >/dev/null 2>&1
"$VENV_DIR/bin/pip" install -r "$PROJECT_DIR/requirements.txt" >/dev/null 2>&1

WRAPPER="/usr/bin/mailspoof"
cat > "$WRAPPER" << 'WEOF'
#!/bin/bash
PROJECT_DIR="/usr/share/mailspoof"
VENV_DIR="$PROJECT_DIR/venv"
exec "$VENV_DIR/bin/python" "$PROJECT_DIR/mailspoof" "$@"
WEOF
chmod +x "$WRAPPER"
EOF

cat > "$BUILD_DIR/mailspoof/DEBIAN/prerm" << 'EOF'
#!/bin/bash
VENV_DIR="/usr/share/mailspoof/venv"
WRAPPER="/usr/bin/mailspoof"
[[ -f "$WRAPPER" ]] && rm -f "$WRAPPER"
[[ -d "$VENV_DIR" ]] && rm -rf "$VENV_DIR"
EOF

chmod +x "$BUILD_DIR/mailspoof/DEBIAN/postinst" "$BUILD_DIR/mailspoof/DEBIAN/prerm"

echo "[+] Building .deb package..."
dpkg-deb --build "$BUILD_DIR/mailspoof" "$SCRIPT_DIR/$DEB_NAME"

echo "[+] Cleaning up..."
rm -rf "$BUILD_DIR"

echo "[+] Done: $SCRIPT_DIR/$DEB_NAME"
