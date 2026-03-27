from __future__ import annotations

from pathlib import Path

from tradlint.config import Config
from tradlint.models import ScanResult, SourceFile
from tradlint.rules.mql_generic import all_rules


VALID_EXTENSIONS = {".mq4", ".mq5"}


def discover_files(target: Path, recursive: bool) -> list[Path]:
    if target.is_file():
        return [target]

    if not target.is_dir():
        raise FileNotFoundError(f"Path does not exist: {target}")

    if recursive:
        return sorted(
            p for p in target.rglob("*") if p.is_file() and p.suffix.lower() in VALID_EXTENSIONS
        )

    return sorted(
        p for p in target.iterdir() if p.is_file() and p.suffix.lower() in VALID_EXTENSIONS
    )


def analyze_file(path: Path, config: Config) -> ScanResult:
    text = path.read_text(encoding="utf-8", errors="replace")
    source = SourceFile(path=path, text=text)

    result = ScanResult(file_path=str(path))

    for rule in all_rules():
        findings = rule.check(source)
        for finding in findings:
            if config.rule_overrides:
                override = config.rule_overrides.get(finding.rule_id)
                if override:
                    override = override.lower()
                    if override == "off":
                        continue
                    finding.severity = finding.severity.from_string(override)
            result.add(finding)

    result.findings.sort(key=lambda f: (-int(f.severity), f.line or 0, f.rule_id))
    return result
