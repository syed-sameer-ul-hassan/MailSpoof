from __future__ import annotations

import smtplib
import time
from datetime import datetime
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate, make_msgid

from lib.core import Config, Scenario, TestResult

R = "\033[91m"
G = "\033[92m"
Y = "\033[93m"
D = "\033[0m"

def _disclaimer(scenario_name: str, category: str, severity: str, version: str) -> str:
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

def build_mime_email(
    from_email: str,
    from_name: str,
    subject: str,
    body: str,
    target: str,
    scenario_name: str = "Custom",
    category: str = "Custom Test",
    severity: str = "N/A",
    version: str = "1.0.0",
) -> str:
    msg = MIMEMultipart("alternative")
    msg["From"] = f"{from_name} <{from_email}>"
    msg["To"] = target
    msg["Subject"] = Header(subject, "utf-8")
    msg["Date"] = formatdate(localtime=True)
    domain = from_email.split("@")[1] if "@" in from_email else "localhost"
    msg["Message-ID"] = make_msgid(domain=domain)

    full_body = body + _disclaimer(scenario_name, category, severity, version)
    msg.attach(MIMEText(full_body, "plain", "utf-8"))
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
) -> bool:
    try:
        if use_tls or smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=timeout)
        else:
            server = smtplib.SMTP(smtp_host, smtp_port, timeout=timeout)

        with server:
            if not (use_tls or smtp_port == 465):
                try:
                    server.starttls()
                except Exception:
                    pass

            if smtp_user and smtp_pass:
                server.login(smtp_user, smtp_pass)

            server.sendmail(from_email, [to_email], content.encode("utf-8"))
        return True
    except smtplib.SMTPAuthenticationError as exc:
        print(f"\n{R}[!] SMTP Authentication failed: {exc}{D}")
        print(f"    {Y}Check your username/password. For Gmail, use an App Password.{D}")
        return False
    except smtplib.SMTPRecipientsRefused as exc:
        print(f"\n{R}[!] Recipient refused: {exc}{D}")
        return False
    except smtplib.SMTPException as exc:
        print(f"\n{_explain_smtp_error(exc)}")
        return False
    except Exception as exc:
        print(f"\n{_explain_smtp_error(exc)}")
        return False

def run_scenario(
    scenario: Scenario,
    target: str,
    smtp_host: str,
    smtp_port: int,
    config: Config,
    smtp_user: str = "",
    smtp_pass: str = "",
    use_tls: bool = False,
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
        version=config.data.get("version", "1.0.0"),
    )

    print("[STATUS]  Connecting...", end=" ")
    ok = send_email(
        scenario.from_email, target, content,
        smtp_host, smtp_port,
        smtp_user=smtp_user, smtp_pass=smtp_pass, use_tls=use_tls,
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
        version=config.data.get("version", "1.0.0"),
    )

    print("[STATUS]  Connecting...", end=" ")
    ok = send_email(
        from_email, target, content,
        smtp_host, smtp_port,
        smtp_user=smtp_user, smtp_pass=smtp_pass, use_tls=use_tls,
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
