from collections import deque, defaultdict
from semaforo import Semaforo
from vehiculo import Vehiculo
import config

NORTE = "N"
SUR = "S"
ESTE = "E"
OESTE = "W"
ACCESOS_4 = [NORTE, SUR, ESTE, OESTE]
ACCESOS_T = [SUR, ESTE, OESTE]


class Interseccion:
    def __init__(self, accesos):
        self.accesos = accesos
        self.carriles = {a: deque() for a in accesos}
        self.semaforos = {a: Semaforo() for a in accesos}
        self.acceso_verde = None
        self.acceso_proximo = None
        self.tiempo_simulacion = 0.0

        # CASO 3: Historial de conteo frame a frame para occlusion
        self.historial_conteo = {a: deque(maxlen=config.HISTORIAL_TAMANO) for a in accesos}

        # CASO 4: Obstruccion por choque en salida
        self.tiempo_obstruccion = {a: 0.0 for a in accesos}
        self.obstruccion_activa = {a: False for a in accesos}

        # CASO 4/5: Modo desvio forzado
        self.modo_desvio = {a: False for a in accesos}

        # CASO 6: Inundacion / inoperable
        self.tiempo_baja_velocidad = {a: 0.0 for a in accesos}
        self.inoperable = {a: False for a in accesos}

        # CASO 5: Flujo absoluto por vehiculo pesado cruzando linea
        self.cruzando_pesado = {a: False for a in accesos}

        # CASO 7: Camaras
        self.camara_operativa = {a: True for a in accesos}

        # CASO 1: Emergencia
        self.emergencia_activa = {a: False for a in accesos}

        # Mediciones simuladas
        self.velocidad_media = {a: 0.0 for a in accesos}

    # ---- METODOS BASE ----

    def agregar_vehiculo(self, acceso, tipo="auto", tiene_balizas=False, es_emergencia=False):
        v = Vehiculo(acceso, tipo, tiene_balizas, es_emergencia)
        v.tiempo_llegada = self.tiempo_simulacion
        self.carriles[acceso].append(v)
        return v

    def contar_vehiculos(self, acceso=None):
        if acceso:
            return len(self.carriles[acceso])
        return sum(len(q) for q in self.carriles.values())

    def obtener_tiempo_espera_maximo(self, acceso):
        return max((v.tiempo_espera for v in self.carriles[acceso]), default=0.0)

    def obtener_tiempo_espera_promedio(self, acceso):
        cola = self.carriles[acceso]
        if not cola:
            return 0.0
        return sum(v.tiempo_espera for v in cola) / len(cola)

    def vaciar_acceso(self, acceso):
        n = len(self.carriles[acceso])
        self.carriles[acceso].clear()
        return n

    def actualizar(self, dt):
        self.tiempo_simulacion += dt
        for cola in self.carriles.values():
            for v in cola:
                v.actualizar_espera(dt)
        for s in self.semaforos.values():
            s.actualizar(dt)

    # ---- CASO 3: HISTORIAL Y OCULSION ----

    def actualizar_historial(self, acceso):
        self.historial_conteo[acceso].append(len(self.carriles[acceso]))

    def detectar_oclusion(self, acceso):
        """Retorna True si el conteo subio abruptamente en los ultimos frames."""
        hist = list(self.historial_conteo[acceso])
        if len(hist) < 2:
            return False
        salto = hist[-1] - hist[-2]
        return salto >= config.UMBRAL_OCLUSION

    # ---- CASO 5: PESO VISUAL Y FLUJO ABSOLUTO ----

    def calcular_tiempo_estimado_verde(self, acceso):
        """Suma los pesos visuales de todos los vehiculos en el carril."""
        total = sum(v.obtener_peso_visual() for v in self.carriles[acceso])
        return max(config.MIN_GREEN, min(total, config.MAX_GREEN))

    def verificar_vehiculo_cruzando(self, acceso):
        """CASO 5 - Flujo absoluto: verifica si un vehiculo pesado esta cruzando."""
        cola = self.carriles.get(acceso, deque())
        if cola:
            v = cola[0]
            v.cruzando_linea = True
            if v.es_pesado():
                self.cruzando_pesado[acceso] = True
                return True
        self.cruzando_pesado[acceso] = False
        return False

    # ---- CASO 6: INUNDACION / INOPERABLE ----

    def marcar_inundacion(self, acceso):
        self.inoperable[acceso] = True
        self.semaforos[acceso].cambiar_estado(Semaforo.ROJO_PARAPADEANTE)

    def es_inoperable(self, acceso):
        return self.inoperable.get(acceso, False)

    # ---- CASO 4: OBSTRUCCION / CHOQUE ----

    def marcar_obstruccion_salida(self, acceso):
        self.obstruccion_activa[acceso] = True

    # ---- CASO 7: CAMARA ----

    def marcar_camara_fallada(self, acceso):
        self.camara_operativa[acceso] = False

    # ---- CASO 1: EMERGENCIA ----

    def marcar_emergencia(self, acceso):
        self.emergencia_activa[acceso] = True

    def limpiar_emergencia(self, acceso):
        self.emergencia_activa[acceso] = False

    def hay_emergencia(self):
        return any(self.emergencia_activa.values())

    def acceso_emergencia_activo(self):
        for a in self.accesos:
            if self.emergencia_activa[a]:
                return a
        return None

    # ---- UTILIDADES ----

    def accesos_priorizables(self):
        """Retorna accesos que no estan inoperables."""
        return [a for a in self.accesos if not self.inoperable.get(a, False)]

    def accesos_con_camara(self):
        """Retorna accesos con camara operativa."""
        return [a for a in self.accesos if self.camara_operativa.get(a, True)]

    def accesos_sin_camara(self):
        """Retorna accesos con camara fallada."""
        return [a for a in self.accesos if not self.camara_operativa.get(a, True)]

    # ---- ESTADO ----

    def obtener_estado(self):
        accesos_data = {}
        for a in self.accesos:
            sem = self.semaforos[a]
            accesos_data[a] = {
                "estado": sem.estado,
                "parpadeando": sem.esta_parpadeando(),
                "tiempo_estado": round(sem.tiempo_en_estado, 1),
                "vehiculos": self.contar_vehiculos(a),
                "espera_max": round(self.obtener_tiempo_espera_maximo(a), 1),
                "espera_prom": round(self.obtener_tiempo_espera_promedio(a), 1),
                "velocidad_media": round(self.velocidad_media.get(a, 0), 1),
                "inoperable": self.inoperable.get(a, False),
                "camara_operativa": self.camara_operativa.get(a, True),
                "emergencia_activa": self.emergencia_activa.get(a, False),
                "obstruccion_activa": self.obstruccion_activa.get(a, False),
            }
        return {
            "tiempo": round(self.tiempo_simulacion, 1),
            "acceso_verde": self.acceso_verde,
            "accesos": accesos_data,
            "total_vehiculos": self.contar_vehiculos()
        }
