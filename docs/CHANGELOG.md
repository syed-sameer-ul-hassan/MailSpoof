# MailSpoof — Changelog

> Professional Email Spoofing and Phishing Simulation Framework
>
> All notable changes and version history.

All notable changes to MailSpoof are documented here.

## [1.2.0] - 2026-06-11

### Added — Tracking & Features
- **HTTP Tracking Server** — Embedded HTTP server running on port 8080.
- **Bulk Target Lists (CSV)** — Send to hundreds of targets via `--target-list`.
- **Attachment Payloads** — Attach files to test gateway filtering via `--attach`.
- **Advanced Headers** — Inject custom `--reply-to` and `--x-mailer`.
- **Docker Support** — Deploy instantly using `docker-compose up`.
- **17 New Phishing Templates** — Total templates increased from 45 to 62, adding new logistics, credential harvesting, document phishing, and device alert scenarios.

### Fixed
- **Uninstall crash fix** — Resolved a `SyntaxError` crash in `uninstall.py` where `print_banner()` was missing its function body.


## [1.1.0] - 2026-06-06

### Added — Templates
- **45+ built-in phishing templates** (up from 5) covering:
  - Social Media: LinkedIn, Facebook, Instagram, Twitter/X, TikTok, Snapchat, Pinterest, Reddit, Discord, Meta Ads, Twitch
  - SaaS / Cloud: Slack, Zoom, Outlook, Google Workspace, Dropbox, OneDrive, Microsoft Teams, WhatsApp
  - Developer Platforms: GitHub OAuth, GitHub SSO, GitLab OAuth, Bitbucket Access, Salesforce MFA
  - Consumer Services: Spotify, Netflix, Airbnb, Uber, Amazon, Prime Video, Apple ID
  - Financial / Cloud: AWS Root Access, PayPal Invoice, Bank Account Suspension
  - HR / BEC: HR Benefits, Overdue Invoice, Payment Authorization CFO
- All templates redesigned with **realistic HTML**, branded images, and styled CTA buttons (no raw URLs exposed)
- Template metadata support: `Tags`, `Id`, `disk_path`
- `{TODAY}` auto-replacement with current date

### Added — Template Management
- `mailspoof preview <id>` — Preview template body (strips HTML unless `--raw`)
- `mailspoof edit-template <id>` — Edit custom or built-in templates via `$EDITOR` (default nano), auto-reload after save
- `mailspoof remove-template <id>` — Remove custom templates (built-ins protected)
- `mailspoof list --filter <text>` — Filter templates by name, category, tags, or body content
- Custom template IDs are **auto-assigned** and persisted in the file (`Id:` field)

### Added — SMTP Profile Management
- `mailspoof profile list` — List saved SMTP relay profiles
- `mailspoof profile add <name> --host ... --port ...` — Save named relay credentials
- `mailspoof profile remove <name>` — Delete a profile
- `--profile <name>` flag on `start`, `test`, and `custom` commands
- Profiles stored in `~/.mailspoof/config.json`

### Added — Diagnostics & Reporting
- `--verbose` flag on `start`, `test`, `custom` — Shows SMTP stage-by-stage output (connect, TLS, auth, send)
- `send_email()` now returns `(bool, str)` with error details for logging
- `mailspoof report --format csv` — CSV report export alongside JSON
- Per-test error details captured in audit log and CSV report

### Added — Desktop Integration
- `mailspoof.desktop` Linux desktop entry with application icon (`assets/icon.svg`)
- `install.sh` now auto-installs icon to `/usr/share/icons/` (system) or `~/.local/share/icons/` (user)
- `install.sh` auto-installs `.desktop` file to applications directory
- Icon path uses standard `mailspoof.svg` name for cross-device resolution

### Fixed
- **Installation**: `install.sh` installs via pip directly (no venv wrapper), supports both system-wide and user installs
- **Entry point**: Console script correctly points to `lib.cli:main`
- **Templates**: Packaged templates load from `lib/templates/builtins/` on any install type
- **Uninstall**: Inline fallback uninstaller removes wrappers, config, templates, and pip package reliably
- **Custom templates**: Saved to dedicated `~/.mailspoof/templates/custom/` subfolder
- **Email format**: Switched to `multipart/alternative` MIME with HTML + plain text fallback
- **HTML preview**: Templates render as styled preview instead of raw code in terminal
- **Duplicate folders**: Removed repo copy of templates to avoid confusion

### Documentation
- `SECURITY_SCENARIOS.md` — Full 45+ template catalog with categories, severities, and descriptions
- `README.md` — Updated features, usage examples, template format, architecture diagram
- `TROUBLESHOOTING.md` — Added profile issues, template management, verbose diagnostics, desktop launcher
- `DEPLOYMENT.md` — Added post-install steps for desktop launcher, SMTP profiles, and custom templates
- `SECURITY.md` — Added responsible use guidelines and data storage table
- `CHANGELOG.md` — This file

---

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
