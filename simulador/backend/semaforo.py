class Semaforo:
    ROJO = "ROJO"
    AMARILLO = "AMARILLO"
    VERDE = "VERDE"

    def __init__(self):
        self.estado = self.ROJO
        self.tiempo_en_estado = 0.0

    def cambiar_estado(self, nuevo_estado):
        self.estado = nuevo_estado
        self.tiempo_en_estado = 0.0

    def actualizar(self, dt):
        self.tiempo_en_estado += dt

    def es_verde(self):
        return self.estado == self.VERDE

    def es_rojo(self):
        return self.estado == self.ROJO

    def reiniciar(self):
        self.estado = self.ROJO
        self.tiempo_en_estado = 0.0
