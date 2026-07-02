class Semaforo:
    ROJO = "ROJO"
    AMARILLO = "AMARILLO"
    VERDE = "VERDE"
    ROJO_PARAPADEANTE = "ROJO_PARAPADEANTE"

    def __init__(self):
        self.estado = self.ROJO
        self.tiempo_en_estado = 0.0
        self.flash_encendido = False

    def cambiar_estado(self, nuevo_estado):
        self.estado = nuevo_estado
        self.tiempo_en_estado = 0.0

    def actualizar(self, dt):
        self.tiempo_en_estado += dt
        if self.estado == self.ROJO_PARAPADEANTE:
            self.flash_encendido = not self.flash_encendido

    def es_verde(self):
        return self.estado == self.VERDE

    def es_rojo(self):
        return self.estado == self.ROJO

    def esta_parpadeando(self):
        return self.estado == self.ROJO_PARAPADEANTE

    def reiniciar(self):
        self.estado = self.ROJO
        self.tiempo_en_estado = 0.0
        self.flash_encendido = False
