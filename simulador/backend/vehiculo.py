import config


class Vehiculo:
    _contador = 0

    TIPOS = ("moto", "auto", "bus", "truck", "ambulancia", "patrullero")

    def __init__(self, carril, tipo="auto", tiene_balizas=False, es_emergencia=False):
        Vehiculo._contador += 1
        self.id = Vehiculo._contador
        self.carril = carril
        self.tipo = tipo                            # moto, auto, bus, truck, ambulancia, patrullero
        self.tiene_balizas = tiene_balizas
        self.es_emergencia = es_emergencia          # ambulancia o patrullero
        self.velocidad_actual = 0.0                 # km/h simulada
        self.tiempo_llegada = 0.0
        self.tiempo_espera = 0.0
        self.cruzando_linea = False                 # CASO 5 - flujo absoluto

    def actualizar_espera(self, dt):
        self.tiempo_espera += dt

    def obtener_peso_visual(self):
        return config.PESOS_VISUALES.get(self.tipo, 3)

    def es_pesado(self):
        return self.tipo in ("bus", "truck")
