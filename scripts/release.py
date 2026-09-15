#!/usr/bin/env python3
"""
MailSpoof v1.2.1 Release Script
Builds source archives (.tar.gz and .zip), tags git, pushes to remote, and creates GitHub release.
"""
import os
import sys
import shutil
import tarfile
import zipfile
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
VERSION = "1.2.1"
TAG = f"v{VERSION}"
DIST_DIR = REPO_ROOT / "dist"
RELEASE_NOTES = REPO_ROOT / "docs" / f"RELEASE_NOTES_{TAG}.md"

# Patterns to exclude from clean source package
EXCLUDE_DIRS = {
    ".git", ".github", "__pycache__", ".pytest_cache",
    "mailspoof.egg-info", "dist", "build", "rpmbuild", "myscrypts"
}
EXCLUDE_EXTS = {".pyc", ".pyo", ".pyd", ".swp", ".swo", "~"}

def run_cmd(cmd, check=True):
    print(f"[*] Running: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    res = subprocess.run(cmd, cwd=str(REPO_ROOT), shell=isinstance(cmd, str), check=check, text=True, capture_output=True)
    if res.stdout:
        print(res.stdout.strip())
    if res.stderr:
        print(res.stderr.strip(), file=sys.stderr)
    return res

def collect_files():
    file_list = []
    for root, dirs, files in os.walk(REPO_ROOT):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith(".")]
        for file in files:
            if any(file.endswith(ext) for ext in EXCLUDE_EXTS):
                continue
            full_path = Path(root) / file
            rel_path = full_path.relative_to(REPO_ROOT)
            file_list.append((full_path, rel_path))
    return sorted(file_list, key=lambda x: str(x[1]))

def build_archives():
    DIST_DIR.mkdir(exist_ok=True)
    tar_path = DIST_DIR / f"mailspoof-{VERSION}.tar.gz"
    zip_path = DIST_DIR / f"mailspoof-{VERSION}.zip"
    
    files = collect_files()
    prefix = f"mailspoof-{VERSION}"
    
    print(f"[*] Creating {tar_path.name} ({len(files)} files)...")
    with tarfile.open(tar_path, "w:gz") as tar:
        for full, rel in files:
            tar.add(full, arcname=f"{prefix}/{rel}")
            
    print(f"[*] Creating {zip_path.name} ({len(files)} files)...")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for full, rel in files:
            zipf.write(full, arcname=f"{prefix}/{rel}")
            
    print(f"[+] Archives created:")
    print(f"    - {tar_path} ({tar_path.stat().st_size / 1024:.1f} KB)")
    print(f"    - {zip_path} ({zip_path.stat().st_size / 1024:.1f} KB)")
    return tar_path, zip_path

def main():
    print(f"=== Preparing MailSpoof {TAG} Release ===")
    
    if not RELEASE_NOTES.exists():
        print(f"[-] Release notes not found at {RELEASE_NOTES}", file=sys.stderr)
        sys.exit(1)

    # 1. Commit release notes and release script if needed
    run_cmd(["git", "add", "docs/RELEASE_NOTES_v1.2.1.md", "scripts/release.py"])
    st = run_cmd(["git", "status", "--porcelain"])
    if st.stdout.strip():
        print("[*] Committing release documentation and release script...")
        run_cmd(["git", "commit", "-m", f"docs: add release notes and release script for {TAG}"])
        print("[*] Pushing commit to origin main...")
        run_cmd(["git", "push", "origin", "main"])
    else:
        print("[*] Working tree clean.")

    # 2. Build archives
    tar_path, zip_path = build_archives()

    # 3. Create or update tag
    tag_check = subprocess.run(["git", "tag", "-l", TAG], cwd=str(REPO_ROOT), text=True, capture_output=True)
    if TAG in tag_check.stdout.split():
        print(f"[*] Tag {TAG} already exists locally. Pushing with --tags...")
    else:
        print(f"[*] Creating git tag {TAG}...")
        run_cmd(["git", "tag", "-a", TAG, "-m", f"MailSpoof Release {TAG}"])

    print(f"[*] Pushing tag {TAG} to origin...")
    run_cmd(["git", "push", "origin", TAG])

    # 4. Create GitHub release with assets
    print(f"[*] Publishing GitHub Release {TAG} via gh CLI...")
    gh_cmd = [
        "gh", "release", "create", TAG,
        str(tar_path),
        str(zip_path),
        "--title", f"MailSpoof {TAG}",
        "--notes-file", str(RELEASE_NOTES)
    ]
    run_cmd(gh_cmd)
    print(f"\n[✓] Release {TAG} published successfully with source archives!")

if __name__ == "__main__":
    main()
