import config
from semaforo import Semaforo


class MaquinaEstados:
    """CASO 9: Maquina de estados estricta: VERDE -> AMARILLO (3s) -> TODO_ROJO (1s) -> SIGUIENTE_VERDE.
    
    Estados posibles:
        REPOSO       - Todo rojo, esperando trafico (CASO 2)
        VERDE        - Acceso actual en verde
        AMARILLO     - Transicion, duracion fija config.YELLOW_DURATION
        TODO_ROJO    - Pausa de seguridad entre cambios, config.ALL_RED_DURATION
    """

    REPOSO = "REPOSO"
    VERDE = "VERDE"
    AMARILLO = "AMARILLO"
    TODO_ROJO = "TODO_ROJO"

    def __init__(self):
        self.fase = self.REPOSO
        self.tiempo_fase = 0.0
        self.acceso_actual = None       # acceso que esta en VERDE
        self.acceso_siguiente = None    # proximo acceso a poner en VERDE
        self.emergencia_pendiente = None

    # ---- LOGGING ----

    def _log(self, msg):
        t = f"[T={self.tiempo_fase:.1f}s]"
        print(f"  {t} MAQ: {msg}")

    # ---- TRANSICIONES ----

    def iniciar(self, acceso):
        """Sale de REPOSO y pone un acceso en VERDE."""
        self.fase = self.VERDE
        self.tiempo_fase = 0.0
        self.acceso_actual = acceso
        self.acceso_siguiente = None
        self.emergencia_pendiente = None
        self._log(f"INICIO -> {acceso} VERDE")

    def iniciar_transicion(self, acceso_siguiente):
        """CASO 9: Inicia la secuencia VERDE -> AMARILLO para cambiar de acceso."""
        if self.fase != self.VERDE:
            return
        self.acceso_siguiente = acceso_siguiente
        self.fase = self.AMARILLO
        self.tiempo_fase = 0.0
        self._log(f"{self.acceso_actual} -> AMARILLO (destino: {acceso_siguiente})")

    def interrumpir_para_emergencia(self, acceso_emergencia):
        """CASO 1: Interrumpe el ciclo actual para dar paso a una emergencia.
        
        Si esta en VERDE: corta inmediatamente a AMARILLO (0s) -> TODO_ROJO -> VERDE emergencia.
        Si esta en REPOSO: va directamente a VERDE emergencia.
        """
        self.emergencia_pendiente = acceso_emergencia

        if self.fase == self.VERDE:
            self.fase = self.AMARILLO
            self.tiempo_fase = 0.0
            self._log(f"🚨 INTERRUPCION: {self.acceso_actual} -> AMARILLO (corte inmediato)")
            # Acelera: amarillo instantaneo
            self.tiempo_fase = config.YELLOW_DURATION
        elif self.fase == self.REPOSO:
            self.fase = self.VERDE
            self.tiempo_fase = 0.0
            self.acceso_actual = acceso_emergencia
            self.emergencia_pendiente = None
            self._log(f"🚨 REPOSO -> {acceso_emergencia} VERDE (emergencia)")

    def volver_a_reposo(self):
        """CASO 2: Vuelve a reposo cuando no hay trafico."""
        self.fase = self.REPOSO
        self.tiempo_fase = 0.0
        self.acceso_actual = None
        self.acceso_siguiente = None
        self._log("💤 REPOSO: Todo ROJO - Sin trafico")

    # ---- TICK PRINCIPAL ----

    def tick(self, dt):
        """Avanza la maquina un tick.
        
        Retorna: (nuevo_acceso_verde | None, evento | None)
        """
        self.tiempo_fase += dt

        if self.fase == self.AMARILLO:
            if self.tiempo_fase >= config.YELLOW_DURATION:
                self.fase = self.TODO_ROJO
                self.tiempo_fase = 0.0
                self._log(f"AMARILLO -> TODO_ROJO (1s)")
                return (None, "TO_ALL_RED")

        elif self.fase == self.TODO_ROJO:
            if self.tiempo_fase >= config.ALL_RED_DURATION:
                if self.emergencia_pendiente:
                    destino = self.emergencia_pendiente
                    self.emergencia_pendiente = None
                    self._log(f"🚨 TODO_ROJO -> {destino} VERDE (emergencia)")
                else:
                    destino = self.acceso_siguiente

                self.fase = self.VERDE
                self.tiempo_fase = 0.0
                self.acceso_actual = destino
                self._log(f"TODO_ROJO -> {destino} VERDE")
                return (destino, "TO_GREEN")

        return (None, None)

    def obtener_info_fase(self):
        """Retorna informacion legible de la fase actual."""
        return {
            "fase": self.fase,
            "tiempo_fase": round(self.tiempo_fase, 1),
            "acceso_actual": self.acceso_actual,
            "acceso_siguiente": self.acceso_siguiente
        }
