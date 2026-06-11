Name:           mailspoof
Version:        1.2.0
Release:        1%{?dist}
Summary:        Professional Email Spoofing and Phishing Simulation Framework

License:        Apache-2.0
URL:            https://github.com/syed-sameer-ul-hassan/MailSpoof
Source0:        %{url}/archive/refs/tags/v%{version}.tar.gz

BuildArch:      noarch
Requires:      python3 >= 3.8, python3-pip, python3-virtualenv

%description
MailSpoof is a modular email spoofing assessment tool for authorized
penetration testing, red team exercises, and security awareness training.
It features a built-in SMTP server, pre-built phishing scenarios,
custom template creation, audit logging, and JSON report generation.

%prep
%setup -q

%build

%install
install -dm755 %{buildroot}/usr/share/mailspoof
cp -r lib templates mailspoof requirements.txt %{buildroot}/usr/share/mailspoof/

install -dm755 %{buildroot}/usr/bin
cat > %{buildroot}/usr/bin/mailspoof << 'EOF'
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
chmod 755 %{buildroot}/usr/bin/mailspoof

install -Dm644 LICENSE %{buildroot}%{_defaultlicensedir}/%{name}/LICENSE

%files
/usr/share/mailspoof
/usr/bin/mailspoof
%license LICENSE

%changelog
* Thu Jun 11 2026 Syed Sameer Ul Hassan <support@mailspoof.local> - 1.2.0-1
- Initial RPM release
