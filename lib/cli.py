
from __future__ import annotations

import argparse
import os
import sys

import threading
import time

from lib.core import Config, TEMPLATES_DIR, __version__, __author__, __license__
from lib.engine import run_custom, run_scenario
from lib.audit import show_logs, generate_report
from lib.server import SMTPServer
from lib.banner import print_banner, print_server_banner, clear_screen, print_legal, G, R, Y, C, B, D

if len(sys.argv) > 1 and sys.argv[1] == "-t":
    sys.argv[1] = "create"

if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help"):
    pass

def _prompt(text: str, default: str = "") -> str:
    if default:
        prompt = f"{text} [{default}]: "
    else:
        prompt = f"{text}: "
    try:
        val = input(prompt).strip()
    except EOFError:
        val = ""
    return val if val else default

def _prompt_required(text: str) -> str:
    while True:
        val = input(f"{text}: ").strip()
        if val:
            return val
        print("    [!] This field is required.")

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mailspoof",
        description="MailSpoof - Professional Email Security Assessment Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""Examples:
  mailspoof server --port 2525
  mailspoof start --port 2525
  mailspoof list
  mailspoof test 1 target@company.com
  mailspoof create
  mailspoof custom --from-email "ceo@company.com" --from-name "CEO" \\
                   --subject "Urgent" --body "Handle this" --target "user@company.com"
  mailspoof logs --lines 50
  mailspoof report --output /path/to/report.json
""")
    return parser

def _cmd_server(args):
    config = Config()
    server = SMTPServer(args.host, args.port, config)
    server.start()

def _cmd_test(args, config: Config):
    scenario = config.scenario_by_id(args.id)
    if not scenario:
        print(f"{R}[!] Invalid scenario ID: {args.id}{D}")
        print(f"    Run 'mailspoof list' to see available IDs.")
        sys.exit(1)
    ok = run_scenario(
        scenario, args.target, args.smtp_host, args.smtp_port, config,
        smtp_user=getattr(args, "smtp_user", ""),
        smtp_pass=getattr(args, "smtp_pass", ""),
        use_tls=getattr(args, "use_tls", False),
    )
    sys.exit(0 if ok else 1)

def _cmd_custom(args, config: Config):
    ok = run_custom(
        args.from_email, args.from_name, args.subject, args.body,
        args.target, args.smtp_host, args.smtp_port, config,
        smtp_user=getattr(args, "smtp_user", ""),
        smtp_pass=getattr(args, "smtp_pass", ""),
        use_tls=getattr(args, "use_tls", False),
    )
    sys.exit(0 if ok else 1)

def _cmd_start(args, config: Config):
    if args.port <= 1024 and os.geteuid() != 0:
        print(f"{R}[!] Port {args.port} requires root.{D}")
        print(f"    Use --port 2525  or  sudo mailspoof start --port {args.port}")
        sys.exit(1)

    clear_screen()
    print_banner()
    print_legal()

    server = SMTPServer(args.host, args.port, config)
    server.start_background()
    time.sleep(0.5)
    print(f"\n{G}[+] SMTP server running on {args.host}:{args.port}{D}")

    if args.smtp_host in ("localhost", "127.0.0.1"):
        print(f"\n{Y}[!] WARNING:{D} Direct MX relay usually fails.")
        print(f"    Most providers (Gmail, Yahoo, Outlook) block residential IPs.")
        print(f"    {G}Use an external SMTP relay for reliable delivery.{D}")
        print(f"    You will be asked for relay settings below.\n")

    if getattr(args, "server_only", False):
        print(f"{Y}[~] Server-only mode. Press Ctrl+C to stop.{D}\n")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print(f"\n{G}[+] Server stopped.{D}")
        return

    defaults = config.scenario_by_id(1)
    if not defaults:
        defaults = config.scenarios()[0]

    print(f"\n{C}--- Interactive Spoofing Session ---{D}\n")

    target = _prompt_required(f"{Y}Target email{D}")

    from_email = _prompt(f"{Y}Spoof from email{D}", defaults.from_email)
    if not from_email:
        from_email = _prompt_required(f"{Y}Spoof from email{D}")
    while "@" not in from_email:
        print(f"{R}    [!] Email must contain '@'. Example: attacker@example.com{D}")
        from_email = _prompt_required(f"{Y}Spoof from email{D}")

    from_name = _prompt(f"{Y}Sender display name{D}", defaults.from_name)
    if not from_name:
        from_name = _prompt_required(f"{Y}Sender display name{D}")

    subject = _prompt(f"{Y}Subject{D}", defaults.subject)
    if not subject:
        subject = _prompt_required(f"{Y}Subject{D}")

    print(f"\n{C}--- SMTP Relay Settings ---{D}")
    print(f"  {Y}Direct MX relay often fails (Gmail/Yahoo block IPs).{D}")
    print(f"  Use an external SMTP server (Gmail, SendGrid, your own) for success.\n")

    use_external = input(f"{Y}Use external SMTP relay? [y/N]: {D}").strip().lower()
    smtp_user = ""
    smtp_pass = ""
    use_tls = False

    if use_external in ("y", "yes"):
        ext_host = _prompt_required(f"{Y}SMTP host{D}")
        ext_port_str = _prompt(f"{Y}SMTP port{D}", "587")
        try:
            ext_port = int(ext_port_str)
        except ValueError:
            ext_port = 587
        args.smtp_host = ext_host
        args.smtp_port = ext_port

        smtp_user = _prompt(f"{Y}SMTP username{D}")
        if smtp_user:
            import getpass
            smtp_pass = getpass.getpass(f"{Y}SMTP password: {D}")

        tls_input = input(f"{Y}Use TLS/SSL? [Y/n]: {D}").strip().lower()
        use_tls = tls_input in ("", "y", "yes")

    clear_screen()
    print_banner()
    print(f"\n{C}--- Choose Email Body Template ---{D}\n")
    _cmd_list(config)

    sid_str = _prompt_required(f"{Y}Enter template ID{D}")
    try:
        sid = int(sid_str)
    except ValueError:
        print(f"{R}[!] Invalid ID. Must be a number.{D}")
        sys.exit(1)

    scenario = config.scenario_by_id(sid)
    if not scenario:
        print(f"{R}[!] Invalid scenario ID: {sid}{D}")
        print(f"    Run 'mailspoof list' to see available IDs.")
        sys.exit(1)

    print(f"\n{C}--- Ready to Send ---{D}\n")
    print(f"  {B}Target:{D}   {target}")
    print(f"  {B}From:{D}     {from_name} <{from_email}>")
    print(f"  {B}Subject:{D}  {subject}")
    print(f"  {B}Template:{D} {scenario.name} ({'custom' if scenario.source == 'custom' else 'built-in'})")
    print(f"  {B}Server:{D}   {args.smtp_host}:{args.smtp_port}")
    if smtp_user:
        print(f"  {B}Auth:{D}     {smtp_user}")
        print(f"  {B}TLS:{D}      {'Yes' if use_tls else 'No'}")
    print()

    confirm = input(f"{G}Send email? [Y/n]: {D}").strip().lower()
    if confirm and confirm not in ("y", "yes"):
        print(f"{Y}[~] Cancelled by user.{D}")
        sys.exit(0)

    from lib.core import Scenario
    active = Scenario(
        id=scenario.id,
        name=scenario.name,
        category=scenario.category,
        severity=scenario.severity,
        from_email=from_email,
        from_name=from_name,
        subject=subject,
        body=scenario.body,
        description=scenario.description,
        source=scenario.source,
    )

    ok = run_scenario(
        active, target, args.smtp_host, args.smtp_port, config,
        smtp_user=smtp_user, smtp_pass=smtp_pass, use_tls=use_tls,
    )
    if ok:
        print(f"\n{G}[+] Email sent successfully.{D}")
    else:
        print(f"\n{R}[!] Failed to send email.{D}")
        print(f"{Y}    Tips:{D}")
        print(f"    - Use an external SMTP relay (Gmail, Outlook, SendGrid)")
        print(f"    - Enable 'Less secure apps' or use App Passwords")
        print(f"    - Port 587 with TLS usually works best")
    sys.exit(0 if ok else 1)

def _cmd_create(args, config: Config):
    clear_screen()
    print_banner()
    print(f"\n{C}--- Create Custom Template ---{D}\n")

    name = _prompt_required(f"{Y}Template name{D}")
    category = _prompt(f"{Y}Category{D}", "Custom")
    severity = _prompt(f"{Y}Severity{D}", "Medium")
    from_email = _prompt(f"{Y}Default From Email{D}")
    from_name = _prompt(f"{Y}Default From Name{D}")
    subject = _prompt(f"{Y}Default Subject{D}")
    description = _prompt(f"{Y}Description{D}", f"Custom template: {name}")

    print(f"\n{Y}Enter body text (type 'EOF' on a new line to finish):{D}")
    body_lines: list[str] = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line == "EOF":
            break
        body_lines.append(line)

    body = "\n".join(body_lines)
    if not body.strip():
        print(f"{R}[!] Body cannot be empty.{D}")
        sys.exit(1)

    content = f"""Name: {name}
Category: {category}
Severity: {severity}
From Email: {from_email}
From Name: {from_name}
Subject: {subject}
Body:
{body}
Description: {description}
"""

    out_path = TEMPLATES_DIR / f"{name.replace(' ', '_').lower()}.txt"
    out_path.write_text(content, encoding="utf-8")
    print(f"{G}[+] Template saved: {out_path}{D}")

def _cmd_help():
    clear_screen()
    print_banner()
    print(f"""
{C}--- Commands Help ---{D}

  {G}mailspoof{D}                Start interactive spoofing session (default)
                           Same as: mailspoof start

  {G}mailspoof start{D}          Start server + interactive spoofing session
                           Options: --host, --port, --smtp-host, --smtp-port
                           --server-only  (-s)  Start server only

  {G}mailspoof list{D}           List all built-in and custom templates

  {G}mailspoof create{D}         Create a custom template interactively
  {G}mailspoof -t{D}             Alias for 'create'

  {G}mailspoof test <id> <email>{D}
                           Run a built-in scenario by ID

  {G}mailspoof custom{D}         Run a fully custom spoofing test
                           Required: --from-email, --from-name, --subject,
                                     --body, --target

  {G}mailspoof logs{D}           View test logs
                           Option: --lines N

  {G}mailspoof report{D}        Generate assessment report
                           Option: --output <path>

  {G}mailspoof server{D}         Start SMTP server only
                           Options: --host, --port

  {G}mailspoof update{D}         Update MailSpoof from Git repo

  {G}mailspoof uninstall{D}      Remove MailSpoof from system

  {G}mailspoof help{D}           Show this help page
  {G}mailspoof -h{D}             Show this help page
  {G}mailspoof --version{D}      Show version
  {G}mailspoof -v{D}             Show version

{C}--- Shorthand Mapping ---{D}

  No args     →  Interactive start (server + send)
  start       →  Interactive start
  start -s    →  Server only
  list        →  List templates
  create / -t →  Create template
  logs        →  View logs
  report      →  Generate report
  server      →  Server only
  update      →  Update from Git repo
  uninstall   →  Remove MailSpoof
""")

def _cmd_update():
    import subprocess
    clear_screen()
    print_banner()
    print(f"\n{C}--- Update MailSpoof ---{D}\n")

    script_path = os.path.abspath(__file__)
    project_dir = os.path.dirname(os.path.dirname(script_path))

    git_dir = os.path.join(project_dir, ".git")
    if not os.path.isdir(git_dir):
        print(f"{R}[!] Not a Git repository.{D}")
        print(f"    Project dir: {project_dir}")
        print(f"    Install via .deb or git clone to use update.")
        print(f"\n{Y}[~] Manual update options:{D}")
        print(f"    1) Git clone:  git clone <repo-url> && cd MailSpoof && bash install.sh")
        print(f"    2) .deb:       sudo dpkg -i mailspoof_*.deb")
        sys.exit(1)

    print(f"{G}[+] Found Git repo: {project_dir}{D}")
    print(f"{Y}[*] Pulling latest changes...{D}\n")

    try:
        result = subprocess.run(
            ["git", "pull"],
            cwd=project_dir,
            capture_output=True,
            text=True,
        )
        print(result.stdout)
        if result.returncode != 0:
            print(f"{R}[!] Git pull failed:{D}")
            print(result.stderr)
            sys.exit(1)
    except FileNotFoundError:
        print(f"{R}[!] 'git' command not found. Install git first.{D}")
        sys.exit(1)

    install_script = os.path.join(project_dir, "install.sh")
    if os.path.isfile(install_script):
        print(f"\n{Y}[*] Re-running install.sh...{D}\n")
        try:
            subprocess.run(["bash", install_script], cwd=project_dir, check=True)
        except subprocess.CalledProcessError as exc:
            print(f"{R}[!] Install script failed: {exc}{D}")
            sys.exit(1)
    else:
        print(f"{Y}[~] No install.sh found. Update complete.{D}")
        print(f"    You may need to restart the tool manually.")

    print(f"\n{G}[+] Update complete!{D}")
    sys.exit(0)

def _cmd_uninstall():
    import subprocess
    clear_screen()
    print_banner()
    print(f"\n{C}--- Uninstall MailSpoof ---{D}\n")

    script_path = os.path.abspath(__file__)
    project_dir = os.path.dirname(os.path.dirname(script_path))
    uninstall_script = os.path.join(project_dir, "uninstall.py")

    if not os.path.isfile(uninstall_script):
        print(f"{R}[!] uninstall.py not found.{D}")
        print(f"    Expected: {uninstall_script}")
        print(f"\n{Y}[~] Manual uninstall:{D}")
        print(f"    rm -f ~/.local/bin/mailspoof")
        print(f"    sudo rm -f /usr/local/bin/mailspoof")
        print(f"    sudo rm -f /usr/bin/mailspoof")
        print(f"    sudo rm -rf /usr/share/mailspoof")
        print(f"    rm -rf ~/.mailspoof")
        sys.exit(1)

    try:
        subprocess.run([sys.executable, uninstall_script])
    except KeyboardInterrupt:
        pass
    sys.exit(0)

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "-t":
        sys.argv[1] = "create"

    if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help"):
        _cmd_help()
        sys.exit(0)

    if len(sys.argv) > 1 and sys.argv[1] == "-v":
        print_banner()
        print(f"MailSpoof v{__version__}")
        sys.exit(0)

    parser = _build_parser()
    args = parser.parse_args()

    config = Config()

    if not args.command:
        class FakeArgs:
            host = "0.0.0.0"
            port = 2525
            smtp_host = "localhost"
            smtp_port = 2525
            smtp_user = ""
            smtp_pass = ""
            use_tls = False
            server_only = False
        _cmd_start(FakeArgs(), config)
        sys.exit(0)

    if args.command not in ("start", "list", "create", "server"):
        clear_screen()
        print_banner()
        print_legal()

    if args.command == "server":
        _cmd_server(args)
    elif args.command == "start":
        _cmd_start(args, config)
    elif args.command == "list":
        _cmd_list(config)
    elif args.command == "test":
        _cmd_test(args, config)
    elif args.command == "create":
        _cmd_create(args, config)
    elif args.command == "custom":
        _cmd_custom(args, config)
    elif args.command == "logs":
        show_logs(config, args.lines)
    elif args.command == "report":
        generate_report(config, args.output)
    elif args.command == "help":
        _cmd_help()
    elif args.command == "update":
        _cmd_update()
    elif args.command == "uninstall":
        _cmd_uninstall()
