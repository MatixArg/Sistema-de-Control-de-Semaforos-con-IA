import random
import config
from interseccion import Interseccion, NORTE, SUR, ESTE, OESTE


class ModuloIASimulado:
    """Simula el modulo de vision por computadora (YOLO + OpenCV).
    
    Emula:
      - Deteccion y conteo de vehiculos
      - Clasificacion por tipo (moto, auto, bus, truck, ambulancia, patrullero)
      - Medicion de velocidad
      - Deteccion de balizas de emergencia
      - Deteccion de oclusiones (camion tapando autos)
      - Fallo de camara
      - Vehiculos cruzando la linea de parada
    """

    def __init__(self, interseccion):
        self.interseccion = interseccion
        self.frame_count = 0
        self.emergencia_activa = False
        self.camara_fallada = None  # acceso con camara fallada o None

    def detectar(self):
        """Ejecuta un ciclo de deteccion simulado.
        
        Retorna un dict con la estructura JSON que recibiria el controlador logico.
        """
        self.frame_count += 1
        inter = self.interseccion
        accesos_data = {}

        for a in inter.accesos:
            # Simular si la camara esta operativa
            if not inter.camara_operativa.get(a, True):
                accesos_data[a] = {
                    "conteo": -1,
                    "velocidad_media": -1,
                    "tipo_vehiculos": [],
                    "tiene_emergencia": False,
                    "tiene_balizas": False,
                    "camara_operativa": False,
                    "vehiculo_cruzando_linea": False,
                    "hay_obstruccion_salida": False
                }
                continue

            cola = inter.carriles[a]
            conteo = len(cola)
            tipos = [v.tipo for v in cola]
            tiene_emergencia = any(v.es_emergencia for v in cola)
            tiene_balizas = any(v.tiene_balizas for v in cola)

            # Simular velocidad: mas lento si hay muchos autos o si hay obstruccion
            if inter.obstruccion_activa.get(a, False):
                vel_base = 0.0
            elif inter.inoperable.get(a, False):
                vel_base = random.uniform(0, 2)
            elif conteo > 10:
                vel_base = random.uniform(5, 15)
            elif conteo > 5:
                vel_base = random.uniform(15, 30)
            else:
                vel_base = random.uniform(30, 50)

            inter.velocidad_media[a] = vel_base

            # Simular vehiculo cruzando la linea (solo si el semaforo esta verde)
            cruzando = False
            if inter.acceso_verde == a and inter.semaforos[a].es_verde():
                if cola and random.random() < 0.3:
                    v = cola[0]
                    v.cruzando_linea = True
                    if v.es_pesado():
                        cruzando = True
                        inter.cruzando_pesado[a] = True
                    else:
                        inter.cruzando_pesado[a] = False

            accesos_data[a] = {
                "conteo": conteo,
                "velocidad_media": round(vel_base, 1),
                "tipo_vehiculos": tipos,
                "tiene_emergencia": tiene_emergencia,
                "tiene_balizas": tiene_balizas,
                "camara_operativa": True,
                "vehiculo_cruzando_linea": cruzando,
                "hay_obstruccion_salida": inter.obstruccion_activa.get(a, False)
            }

        return {
            "frame": self.frame_count,
            "timestamp": round(inter.tiempo_simulacion, 1),
            "accesos": accesos_data,
            "total_vehiculos": inter.contar_vehiculos()
        }

    def spawn_vehiculos(self):
        """Genera vehiculos aleatoriamente en los accesos."""
        inter = self.interseccion

        for a in inter.accesos:
            if not inter.camara_operativa.get(a, True):
                continue
            if inter.inoperable.get(a, False):
                continue

            # Spawn normal
            if random.random() < config.PROB_SPAWN:
                tipo = self._generar_tipo()
                es_emergencia = tipo in ("ambulancia", "patrullero")
                tiene_balizas = es_emergencia
                inter.agregar_vehiculo(a, tipo, tiene_balizas, es_emergencia)

            # Spawn de emergencia (CASO 1) independiente
            if random.random() < config.PROB_EMERGENCIA:
                tipo_emergencia = random.choice(["ambulancia", "patrullero"])
                inter.agregar_vehiculo(a, tipo_emergencia, True, True)

    def _generar_tipo(self):
        r = random.random()
        if r < 0.05:
            return "ambulancia" if random.random() < 0.3 else "patrullero"
        if r < 0.15:
            return "bus"
        if r < 0.25:
            return "truck"
        if r < 0.40:
            return "moto"
        return "auto"

    def simular_fallo_camara(self):
        """Simula aleatoriamente fallo de camara en algun acceso."""
        inter = self.interseccion
        if random.random() < config.PROB_CAMARA_FALLA:
            accesos_operativos = [a for a in inter.accesos if inter.camara_operativa.get(a, True)]
            if accesos_operativos:
                affected = random.choice(accesos_operativos)
                inter.marcar_camara_fallada(affected)
                print(f"  [SIM] ⚠️ CAMARA FALLADA en acceso {affected}")

    def recuperar_camara(self, acceso):
        """Recupera una camara que habia fallado."""
        self.interseccion.camara_operativa[acceso] = True
        print(f"  [SIM] ✅ CAMARA RECUPERADA en acceso {acceso}")
