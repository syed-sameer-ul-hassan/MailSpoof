# MailSpoof — Changelog

> Professional Email Spoofing and Phishing Simulation Framework
>
> All notable changes and version history.

All notable changes to MailSpoof are documented here.

## [1.0.0] - 2026-06-04

### Added
- Built-in SMTP server with MX relay support
- 5 pre-built spoofing scenarios
- Custom template creation (`mailspoof create`)
- Audit logging (`mailspoof logs`)
- JSON report generation (`mailspoof report`)
- External SMTP relay support with TLS/auth
- IP-blacklist error detection and actionable advice
- Debian package (`mailspoof-v1.0.0.deb`)
- `.deb` postinst creates `/usr/bin/mailspoof` wrapper
- Shared banner module (`lib/banner.py`)
- Apache-2.0 License
- GitHub Actions CI pipeline
- Issue templates (bug report, feature request)

### Fixed
- Direct MX delivery now returns specific SMTP error codes
- Uninstaller handles `/usr/bin/mailspoof` (`.deb` installs)
- Removed stray `DEBIAN/` from package contents
- Excluded `__pycache__` and `.pyc` from `.deb`
