from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from tradlint.models import Severity


@dataclass(slots=True)
class Config:
    fail_on: Severity = Severity.ERROR
    default_format: str = "text"
    recursive: bool = False
    rule_overrides: dict[str, str] | None = None


def load_config(start_path: Path) -> Config:
    """
    Minimal config loader.
    Keeps v1 simple: if tradlint.toml exists, parse only a tiny subset manually.
    """
    current = start_path.resolve()
    if current.is_file():
        current = current.parent

    for directory in [current, *current.parents]:
        cfg = directory / "tradlint.toml"
        if cfg.exists():
            return _parse_simple_toml(cfg)

    return Config()


def _parse_simple_toml(path: Path) -> Config:
    fail_on = Severity.ERROR
    default_format = "text"
    recursive = False
    rule_overrides: dict[str, str] = {}

    section = None
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1].strip()
            continue
        if "=" not in line:
            continue

        key, value = [part.strip() for part in line.split("=", 1)]
        value = value.strip('"').strip("'")

        if section == "general":
            if key == "fail_on":
                fail_on = Severity.from_string(value)
            elif key == "default_format":
                default_format = value
            elif key == "recursive":
                recursive = value.lower() == "true"
        elif section == "rules":
            rule_overrides[key] = value

    return Config(
        fail_on=fail_on,
        default_format=default_format,
        recursive=recursive,
        rule_overrides=rule_overrides,
    )
