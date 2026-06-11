from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import threading
import time

from lib.core import Config, TEMPLATES_DIR, __version__, __author__, __license__, load_user_templates, load_builtin_templates
from lib.engine import _strip_html, run_custom, run_scenario
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
  mailspoof custom --from-email "ceo@company.com" --from-name "CEO" \
                   --subject "Urgent" --body "Handle this" --target "user@company.com"
  mailspoof logs --lines 50
  mailspoof report --output /path/to/report.json
""",
    )

    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"MailSpoof v{__version__}",
    )

    subparsers = parser.add_subparsers(dest="command")

    p_server = subparsers.add_parser("server", help="Start SMTP server only")
    p_server.add_argument("--host", default="0.0.0.0")
    p_server.add_argument("--port", type=int, default=2525)

    p_start = subparsers.add_parser("start", help="Start server + interactive session")
    p_start.add_argument("--host", default="0.0.0.0")
    p_start.add_argument("--port", type=int, default=2525)
    p_start.add_argument("--smtp-host", default="localhost")
    p_start.add_argument("--smtp-port", type=int, default=2525)
    p_start.add_argument("--smtp-user", default="")
    p_start.add_argument("--smtp-pass", default="")
    p_start.add_argument("--use-tls", action="store_true")
    p_start.add_argument("--profile", default="", help="Use named SMTP profile")
    p_start.add_argument("--verbose", action="store_true", help="Show detailed send stages")
    p_start.add_argument("-s", "--server-only", action="store_true")

    p_list = subparsers.add_parser("list", help="List all templates")
    p_list.add_argument("--filter", default="", help="Filter by text or tag")

    p_test = subparsers.add_parser("test", help="Run a built-in scenario by ID")
    p_test.add_argument("id", type=int)
    p_test.add_argument("target", nargs="?", help="Target email address")
    p_test.add_argument("--target-list", help="CSV file containing target email addresses")
    p_test.add_argument("--smtp-host", default="localhost")
    p_test.add_argument("--smtp-port", type=int, default=2525)
    p_test.add_argument("--smtp-user", default="")
    p_test.add_argument("--smtp-pass", default="")
    p_test.add_argument("--use-tls", action="store_true")
    p_test.add_argument("--profile", default="", help="Use named SMTP profile")
    p_test.add_argument("--verbose", action="store_true", help="Show detailed send stages")
    p_test.add_argument("--attach", action="append", help="File to attach (can be used multiple times)")
    p_test.add_argument("--reply-to", help="Custom Reply-To header")
    p_test.add_argument("--x-mailer", help="Custom X-Mailer header")

    subparsers.add_parser("create", help="Create a custom template")
    subparsers.add_parser("-t", help="Alias for create")
    p_custom = subparsers.add_parser("custom", help="Run a fully custom spoofing test")
    p_custom.add_argument("--from-email", required=True)
    p_custom.add_argument("--from-name", required=True)
    p_custom.add_argument("--subject", required=True)
    p_custom.add_argument("--body", required=True)
    p_custom.add_argument("--target", required=False, help="Target email address")
    p_custom.add_argument("--target-list", help="CSV file containing target email addresses")
    p_custom.add_argument("--smtp-host", default="localhost")
    p_custom.add_argument("--smtp-port", type=int, default=2525)
    p_custom.add_argument("--smtp-user", default="")
    p_custom.add_argument("--smtp-pass", default="")
    p_custom.add_argument("--use-tls", action="store_true")
    p_custom.add_argument("--profile", default="", help="Use named SMTP profile")
    p_custom.add_argument("--verbose", action="store_true", help="Show detailed send stages")
    p_custom.add_argument("--attach", action="append", help="File to attach (can be used multiple times)")
    p_custom.add_argument("--reply-to", help="Custom Reply-To header")
    p_custom.add_argument("--x-mailer", help="Custom X-Mailer header")
    p_logs = subparsers.add_parser("logs", help="View test logs")
    p_logs.add_argument("--lines", type=int, default=20)
    p_report = subparsers.add_parser("report", help="Generate assessment report")
    p_report.add_argument("--output", default=None)
    p_report.add_argument("--format", choices=["json", "csv"], default="json")
    subparsers.add_parser("update", help="Update MailSpoof from Git repo")
    subparsers.add_parser("uninstall", help="Remove MailSpoof from system")
    subparsers.add_parser("help", help="Show this help page")

    p_preview = subparsers.add_parser("preview", help="Preview a template by ID")
    p_preview.add_argument("id", type=int)
    p_preview.add_argument("--raw", action="store_true", help="Show raw body without stripping HTML")

    p_remove_tpl = subparsers.add_parser("remove-template", help="Remove a custom template by ID")
    p_remove_tpl.add_argument("id", type=int, help="Template ID to remove")

    p_edit_tpl = subparsers.add_parser("edit-template", help="Edit a custom template by ID using nano")
    p_edit_tpl.add_argument("id", type=int, help="Template ID to edit")

    p_profile = subparsers.add_parser("profile", help="Manage SMTP profiles")
    p_profile.add_argument("action", choices=["list", "add", "remove"], help="Profile action")
    p_profile.add_argument("name", nargs="?", help="Profile name")
    p_profile.add_argument("--host", help="SMTP host")
    p_profile.add_argument("--port", type=int, help="SMTP port")
    p_profile.add_argument("--user", help="SMTP username")
    p_profile.add_argument("--pass", dest="password", help="SMTP password")
    p_profile.add_argument("--use-tls", action="store_true", help="Use TLS")

    return parser

def _cmd_server(args):
    config = Config()
    server = SMTPServer(args.host, args.port, config)
    server.start()

def _get_targets(args) -> list[str]:
    targets = []
    if getattr(args, "target", None):
        targets.append(args.target)
    if getattr(args, "target_list", None):
        try:
            import csv
            with open(args.target_list, "r") as f:
                reader = csv.reader(f)
                for row in reader:
                    if row and row[0]:
                        targets.append(row[0].strip())
        except Exception as exc:
            print(f"{R}[!] Failed to read target list: {exc}{D}")
            sys.exit(1)
    if not targets:
        print(f"{R}[!] No targets specified. Use --target or --target-list{D}")
        sys.exit(1)
    return targets

def _get_headers(args) -> dict[str, str]:
    headers = {}
    if getattr(args, "reply_to", None):
        headers["Reply-To"] = args.reply_to
    if getattr(args, "x_mailer", None):
        headers["X-Mailer"] = args.x_mailer
    return headers

def _cmd_test(args, config: Config):
    scenario = config.scenario_by_id(args.id)
    if not scenario:
        print(f"{R}[!] Invalid scenario ID: {args.id}{D}")
        print(f"    Run 'mailspoof list' to see available IDs.")
        sys.exit(1)
    smtp_host, smtp_port, smtp_user, smtp_pass, use_tls = _resolve_smtp(args, config)
    targets = _get_targets(args)
    headers = _get_headers(args)
    attachments = getattr(args, "attach", None)

    all_ok = True
    for t in targets:
        ok = run_scenario(
            scenario, t, smtp_host, smtp_port, config,
            smtp_user=smtp_user,
            smtp_pass=smtp_pass,
            use_tls=use_tls,
            verbose=getattr(args, "verbose", False),
            attachments=attachments,
            headers=headers,
        )
        if not ok: all_ok = False
    sys.exit(0 if all_ok else 1)

def _cmd_custom(args, config: Config):
    smtp_host, smtp_port, smtp_user, smtp_pass, use_tls = _resolve_smtp(args, config)
    targets = _get_targets(args)
    headers = _get_headers(args)
    attachments = getattr(args, "attach", None)

    all_ok = True
    for t in targets:
        ok = run_custom(
            args.from_email, args.from_name, args.subject, args.body,
            t, smtp_host, smtp_port, config,
            smtp_user=smtp_user,
            smtp_pass=smtp_pass,
            use_tls=use_tls,
            verbose=getattr(args, "verbose", False),
            attachments=attachments,
            headers=headers,
        )
        if not ok: all_ok = False
    sys.exit(0 if all_ok else 1)

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
        all_scenarios = config.scenarios()
        if not all_scenarios:
            print(f"{R}[!] No templates found. Built-in templates may be missing from the installation.{D}")
            print(f"    Reinstall or copy templates to ~/.mailspoof/templates")
            sys.exit(1)
        defaults = all_scenarios[0]

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

    smtp_host, smtp_port, smtp_user, smtp_pass, use_tls = _resolve_smtp(args, config, smtp_user, smtp_pass, use_tls)
    ok = run_scenario(
        active, target, smtp_host, smtp_port, config,
        smtp_user=smtp_user, smtp_pass=smtp_pass, use_tls=use_tls,
        verbose=getattr(args, "verbose", False),
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

    next_id = max([s.id for s in config.scenarios()] or [0]) + 1

    custom_dir = TEMPLATES_DIR / "custom"
    custom_dir.mkdir(parents=True, exist_ok=True)
    out_path = custom_dir / f"{name.replace(' ', '_').lower()}.txt"
    content = (
        f"Name: {name}\n"
        f"Category: {category}\n"
        f"Severity: {severity}\n"
        f"From Email: {from_email}\n"
        f"From Name: {from_name}\n"
        f"Subject: {subject}\n"
        f"Description: {description}\n\n"
        f"Body:\n{body}\n"
    )

    out_path.write_text(content, encoding="utf-8")
    print(f"{G}[+] Template saved: {out_path}  (ID {next_id}){D}")

    config._custom_templates = load_user_templates(start_id=len(config._builtin_templates) + 1)

def _cmd_list(args, config: Config):
    filter_text = getattr(args, "filter", "").lower().strip()
    scenarios = config.scenarios()
    print(f"\n{C}--- Available Templates ---{D}\n")
    for s in scenarios:
        if filter_text:
            hay = " ".join([
                s.name, s.category, s.severity, s.subject, s.description,
                " ".join(getattr(s, "tags", []) or []), s.body[:200],
            ]).lower()
            if filter_text not in hay:
                continue
        sev_color = R if s.severity == "Critical" else Y if s.severity == "High" else G
        tags_text = f" ({','.join(s.tags)})" if getattr(s, "tags", []) else ""
        print(f"  [{s.id:2d}] {s.name:40s}  [{sev_color}{s.severity}{D}] {tags_text}")
    custom_count = sum(1 for s in scenarios if s.source == "custom")
    print(f"\n  [+] Custom templates: {custom_count} found in ~/.mailspoof/templates/")
    print()

def _resolve_smtp(args, config: Config, smtp_user: str = "", smtp_pass: str = "", use_tls: bool = False):
    host = getattr(args, "smtp_host", "localhost")
    port = getattr(args, "smtp_port", 2525)

    profile_name = getattr(args, "profile", "") or ""
    profiles = config.data.get("smtp_profiles", {})
    if profile_name:
        profile = profiles.get(profile_name)
        if not profile:
            print(f"{R}[!] SMTP profile '{profile_name}' not found.{D}")
            sys.exit(1)
        host = profile.get("host", host)
        port = int(profile.get("port", port))
        smtp_user = profile.get("user", smtp_user)
        smtp_pass = profile.get("pass", smtp_pass)
        use_tls = bool(profile.get("use_tls", use_tls))

    if getattr(args, "use_tls", False):
        use_tls = True

    if getattr(args, "smtp_user", None):
        smtp_user = args.smtp_user
    if getattr(args, "smtp_pass", None):
        smtp_pass = args.smtp_pass

    return host, port, smtp_user, smtp_pass, use_tls

def _cmd_profile(args, config: Config):
    action = args.action
    profiles = config.data.get("smtp_profiles", {})

    if action == "list":
        if not profiles:
            print("No SMTP profiles found.")
            return
        print("\nProfiles:\n")
        for name, p in profiles.items():
            tls = "yes" if p.get("use_tls") else "no"
            user = p.get("user", "")
            print(f"  - {name}: {p.get('host','?')}:{p.get('port','?')} tls={tls} user={user}")
        return

    if not args.name:
        print(f"{R}[!] Profile name required.{D}")
        sys.exit(1)

    if action == "remove":
        if args.name in profiles:
            profiles.pop(args.name, None)
            config.data["smtp_profiles"] = profiles
            config._save(config.data)
            print(f"Removed profile '{args.name}'.")
        else:
            print(f"Profile '{args.name}' not found.")
        return

    if action == "add":
        if not args.host or not args.port:
            print(f"{R}[!] --host and --port are required to add a profile.{D}")
            sys.exit(1)
        profiles[args.name] = {
            "host": args.host,
            "port": args.port,
            "user": args.user or "",
            "pass": args.password or "",
            "use_tls": bool(args.use_tls),
        }
        config.data["smtp_profiles"] = profiles
        config._save(config.data)
        print(f"Saved profile '{args.name}'.")

def _cmd_remove_template(args, config: Config):
    tpl_id = args.id
    scenarios = config.scenarios()
    match = None
    for s in scenarios:
        if s.id == tpl_id:
            match = s
            break
    if not match:
        print(f"{R}[!] Template ID {tpl_id} not found.{D}")
        sys.exit(1)
    if match.source != "custom":
        print(f"{R}[!] Cannot remove built-in templates (ID {tpl_id}).{D}")
        sys.exit(1)

    filename = f"{match.name.replace(' ', '_').lower()}.txt"
    custom_dir = TEMPLATES_DIR / "custom"
    candidates = [custom_dir / filename, TEMPLATES_DIR / filename]
    removed = False
    for path in candidates:
        if path.exists():
            path.unlink()
            removed = True

    config._custom_templates = load_user_templates(start_id=len(config._builtin_templates) + 1)

    if removed:
        print(f"{G}[+] Removed custom template ID {tpl_id}: {match.name}{D}")
    else:
        print(f"{Y}[~]{D} Custom template file not found on disk; index refreshed.")

def _cmd_edit_template(args, config: Config):
    tpl_id = args.id
    scenarios = config.scenarios()
    match = None
    for s in scenarios:
        if s.id == tpl_id:
            match = s
            break
    if not match:
        print(f"{R}[!] Template ID {tpl_id} not found.{D}")
        sys.exit(1)
    if match.source == "custom":
        filename = f"{match.name.replace(' ', '_').lower()}.txt"
        custom_dir = TEMPLATES_DIR / "custom"
        path = custom_dir / filename
    else:
        path_str = getattr(match, "disk_path", "")
        if not path_str:
            print(f"{R}[!] Built-in template path unknown.{D}")
            sys.exit(1)
        path = Path(path_str)

    if not path.exists():
        print(f"{R}[!] Template file not found on disk: {path}{D}")
        sys.exit(1)

    editor = os.environ.get("EDITOR", "nano")
    os.system(f"{editor} '{path}'")

    config._builtin_templates = load_builtin_templates()
    config._custom_templates = load_user_templates(start_id=len(config._builtin_templates) + 1)
    print(f"{G}[+] Reloaded templates after edit.{D}")

def _cmd_preview(args, config: Config):
    scenario = config.scenario_by_id(args.id)
    if not scenario:
        print(f"{R}[!] Invalid scenario ID: {args.id}{D}")
        sys.exit(1)
    print(f"\n{C}--- Preview: {scenario.name} (ID {scenario.id}) ---{D}\n")
    if scenario.body.strip().startswith("<html") and not args.raw:
        print(_strip_html(scenario.body))
    else:
        print(scenario.body)
    print()

def _cmd_help():
    clear_screen()
    print_banner()

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
    import shutil

    clear_screen()
    print_banner()
    print(f"\n{C}--- Uninstall MailSpoof ---{D}\n")

    print(f"{Y}[~]{D} Using built-in uninstaller...")

    def ask_yes_no(prompt: str, default: str = "n") -> bool:
        while True:
            try:
                ans = input(f"{prompt} [Y/n] (default: {default}): ").strip() or default
            except (EOFError, KeyboardInterrupt):
                return False
            low = ans.lower()
            if low in ("y", "yes"):
                return True
            if low in ("n", "no"):
                return False
            print("    Please answer yes or no.")

    def _sudo_rm(path: str, is_dir: bool = False) -> bool:
        try:
            cmd = ["sudo", "rm", "-rf" if is_dir else "-f", path]
            subprocess.run(cmd, check=True)
            print(f"{G}[+]{D} Removed {path} (with sudo)")
            return True
        except subprocess.CalledProcessError:
            print(f"{R}[!]{D} Failed to remove {path} even with sudo")
            return False

    def remove_file(path: str) -> bool:
        try:
            os.remove(path)
            print(f"{G}[+]{D} Removed {path}")
            return True
        except PermissionError:
            print(f"{Y}[*]{D} Permission denied: {path}")
            return _sudo_rm(path, is_dir=False)
        except FileNotFoundError:
            return True

    def remove_dir(path: str) -> bool:
        try:
            shutil.rmtree(path)
            print(f"{G}[+]{D} Removed {path}")
            return True
        except PermissionError:
            print(f"{Y}[*]{D} Permission denied: {path}")
            return _sudo_rm(path, is_dir=True)
        except FileNotFoundError:
            return True

    wrappers = [
        os.path.expanduser("~/.local/bin/mailspoof"),
        "/usr/local/bin/mailspoof",
        "/usr/bin/mailspoof",
    ]
    config_dir = os.path.expanduser("~/.mailspoof")
    sys_share = "/usr/share/mailspoof"
    pkg_templates = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib", "templates")

    print(f"{Y}[*]{D} The following will be removed if present:")
    for path in wrappers + [config_dir, sys_share, pkg_templates]:
        print(f"    - {path}")
    print("    - pip package: mailspoof (if installed)")

    if not ask_yes_no("Proceed with uninstall?", "n"):
        print(f"{Y}[~]{D} Uninstall cancelled.")
        sys.exit(0)

    for wrapper in wrappers:
        remove_file(wrapper)

    remove_dir(config_dir)
    remove_dir(sys_share)
    remove_dir(pkg_templates)

    try:
        subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "mailspoof"], check=False)
    except Exception:
        print(f"{Y}[~]{D} Could not auto-run pip uninstall; please run 'pip uninstall mailspoof' manually if needed.")

    print(f"\n{G}[+]{D} MailSpoof removal complete. Some files may require sudo; verify above output.")
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
        _cmd_list(args, config)
    elif args.command == "test":
        _cmd_test(args, config)
    elif args.command == "create":
        _cmd_create(args, config)
    elif args.command == "custom":
        _cmd_custom(args, config)
    elif args.command == "logs":
        show_logs(config, args.lines)
    elif args.command == "report":
        generate_report(config, args.output, args.format)
    elif args.command == "preview":
        _cmd_preview(args, config)
    elif args.command == "remove-template":
        _cmd_remove_template(args, config)
    elif args.command == "edit-template":
        _cmd_edit_template(args, config)
    elif args.command == "profile":
        _cmd_profile(args, config)
    elif args.command == "help":
        _cmd_help()
    elif args.command == "update":
        _cmd_update()
    elif args.command == "uninstall":
        _cmd_uninstall()
if __name__ == "__main__":
    main()
