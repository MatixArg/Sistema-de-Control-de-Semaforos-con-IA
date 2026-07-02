from collections import deque
from semaforo import Semaforo
from vehiculo import Vehiculo

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

    def agregar_vehiculo(self, acceso):
        v = Vehiculo(acceso)
        v.tiempo_llegada = self.tiempo_simulacion
        self.carriles[acceso].append(v)
        return v

    def contar_vehiculos(self, acceso=None):
        if acceso:
            return len(self.carriles[acceso])
        return sum(len(q) for q in self.carriles.values())

    def obtener_tiempo_espera_maximo(self, acceso):
        max_espera = 0.0
        for v in self.carriles[acceso]:
            if v.tiempo_espera > max_espera:
                max_espera = v.tiempo_espera
        return max_espera

    def obtener_tiempo_espera_promedio(self, acceso):
        total = 0.0
        count = 0
        for v in self.carriles[acceso]:
            total += v.tiempo_espera
            count += 1
        return total / count if count > 0 else 0.0

    def vaciar_acceso(self, acceso):
        count = len(self.carriles[acceso])
        self.carriles[acceso].clear()
        return count

    def actualizar(self, dt):
        self.tiempo_simulacion += dt
        for cola in self.carriles.values():
            for v in cola:
                v.actualizar_espera(dt)
        for s in self.semaforos.values():
            s.actualizar(dt)

    def obtener_estado(self):
        accesos_data = {}
        for a in self.accesos:
            sem = self.semaforos[a]
            accesos_data[a] = {
                "estado": sem.estado,
                "tiempo_estado": round(sem.tiempo_en_estado, 1),
                "vehiculos": self.contar_vehiculos(a),
                "espera_max": round(self.obtener_tiempo_espera_maximo(a), 1),
                "espera_prom": round(self.obtener_tiempo_espera_promedio(a), 1)
            }
        return {
            "tiempo": round(self.tiempo_simulacion, 1),
            "acceso_verde": self.acceso_verde,
            "accesos": accesos_data,
            "total_vehiculos": self.contar_vehiculos()
        }
