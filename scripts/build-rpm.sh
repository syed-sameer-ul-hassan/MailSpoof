#!/bin/bash
# Build RPM package for MailSpoof
set -e

# Resolve repo root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && cd .. && pwd)"
VERSION="1.2.1"
RELEASE="1"
PKG_NAME="mailspoof"
RPM_BUILD_ROOT="$HOME/rpmbuild"

echo "[+] Checking build dependencies..."
for cmd in rpmbuild python3 pip3; do
    if ! command -v "$cmd" &>/dev/null; then
        echo "[!] Required command not found: $cmd"
        echo "    Install with: sudo dnf install rpm-build python3 python3-pip"
        exit 1
    fi
done

echo "[+] Preparing rpmbuild directory tree..."
mkdir -p "$RPM_BUILD_ROOT"/{BUILD,RPMS,SOURCES,SPECS,SRPMS}

echo "[+] Creating source tarball..."
TARBALL="$RPM_BUILD_ROOT/SOURCES/${PKG_NAME}-${VERSION}.tar.gz"
STAGING="/tmp/${PKG_NAME}-${VERSION}"

rm -rf "$STAGING"
mkdir -p "$STAGING"

# Copy source files
cp -r "$SCRIPT_DIR/lib"           "$STAGING/"
cp -r "$SCRIPT_DIR/assets"        "$STAGING/"
cp    "$SCRIPT_DIR/mailspoof"      "$STAGING/"
cp    "$SCRIPT_DIR/requirements.txt" "$STAGING/"
cp    "$SCRIPT_DIR/setup.py"       "$STAGING/"
cp    "$SCRIPT_DIR/pyproject.toml" "$STAGING/"
cp    "$SCRIPT_DIR/mailspoof.desktop" "$STAGING/"
cp    "$SCRIPT_DIR/LICENSE"        "$STAGING/"
cp    "$SCRIPT_DIR/README.md"      "$STAGING/"

# Strip pycache
find "$STAGING" -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
find "$STAGING" -type f -name '*.pyc' -delete 2>/dev/null || true
rm -rf "$STAGING/venv" 2>/dev/null || true

# Create tarball
tar -czf "$TARBALL" -C /tmp "${PKG_NAME}-${VERSION}"
rm -rf "$STAGING"
echo "[+] Tarball: $TARBALL"

echo "[+] Writing spec file..."
SPEC="$RPM_BUILD_ROOT/SPECS/${PKG_NAME}.spec"

cat > "$SPEC" << SPECEOF
Name:           ${PKG_NAME}
Version:        ${VERSION}
Release:        ${RELEASE}%{?dist}
Summary:        Professional Email Spoofing and Phishing Simulation Framework

License:        Apache-2.0
URL:            https://github.com/syed-sameer-ul-hassan/MailSpoof
Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch
Requires:       python3 >= 3.8, python3-pip

%description
MailSpoof is a modular email spoofing assessment tool for authorized
penetration testing, red team exercises, and security awareness training.
Features: built-in SMTP server with upstream relay support, 62 pre-built
HTML phishing templates, custom template engine, SMTP profile management,
auto default profile loading, audit logging, and JSON/CSV report generation.

%prep
%setup -q

%build
# No compiled artifacts

%install
# Install package files
install -dm755 %{buildroot}/usr/share/%{name}
cp -r lib assets mailspoof requirements.txt setup.py pyproject.toml \
    %{buildroot}/usr/share/%{name}/

# Install desktop entry
install -Dm644 mailspoof.desktop \
    %{buildroot}/usr/share/applications/mailspoof.desktop

# Install icon
install -Dm644 assets/icon.svg \
    %{buildroot}/usr/share/icons/hicolor/scalable/apps/mailspoof.svg

# Install wrapper script
install -dm755 %{buildroot}/usr/bin
cat > %{buildroot}/usr/bin/mailspoof << 'WEOF'
#!/bin/bash
PYTHON3="\$(command -v python3 2>/dev/null)"
if [[ -z "\$PYTHON3" ]]; then
    echo "[!] python3 not found." >&2
    exit 1
fi
exec "\$PYTHON3" -m pip install --quiet --break-system-packages /usr/share/mailspoof 2>/dev/null || true
exec "\$PYTHON3" -m mailspoof "\$@"
WEOF
chmod 755 %{buildroot}/usr/bin/mailspoof

# Install license
install -Dm644 LICENSE %{buildroot}%{_defaultlicensedir}/%{name}/LICENSE

%post
PYTHON3="\$(command -v python3 2>/dev/null)"
if [[ -z "\$PYTHON3" ]]; then
    echo "[!] python3 not found. Install manually." >&2
    exit 0
fi
echo "[*] Installing MailSpoof via pip..."
"\$PYTHON3" -m pip install --quiet /usr/share/mailspoof 2>/dev/null || \
"\$PYTHON3" -m pip install --quiet --break-system-packages /usr/share/mailspoof 2>/dev/null || true
echo "[+] MailSpoof ${VERSION} installed."

%preun
PYTHON3="\$(command -v python3 2>/dev/null)"
if [[ -n "\$PYTHON3" ]]; then
    "\$PYTHON3" -m pip uninstall -y mailspoof 2>/dev/null || true
fi

%files
/usr/share/%{name}
/usr/bin/mailspoof
/usr/share/applications/mailspoof.desktop
/usr/share/icons/hicolor/scalable/apps/mailspoof.svg
%license LICENSE

%changelog
* Mon Sep 15 2026 Syed Sameer Ul Hassan <support@mailspoof.local> - ${VERSION}-${RELEASE}
- Upstream relay support in SMTPServer (relay_host, relay_port, relay_user, relay_pass, relay_tls)
- Auto device IP detection on start
- Auto default SMTP profile loading across all commands
- RFC 5322 header compliance fix using formataddr
- SSL WRONG_VERSION_NUMBER bug fix
- Updated to 62 phishing templates

* Thu Jun 11 2026 Syed Sameer Ul Hassan <support@mailspoof.local> - 1.2.0-1
- HTTP tracking server on port 8080
- Bulk target CSV support
- Attachment payload testing
- Docker support
- 17 new phishing templates

* Wed Jun 04 2026 Syed Sameer Ul Hassan <support@mailspoof.local> - 1.0.0-1
- Initial RPM release
SPECEOF

echo "[+] Building RPM..."
rpmbuild -ba "$SPEC"

RPM_FILE=$(find "$RPM_BUILD_ROOT/RPMS" -name "${PKG_NAME}-${VERSION}*.rpm" | head -1)
if [[ -n "$RPM_FILE" ]]; then
    cp "$RPM_FILE" "$SCRIPT_DIR/"
    echo "[+] Done: $SCRIPT_DIR/$(basename "$RPM_FILE")"
else
    echo "[!] RPM build completed but package not found in $RPM_BUILD_ROOT/RPMS"
    echo "    Check $RPM_BUILD_ROOT/RPMS for the output file."
fi
