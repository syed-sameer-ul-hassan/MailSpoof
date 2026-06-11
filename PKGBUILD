
pkgname=mailspoof
pkgver=1.2.0
pkgrel=1
pkgdesc="Professional Email Spoofing and Phishing Simulation Framework"
arch=('any')
url="https://github.com/syed-sameer-ul-hassan/MailSpoof"
license=('Apache-2.0')
depends=('python>=3.8' 'python-pip' 'python-virtualenv')
makedepends=()
source=("$pkgname-$pkgver.tar.gz::$url/archive/refs/tags/v$pkgver.tar.gz")
sha256sums=('SKIP')

package() {
    cd "$srcdir/MailSpoof-$pkgver"

    install -dm755 "$pkgdir/usr/share/mailspoof"
    cp -r lib templates mailspoof requirements.txt "$pkgdir/usr/share/mailspoof/"

    install -dm755 "$pkgdir/usr/bin"
    cat > "$pkgdir/usr/bin/mailspoof" << 'EOF'
#!/bin/bash
PROJECT_DIR="/usr/share/mailspoof"
PYTHON3="/usr/bin/python3"
VENV_DIR="$PROJECT_DIR/venv"

if [[ ! -d "$VENV_DIR" ]]; then
    "$PYTHON3" -m venv "$VENV_DIR"
    "$VENV_DIR/bin/pip" install --upgrade pip >/dev/null 2>&1
    "$VENV_DIR/bin/pip" install -r "$PROJECT_DIR/requirements.txt" >/dev/null 2>&1
fi

exec "$VENV_DIR/bin/python" "$PROJECT_DIR/mailspoof" "$@"
EOF
    chmod 755 "$pkgdir/usr/bin/mailspoof"

    install -Dm644 LICENSE "$pkgdir/usr/share/licenses/$pkgname/LICENSE"
}
