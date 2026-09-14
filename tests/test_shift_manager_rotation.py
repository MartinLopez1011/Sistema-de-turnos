import pytest
import json
import sys
import os
from datetime import date

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from models.shift_manager import ShiftManager

@pytest.fixture
def base_config(tmp_path):
    """
    Fixture que crea un archivo config.json temporal con un estado inicial limpio.
    Usa tmp_path de pytest para asegurar que la base de datos real del usuario no se toque.
    """
    config_file = tmp_path / "config.json"
    
    initial_data = {
        "inicio": {},
        "historial": {},
        "personal": [
            {"id": 1, "nombre": "SGT (F) PEREZ JUAN"},
            {"id": 2, "nombre": "CBO (M) GOMEZ ANA"},
            {"id": 3, "nombre": "CBO (F) DIAZ LUIS"},
            {"id": 4, "nombre": "CBO (F) SILVA MARIA"},
            {"id": 5, "nombre": "CBO (M) ROJAS PEDRO"},
            {"id": 6, "nombre": "CBO (F) MUÑOZ SARA"}
        ],
        "siguiente_id": 1,
        "pendientes": [],
        "snapshots": {},
        "excepciones": {}
    }
    
    config_file.write_text(json.dumps(initial_data, indent=2, ensure_ascii=False), encoding='utf-8')
    return config_file

@pytest.fixture
def manager(base_config):
    """Fixture que devuelve una instancia de ShiftManager aislada usando el config temporal."""
    return ShiftManager(str(base_config))

def test_excepcion_y_recuperacion(manager):
    """
    Edge Case 1: Excepciones y Recuperación de Pendientes
    Verifica que si la persona en turno tiene una excepción, salta la semana,
    entra a pendientes, y recupera en la semana inmediatamente posterior disponible,
    mientras la cola sigue avanzando.
    """
    # Enero 2024 tiene 5 semanas calendario.
    # W1: Jan 1-7, W2: Jan 8-14, W3: Jan 15-21, W4: Jan 22-28, W5: Jan 29-Feb 4
    excepciones = [
        {"persona": "SGT (F) PEREZ JUAN", "fecha": date(2024, 1, 3), "tipo": "FL"}
    ]
    
    shifts, final_id, pendientes = manager.generate_shifts(2024, 1, excepciones)
    
    # Semana 1: JUAN tiene excepción. El turno salta a la siguiente (ANA, id=2)
    assert shifts[0]['persona'] == "CBO (M) GOMEZ ANA"
    assert any(s['persona'] == "SGT (F) PEREZ JUAN" for s in shifts[0]['saltados'])
    
    # Semana 2: JUAN ya no tiene excepción y está primero en pendientes. Recupera turno.
    assert shifts[1]['persona'] == "SGT (F) PEREZ JUAN"
    assert shifts[1].get('es_recuperacion') is True
    
    # Semana 3: El puntero de cola normal retoma donde se quedó (después de ANA, le toca a LUIS id=3)
    assert shifts[2]['persona'] == "CBO (F) DIAZ LUIS"
    
    # Semana 4: MARIA (id=4)
    assert shifts[3]['persona'] == "CBO (F) SILVA MARIA"
    
    # Semana 5: PEDRO (id=5)
    assert shifts[4]['persona'] == "CBO (M) ROJAS PEDRO"
    
    # Verificaciones finales del estado devuelto
    # JUAN ya no debe estar en pendientes
    assert 1 not in pendientes
    # El ID guardado para el próximo mes debe ser 6 (SARA), ya que PEDRO (5) tomó la última semana
    assert final_id == 6

def test_multiples_excepciones_fifo(manager):
    """
    Edge Case 2: Prioridad y Orden de Múltiples Pendientes Simultáneos.
    Verifica que si múltiples personas tienen excepciones y entran a pendientes,
    se respetará el orden en que entraron (FIFO) para su recuperación,
    sin colapsar la asignación del resto del equipo.
    """
    # Marzo 2024 tiene 5 semanas
    # W1: Feb 26-Mar 3, W2: Mar 4-10, W3: Mar 11-17, W4: Mar 18-24, W5: Mar 25-31
    # Asumimos que inicialmente le toca a JUAN (id 1).
    
    # En la semana 1, tanto JUAN como ANA (los primeros en la cola) tienen excepciones.
    excepciones = [
        {"persona": "SGT (F) PEREZ JUAN", "fecha": date(2024, 2, 28), "tipo": "FL"},
        {"persona": "CBO (M) GOMEZ ANA", "fecha": date(2024, 3, 1), "tipo": "LIC"}
    ]
    
    shifts, final_id, pendientes = manager.generate_shifts(2024, 3, excepciones)
    
    # Semana 1: JUAN y ANA bloqueados. El turno cae en LUIS (id=3).
    assert shifts[0]['persona'] == "CBO (F) DIAZ LUIS"
    saltados = [s['persona'] for s in shifts[0]['saltados']]
    assert "SGT (F) PEREZ JUAN" in saltados
    assert "CBO (M) GOMEZ ANA" in saltados
    
    # Semana 2: JUAN es el primero en pendientes y ya no tiene excepción. Recupera.
    assert shifts[1]['persona'] == "SGT (F) PEREZ JUAN"
    assert shifts[1].get('es_recuperacion') is True
    
    # Semana 3: ANA es la segunda en pendientes y recupera.
    assert shifts[2]['persona'] == "CBO (M) GOMEZ ANA"
    assert shifts[2].get('es_recuperacion') is True
    
    # Semana 4: Pendientes vacíos. Se retoma la cola normal.
    # El último turno normal lo hizo LUIS (id 3). Le toca a MARIA (id 4).
    assert shifts[3]['persona'] == "CBO (F) SILVA MARIA"
    
    # Semana 5: PEDRO (id 5)
    assert shifts[4]['persona'] == "CBO (M) ROJAS PEDRO"
    
    # Verificaciones finales
    assert len(pendientes) == 0
    assert final_id == 6

def test_transicion_mes_y_snapshots(manager):
    """
    Edge Case 3: Wrap-around del Puntero y Transición de Mes (Snapshots).
    Verifica que al cerrar un mes (advance_month), los pendientes que no 
    alcanzaron a recuperar turno se arrastran correctamente al mes siguiente,
    respetando las semanas compartidas (historial) y el ID de continuación.
    """
    # Mes 1: Abril 2024. Semanas (Lunes a Domingo):
    # W1: Apr 1-7 (JUAN, id 1)
    # W2: Apr 8-14 (ANA, id 2)
    # W3: Apr 15-21 (LUIS, id 3)
    # W4: Apr 22-28 (MARIA, id 4)
    # W5: Apr 29-May 5 -> Le toca a PEDRO (id 5), pero pide excepción. SARA (id 6) lo reemplaza.
    # Resultado final de Abril: final_id debe dar la vuelta a 1. PEDRO queda pendiente.
    
    excepciones_abril = [
        {"persona": "CBO (M) ROJAS PEDRO", "fecha": date(2024, 5, 2), "tipo": "DA"}
    ]
    
    # Simulamos el cierre del mes de Abril
    manager.advance_month(2024, 4, excepciones_abril)
    
    # Comprobamos el estado interno de manager luego del avance
    assert manager.siguiente_id == 1
    assert 5 in manager.pendientes  # El ID de Pedro es 5
    assert "2024-05" in manager.snapshots
    assert manager.snapshots["2024-05"]["pendientes"] == [5]
    
    # Ahora generamos los turnos para Mayo 2024
    # W1: Apr 29-May 5 (Compartida con Abril, debería estar fijada por historial a SARA)
    # W2: May 6-12 (PEDRO recupera turno)
    # W3: May 13-19 (Normal queue: le toca a JUAN, id 1)
    # W4: May 20-26 (ANA, id 2)
    # W5: May 27-Jun 2 (LUIS, id 3)
    
    shifts_mayo, final_id_mayo, pendientes_mayo = manager.generate_shifts(2024, 5, [])
    
    # Semana compartida fijada en el historial
    assert shifts_mayo[0]['persona'] == "CBO (F) MUÑOZ SARA"
    assert shifts_mayo[0]['semana'][0] == date(2024, 4, 29)
    
    # Semana 2: Pedro (Pendiente arrastrado del mes anterior) recupera
    assert shifts_mayo[1]['persona'] == "CBO (M) ROJAS PEDRO"
    assert shifts_mayo[1].get('es_recuperacion') is True
    
    # Semana 3: El puntero normal guardado en el snapshot retoma en JUAN (id 1)
    assert shifts_mayo[2]['persona'] == "SGT (F) PEREZ JUAN"
    
    # Semana 4: ANA
    assert shifts_mayo[3]['persona'] == "CBO (M) GOMEZ ANA"
    
    # Semana 5: LUIS
    assert shifts_mayo[4]['persona'] == "CBO (F) DIAZ LUIS"
    
    # Verificaciones finales de Mayo
    assert len(pendientes_mayo) == 0
    assert final_id_mayo == 4  # Después de Luis (id 3) le toca a Maria (id 4) para Junio
