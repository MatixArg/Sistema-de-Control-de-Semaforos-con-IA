from collections import deque
from semaforo import Semaforo
from vehiculo import Vehiculo

CARRIL_NORTE = "N"
CARRIL_SUR = "S"
CARRIL_ESTE = "E"
CARRIL_OESTE = "W"

TODOS_CARRILES = [CARRIL_NORTE, CARRIL_SUR, CARRIL_ESTE, CARRIL_OESTE]

class Interseccion:
    def __init__(self):
        self.carriles = {
            CARRIL_NORTE: deque(),
            CARRIL_SUR: deque(),
            CARRIL_ESTE: deque(),
            CARRIL_OESTE: deque()
        }
        self.semaforo_ns = Semaforo()
        self.semaforo_ew = Semaforo()
        self.grupo_verde = "NS"
        self.tiempo_simulacion = 0.0

    def agregar_vehiculo(self, carril):
        v = Vehiculo(carril)
        v.tiempo_llegada = self.tiempo_simulacion
        self.carriles[carril].append(v)
        return v

    def contar_vehiculos(self, carril=None):
        if carril:
            return len(self.carriles[carril])
        return sum(len(q) for q in self.carriles.values())

    def contar_vehiculos_grupo(self, grupo):
        if grupo == "NS":
            return len(self.carriles[CARRIL_NORTE]) + len(self.carriles[CARRIL_SUR])
        return len(self.carriles[CARRIL_ESTE]) + len(self.carriles[CARRIL_OESTE])

    def obtener_carriles_grupo(self, grupo):
        if grupo == "NS":
            return [CARRIL_NORTE, CARRIL_SUR]
        return [CARRIL_ESTE, CARRIL_OESTE]

    def obtener_tiempo_espera_maximo(self, grupo):
        max_espera = 0.0
        for c in self.obtener_carriles_grupo(grupo):
            for v in self.carriles[c]:
                if v.tiempo_espera > max_espera:
                    max_espera = v.tiempo_espera
        return max_espera

    def obtener_tiempo_espera_promedio(self, grupo):
        total = 0.0
        count = 0
        for c in self.obtener_carriles_grupo(grupo):
            for v in self.carriles[c]:
                total += v.tiempo_espera
                count += 1
        return total / count if count > 0 else 0.0

    def vaciar_carriles_grupo(self, grupo):
        total = 0
        for c in self.obtener_carriles_grupo(grupo):
            total += len(self.carriles[c])
            self.carriles[c].clear()
        return total

    def actualizar(self, dt):
        self.tiempo_simulacion += dt
        for cola in self.carriles.values():
            for v in cola:
                v.actualizar_espera(dt)
        self.semaforo_ns.actualizar(dt)
        self.semaforo_ew.actualizar(dt)

    def obtener_estado(self):
        return {
            "tiempo": round(self.tiempo_simulacion, 1),
            "grupo_verde": self.grupo_verde,
            "ns": {
                "estado": self.semaforo_ns.estado,
                "tiempo_estado": round(self.semaforo_ns.tiempo_en_estado, 1),
                "vehiculos": self.contar_vehiculos_grupo("NS"),
                "espera_max": round(self.obtener_tiempo_espera_maximo("NS"), 1),
                "espera_prom": round(self.obtener_tiempo_espera_promedio("NS"), 1)
            },
            "ew": {
                "estado": self.semaforo_ew.estado,
                "tiempo_estado": round(self.semaforo_ew.tiempo_en_estado, 1),
                "vehiculos": self.contar_vehiculos_grupo("EW"),
                "espera_max": round(self.obtener_tiempo_espera_maximo("EW"), 1),
                "espera_prom": round(self.obtener_tiempo_espera_promedio("EW"), 1)
            },
            "norte": len(self.carriles[CARRIL_NORTE]),
            "sur": len(self.carriles[CARRIL_SUR]),
            "este": len(self.carriles[CARRIL_ESTE]),
            "oeste": len(self.carriles[CARRIL_OESTE]),
            "total_vehiculos": self.contar_vehiculos()
        }
