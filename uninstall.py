#!/usr/bin/env python3

import os
import re
import shutil
import sys

INSTALL_DIR = "/usr/local/bin"
SYS_INSTALL_DIR2 = "/usr/bin"
USER_INSTALL_DIR = os.path.expanduser("~/.local/bin")
PROJECT_DIR = ""

G = "\033[92m"
R = "\033[91m"
Y = "\033[93m"
D = "\033[0m"

def print_banner():
    print("""
  ▄▄███▄▄     ▄██████  ██ ▄█   ▄███████    ▄█████▄  ▄█████▄  ▄█████▄   ▄███████
 ██▀▀██▀▀█▄   ██   ██  ▄█ ██   ██    ██   ██    ██ ██    ██ ██    ██   ██    ██
 ██  ██  ██   ██   ██  ██ ██   ██    █▀   ██    ██ ██    ██ ██    ██   ██    █▀
 ██  ██  ██   ██   ██  ██ ██   ██         ██    ██ ██    ██ ██    ██  ▄██▄▄
 ██  ██  ██ ▀████████  ██ ██   ▀████████ ▀███████▀ ██    ██ ██    ██ ▀▀██▀▀
 ██  ██  ██   ██   ██  ██ ██          ██   ██      ██    ██ ██    ██   ██
 ██  ██  ██   ██   ██  ██ ██▌  ▄      ██   ██      ██    ██ ██    ██   ██
 ▀█  ██  █▀   ██   █▀  █▀ ███▄ ▄███████▀  ▄███▀    ▀█████▀   ▀█████▀   ███
    """)
    print("       MailSpoof v1.2.0 — Uninstaller")
    print()


    while True:
        try:
            ans = input(f"{prompt} [Y/n] (default: {default}): ").strip()
        except (EOFError, KeyboardInterrupt):
            return False
        ans = ans if ans else default
        if ans.lower() in ("y", "yes"):
            return True
        if ans.lower() in ("n", "no"):
            return False
        print("    Please answer yes or no.")

def _extract_project_dir(wrapper_path):
    try:
        with open(wrapper_path, "r") as fh:
            content = fh.read()
        match = re.search(r'PROJECT_DIR="([^"]+)"', content)
        if match:
            return match.group(1)
    except Exception:
        pass
    return ""

def find_install():
    global PROJECT_DIR
    user_wrapper = os.path.join(USER_INSTALL_DIR, "mailspoof")
    sys_wrapper = os.path.join(INSTALL_DIR, "mailspoof")
    sys_wrapper2 = os.path.join(SYS_INSTALL_DIR2, "mailspoof")

    if os.path.isfile(user_wrapper):
        PROJECT_DIR = _extract_project_dir(user_wrapper)
        return "user"
    if os.path.isfile(sys_wrapper):
        PROJECT_DIR = _extract_project_dir(sys_wrapper)
        return "system"
    if os.path.isfile(sys_wrapper2):
        PROJECT_DIR = _extract_project_dir(sys_wrapper2)
        return "system"
    return "none"

def _sudo_remove_file(path):
    import subprocess
    try:
        subprocess.run(["sudo", "rm", "-f", path], check=True)
        print(f"{G}[+]{D} Removed {path} (with sudo)")
        return True
    except subprocess.CalledProcessError:
        print(f"{R}[!]{D} Failed to remove {path} even with sudo")
        return False
    except FileNotFoundError:
        return True

def _sudo_remove_dir(path):
    import subprocess
    try:
        subprocess.run(["sudo", "rm", "-rf", path], check=True)
        print(f"{G}[+]{D} Removed {path} (with sudo)")
        return True
    except subprocess.CalledProcessError:
        print(f"{R}[!]{D} Failed to remove {path} even with sudo")
        return False
    except FileNotFoundError:
        return True

def remove_file(path):
    try:
        os.remove(path)
        print(f"{G}[+]{D} Removed {path}")
        return True
    except PermissionError:
        print(f"{Y}[*]{D} Permission denied: {path}")
        print(f"    Retrying with sudo...")
        return _sudo_remove_file(path)
    except FileNotFoundError:
        return True

def remove_dir(path):
    try:
        shutil.rmtree(path)
        print(f"{G}[+]{D} Removed {path}")
        return True
    except PermissionError:
        print(f"{Y}[*]{D} Permission denied: {path}")
        print(f"    Retrying with sudo...")
        return _sudo_remove_dir(path)
    except FileNotFoundError:
        return True

def main():
    print_banner()

    install_type = find_install()

    if install_type == "none":
        print(f"{R}[!]{D} MailSpoof not found in PATH.")
        print("    Nothing to uninstall.")
        sys.exit(0)

    print(f"{G}[+]{D} Found MailSpoof installation: {install_type}")
    if PROJECT_DIR:
        print(f"    Project dir: {PROJECT_DIR}")
    print()

    if not ask_yes_no("Do you want to uninstall MailSpoof?", "n"):
        print(f"{Y}[~]{D} Uninstall cancelled.")
        sys.exit(0)

    print()
    print(f"{Y}[*]{D} Removing all MailSpoof files and directories...")
    print()

    all_wrappers = [
        os.path.join(USER_INSTALL_DIR, "mailspoof"),
        os.path.join(INSTALL_DIR, "mailspoof"),
        os.path.join(SYS_INSTALL_DIR2, "mailspoof"),
    ]
    for wrapper in all_wrappers:
        if os.path.isfile(wrapper):
            print(f"{Y}[*]{D} Removing wrapper: {wrapper}")
            remove_file(wrapper)

    if PROJECT_DIR and os.path.isdir(PROJECT_DIR):
        print(f"{Y}[*]{D} Removing project dir: {PROJECT_DIR}")
        remove_dir(PROJECT_DIR)

    sys_share = "/usr/share/mailspoof"
    if os.path.isdir(sys_share):
        print(f"{Y}[*]{D} Removing system dir: {sys_share}")
        remove_dir(sys_share)

    repo_dir = os.path.expanduser("~/.mailspoof/repo")
    if os.path.isdir(repo_dir):
        print(f"{Y}[*]{D} Removing cloned repo: {repo_dir}")
        remove_dir(repo_dir)

    config_dir = os.path.expanduser("~/.mailspoof")
    if os.path.isdir(config_dir):
        print(f"{Y}[*]{D} Removing config dir: {config_dir}")
        remove_dir(config_dir)

    for deb in ["mailspoof-v1.2.0.deb", "mailspoof_1.2.0_all.deb"]:
        deb_path = os.path.join(os.path.expanduser("~"), deb)
        if os.path.isfile(deb_path):
            print(f"{Y}[*]{D} Removing package: {deb_path}")
            remove_file(deb_path)

    print()
    print(f"{G}[+]{D} MailSpoof completely removed from your system.")
    print()

if __name__ == "__main__":
    main()
