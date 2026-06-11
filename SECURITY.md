# MailSpoof — Security Policy

> Professional Email Spoofing and Phishing Simulation Framework
>
> Supported versions, responsible use guidelines, and vulnerability reporting.

## Supported Versions

| Version | Supported | Status |
|---------|-----------|--------|
| 1.2.0   | Yes     | Stable (Current) |
| 1.1.0   | Yes     | Stable (upgrade recommended) |
| 1.0.0   | No      | ~~Legacy~~ (upgrade recommended) |

## Responsible Use

MailSpoof is designed for **authorized security testing only**.

- Use only on systems you own or have explicit written permission to test.
- Do not send spoofed emails to unsuspecting individuals.
- Store SMTP credentials (profiles) securely; they are saved in `~/.mailspoof/config.json`.
- Custom templates may contain HTML with links; review before sending.

## Data Storage

MailSpoof stores the following on your local machine:

| File/Directory | Contents |
|----------------|----------|
| `~/.mailspoof/config.json` | SMTP profiles, server settings |
| `~/.mailspoof/audit.log` | Test logs (timestamp, target, result) |
| `~/.mailspoof/tracking.log` | Open/click tracking events (HTTP server) |
| `~/.mailspoof/reports/` | Generated assessment reports |
| `~/.mailspoof/templates/custom/` | User-created phishing templates |

## Reporting a Vulnerability

If you discover a security vulnerability, please email **security.mailspoof@orildo.sbs** with details. Do not open public issues for security bugs.

We will respond within 48 hours and work with you to verify and fix the issue before disclosure.
