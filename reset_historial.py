import json
import os

def resetear_historial():
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    
    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    # 1. Vaciar el historial
    data["historial"] = {}
    
    # 2. Vaciar las copias de seguridad (snapshots)
    data["snapshots"] = {}
    
    # 3. Vaciar los pendientes
    data["pendientes"] = []

    # 4. Vaciar las excepciones
    data["excepciones"] = {}
    
    # 4. Calcular el siguiente_id en base a la última persona del "inicio"
    inicio = data.get("inicio", {})
    if inicio:
        # Obtener el último nombre asignado en inicio
        ultima_llave = sorted(inicio.keys())[-1]
        ultimo_nombre = inicio[ultima_llave]
        
        # Buscar su ID en la lista de personal
        personal = data.get("personal", [])
        ultimo_id = 1
        for p in personal:
            if p["nombre"] == ultimo_nombre:
                ultimo_id = p["id"]
                break
                
        siguiente = ultimo_id + 1
        if siguiente > len(personal):
            siguiente = 1
            
        data["siguiente_id"] = siguiente
    else:
        data["siguiente_id"] = 1
        
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        
    print("El historial ha sido reseteado. El sistema ha vuelto a los datos de inicio.")

if __name__ == "__main__":
    resetear_historial()
