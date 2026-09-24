import json
from datetime import date

from models.config_repository import ConfigRepository
from models.domain_types import ShiftAssignment
from models.shift_manager import ShiftManager


def test_config_repository_round_trip_is_atomic(tmp_path):
    path = tmp_path / "config.json"
    repository = ConfigRepository(str(path), lambda: {})
    payload = {
        "notificaciones": {},
        "personal": [],
        "inicio": {},
        "historial": {},
        "siguiente_id": 1,
        "pendientes": [],
        "snapshots": {},
        "excepciones": {},
        "asignaciones_manuales": {},
        "asignaciones_manuales_motivos": {},
        "auditoria": [],
        "schema_version": 2,
    }

    assert repository.save(payload)
    assert json.loads(path.read_text(encoding="utf-8"))["schema_version"] == 2
    assert repository.load()["schema_version"] == 2
    assert not (tmp_path / "config.json.tmp").exists()


def test_rotation_engine_preserves_legacy_output_contract(tmp_path):
    manager = ShiftManager(str(tmp_path / "config.json"))
    manager.add_person("Persona Uno")

    shifts, _, _ = manager.rotation_engine.generate(2026, 1, [])

    assert shifts
    assert "semana" in shifts[0]
    assert "persona" in shifts[0]


def test_shift_assignment_can_adapt_to_legacy_output():
    assignment = ShiftAssignment(
        start=date(2026, 1, 5),
        end=date(2026, 1, 11),
        person="Persona Uno",
        is_manual=True,
    )

    assert assignment.as_legacy_dict() == {
        "semana": (date(2026, 1, 5), date(2026, 1, 11)),
        "persona": "Persona Uno",
        "saltados": [],
        "es_manual": True,
    }
