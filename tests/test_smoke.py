from pathlib import Path

from tradlint.analyzer import analyze_file
from tradlint.config import Config


def test_bad_fixture_has_findings():
    path = Path("tests/fixtures/bad_ea.mq5")
    result = analyze_file(path, Config())
    assert result.findings
    rule_ids = {f.rule_id for f in result.findings}
    assert "MQL001" in rule_ids


def test_safe_fixture_scans():
    path = Path("tests/fixtures/safe_ea.mq5")
    result = analyze_file(path, Config())
    assert result.file_path.endswith("safe_ea.mq5")
