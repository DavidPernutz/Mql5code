from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tradlint.analyzer import analyze_file, discover_files
from tradlint.config import load_config
from tradlint.formatters import format_json, format_markdown, format_text
from tradlint.models import Severity
from tradlint.rules.mql_generic import RULE_EXPLANATIONS


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tradlint", description="Static linter/auditor for trading bots")
    sub = parser.add_subparsers(dest="command", required=True)

    scan = sub.add_parser("scan", help="Scan a file or directory")
    scan.add_argument("target", help="Path to a .mq4/.mq5 file or directory")
    scan.add_argument(
        "--format",
        dest="output_format",
        choices=["text", "json", "markdown"],
        default=None,
        help="Output format",
    )
    scan.add_argument(
        "--recursive",
        action="store_true",
        help="Recursively scan directories for .mq4/.mq5 files",
    )
    scan.add_argument(
        "--fail-on",
        choices=["info", "warning", "error"],
        default=None,
        help="Exit with code 1 if findings at or above this severity exist",
    )

    explain = sub.add_parser("explain", help="Explain a rule")
    explain.add_argument("rule_id", help="Rule id, e.g. MQL001")

    return parser


def _print_scan(results, output_format: str) -> None:
    if output_format == "json":
        print(format_json(results))
    elif output_format == "markdown":
        print(format_markdown(results))
    else:
        print(format_text(results))


def _highest_finding_severity(results) -> Severity | None:
    highest = None
    for result in results:
        current = result.highest_severity()
        if current is None:
            continue
        if highest is None or current > highest:
            highest = current
    return highest


def cmd_scan(args: argparse.Namespace) -> int:
    target = Path(args.target)
    config = load_config(target)

    recursive = args.recursive or config.recursive
    output_format = args.output_format or config.default_format
    fail_on = Severity.from_string(args.fail_on) if args.fail_on else config.fail_on

    try:
        files = discover_files(target, recursive=recursive)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if not files:
        print("No .mq4/.mq5 files found.", file=sys.stderr)
        return 2

    results = []
    for path in files:
        results.append(analyze_file(path, config=config))

    _print_scan(results, output_format)

    highest = _highest_finding_severity(results)
    if highest is not None and highest >= fail_on:
        return 1

    return 0


def cmd_explain(args: argparse.Namespace) -> int:
    rule_id = args.rule_id.upper().strip()
    meta = RULE_EXPLANATIONS.get(rule_id)
    if not meta:
        print(f"Unknown rule id: {rule_id}", file=sys.stderr)
        return 2

    print(f"{meta.rule_id} - {meta.title}")
    print(f"default severity: {meta.default_severity.to_string()}")
    print(meta.explanation)
    return 0


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "scan":
        raise SystemExit(cmd_scan(args))
    if args.command == "explain":
        raise SystemExit(cmd_explain(args))

    raise SystemExit(2)
