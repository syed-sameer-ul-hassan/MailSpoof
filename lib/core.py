from __future__ import annotations

import json
import logging
import os
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

__version__ = "1.2.0"
__author__ = "Syed Sameer Ul Hassan"
__license__ = "Apache-2.0"

CONFIG_DIR = Path.home() / ".mailspoof"
CONFIG_FILE = CONFIG_DIR / "config.json"
LOG_FILE = CONFIG_DIR / "audit.log"
REPORTS_DIR = CONFIG_DIR / "reports"
TEMPLATES_DIR = CONFIG_DIR / "templates"

_PACKAGE_TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
_REPO_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"

@dataclass
class Scenario:
    id: int
    name: str
    category: str
    severity: str
    from_email: str
    from_name: str
    subject: str
    body: str
    description: str = ""
    source: str = "built-in"
    tags: List[str] = field(default_factory=list)
    disk_path: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class TestResult:
    timestamp: str
    test_type: str
    scenario: str
    target: str
    from_email: str
    success: bool
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

def _get_builtin_dir() -> Path:
    for path in (
        _PACKAGE_TEMPLATES_DIR / "builtins",
        _REPO_TEMPLATES_DIR / "builtins",
    ):
        if path.exists():
            return path
    return _REPO_TEMPLATES_DIR / "builtins"

import re

def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")

def load_builtin_templates() -> List[Dict[str, Any]]:
    scenarios: List[Dict[str, Any]] = []
    builtin_dir = _get_builtin_dir()
    if not builtin_dir.exists():
        return scenarios

    files = sorted(builtin_dir.glob("*.txt"))
    for idx, path in enumerate(files, start=1):
        try:
            text = path.read_text(encoding="utf-8")
            text = text.replace("{TODAY}", datetime.now().strftime("%Y-%m-%d"))
            data = _parse_template(text)
            data["id"] = idx
            data["source"] = "built-in"
            data["disk_path"] = str(path)
            scenarios.append(data)
        except Exception as exc:
            logging.warning(f"Failed to load built-in template {path.name}: {exc}")
    return scenarios

_TEMPLATE_KEYS = {
    "id", "name", "category", "severity", "from email", "from name",
    "subject", "body", "description", "tags",
}

def load_user_templates(start_id: int = 6) -> List[Dict[str, Any]]:
    TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
    scenarios: List[Dict[str, Any]] = []

    search_paths = [TEMPLATES_DIR]
    for extra in (_PACKAGE_TEMPLATES_DIR, _REPO_TEMPLATES_DIR):
        if extra.exists() and extra != TEMPLATES_DIR and extra not in search_paths:
            search_paths.append(extra)

    all_files: List[Path] = []
    for sp in search_paths:
        for p in sorted(sp.rglob("*.txt")):
            if "builtins" not in str(p.parent):
                all_files.append(p)

    seen: set[str] = set()
    unique_files: List[Path] = []
    for p in all_files:
        if p.name not in seen:
            seen.add(p.name)
            unique_files.append(p)

    for idx, path in enumerate(unique_files, start=start_id):
        try:
            text = path.read_text(encoding="utf-8")
            has_headers = False
            for line in text.splitlines():
                lower = line.lower().strip()
                for key in _TEMPLATE_KEYS:
                    if lower.startswith(key + ":"):
                        has_headers = True
                        break
                if has_headers:
                    break

            if has_headers:
                data = _parse_template(text)
            else:
                data = {
                    "name": path.stem.replace("_", " ").title(),
                    "category": "Custom",
                    "severity": "User-defined",
                    "from_email": "",
                    "from_name": "",
                    "subject": "",
                    "body": text.strip(),
                    "description": f"Custom body-only template: {path.name}",
                }

            data["id"] = int(data.get("id", idx) or idx)
            data["source"] = "custom"
            data["disk_path"] = str(path)
            scenarios.append(data)
        except Exception as exc:
            logging.warning(f"Failed to load user template {path.name}: {exc}")

    return scenarios

def _parse_template(text: str) -> Dict[str, str]:
    lines = text.splitlines()
    result: Dict[str, str] = {}
    current_key: str | None = None
    body_lines: List[str] = []
    in_body = False

    for raw in lines:
        line = raw.rstrip()
        if not line:
            if in_body:
                body_lines.append("")
            continue

        lower = line.lower()
        matched_key = None
        for key in _TEMPLATE_KEYS:
            prefix = key + ":"
            if lower.startswith(prefix):
                matched_key = key
                break

        if matched_key:
            if in_body and matched_key != "description":
                pass
            elif matched_key == "body":
                in_body = True
                current_key = matched_key
                val = line[len(matched_key) + 1:].strip()
                if val:
                    body_lines.append(val)
                continue
            else:
                in_body = False
                current_key = matched_key
                val = line[len(matched_key) + 1:].strip()
                result[current_key] = val
                continue

        if in_body:
            body_lines.append(line)

    if body_lines:
        while body_lines and body_lines[0] == "":
            body_lines.pop(0)
        while body_lines and body_lines[-1] == "":
            body_lines.pop()
        result["body"] = "\n".join(body_lines)

    mapping = {
        "id": "id",
        "name": "name",
        "category": "category",
        "severity": "severity",
        "from email": "from_email",
        "from name": "from_name",
        "subject": "subject",
        "body": "body",
        "description": "description",
        "tags": "tags",
    }
    normalized: Dict[str, str] = {}
    for old_key, new_key in mapping.items():
        normalized[new_key] = result.get(old_key, "")

    normalized.setdefault("description", f"Custom template.")
    normalized.setdefault("severity", "Medium")
    normalized.setdefault("category", "Custom")
    tags_raw = normalized.get("tags", "")
    normalized["tags"] = [t.strip() for t in tags_raw.split(",") if t.strip()] if isinstance(tags_raw, str) else []

    return normalized

class Config:

    def __init__(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
        self.data = self._load()
        self._builtin_templates = load_builtin_templates()
        self._custom_templates = load_user_templates(start_id=len(self._builtin_templates) + 1)
        self._init_logging()

    def _load(self) -> Dict[str, Any]:
        defaults: Dict[str, Any] = {
            "version": __version__,
            "smtp_server": {"host": "0.0.0.0", "port": 2525, "timeout": 30},
            "reporting": {"format": "json", "auto_generate": True},
            "smtp_profiles": {},
        }
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r") as fh:
                    loaded = json.load(fh)
                for key, value in defaults.items():
                    loaded.setdefault(key, value)
                return loaded
            except Exception as exc:
                logging.warning(f"Config load failed: {exc}; using defaults")
                return defaults
        else:
            self._save(defaults)
            return defaults

    def _save(self, data: Dict[str, Any]):
        try:
            with open(CONFIG_FILE, "w") as fh:
                json.dump(data, fh, indent=2)
        except Exception as exc:
            logging.warning(f"Config save failed: {exc}")

    def _init_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s | %(levelname)s | %(message)s",
            handlers=[
                logging.FileHandler(LOG_FILE),
                logging.StreamHandler(sys.stdout),
            ],
        )
        self.logger = logging.getLogger("MailSpoof")

    def scenarios(self) -> List[Scenario]:
        built_in = [Scenario(**s) for s in self._builtin_templates]
        custom = [Scenario(**s) for s in self._custom_templates]
        return built_in + custom

    def scenario_by_id(self, sid: int) -> Scenario | None:
        for s in self.scenarios():
            if s.id == sid:
                return s
        return None
