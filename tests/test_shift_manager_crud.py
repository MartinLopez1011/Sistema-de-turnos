import pytest
import json
import sys
import os
from datetime import date

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from models.shift_manager import ShiftManager

@pytest.fixture
def base_config_crud(tmp_path):
    """
    Fixture con datos preexistentes (historial, excepciones) para probar 
    que el CRUD de personas actualiza correctamente todo el ecosistema 
    sin corromper los calendarios.
    """
    config_file = tmp_path / "config.json"
    
    initial_data = {
        "inicio": {
            "2023-12-25_2023-12-31": "SGT (F) PEREZ JUAN"
        },
        "historial": {
            "2024-01-01_2024-01-07": "CBO (M) GOMEZ ANA"
        },
        "personal": [
            {"id": 1, "nombre": "SGT (F) PEREZ JUAN"},
            {"id": 2, "nombre": "CBO (M) GOMEZ ANA"},
            {"id": 3, "nombre": "CBO (F) DIAZ LUIS"}
        ],
        "siguiente_id": 2,
        "pendientes": [3],
        "snapshots": {},
        "excepciones": {
            "2024-01": [
                {"persona": "SGT (F) PEREZ JUAN", "fecha": "2024-01-03", "tipo": "FL"}
            ]
        }
    }
    
    config_file.write_text(json.dumps(initial_data, indent=2, ensure_ascii=False), encoding='utf-8')
    return config_file

@pytest.fixture
def manager(base_config_crud):
    return ShiftManager(str(base_config_crud))


def test_add_person(manager):
    """Prueba que agregar una persona le asigna un ID único e incremental."""
    nuevo_id = manager.add_person("CBO (M) NUEVO PEDRO")
    
    assert nuevo_id == 4
    assert len(manager.personal) == 4
    assert manager.personal[-1]["nombre"] == "CBO (M) NUEVO PEDRO"
    assert manager.personal[-1]["id"] == 4


def test_edit_person_updates_history_and_exceptions(manager):
    """
    Prueba MUY IMPORTANTE: Al editar el nombre de una persona, 
    debe cambiar también en historial, inicio y excepciones para no quebrar
    los calendarios ni las validaciones pasadas.
    """
    # Editamos a Juan (ID 1)
    exito = manager.edit_person(1, "SGT (F) PEREZ JUAN EDITADO")
    
    assert exito is True
    # Verificamos lista de personal
    assert manager.personal[0]["nombre"] == "SGT (F) PEREZ JUAN EDITADO"
    
    # Verificamos Inicio
    assert manager.inicio["2023-12-25_2023-12-31"] == "SGT (F) PEREZ JUAN EDITADO"
    
    # Verificamos Excepciones
    excepcion_juan = manager.excepciones["2024-01"][0]
    assert excepcion_juan["persona"] == "SGT (F) PEREZ JUAN EDITADO"


def test_remove_person_updates_pointer(manager):
    """
    Prueba que al eliminar a una persona, si el puntero de 'siguiente_id'
    la apuntaba, este se resetea para no romper la rotación.
    """
    # manager.siguiente_id inicialmente es 2 (Ana)
    exito = manager.remove_person(2)
    
    assert exito is True
    assert len(manager.personal) == 2
    # Como borramos a Ana (que era el siguiente_id), el sistema debería 
    # apuntar a la primera persona disponible (Juan, id 1)
    assert manager.siguiente_id == 1
    # Y Ana ya no debe estar en la lista
    assert not any(p["id"] == 2 for p in manager.personal)


def test_move_person_order(manager):
    """
    Prueba subir y bajar personas en la lista, lo cual altera 
    el orden de rotación, pero mantiene intactos los IDs.
    """
    # Orden inicial: Juan(1), Ana(2), Luis(3)
    
    # Bajamos a Juan
    manager.move_person_down(1)
    assert manager.personal[0]["nombre"] == "CBO (M) GOMEZ ANA"
    assert manager.personal[1]["nombre"] == "SGT (F) PEREZ JUAN"
    
    # Subimos a Luis
    manager.move_person_up(3)
    assert manager.personal[1]["nombre"] == "CBO (F) DIAZ LUIS"
    assert manager.personal[2]["nombre"] == "SGT (F) PEREZ JUAN"
    
    # Intentar subir al primero no debe hacer nada ni fallar
    exito_falso = manager.move_person_up(2)  # Ana es la primera ahora
    assert exito_falso is False
    assert manager.personal[0]["nombre"] == "CBO (M) GOMEZ ANA"
