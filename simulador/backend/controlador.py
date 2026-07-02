class Controlador:
    def __init__(self, peso_cantidad=2.0, peso_espera=1.5,
                 verde_minimo=5, verde_maximo=30,
                 starvation_limite=45):
        self.peso_cantidad = peso_cantidad
        self.peso_espera = peso_espera
        self.verde_minimo = verde_minimo
        self.verde_maximo = verde_maximo
        self.starvation_limite = starvation_limite

    def calcular_puntaje(self, interseccion, grupo):
        cantidad = interseccion.contar_vehiculos_grupo(grupo)
        espera_max = interseccion.obtener_tiempo_espera_maximo(grupo)
        return (cantidad * self.peso_cantidad) + (espera_max * self.peso_espera)

    def detectar_starvation(self, interseccion):
        for grupo in ["NS", "EW"]:
            espera_max = interseccion.obtener_tiempo_espera_maximo(grupo)
            if espera_max >= self.starvation_limite:
                return grupo
        return None

    def calcular_prioridad(self, interseccion):
        starvation = self.detectar_starvation(interseccion)
        if starvation:
            return starvation

        puntaje_ns = self.calcular_puntaje(interseccion, "NS")
        puntaje_ew = self.calcular_puntaje(interseccion, "EW")

        return "NS" if puntaje_ns >= puntaje_ew else "EW"

    def deberia_cambiar(self, interseccion):
        grupo_actual = interseccion.grupo_verde

        if grupo_actual == "NS":
            tiempo_verde = interseccion.semaforo_ns.tiempo_en_estado
        else:
            tiempo_verde = interseccion.semaforo_ew.tiempo_en_estado

        if tiempo_verde < self.verde_minimo:
            return False
        if tiempo_verde >= self.verde_maximo:
            return True

        return self.calcular_prioridad(interseccion) != grupo_actual

    def decidir(self, interseccion):
        if self.deberia_cambiar(interseccion):
            return self.calcular_prioridad(interseccion)
        return interseccion.grupo_verde
