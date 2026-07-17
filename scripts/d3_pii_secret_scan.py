"""D3: scan tracked git files for secrets and contact PII (Hoàng).

Writes a redacted summary under docs/03-project/ and a private JSON under
.ai-log-private/ (gitignored). Does not print full secret values.
"""

from __future__ import annotations

import json
import re
import subprocess
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PATTERNS: dict[str, re.Pattern[str]] = {
    "aws_access_key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "github_pat": re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    "github_oauth": re.compile(r"gho_[A-Za-z0-9]{20,}"),
    "openai_sk": re.compile(r"sk-[A-Za-z0-9]{20,}"),
    "langchain": re.compile(r"lsv2_[a-z]+_[a-f0-9_]{20,}"),
    "private_key_header": re.compile(r"BEGIN (RSA |OPENSSH |EC )?PRIVATE KEY"),
    "vn_mobile": re.compile(
        r"(?<!\d)(?:0|\+84)(?:3[2-9]|5[2689]|7[06-9]|8[1-9]|9\d)\d{7}(?!\d)"
    ),
    "email": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
}

EMAIL_ALLOW = {"noreply@github.com"}
BINARY_SKIP_EXT = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".ico",
    ".pdf",
    ".zip",
    ".xlsx",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
    ".mp4",
    ".lock",
}


def redact(value: str) -> str:
    if len(value) <= 8:
        return "***"
    return f"{value[:3]}…{value[-2:]}"


def tracked_files() -> list[str]:
    raw = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT)
    return [p.decode("utf-8", errors="replace") for p in raw.split(b"\0") if p]


def check_ignore(path: str) -> str:
    r = subprocess.run(
        ["git", "check-ignore", "-v", path],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return (r.stdout or r.stderr or "NOT_IGNORED").strip()


def main() -> int:
    files = tracked_files()
    findings: list[dict[str, object]] = []

    for rel in files:
        path = ROOT / rel
        if not path.is_file():
            continue
        if path.suffix.lower() in BINARY_SKIP_EXT or rel.endswith("package-lock.json"):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            findings.append({"file": rel, "kind": "read_error", "detail": str(exc)})
            continue

        for kind, rx in PATTERNS.items():
            for match in rx.finditer(text):
                value = match.group(0)
                if kind == "email":
                    lower = value.lower()
                    if lower in EMAIL_ALLOW:
                        continue
                    if (
                        "example.com" in lower
                        or "your-" in lower
                        or lower.endswith("@localhost")
                    ):
                        continue
                line = text.count("\n", 0, match.start()) + 1
                findings.append(
                    {
                        "file": rel,
                        "line": line,
                        "kind": kind,
                        "preview": redact(value),
                    }
                )

    tz = timezone(timedelta(hours=7))
    payload = {
        "scanned_at": datetime.now(tz).isoformat(),
        "repo": "https://github.com/phanthutrang410/ABG_team",
        "tracked_files_scanned": len(files),
        "findings_count": len(findings),
        "findings_by_kind": dict(Counter(str(f["kind"]) for f in findings)),
        "findings": findings,
        "gitignore_checks": {
            ".env": check_ignore(".env"),
            "reference-Learning-Analytics-AI/": check_ignore(
                "reference-Learning-Analytics-AI/"
            ),
        },
    }

    private_dir = ROOT / ".ai-log-private"
    private_dir.mkdir(exist_ok=True)
    private_path = private_dir / "d3-pii-secret-scan.json"
    private_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"tracked_files={len(files)}")
    print(f"findings={len(findings)}")
    print(f"by_kind={payload['findings_by_kind']}")
    print(f"private_json={private_path.relative_to(ROOT).as_posix()}")
    for item in findings:
        print(f"{item['kind']}\t{item['file']}:{item['line']}\t{item['preview']}")
    return 0 if not findings else 2


if __name__ == "__main__":
    raise SystemExit(main())
