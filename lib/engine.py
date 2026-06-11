from __future__ import annotations

import smtplib
import time
import re
import html
import os
from datetime import datetime
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from email.utils import formatdate, make_msgid

from lib.core import Config, Scenario, TestResult

R = "\033[91m"
G = "\033[92m"
Y = "\033[93m"
D = "\033[0m"

def _disclaimer_text(scenario_name: str, category: str, severity: str, version: str) -> str:
    return (
        f"\n{'─' * 64}\n"
        "This email was sent using MailSpoof for authorized security testing.\n"
        "If you received this unexpectedly, contact your IT security team.\n\n"
        f"Test Details:\n"
        f"  Scenario : {scenario_name}\n"
        f"  Category : {category}\n"
        f"  Severity : {severity}\n"
        f"  Timestamp: {datetime.now().isoformat()}\n\n"
        f"MailSpoof v{version} - Professional Email Security Assessment\n"
        f"{'─' * 64}"
    )

def _disclaimer_html(scenario_name: str, category: str, severity: str, version: str) -> str:
    return (
        "<hr style=\"margin:18px 0; border:0; border-top:1px solid #e5e7eb;\">"
        "<p style=\"font-size:12px; color:#6b7280; line-height:1.6;\">"
        "This email was sent using <strong>MailSpoof</strong> for authorized security testing.<br>"
        "If you received this unexpectedly, contact your IT security team.<br><br>"
        f"Test Details:<br>"
        f"Scenario: {html.escape(scenario_name)}<br>"
        f"Category: {html.escape(category)}<br>"
        f"Severity: {html.escape(severity)}<br>"
        f"Timestamp: {datetime.now().isoformat()}<br><br>"
        f"MailSpoof v{html.escape(version)} - Professional Email Security Assessment"
        "</p>"
    )

def _strip_html(html_body: str) -> str:
    text = re.sub(r"<\s*br\s*/?>", "\n", html_body, flags=re.IGNORECASE)
    text = re.sub(r"<\s*/p\s*>", "\n\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    return html.unescape(text)

def build_mime_email(
    from_email: str,
    from_name: str,
    subject: str,
    body: str,
    target: str,
    scenario_name: str = "Custom",
    category: str = "Custom Test",
    severity: str = "N/A",
    version: str = "1.2.0",
    attachments: list[str] = None,
    headers: dict[str, str] = None,
) -> str:
    msg = MIMEMultipart("mixed") if attachments else MIMEMultipart("alternative")
    msg["From"] = f"{from_name} <{from_email}>"
    msg["To"] = target
    msg["Subject"] = Header(subject, "utf-8")
    msg["Date"] = formatdate(localtime=True)
    domain = from_email.split("@")[1] if "@" in from_email else "localhost"
    msg["Message-ID"] = make_msgid(domain=domain)

    if headers:
        for k, v in headers.items():
            msg[k] = v

    is_html = "<html" in body.lower()

    if is_html:
        plain_body = _strip_html(body)
        html_body = body
    else:
        plain_body = body
        html_body = f"<html><body><pre style=\"font-family:Arial, sans-serif; white-space:pre-wrap;\">{html.escape(body)}</pre></body></html>"

    full_plain = plain_body + _disclaimer_text(scenario_name, category, severity, version)
    full_html = html_body + _disclaimer_html(scenario_name, category, severity, version)

    if attachments:
        alt_part = MIMEMultipart("alternative")
        alt_part.attach(MIMEText(full_plain, "plain", "utf-8"))
        alt_part.attach(MIMEText(full_html, "html", "utf-8"))
        msg.attach(alt_part)
        
        for filepath in attachments:
            if not os.path.isfile(filepath):
                print(f"{R}[!] Attachment not found: {filepath}{D}")
                continue
            try:
                with open(filepath, "rb") as f:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(f.read())
                encoders.encode_base64(part)
                filename = os.path.basename(filepath)
                part.add_header("Content-Disposition", f"attachment; filename={filename}")
                msg.attach(part)
            except Exception as exc:
                print(f"{R}[!] Failed to attach {filepath}: {exc}{D}")
    else:
        msg.attach(MIMEText(full_plain, "plain", "utf-8"))
        msg.attach(MIMEText(full_html, "html", "utf-8"))

    return msg.as_string()

def _explain_smtp_error(exc: Exception) -> str:
    err = str(exc).lower()
    msg = str(exc)

    if any(x in err for x in ("tss09", "permanently deferred", "blacklist", "blocked", "rbl", "spamhaus", "barracuda")):
        return (
            f"{R}[!] Your IP is blacklisted by the recipient's mail server.{D}\n"
            f"    {Y}Fix: Use an external SMTP relay instead of direct MX delivery.{D}\n"
            f"    mailspoof start --smtp-host smtp.gmail.com --smtp-port 587\n"
            f"    Or:   ./mailspoof start  (interactive mode lets you set relay)"
        )
    if any(x in err for x in ("connection refused", "connection reset", "timed out", "timeout")):
        if "port 25" in err or "mx" in err:
            return (
                f"{R}[!] Cannot connect to recipient MX server (port 25 blocked?).{D}\n"
                f"    {Y}Fix: Use an external SMTP relay with authentication.{D}\n"
                f"    mailspoof start --smtp-host smtp.gmail.com --smtp-port 587\n"
                f"    Or:   mailspoof test <id> <target> --smtp-host <host> --smtp-port 587"
            )
    if any(x in err for x in ("spf", "dkim", "dmarc", "domain", "policy")):
        return (
            f"{R}[!] Domain policy rejected the email (SPF/DKIM/DMARC).{D}\n"
            f"    {Y}Fix: Use an external SMTP relay that passes these checks.{D}"
        )
    if any(x in err for x in ("relay", "rejected", "550", "553", "554")):
        return (
            f"{R}[!] Mail server rejected the message.{D}\n"
            f"    {Y}Fix: Use an external SMTP relay with valid credentials.{D}\n"
            f"    mailspoof start --smtp-host smtp.gmail.com --smtp-port 587\n"
            f"    Or:   mailspoof test <id> <target> --smtp-host <host> --smtp-port 587"
        )
    return f"{R}[!] SMTP Error: {msg}{D}"

def send_email(
    from_email: str,
    to_email: str,
    content: str,
    smtp_host: str = "localhost",
    smtp_port: int = 2525,
    timeout: int = 30,
    smtp_user: str = "",
    smtp_pass: str = "",
    use_tls: bool = False,
    verbose: bool = False,
) -> tuple[bool, str]:
    try:
        if verbose:
            print(f"[SMTP] connect {smtp_host}:{smtp_port} tls={'yes' if use_tls else 'no'}")
        if use_tls or smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=timeout)
        else:
            server = smtplib.SMTP(smtp_host, smtp_port, timeout=timeout)

        with server:
            if verbose:
                print("[SMTP] connected")
            if not (use_tls or smtp_port == 465):
                try:
                    server.starttls()
                    if verbose:
                        print("[SMTP] starttls ok")
                except Exception as exc:
                    if verbose:
                        print(f"[SMTP] starttls failed: {exc}")
            if smtp_user and smtp_pass:
                if verbose:
                    print(f"[SMTP] login as {smtp_user}")
                server.login(smtp_user, smtp_pass)
            if verbose:
                print("[SMTP] sending...")
            server.sendmail(from_email, [to_email], content.encode("utf-8"))
        return True, ""
    except smtplib.SMTPAuthenticationError as exc:
        print(f"\n{R}[!] SMTP Authentication failed: {exc}{D}")
        print(f"    {Y}Check your username/password. For Gmail, use an App Password.{D}")
        return False, str(exc)
    except smtplib.SMTPRecipientsRefused as exc:
        print(f"\n{R}[!] Recipient refused: {exc}{D}")
        return False, str(exc)
    except smtplib.SMTPException as exc:
        print(f"\n{_explain_smtp_error(exc)}")
        return False, str(exc)
    except Exception as exc:
        print(f"\n{_explain_smtp_error(exc)}")
        return False, str(exc)

def run_scenario(
    scenario: Scenario,
    target: str,
    smtp_host: str,
    smtp_port: int,
    config: Config,
    smtp_user: str = "",
    smtp_pass: str = "",
    use_tls: bool = False,
    verbose: bool = False,
    attachments: list[str] = None,
    headers: dict[str, str] = None,
) -> bool:
    print(f"\n[TARGET]  {target}")
    print(f"[FROM]    {scenario.from_name} <{scenario.from_email}>")
    print(f"[SUBJECT] {scenario.subject}")
    print(f"[SERVER]  {smtp_host}:{smtp_port}")

    content = build_mime_email(
        from_email=scenario.from_email,
        from_name=scenario.from_name,
        subject=scenario.subject,
        body=scenario.body,
        target=target,
        scenario_name=scenario.name,
        category=scenario.category,
        severity=scenario.severity,
        version=config.data.get("version", "1.2.0"),
        attachments=attachments,
        headers=headers,
    )

    print("[STATUS]  Connecting...", end=" ")
    ok, err = send_email(
        scenario.from_email, target, content,
        smtp_host, smtp_port,
        smtp_user=smtp_user, smtp_pass=smtp_pass, use_tls=use_tls,
        verbose=verbose,
    )

    if ok:
        print(f"{G}SENT{D}")
    else:
        print(f"{R}FAILED{D}")
        if smtp_host in ("localhost", "127.0.0.1") and not smtp_user:
            print(f"\n{Y}[~] Why it failed:{D}")
            print(f"    Direct MX delivery from your IP is blocked by most providers.")
            print(f"    {G}Solution:{D} Use an external SMTP relay with auth:")
            print(f"    mailspoof test {scenario.id} {target} \\")
            print(f"        --smtp-host smtp.gmail.com --smtp-port 587 \\")
            print(f"        --smtp-user YOUR_EMAIL --smtp-pass APP_PASSWORD")

    result = TestResult(
        timestamp=datetime.now().isoformat(),
        test_type="scenario",
        scenario=scenario.name,
        target=target,
        from_email=scenario.from_email,
        success=ok,
        details={
            "category": scenario.category,
            "severity": scenario.severity,
            "smtp_server": f"{smtp_host}:{smtp_port}",
            "error": err if not ok else "",
        },
    )
    _append_log(result, config)
    return ok

def run_custom(
    from_email: str,
    from_name: str,
    subject: str,
    body: str,
    target: str,
    smtp_host: str,
    smtp_port: int,
    config: Config,
    smtp_user: str = "",
    smtp_pass: str = "",
    use_tls: bool = False,
    verbose: bool = False,
    attachments: list[str] = None,
    headers: dict[str, str] = None,
) -> bool:
    print(f"\n[TARGET]  {target}")
    print(f"[FROM]    {from_name} <{from_email}>")
    print(f"[SUBJECT] {subject}")
    print(f"[SERVER]  {smtp_host}:{smtp_port}")

    content = build_mime_email(
        from_email=from_email,
        from_name=from_name,
        subject=subject,
        body=body,
        target=target,
        version=config.data.get("version", "1.2.0"),
        attachments=attachments,
        headers=headers,
    )

    print("[STATUS]  Connecting...", end=" ")
    ok, err = send_email(
        from_email, target, content,
        smtp_host, smtp_port,
        smtp_user=smtp_user, smtp_pass=smtp_pass, use_tls=use_tls,
        verbose=verbose,
    )

    if ok:
        print(f"{G}SENT{D}")
    else:
        print(f"{R}FAILED{D}")
        if smtp_host in ("localhost", "127.0.0.1") and not smtp_user:
            print(f"\n{Y}[~] Why it failed:{D}")
            print(f"    Direct MX delivery from your IP is blocked by most providers.")
            print(f"    {G}Solution:{D} Use an external SMTP relay with auth:")
            print(f"    mailspoof custom \\")
            print(f"        --target {target} --from-email {from_email} \\")
            print(f"        --smtp-host smtp.gmail.com --smtp-port 587 \\")
            print(f"        --smtp-user YOUR_EMAIL --smtp-pass APP_PASSWORD")

    result = TestResult(
        timestamp=datetime.now().isoformat(),
        test_type="custom",
        scenario="custom",
        target=target,
        from_email=from_email,
        success=ok,
        details={
            "from_name": from_name,
            "subject": subject,
            "body_length": len(body),
            "smtp_server": f"{smtp_host}:{smtp_port}",
            "error": err if not ok else "",
        },
    )
    _append_log(result, config)
    return ok

def _append_log(result: TestResult, config: Config):
    from lib.core import LOG_FILE
    import json as _json
    try:
        with open(LOG_FILE, "a") as fh:
            fh.write(_json.dumps(result.to_dict()) + "\n")
    except Exception as exc:
        config.logger.error(f"Audit log failed: {exc}")
