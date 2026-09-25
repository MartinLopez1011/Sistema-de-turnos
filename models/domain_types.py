from dataclasses import dataclass, field
from datetime import date
from typing import Any


@dataclass(frozen=True)
class ExceptionRecord:
    person: str
    date: date
    kind: str
    reason: str = ""


@dataclass(frozen=True)
class ShiftAssignment:
    start: date
    end: date
    person: str | None
    skipped: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    is_manual: bool = False
    is_recovery: bool = False

    def as_legacy_dict(self) -> dict[str, Any]:
        result = {
            "semana": (self.start, self.end),
            "persona": self.person,
            "saltados": list(self.skipped),
        }
        if self.is_manual:
            result["es_manual"] = True
        if self.is_recovery:
            result["es_recuperacion"] = True
        return result
