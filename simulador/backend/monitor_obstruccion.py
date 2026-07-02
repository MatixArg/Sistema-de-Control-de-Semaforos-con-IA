import config
from interseccion import Interseccion
from semaforo import Semaforo


class MonitorObstruccion:
    """Monitorea condiciones de obstruccion en los accesos.
    
    CASO 4 - Esquina Vecina Trancada:
        Si la velocidad en salida es 0 km/h sostenida tras 15s de verde,
        se congela el semaforo RECTO en ROJO y se activa giro/desvio.
    
    CASO 6 - Calle Anegada:
        Si la velocidad media es < 3 km/h sostenida tras 15s de verde,
        se marca como inoperable y conmuta a ROJO PARPADEANTE.
    """

    def __init__(self):
        self.tiempo_baja_velocidad = {}   # {acceso: tiempo_acumulado}
        self.tiempo_choque = {}           # {acceso: tiempo_acumulado}

    def analizar(self, interseccion, dt, frame_ia):
        """Analiza todos los accesos en busca de obstrucciones."""
        acceso_verde = interseccion.acceso_verde
        if acceso_verde is None:
            return

        sem_verde = interseccion.semaforos.get(acceso_verde)
        if sem_verde is None or not sem_verde.es_verde():
            return

        tiempo_verde = sem_verde.tiempo_en_estado
        acceso_data = frame_ia["accesos"].get(acceso_verde, {})
        velocidad = acceso_data.get("velocidad_media", -1)

        # Solo evaluar si paso suficiente tiempo desde que se dio verde
        if tiempo_verde < config.TIEMPO_CONFIRMAR_CHOQUE:
            self._resetear_contadores(acceso_verde)
            return

        # ---- CASO 4: VELOCIDAD 0 (CHOQUE / BLOQUEO) ----
        if velocidad == config.VELOCIDAD_CHOQUE:
            self.tiempo_choque[acceso_verde] = self.tiempo_choque.get(acceso_verde, 0) + dt
            if self.tiempo_choque[acceso_verde] >= config.TIEMPO_CONFIRMAR_CHOQUE:
                self._activar_modo_choque(interseccion, acceso_verde)
        else:
            self.tiempo_choque[acceso_verde] = 0

        # ---- CASO 6: VELOCIDAD < 3 KM/H (INUNDACION) ----
        if 0 < velocidad < config.VELOCIDAD_INUNDACION:
            self.tiempo_baja_velocidad[acceso_verde] = self.tiempo_baja_velocidad.get(acceso_verde, 0) + dt
            if self.tiempo_baja_velocidad[acceso_verde] >= config.TIEMPO_CONFIRMAR_INUNDACION:
                self._activar_modo_inundacion(interseccion, acceso_verde)
        else:
            self.tiempo_baja_velocidad[acceso_verde] = 0

    def _resetear_contadores(self, acceso):
        self.tiempo_choque[acceso] = 0
        self.tiempo_baja_velocidad[acceso] = 0

    def _activar_modo_choque(self, interseccion, acceso):
        """CASO 4: Congela RECTO en ROJO, activa giro/desvio."""
        print(f"\n  ⚠️⚠️⚠️ CASO 4 - ESQUINA TRANCADA en {acceso}")
        print(f"  Velocidad 0 km/h sostenida por {config.TIEMPO_CONFIRMAR_CHOQUE}s")
        interseccion.marcar_obstruccion_salida(acceso)
        interseccion.modo_desvio[acceso] = True
        print(f"  🔀 Activando GIRO/DESVIO en {acceso}")
        print(f"  🔴 RECTO {acceso} -> ROJO FORZADO\n")
        self.tiempo_choque[acceso] = 0

    def _activar_modo_inundacion(self, interseccion, acceso):
        """CASO 6: Marca como inoperable, conmuta a ROJO PARPADEANTE."""
        print(f"\n  🌊🌊🌊 CASO 6 - CALLE ANEGADA en {acceso}")
        print(f"  Velocidad < {config.VELOCIDAD_INUNDACION} km/h por {config.TIEMPO_CONFIRMAR_INUNDACION}s")
        interseccion.marcar_inundacion(acceso)
        print(f"  ⛔ {acceso} marcado como INOPERABLE")
        print(f"  🔴🔴🔴 ROJO PARPADEANTE activado en {acceso}\n")
        self.tiempo_baja_velocidad[acceso] = 0
