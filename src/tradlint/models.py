from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from pathlib import Path
from typing import Optional


class Severity(IntEnum):
    INFO = 10
    WARNING = 20
    ERROR = 30

    @classmethod
    def from_string(cls, value: str) -> "Severity":
        value = value.strip().lower()
        mapping = {
            "info": cls.INFO,
            "warning": cls.WARNING,
            "warn": cls.WARNING,
            "error": cls.ERROR,
        }
        if value not in mapping:
            raise ValueError(f"Unknown severity: {value}")
        return mapping[value]

    def to_string(self) -> str:
        if self == Severity.INFO:
            return "info"
        if self == Severity.WARNING:
            return "warning"
        return "error"


@dataclass(slots=True)
class Finding:
    rule_id: str
    title: str
    severity: Severity
    message: str
    file_path: str
    line: Optional[int] = None
    suggestion: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "title": self.title,
            "severity": self.severity.to_string(),
            "message": self.message,
            "file_path": self.file_path,
            "line": self.line,
            "suggestion": self.suggestion,
        }


@dataclass(slots=True)
class ScanResult:
    file_path: str
    findings: list[Finding] = field(default_factory=list)

    def add(self, finding: Finding) -> None:
        self.findings.append(finding)

    def highest_severity(self) -> Optional[Severity]:
        if not self.findings:
            return None
        return max(f.severity for f in self.findings)

    def to_dict(self) -> dict:
        return {
            "file_path": self.file_path,
            "findings": [f.to_dict() for f in self.findings],
        }


@dataclass(slots=True)
class SourceFile:
    path: Path
    text: str

    @property
    def lines(self) -> list[str]:
        return self.text.splitlines()
