class Vehiculo:
    _contador = 0

    def __init__(self, carril):
        Vehiculo._contador += 1
        self.id = Vehiculo._contador
        self.carril = carril
        self.tiempo_llegada = 0.0
        self.tiempo_espera = 0.0

    def actualizar_espera(self, dt):
        self.tiempo_espera += dt
