from datetime import date
from typing import Any


class RotationEngine:
    """Domain boundary for shift generation.

    The legacy implementation remains on ShiftManager during migration so
    existing integrations keep receiving the historical dictionary format.
    """

    def __init__(self, manager):
        self._manager = manager

    def generate(
        self,
        year: int,
        month: int,
        exceptions: list[dict[str, Any]],
        state: dict[str, Any] | None = None,
        recalculate_history: bool = False,
        manual_assignments: dict[str, str] | None = None,
    ):
        return self._manager._generate_shifts_legacy(
            year,
            month,
            exceptions,
            state=state,
            recalculate_history=recalculate_history,
            manual_assignments=manual_assignments,
        )
