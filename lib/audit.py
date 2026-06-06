from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List

from lib.core import Config, LOG_FILE, REPORTS_DIR, __version__

def load_entries(config: Config) -> List[Dict[str, Any]]:
    if not LOG_FILE.exists():
        return []
    entries = []
    with open(LOG_FILE, "r") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entries

def show_logs(config: Config, lines: int = 20):
    entries = load_entries(config)
    if not entries:
        print("No logs found yet.")
        return

    recent = entries[-lines:]
    print(f"\n{'═' * 70}")
    print(f"  MailSpoof Audit Log (last {len(recent)} of {len(entries)} entries)")
    print(f"{'═' * 70}\n")

    for entry in recent:
        ts = entry.get("timestamp", "?")[:19].replace("T", " ")
        status = "PASS" if entry.get("success") else "FAIL"
        scenario = entry.get("scenario", "?")
        target = entry.get("target", "?")
        sender = entry.get("from_email", "?")

        print(f"  {ts}  [{status}]  {entry.get('test_type','?').upper()}")
        print(f"           Scenario: {scenario}")
        print(f"           From: {sender}")
        print(f"           Target: {target}")

        details = entry.get("details", {})
        if "severity" in details:
            print(f"           Severity: {details['severity']}")
        if "error" in details:
            print(f"           Error: {details['error']}")
        print()

    print(f"  Log file: {LOG_FILE}")
    print(f"{'═' * 70}\n")

def generate_report(config: Config, output_path: str | None = None, fmt: str = "json"):
    entries = load_entries(config)
    if not entries:
        print("No test data available for reporting.")
        return

    total = len(entries)
    successful = sum(1 for e in entries if e.get("success"))
    failed = total - successful
    rate = round((successful / total) * 100, 2) if total else 0.0

    by_type: Dict[str, Dict[str, int]] = {}
    for e in entries:
        tt = e.get("test_type", "unknown")
        by_type.setdefault(tt, {"total": 0, "success": 0})
        by_type[tt]["total"] += 1
        if e.get("success"):
            by_type[tt]["success"] += 1

    by_scenario: Dict[str, Dict[str, int]] = {}
    for e in entries:
        sc = e.get("scenario", "unknown")
        by_scenario.setdefault(sc, {"total": 0, "success": 0})
        by_scenario[sc]["total"] += 1
        if e.get("success"):
            by_scenario[sc]["success"] += 1

    recs = []
    if rate > 80:
        recs = [
            "CRITICAL: High spoofing success rate detected.",
            "Implement SPF, DKIM, and DMARC policies immediately.",
            "Deploy email security gateways with spoofing detection.",
            "Conduct urgent security awareness training.",
        ]
    elif rate > 50:
        recs = [
            "HIGH: Moderate spoofing vulnerabilities identified.",
            "Review and strengthen email authentication policies.",
            "Add additional email security controls.",
            "Schedule regular security awareness training.",
        ]
    else:
        recs = [
            "MEDIUM: Some spoofing attempts succeeded.",
            "Continue monitoring email authentication mechanisms.",
            "Periodic refresher training recommended.",
            "Regular penetration testing advised.",
        ]

    timestamps = [e.get("timestamp", "") for e in entries if e.get("timestamp")]
    report = {
        "meta": {
            "tool": "MailSpoof",
            "version": __version__,
            "generated_at": datetime.now().isoformat(),
        },
        "summary": {
            "total_tests": total,
            "successful": successful,
            "failed": failed,
            "success_rate": rate,
            "first_test": min(timestamps) if timestamps else None,
            "last_test": max(timestamps) if timestamps else None,
        },
        "analysis": {
            "by_type": by_type,
            "by_scenario": by_scenario,
        },
        "recommendations": recs,
        "detailed_logs": entries,
    }

    if not output_path:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        ext = "csv" if fmt == "csv" else "json"
        output_path = str(REPORTS_DIR / f"report_{ts}.{ext}")

    if fmt == "csv":
        import csv

        headers = ["timestamp", "test_type", "scenario", "target", "from_email", "success", "category", "severity", "smtp_server", "error"]
        with open(output_path, "w", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=headers)
            writer.writeheader()
            for e in entries:
                details = e.get("details", {}) or {}
                writer.writerow({
                    "timestamp": e.get("timestamp", ""),
                    "test_type": e.get("test_type", ""),
                    "scenario": e.get("scenario", ""),
                    "target": e.get("target", ""),
                    "from_email": e.get("from_email", ""),
                    "success": e.get("success", False),
                    "category": details.get("category", ""),
                    "severity": details.get("severity", ""),
                    "smtp_server": details.get("smtp_server", ""),
                    "error": details.get("error", ""),
                })
    else:
        with open(output_path, "w") as fh:
            json.dump(report, fh, indent=2)

    print(f"\n[REPORT]  Saved to {output_path}")
    print(f"  Total tests: {total}")
    print(f"  Success:     {successful}")
    print(f"  Failed:      {failed}")
    print(f"  Rate:        {rate}%")
    print(f"  Risk:        {'CRITICAL' if rate > 80 else 'HIGH' if rate > 50 else 'MEDIUM'}")
    print()
