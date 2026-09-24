"""Block committed source files that match a known-dangerous security/network pattern.

Static pattern scan only (not a full security audit): it cannot see runtime
behaviour, auth flows, or business-logic flaws, only what is literally
written in tracked source files. Each rule maps to a CWE ID from the
CISA/MITRE 2025 CWE Top 25 and OWASP Top 10:2025 (see the sibling
`qa_manager` repository's `SECURITY_NETWORK_QA_STANDARD.md`, e.g.
`../qa_manager/SECURITY_NETWORK_QA_STANDARD.md` relative to this repo's
root, for the cited sources). A line with an
accompanying `qa:allow` comment is an acknowledged, documented risk and is
not reported as a failure.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

SOURCE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".ps1", ".sh", ".bat", ".cmd",
    ".go", ".rb", ".php", ".java",
}

ALLOW_MARKER = "qa:allow"

# This scanner's own rule definitions/pinned test fixtures necessarily contain
# the literal trigger substrings they detect (e.g. the CWE-78 rule's title
# literally says "shell=True"; the CWE-295 rule's pattern literally contains
# "_create_unverified_context") -- a self-scan would always flag its own
# source as a false positive. Excluded by filename, not by qa:allow, so the
# exclusion is visible in one place instead of scattered across every
# self-matching line.
SELF_EXCLUDE = {"check_security_hotspots.py", "test_security_hotspots.py"}


class Rule:
    def __init__(self, cwe: str, title: str, suggestion: str, pattern: str) -> None:
        self.cwe = cwe
        self.title = title
        self.suggestion = suggestion
        self.regex = re.compile(pattern)


RULES = [
    Rule(
        "CWE-798", "hardcoded credential",
        "remove the literal value and read it from an environment variable or secret store.",
        r"(?i)\b[A-Z0-9_]*(?:API[_-]?KEY|SECRET|PASSWORD|TOKEN|CREDENTIAL)[A-Z0-9_]*"
        r"\s*[:=]\s*['\"](?!(?:xxx|changeme|your_|example|redacted|dummy|test|<|\$\{|\{\{))"
        r"[A-Za-z0-9/+._-]{8,}['\"]",
    ),
    Rule(
        "CWE-78", "shell=True with a dynamic command",
        "build an argument list with shell=False, or add a same-line qa:allow if the "
        "command string is a trusted, operator-authored constant.",
        r"(?<!`)shell\s*=\s*True(?!`)",
    ),
    Rule(
        "CWE-89", "SQL assembled by string formatting",
        "use parameterised placeholders instead of formatting SQL text.",
        r"(?:execute|executemany)\s*\(\s*(?:f['\"]|['\"].*%s.*['\"]\s*%|['\"].*\{.*\}['\"]\s*\.format)",
    ),
    Rule(
        "CWE-95", "eval/exec on external input",
        "replace eval/exec with an explicit parser or an allow-listed branch.",
        r"(?<!\.)\b(?:eval|exec)\s*\(",
    ),
    Rule(
        "CWE-502", "insecure deserialization",
        "use json instead of pickle, or only deserialize trusted data. "
        "yaml.load needs Loader=yaml.SafeLoader, or use yaml.safe_load.",
        r"pickle\.loads?\s*\(|yaml\.load\s*\((?!.*SafeLoader)",
    ),
    Rule(
        "CWE-295", "TLS certificate verification disabled",
        "keep verify=True (the default), or pin a CA bundle for a private CA.",
        r"verify\s*=\s*False|_create_unverified_context|NODE_TLS_REJECT_UNAUTHORIZED\s*=\s*['\"]?0",
    ),
    Rule(
        "CWE-319", "cleartext http to a non-local endpoint",
        "switch to https://; localhost/127.0.0.1/0.0.0.0/example.com/example.org/example.net "
        "(RFC 2606 reserved for docs and tests) and www.w3.org (XML namespace URI, not a fetch) "
        "are excluded from this rule.",
        r"['\"]http://(?!localhost|127\.0\.0\.1|0\.0\.0\.0|example\.(?:com|org|net)|www\.w3\.org)"
        r"[A-Za-z0-9.-]+",
    ),
    Rule(
        "CWE-942", "CORS wide open",
        "allow-list explicit origins instead of a wildcard, especially with credentials.",
        r"Access-Control-Allow-Origin['\"]?\s*[:=]\s*['\"]\*|origin\s*:\s*['\"]\*['\"]",
    ),
]


def tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=REPO_ROOT, check=True, capture_output=True, text=True, encoding="utf-8",
    )
    return [REPO_ROOT / p for p in result.stdout.split("\0") if p]


def scan() -> list[str]:
    findings: list[str] = []
    for path in tracked_files():
        rel_path = path.relative_to(REPO_ROOT).as_posix()
        if path.name != ".gitkeep" and any(rel_path.startswith(prefix) for prefix in (
            "ai_anime/input/", "ai_img_video_aiBoygirl/input/", "ai_img_video_prompt_capcut/input/"
        )):
            findings.append(f"{rel_path}: [TRACKED-USER-INPUT] keep creative inputs local")
            continue
        if path.name in SELF_EXCLUDE:
            continue
        if path.suffix.lower() in {".md", ".txt", ".html"} and path.is_file():
            for line_no, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                if re.search(r"(?i)[A-Z]:\\Users\\[^\\\s]+\\", line):
                    findings.append(f"{rel_path}:{line_no}: [LOCAL-HOME-PATH] use a portable path in public docs")
            continue
        if path.suffix.lower() not in SOURCE_EXTENSIONS or not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for line_no, line in enumerate(text.splitlines(), start=1):
            if ALLOW_MARKER in line:
                continue
            for rule in RULES:
                if rule.regex.search(line):
                    findings.append(
                        f"{rel_path}:{line_no}: [{rule.cwe}] {rule.title} - {rule.suggestion}"
                    )
    return findings


def main() -> int:
    findings = scan()
    if findings:
        print(f"FAIL {len(findings)} unacknowledged security/network hotspot(s):")
        for line in findings:
            print(f"  - {line}")
        print("Acknowledge an accepted risk with a same-line `# qa:allow` comment, or fix it.")
        return 1
    print("OK   no unacknowledged security/network hotspots found (static pattern scan only)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
