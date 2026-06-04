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
▗▄▄▄▖▗▖             ▗▖   ▄▖ ▗▄
▝▀█▀▘▐▌             ▐▌   ▐▙ ▟▌
  █  ▐▙██▖ ▟██▖▐▙██▖▐▌▟▛  █▄█  ▟█▙ ▐▌ ▐▌
  █  ▐▛ ▐▌ ▘▄▟▌▐▛ ▐▌▐▙█   ▝█▘ ▐▛ ▜▌▐▌ ▐▌
  █  ▐▌ ▐▌▗█▀▜▌▐▌ ▐▌▐▛█▖   █  ▐▌ ▐▌▐▌ ▐▌
  █  ▐▌ ▐▌▐▙▄█▌▐▌ ▐▌▐▌▝▙   █  ▝█▄█▘▐▙▄█▌
  ▀  ▝▘ ▝▘ ▀▀▝▘▝▘ ▝▘▝▘ ▀▘  ▀   ▝▀▘  ▀▀▝▘

     MailSpoof Uninstaller v1.0.0
""")


def ask_yes_no(prompt, default="n"):
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

def remove_file(path):
    try:
        os.remove(path)
        print(f"{G}[+]{D} Removed {path}")
        return True
    except PermissionError:
        print(f"{R}[!]{D} Permission denied: {path}")
        print(f"    Try: sudo python3 {sys.argv[0]}")
        return False
    except FileNotFoundError:
        return True

def remove_dir(path):
    try:
        shutil.rmtree(path)
        print(f"{G}[+]{D} Removed {path}")
        return True
    except PermissionError:
        print(f"{R}[!]{D} Permission denied: {path}")
        print(f"    Try: sudo python3 {sys.argv[0]}")
        return False
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

    if install_type == "user":
        path = os.path.join(USER_INSTALL_DIR, "mailspoof")
        print(f"{Y}[*]{D} Removing {path} ...")
        if not remove_file(path):
            sys.exit(1)
    else:
        for sys_path in (os.path.join(INSTALL_DIR, "mailspoof"), os.path.join(SYS_INSTALL_DIR2, "mailspoof")):
            if os.path.isfile(sys_path):
                print(f"{Y}[*]{D} Removing {sys_path} ...")
                if not remove_file(sys_path):
                    sys.exit(1)

    if PROJECT_DIR and os.path.isdir(PROJECT_DIR):
        if ask_yes_no(f"Remove project directory ({PROJECT_DIR})?", "n"):
            print(f"{Y}[*]{D} Removing {PROJECT_DIR} ...")
            if not remove_dir(PROJECT_DIR):
                sys.exit(1)

    config_dir = os.path.expanduser("~/.mailspoof")
    if os.path.isdir(config_dir):
        if ask_yes_no("Remove config directory (~/.mailspoof)?", "n"):
            print(f"{Y}[*]{D} Removing {config_dir} ...")
            if not remove_dir(config_dir):
                sys.exit(1)

    print()
    print(f"{G}[+]{D} MailSpoof uninstalled successfully.")
    print()

if __name__ == "__main__":
    main()
