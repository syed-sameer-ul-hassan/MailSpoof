# MailSpoof — Deployment Guide

> Professional Email Spoofing and Phishing Simulation Framework
>
> Installation methods for Debian, Fedora, Arch, macOS, Termux, and generic Linux.

## Installation Decision Tree

```mermaid
flowchart TD
    A[Choose Installation Method] --> B{Preferred Format?}
    B -->|.deb| C[Debian / Ubuntu]
    B -->|.rpm| D[Fedora / RHEL / CentOS]
    B -->|PKGBUILD| E[Arch / Manjaro]
    B -->|Generic| F[Makefile / install.sh]
    B -->|Manual| G[venv + pip]
    C --> C1[sudo dpkg -i mailspoof-v1.0.0.deb]
    D --> D1[rpmbuild -ba mailspoof.spec]
    E --> E1[makepkg -si]
    F --> F1[bash install.sh]
    G --> G1[python3 -m venv venv]
    G1 --> G2[pip install -r requirements.txt]
```

## Method 1: Universal Installer (Any Distro)

Auto-detects your platform and installs the correct dependencies:

```bash
cd MailSpoof
bash install.sh
```

Supported: Debian, Ubuntu, Fedora, RHEL, CentOS, Rocky, AlmaLinux, Arch, Manjaro, EndeavourOS, macOS, Termux, and generic Python3 installs.

## Method 2: Debian / Ubuntu (.deb)

```bash
sudo dpkg -i mailspoof-v1.0.0.deb
sudo apt-get install -f
```

The `.deb` installs to `/usr/share/mailspoof/` and creates `/usr/bin/mailspoof`.

Or build from source:

```bash
bash scripts/build-deb.sh
```

## Method 3: Fedora / RHEL / CentOS / openSUSE (.rpm)

```bash
sudo dnf install rpm-build
rpmbuild -ba mailspoof.spec
sudo rpm -i ~/rpmbuild/RPMS/noarch/mailspoof-*.rpm
```

## Method 4: Arch Linux (AUR / PKGBUILD)

```bash
cd MailSpoof
makepkg -si
```

Or install from AUR helper:

```bash
yay -S mailspoof
```

## Method 5: Generic Makefile

```bash
make install
sudo make install PREFIX=/usr
make uninstall
```

## Method 6: Manual / Development

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
./mailspoof --version
```

## Requirements

| Distro | Packages |
|--------|----------|
| Debian/Ubuntu | `python3`, `python3-venv`, `python3-pip` |
| Fedora/RHEL | `python3`, `python3-pip`, `python3-virtualenv` |
| Arch | `python`, `python-pip`, `python-virtualenv` |

Optional: `dnspython` for MX record lookups.

## Port Requirements

| Port | Use | Privilege |
|------|-----|-----------|
| 25 | Direct MX relay | Root |
| 2525 | Built-in SMTP server | Any |
| 587 | External SMTP relay (STARTTLS) | Any |
| 465 | External SMTP relay (SSL) | Any |

## Uninstall

```bash
mailspoof uninstall
```

Or manually:

```bash
sudo rm -f /usr/bin/mailspoof
sudo rm -rf /usr/share/mailspoof
rm -rf ~/.mailspoof
```
