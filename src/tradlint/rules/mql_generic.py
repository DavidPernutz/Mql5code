from __future__ import annotations

import re

from tradlint.models import Severity, SourceFile
from tradlint.rules.base import Rule, RuleMeta


def _find_line(lines: list[str], pattern: str) -> int | None:
    rx = re.compile(pattern)
    for idx, line in enumerate(lines, start=1):
        if rx.search(line):
            return idx
    return None


def _function_spans(text: str) -> list[tuple[str, int]]:
    """
    Very simple heuristic:
    returns (function_name, line_count)
    """
    lines = text.splitlines()
    results: list[tuple[str, int]] = []

    signature_rx = re.compile(
        r"^\s*(?:void|int|bool|double|string|long|datetime|float|char)\s+([A-Za-z_]\w*)\s*\([^;]*\)\s*$"
    )

    i = 0
    while i < len(lines):
        line = lines[i]
        match = signature_rx.match(line)
        if not match:
            i += 1
            continue

        func_name = match.group(1)
        brace_balance = 0
        started = False
        start_line = i + 1

        while i < len(lines):
            current = lines[i]
            brace_balance += current.count("{")
            brace_balance -= current.count("}")
            if "{" in current:
                started = True
            i += 1
            if started and brace_balance <= 0:
                end_line = i
                results.append((func_name, end_line - start_line + 1))
                break

    return results


class DeprecatedFreeMarginRule(Rule):
    meta = RuleMeta(
        rule_id="MQL001",
        title="Deprecated free margin constant",
        default_severity=Severity.WARNING,
        explanation="Detects deprecated ACCOUNT_FREEMARGIN usage.",
    )

    def check(self, source: SourceFile):
        lines = source.lines
        line = _find_line(lines, r"\bACCOUNT_FREEMARGIN\b")
        if line is None:
            return []
        return [
            self.make_finding(
                source=source,
                line=line,
                message="Deprecated ACCOUNT_FREEMARGIN found.",
                suggestion="Use ACCOUNT_MARGIN_FREE instead.",
            )
        ]


class HardcodedSymbolRule(Rule):
    meta = RuleMeta(
        rule_id="MQL002",
        title="Hardcoded trading symbol",
        default_severity=Severity.WARNING,
        explanation="Flags symbol strings like US100, XAUUSD, EURUSD instead of _Symbol-based logic.",
    )

    def check(self, source: SourceFile):
        findings = []
        symbol_rx = re.compile(r'"(?:[A-Z]{3,8}|US100|NAS100|XAUUSD|BTCUSD|GER40|USTEC|EURUSD)"')
        for idx, line in enumerate(source.lines, start=1):
            if "_Symbol" in line:
                continue
            if symbol_rx.search(line):
                findings.append(
                    self.make_finding(
                        source=source,
                        line=idx,
                        message="Potential hardcoded symbol detected.",
                        suggestion="Prefer _Symbol or configurable symbol inputs.",
                    )
                )
        return findings


class MissingSpreadFilterRule(Rule):
    meta = RuleMeta(
        rule_id="MQL003",
        title="No obvious spread filter",
        default_severity=Severity.INFO,
        explanation="Warns when no obvious spread filter logic is present.",
    )

    def check(self, source: SourceFile):
        text = source.text
        has_spread = (
            "SYMBOL_SPREAD" in text
            or "MaxSpread" in text
            or "spreadPoints" in text
            or "UseSpreadFilter" in text
        )
        if has_spread:
            return []
        return [
            self.make_finding(
                source=source,
                message="No obvious spread filter found.",
                suggestion="Consider adding spread guards for live trading robustness.",
            )
        ]


class MissingFridayWeekendGuardRule(Rule):
    meta = RuleMeta(
        rule_id="MQL004",
        title="No obvious Friday/weekend guard",
        default_severity=Severity.WARNING,
        explanation="Warns when no obvious Friday close / no-weekend logic is present.",
    )

    def check(self, source: SourceFile):
        text = source.text.lower()
        has_guard = (
            "friday" in text
            or "weekend" in text
            or "day_of_week" in text
            or "saturday" in text
            or "sunday" in text
        )
        if has_guard:
            return []
        return [
            self.make_finding(
                source=source,
                message="No obvious Friday/weekend protection found.",
                suggestion="Consider Friday cutoffs and weekend avoidance.",
            )
        ]


class MissingDailyGuardRule(Rule):
    meta = RuleMeta(
        rule_id="MQL005",
        title="No obvious daily risk guard",
        default_severity=Severity.WARNING,
        explanation="Warns when no daily loss / max loss trades guard is detected.",
    )

    def check(self, source: SourceFile):
        text = source.text.lower()
        has_guard = (
            "maxdailyloss" in text
            or "lossestradesperday" in text
            or "lossestradestoday" in text
            or "dayclosedpnl" in text
            or "dailyloss" in text
        )
        if has_guard:
            return []
        return [
            self.make_finding(
                source=source,
                message="No obvious daily loss guard found.",
                suggestion="Add a daily guard for loss amount and/or loss-trade count.",
            )
        ]


class UnsafeModifyRule(Rule):
    meta = RuleMeta(
        rule_id="MQL006",
        title="Potentially unsafe PositionModify usage",
        default_severity=Severity.WARNING,
        explanation="Flags PositionModify use when no obvious stop-level or delta-check helper exists.",
    )

    def check(self, source: SourceFile):
        text = source.text
        if "PositionModify(" not in text and ".PositionModify(" not in text:
            return []

        has_delta_guard = (
            "NormalizePrice(" in text
            or "stops_level" in text.lower()
            or "SYMBOL_TRADE_STOPS_LEVEL" in text
            or "SafePositionModify" in text
            or "abs(" in text.lower()
        )

        if has_delta_guard:
            return []

        line = _find_line(source.lines, r"PositionModify\s*\(")
        return [
            self.make_finding(
                source=source,
                line=line,
                message="PositionModify detected without clear delta/stops validation.",
                suggestion="Use a helper that skips identical values and validates broker stop distance.",
            )
        ]


class MissingStopsLevelRule(Rule):
    meta = RuleMeta(
        rule_id="MQL007",
        title="No obvious stop-level validation",
        default_severity=Severity.INFO,
        explanation="Warns if SYMBOL_TRADE_STOPS_LEVEL is not referenced.",
    )

    def check(self, source: SourceFile):
        if "SYMBOL_TRADE_STOPS_LEVEL" in source.text:
            return []
        return [
            self.make_finding(
                source=source,
                message="No obvious broker stop-level validation found.",
                suggestion="Use SYMBOL_TRADE_STOPS_LEVEL before modifying or placing stops.",
            )
        ]


class OversizedFunctionRule(Rule):
    meta = RuleMeta(
        rule_id="MQL008",
        title="Oversized function",
        default_severity=Severity.INFO,
        explanation="Flags long functions that may be hard to test or review.",
    )

    def check(self, source: SourceFile):
        findings = []
        for func_name, line_count in _function_spans(source.text):
            if line_count > 120:
                line = _find_line(source.lines, rf"\b{re.escape(func_name)}\s*\(")
                findings.append(
                    self.make_finding(
                        source=source,
                        line=line,
                        message=f"Function '{func_name}' is large ({line_count} lines).",
                        suggestion="Split into smaller testable helpers.",
                    )
                )
        return findings


class FixedBrokerTimeRule(Rule):
    meta = RuleMeta(
        rule_id="MQL009",
        title="Fixed broker-time logic",
        default_severity=Severity.INFO,
        explanation="Warns when fixed broker hours are present without clear relative session logic.",
    )

    def check(self, source: SourceFile):
        text = source.text
        has_fixed_time = (
            "StartHour" in text
            or "EndHour" in text
            or "TradeStartHour" in text
            or "TradeEndHour" in text
            or "VWAPAnchorHour" in text
        )
        has_relative = (
            "MinutesFromAnchor" in text
            or "InitialWaitMinutes" in text
            or "PostOpenPause" in text
            or "GetAnchorTime" in text
        )
        if has_fixed_time and not has_relative:
            line = _find_line(source.lines, r"(TradeStartHour|TradeEndHour|VWAPAnchorHour)")
            return [
                self.make_finding(
                    source=source,
                    line=line,
                    message="Fixed broker-time session logic detected without obvious relative session model.",
                    suggestion="Prefer relative session windows around the anchor/open when possible.",
                )
            ]
        return []


class EntryWithoutObviousSLRule(Rule):
    meta = RuleMeta(
        rule_id="MQL010",
        title="Entry without obvious stop-loss",
        default_severity=Severity.WARNING,
        explanation="Flags Buy/Sell calls when no obvious sl parameter is visible nearby.",
    )

    def check(self, source: SourceFile):
        findings = []
        for idx, line in enumerate(source.lines, start=1):
            if "trade.Buy(" in line or "trade.Sell(" in line:
                if "sl" not in line.lower() and "stop" not in line.lower():
                    findings.append(
                        self.make_finding(
                            source=source,
                            line=idx,
                            message="Trade entry call without obvious SL argument on the same line.",
                            suggestion="Verify that stop-loss is always set explicitly.",
                        )
                    )
        return findings


class MissingCopyCheckRule(Rule):
    meta = RuleMeta(
        rule_id="MQL011",
        title="No obvious CopyRates/CopyBuffer return validation",
        default_severity=Severity.INFO,
        explanation="Warns when CopyRates/CopyBuffer appears without direct comparison checks.",
    )

    def check(self, source: SourceFile):
        text = source.text
        uses_copy = "CopyRates(" in text or "CopyBuffer(" in text
        has_check = "<" in text and ("CopyRates(" in text or "CopyBuffer(" in text)
        if uses_copy and not has_check:
            return [
                self.make_finding(
                    source=source,
                    message="CopyRates/CopyBuffer usage found without obvious return-size checks.",
                    suggestion="Check return values before using copied arrays.",
                )
            ]
        return []


class MissingBidAskValidityRule(Rule):
    meta = RuleMeta(
        rule_id="MQL012",
        title="No obvious Ask/Bid validity checks",
        default_severity=Severity.INFO,
        explanation="Warns if ask/bid are used without visible <= 0 checks.",
    )

    def check(self, source: SourceFile):
        text = source.text
        uses_quotes = "SYMBOL_ASK" in text or "SYMBOL_BID" in text
        has_validity = "<= 0.0" in text or "<=0.0" in text or "<= 0" in text
        if uses_quotes and not has_validity:
            return [
                self.make_finding(
                    source=source,
                    message="Bid/Ask usage found without obvious validity checks.",
                    suggestion="Check ask/bid values before relying on them.",
                )
            ]
        return []


def all_rules() -> list[Rule]:
    return [
        DeprecatedFreeMarginRule(),
        HardcodedSymbolRule(),
        MissingSpreadFilterRule(),
        MissingFridayWeekendGuardRule(),
        MissingDailyGuardRule(),
        UnsafeModifyRule(),
        MissingStopsLevelRule(),
        OversizedFunctionRule(),
        FixedBrokerTimeRule(),
        EntryWithoutObviousSLRule(),
        MissingCopyCheckRule(),
        MissingBidAskValidityRule(),
    ]


RULE_EXPLANATIONS = {rule.meta.rule_id: rule.meta for rule in all_rules()}
