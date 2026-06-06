from lib.core import __version__

C = "\033[96m"
B = "\033[1m"
G = "\033[92m"
R = "\033[91m"
Y = "\033[93m"
D = "\033[0m"

def print_banner():
    print(LOGO)
    print(f"     {B}Professional Email Security Assessment v{__version__}{D}")

def print_server_banner(host: str, port: int, log_file: str = ""):
    print(LOGO)
    print(f"     {B}MailSpoof SMTP Server v{__version__}{D}")
    print()
    print(f"  Listening on {host}:{port}")
    if log_file:
        print(f"  Logs: {log_file}")
    print()
    print("  Press Ctrl+C to stop.")

def clear_screen():
    import os
    os.system("clear" if os.name != "nt" else "cls")

def print_legal():
    print(f"{Y}[!] Legal Notice:{D} Use only on systems you own or have explicit permission to test.")
    print()
