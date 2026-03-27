from __future__ import annotations

import json
from tradlint.models import ScanResult


def format_text(results: list[ScanResult]) -> str:
    blocks: list[str] = []

    for result in results:
        lines = [f"FILE: {result.file_path}"]
        if not result.findings:
            lines.append("  OK - no findings")
        else:
            for f in result.findings:
                pos = f"line {f.line}" if f.line else "line ?"
                lines.append(
                    f"  [{f.severity.to_string().upper()}] {f.rule_id} {f.title} ({pos})"
                )
                lines.append(f"    {f.message}")
                if f.suggestion:
                    lines.append(f"    suggestion: {f.suggestion}")
        blocks.append("\n".join(lines))

    return "\n\n".join(blocks)


def format_json(results: list[ScanResult]) -> str:
    return json.dumps([r.to_dict() for r in results], indent=2, ensure_ascii=False)


def format_markdown(results: list[ScanResult]) -> str:
    parts: list[str] = ["# tradlint report", ""]
    for result in results:
        parts.append(f"## `{result.file_path}`")
        if not result.findings:
            parts.append("")
            parts.append("- OK: no findings")
            parts.append("")
            continue

        parts.append("")
        parts.append("| Severity | Rule | Line | Message | Suggestion |")
        parts.append("|---|---|---:|---|---|")
        for f in result.findings:
            suggestion = f.suggestion or ""
            line = f.line if f.line is not None else ""
            parts.append(
                f"| {f.severity.to_string()} | {f.rule_id} | {line} | {f.message} | {suggestion} |"
            )
        parts.append("")

    return "\n".join(parts)
