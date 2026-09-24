import json

from models.shift_manager import ShiftManager


def test_save_adds_schema_and_audit_entry(tmp_path):
    config_path = tmp_path / "config.json"
    manager = ShiftManager(str(config_path))

    assert manager.add_person("Persona Uno") == 1
    manager.set_manual_assignment(
        "2026-10",
        "2026-10-05_2026-10-11",
        "Persona Uno",
        motivo="Permuta",
    )

    payload = json.loads(config_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 2
    assert payload["auditoria"][-1]["action"] == "SET_MANUAL_ASSIGNMENT"


def test_restore_backup_validates_and_reloads_state(tmp_path):
    config_path = tmp_path / "config.json"
    manager = ShiftManager(str(config_path))
    manager.add_person("Persona Original")
    backup_path = manager.create_backup("test")
    manager.add_person("Persona Temporal")

    success, message = manager.restore_backup(backup_path)

    assert success, message
    assert manager.get_person_by_id(1) == "Persona Original"
    assert manager.get_person_by_id(2) == "Desconocido"
