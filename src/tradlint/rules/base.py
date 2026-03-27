from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from tradlint.models import Finding, Severity, SourceFile


@dataclass(slots=True)
class RuleMeta:
    rule_id: str
    title: str
    default_severity: Severity
    explanation: str


class Rule(ABC):
    meta: RuleMeta

    @abstractmethod
    def check(self, source: SourceFile) -> list[Finding]:
        raise NotImplementedError

    def make_finding(
        self,
        *,
        source: SourceFile,
        message: str,
        line: Optional[int] = None,
        suggestion: Optional[str] = None,
        severity: Optional[Severity] = None,
    ) -> Finding:
        return Finding(
            rule_id=self.meta.rule_id,
            title=self.meta.title,
            severity=severity or self.meta.default_severity,
            message=message,
            file_path=str(source.path),
            line=line,
            suggestion=suggestion,
        )
