# MailSpoof v1.2.1 — Release Notes

**Release date:** 2026-09-15

## What is MailSpoof

MailSpoof is a professional email spoofing and phishing simulation framework for authorized penetration testing, red team exercises, and security awareness training. It ships a built-in SMTP server, 62 pre-built HTML phishing templates, custom template engine, audit logging, and JSON/CSV report generation.

## What changed in v1.2.1

This release focuses on reliable email delivery. The embedded SMTP server now supports an upstream relay, which routes outbound mail through an authenticated provider (Gmail, Brevo, SendGrid, etc.) instead of attempting direct MX delivery that major providers block. A one-time profile save makes every future run fully automatic with no relay prompts.

### Added

- **Upstream relay in SMTPServer** — `SMTPServer` now accepts `relay_host`, `relay_port`, `relay_user`, `relay_pass`, and `relay_tls` parameters. When a relay is configured, the embedded SMTP listener forwards all outbound mail through it instead of direct MX delivery.
- **Auto device IP detection** — `mailspoof start` detects the machine's real network IP and uses it for the outbound connection, replacing the previous `localhost` reference that caused SSL handshake failures.
- **Auto default SMTP profile** — saving a profile named `default` makes all commands (`start`, `test`, `custom`) load it silently with no relay prompts. One-time setup, zero friction after that.
- **Silent relay reconfiguration** — the running embedded server is live-wired with relay credentials as soon as the default profile is loaded, so every email in the session goes through the relay.
- **RPM build script** — `scripts/build-rpm.sh` builds a proper RPM package with `%post`/`%preun` scriptlets for pip install/uninstall, desktop entry, and icon.

### Fixed

- **RFC 5322 duplicate header bug** — the relay path no longer prepends `From:`/`To:` headers that the MIME message already contains. Duplicate headers caused strict MTAs to reject the message.
- **SSL `WRONG_VERSION_NUMBER` error** — `SMTPServer` was initialized with `relay_host=localhost` by default, causing an SSL handshake against itself. The server now starts with no relay and configures one only after credentials are confirmed.
- **`_cmd_list` TypeError** — fixed a crash when `_cmd_list` was called with a positional argument it did not accept.
- **`uninstall.py` SyntaxError** — restored the missing `def ask_yes_no(prompt):` function header.
- **`formataddr` header construction** — `lib/engine.py` uses `email.utils.formataddr` for RFC-compliant `Display Name <email>` formatting.
- **Desktop icon not showing** — `mailspoof.desktop` now uses `Icon=mailspoof` (bare name) instead of an absolute path, and `install.sh` runs `gtk-update-icon-cache` and `update-desktop-database` after install so the icon appears immediately.

### How delivery works now

```
Your machine
    -> MailSpoof SMTP server (device IP:2525)
        -> Upstream relay (smtp.gmail.com:587, authenticated)
            -> Recipient mail server
                -> Inbox shows: From: ceo@company.com
```

The spoofed `From` address is what the recipient sees. The relay is the transport only and is never exposed to the recipient.

### One-time setup

```bash
mailspoof profile add default \
  --host smtp.gmail.com \
  --port 587 \
  --user your.email@gmail.com \
  --pass "xxxx xxxx xxxx xxxx" \
  --use-tls
```

After that, `mailspoof start` sends with no prompts.

## Installation

### One-line install (Linux, macOS, Termux)

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/syed-sameer-ul-hassan/MailSpoof/main/install.sh)
```

### Debian / Ubuntu

```bash
sudo dpkg -i mailspoof-v1.2.1.deb
sudo apt-get install -f
```

### Fedora / RHEL / CentOS

```bash
sudo rpm -i mailspoof-1.2.1-1.noarch.rpm
```

### Arch Linux

```bash
makepkg -si
```

### From source

```bash
git clone https://github.com/syed-sameer-ul-hassan/MailSpoof.git
cd MailSpoof
bash install.sh
```

## Upgrading from v1.2.0

```bash
cd MailSpoof
git pull
bash install.sh
```

Existing SMTP profiles and custom templates in `~/.mailspoof/` are preserved.

## Full changelog

See [docs/CHANGELOG.md](docs/CHANGELOG.md) for the complete version history.
