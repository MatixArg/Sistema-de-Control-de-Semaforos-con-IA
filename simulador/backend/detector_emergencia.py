import config


class DetectorEmergencia:
    """CASO 1: Detecta vehiculos de emergencia y fuerza interrupcion del ciclo.
    
    Escanea el frame JSON de la IA en busca de ambulancias o patrulleros
    con balizas activas en carriles que NO estan en verde.
    """

    def __init__(self, controlador_logico):
        self.controlador = controlador_logico

    def escanear(self, frame_ia, interseccion):
        """Analiza el frame en busca de emergencias.
        
        Retorna el acceso con emergencia o None.
        """
        accesos_data = frame_ia.get("accesos", {})

        for acceso, data in accesos_data.items():
            if not data.get("camara_operativa", True):
                continue

            tiene_emergencia = data.get("tiene_emergencia", False)
            tiene_balizas = data.get("tiene_balizas", False)

            if not (tiene_emergencia or tiene_balizas):
                continue

            # Ignorar si ya esta en verde (no necesita interrupcion)
            if interseccion.acceso_verde == acceso:
                continue

            # Ignorar si el acceso esta inoperable
            if interseccion.es_inoperable(acceso):
                continue

            print(f"\n  🚨🚨🚨 CASO 1 - EMERGENCIA DETECTADA en acceso {acceso}")
            print(f"  Vehiculo de emergencia detectado")
            if tiene_emergencia:
                tipos = [t for t in data.get("tipo_vehiculos", []) if t in ("ambulancia", "patrullero")]
                print(f"{' / '.join(tipos) if tipos else 'Desconocido'}")
            if tiene_balizas:
                print(f"  Balizas activas: SI")
            print(f"  Interrumpiendo ciclo actual...")

            interseccion.marcar_emergencia(acceso)
            return acceso

        return None

    def limpiar_emergencia_atendida(self, interseccion, acceso):
        """Limpia la bandera de emergencia una vez que el acceso se puso en verde."""
        interseccion.limpiar_emergencia(acceso)
        print(f"  ✅ Emergencia atendida en acceso {acceso}")
