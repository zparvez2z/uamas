from __future__ import annotations

import re
import subprocess
from pathlib import Path


TOKEN_PATTERNS = (
    re.compile(r"github_" + r"pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"gh" + r"[pousr]_[A-Za-z0-9_]{20,}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
)
ASSIGNMENT_PATTERN = re.compile(
    r"(?im)^[ \t]*(?:GITHUB_TOKEN|UAMAS_ADMIN_TOKEN|UAMAS_API_TOKEN|"
    r"UAMAS_SESSION_SECRET)[ \t]*=[ \t]*([^\s#]+)"
)
PLACEHOLDER_VALUES = {
    "changeme",
    "example",
    "placeholder",
    "replace-me",
    "replace_me",
}


def scan_text(text: str) -> list[str]:
    findings: list[str] = []
    for pattern in TOKEN_PATTERNS:
        if pattern.search(text):
            findings.append(f"matched secret pattern: {pattern.pattern}")
    for match in ASSIGNMENT_PATTERN.finditer(text):
        value = match.group(1).strip().strip("\"'")
        if value and value.lower() not in PLACEHOLDER_VALUES:
            findings.append(
                f"non-placeholder secret assignment: {match.group(0).split('=', 1)[0].strip()}"
            )
    return findings


def repository_files() -> list[Path]:
    result = subprocess.run(
        [
            "git",
            "ls-files",
            "-z",
            "--cached",
            "--others",
            "--exclude-standard",
        ],
        check=True,
        capture_output=True,
    )
    return [
        Path(raw.decode("utf-8"))
        for raw in result.stdout.split(b"\0")
        if raw
    ]


def main() -> int:
    findings: list[str] = []
    for path in repository_files():
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for finding in scan_text(content):
            findings.append(f"{path}: {finding}")

    if findings:
        print("Potential secrets detected in tracked files:")
        for finding in findings:
            print(f"- {finding}")
        return 1

    print("Tracked-file secret scan passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
