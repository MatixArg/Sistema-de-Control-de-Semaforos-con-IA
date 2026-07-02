class Controlador:
    def __init__(self, accesos, peso_cantidad=2.0, peso_espera=1.5,
                 verde_minimo=5, verde_maximo=30, starvation_limite=45):
        self.accesos = accesos
        self.peso_cantidad = peso_cantidad
        self.peso_espera = peso_espera
        self.verde_minimo = verde_minimo
        self.verde_maximo = verde_maximo
        self.starvation_limite = starvation_limite

    def calcular_puntaje(self, interseccion, acceso):
        cantidad = interseccion.contar_vehiculos(acceso)
        espera_max = interseccion.obtener_tiempo_espera_maximo(acceso)
        return (cantidad * self.peso_cantidad) + (espera_max * self.peso_espera)

    def detectar_starvation(self, interseccion):
        for a in self.accesos:
            if interseccion.obtener_tiempo_espera_maximo(a) >= self.starvation_limite:
                return a
        return None

    def decidir(self, interseccion):
        starvation = self.detectar_starvation(interseccion)
        if starvation:
            return starvation

        puntajes = {a: self.calcular_puntaje(interseccion, a) for a in self.accesos}
        mejor_acceso = max(puntajes, key=puntajes.get)
        acceso_actual = interseccion.acceso_verde

        if acceso_actual is None:
            return mejor_acceso

        semaforo_actual = interseccion.semaforos[acceso_actual]

        if semaforo_actual.tiempo_en_estado < self.verde_minimo:
            return acceso_actual
        if semaforo_actual.tiempo_en_estado >= self.verde_maximo:
            return mejor_acceso
        if mejor_acceso != acceso_actual:
            if puntajes[mejor_acceso] > puntajes[acceso_actual] * 1.2:
                return mejor_acceso

        return acceso_actual
