import config
from semaforo import Semaforo
from maquina_estados import MaquinaEstados
from monitor_obstruccion import MonitorObstruccion
from detector_emergencia import DetectorEmergencia


class ControladorLogico:
    """Cerebro central del sistema. Implementa los 8 casos de negocio.
    
    Recibe frames JSON del modulo de IA y controla la maquina de estados
    para decidir que acceso debe estar en verde.
    """

    def __init__(self, interseccion, maquina_estados, monitor_obstruccion, detector_emergencia):
        self.interseccion = interseccion
        self.maquina = maquina_estados
        self.monitor = monitor_obstruccion
        self.detector = detector_emergencia

        self.tiempo_sin_trafico = 0.0
        self.ultimo_evento_log = ""

        # CASO 7: Control de ciclo de reinsercion para camaras falladas
        self.accesos_procesados_en_ciclo = []
        self.en_ventana_ciega = False
        self.tiempo_ventana_ciega = 0.0

    def _log(self, msg):
        if msg != self.ultimo_evento_log:
            print(f"  ⚙️ CTRL: {msg}")
            self.ultimo_evento_log = msg

    # ---- ENTRY POINT PRINCIPAL ----

    def procesar_frame(self, frame_ia, dt):
        """Procesa un frame de la IA y ejecuta las reglas de negocio."""
        inter = self.interseccion
        accesos_data = frame_ia.get("accesos", {})
        total = frame_ia.get("total_vehiculos", 0)

        # ---- PASO 1: CASO 1 - EMERGENCIA (prioridad mas alta) ----
        acceso_emergencia = self.detector.escanear(frame_ia, inter)
        if acceso_emergencia and inter.acceso_verde != acceso_emergencia:
            if inter.semaforos[acceso_emergencia].es_rojo():
                self.maquina.interrumpir_para_emergencia(acceso_emergencia)
                self._aplicar_verde_inmediato(acceso_emergencia)
                return

        # ---- PASO 2: ACTUALIZAR MONITOR DE OBSTRUCCION ----
        self.monitor.analizar(inter, dt, frame_ia)

        # ---- PASO 3: CASO 2 - TRAFICO CERO (REPOSO) ----
        if total == 0:
            self.tiempo_sin_trafico += dt
            if self.tiempo_sin_trafico >= 2.0 and self.maquina.fase != MaquinaEstados.REPOSO:
                self._ir_a_reposo()
            return
        else:
            self.tiempo_sin_trafico = 0.0

            # Salir de reposo si el primer auto aparece
            if self.maquina.fase == MaquinaEstados.REPOSO:
                primer_acceso = self._primer_acceso_con_vehiculos(inter, accesos_data)
                if primer_acceso:
                    self._log(f"CASO 2 - Trafico detectado en {primer_acceso}. Activando verde.")
                    inter.semaforos[primer_acceso].cambiar_estado(Semaforo.VERDE)
                    inter.acceso_verde = primer_acceso
                    self.maquina.iniciar(primer_acceso)
                return

        # ---- PASO 4: ACTUALIZAR HISTORIAL (para CASO 3) ----
        for a in inter.accesos:
            inter.actualizar_historial(a)

        # ---- PASO 5: SI ESTA EN VERDE, EVALUAR REGLAS DE NEGOCIO ----
        if self.maquina.fase == MaquinaEstados.VERDE:
            self._evaluar_verde(frame_ia, dt)

        # ---- PASO 6: EJECUTAR MAQUINA DE ESTADOS ----
        nuevo_acceso, evento = self.maquina.tick(dt)
        if nuevo_acceso:
            self._aplicar_verde(nuevo_acceso)

    # ---- EVALUACION EN VERDE ----

    def _evaluar_verde(self, frame_ia, dt):
        inter = self.interseccion
        acceso_actual = inter.acceso_verde
        if acceso_actual is None:
            return

        sem_actual = inter.semaforos[acceso_actual]
        tiempo_verde = sem_actual.tiempo_en_estado

        # CASO 3: Detectar occlusion y extender verde
        if inter.detectar_oclusion(acceso_actual):
            self._log(f"🔍 CASO 3 - OCLUSION: Conteo subio abruptamente en {acceso_actual}. Extendiendo verde.")

        # CASO 5: Verificar vehiculo pesado cruzando (flujo absoluto)
        pesado = inter.verificar_vehiculo_cruzando(acceso_actual)
        if pesado:
            self._log(f"🐢 CASO 5 - FLUJO ABSOLUTO: Vehiculo pesado cruzando en {acceso_actual}. Manteniendo verde.")

        # CASO 5: Calcular tiempo estimado por peso visual
        tiempo_estimado = inter.calcular_tiempo_estimado_verde(acceso_actual)

        # Evaluar si debe transicionar
        if self._deberia_transicionar(acceso_actual, tiempo_verde, tiempo_estimado, frame_ia, pesado):
            proximo = self._seleccionar_proximo_acceso(frame_ia)
            if proximo and proximo != acceso_actual:
                self.maquina.iniciar_transicion(proximo)
                self._log(f"🔄 Transicionando: {acceso_actual} -> {proximo}")

    def _deberia_transicionar(self, acceso_actual, tiempo_verde, tiempo_estimado, frame_ia, pesado_cruzando=False):
        """Evalua si es momento de cambiar de acceso en verde."""
        # Nunca cortar antes del minimo
        if tiempo_verde < config.MIN_GREEN:
            return False

        # Si hay vehiculo pesado cruzando, mantener verde (CASO 5 flujo absoluto)
        if pesado_cruzando:
            return False

        # Si se detecto occlusion, extender (CASO 3)
        if self.interseccion.detectar_oclusion(acceso_actual):
            return False

        # Anti-starvation: si otro acceso supero el limite, cambiar
        for a in self.interseccion.accesos:
            if a != acceso_actual:
                espera = self.interseccion.obtener_tiempo_espera_maximo(a)
                if espera >= config.STARVATION_LIMIT:
                    self._log(f"⏰ STARVATION: {a} espero {espera:.0f}s. Forzando cambio.")
                    return True

        # Maximo tiempo de verde alcanzado
        if tiempo_verde >= config.MAX_GREEN:
            return True

        # Tiempo estimado por peso visual alcanzado (CASO 5)
        if tiempo_verde >= tiempo_estimado:
            return True

        # Evaluar prioridad: comparar puntaje del actual vs otros
        puntaje_actual = self._calcular_puntaje_acceso(acceso_actual, frame_ia)
        for a in self.interseccion.accesos:
            if a == acceso_actual:
                continue
            if self.interseccion.es_inoperable(a):
                continue
            puntaje_otro = self._calcular_puntaje_acceso(a, frame_ia)
            if puntaje_otro > puntaje_actual * 1.5:
                return True

        return False

    # ---- SELECCION DE PROXIMO ACCESO ----

    def _seleccionar_proximo_acceso(self, frame_ia):
        """Elige el proximo acceso que debe recibir verde.
        
        CASO 7: Si hay camaras falladas, inserta ventana de 30s para acceso ciego.
        """
        inter = self.interseccion

        # CASO 7: Verificar si estamos en ventana ciega
        if self.en_ventana_ciega:
            self.tiempo_ventana_ciega += config.DT
            if self.tiempo_ventana_ciega >= config.VENTANA_CIEGA:
                self.en_ventana_ciega = False
                self.tiempo_ventana_ciega = 0.0
                self._log(f"📷 CASO 7 - Ventana ciega finalizada. Volviendo a control IA.")
            else:
                acceso_ciego = inter.accesos_sin_camara()
                if acceso_ciego:
                    self._log(f"📷 CASO 7 - Ventana ciega: {acceso_ciego[0]} por {config.VENTANA_CIEGA}s")
                    return acceso_ciego[0]

        # Evaluar prioridades de accesos con camara operativa
        accesos_priorizables = []
        for a in inter.accesos_priorizables():
            if not inter.camara_operativa.get(a, True):
                continue
            if a == inter.acceso_verde:
                continue
            accesos_priorizables.append((self._calcular_puntaje_acceso(a, frame_ia), a))

        if not accesos_priorizables:
            # Si no hay accesos priorizables, verificar si hay accesos sin camara
            if inter.accesos_sin_camara():
                self.en_ventana_ciega = True
                self.tiempo_ventana_ciega = 0.0
                self._log(f"📷 CASO 7 - Todos los carriles IA procesados. Insertando ventana de {config.VENTANA_CIEGA}s para acceso ciego.")
                return inter.accesos_sin_camara()[0]
            return None

        # Elegir el de mayor puntaje
        accesos_priorizables.sort(reverse=True, key=lambda x: x[0])
        return accesos_priorizables[0][1]

    def _calcular_puntaje_acceso(self, acceso, frame_ia):
        """Calcula prioridad: cantidad * peso + espera_max * peso."""
        cant = self.interseccion.contar_vehiculos(acceso)
        espera = self.interseccion.obtener_tiempo_espera_maximo(acceso)

        # Penalizar si hay obstruccion activa
        penalidad = 0
        if self.interseccion.obstruccion_activa.get(acceso, False):
            penalidad = 50
        if self.interseccion.es_inoperable(acceso):
            penalidad = 100

        puntaje = (cant * 2.0) + (espera * 1.5) - penalidad
        return max(0, puntaje)

    # ---- APLICAR CAMBIOS FISICOS ----

    def _aplicar_verde(self, acceso):
        """Aplica el estado VERDE a un acceso y ROJO a los demas."""
        inter = self.interseccion
        for a in inter.accesos:
            if a == acceso:
                if not inter.semaforos[a].es_verde():
                    inter.semaforos[a].cambiar_estado(Semaforo.VERDE)
            else:
                if not inter.semaforos[a].es_rojo() and not inter.semaforos[a].esta_parpadeando():
                    inter.semaforos[a].cambiar_estado(Semaforo.ROJO)
        inter.acceso_verde = acceso

        # Limpiar emergencia si estaba activa
        if inter.emergencia_activa.get(acceso, False):
            self.detector.limpiar_emergencia_atendida(inter, acceso)

    def _aplicar_verde_inmediato(self, acceso):
        """CASO 1: Aplica verde inmediatamente para emergencia (salta amarillo)."""
        inter = self.interseccion
        for a in inter.accesos:
            if a == acceso:
                inter.semaforos[a].cambiar_estado(Semaforo.VERDE)
            else:
                inter.semaforos[a].cambiar_estado(Semaforo.ROJO)
        inter.acceso_verde = acceso
        self._log(f"🚨 VERDE INMEDIATO para EMERGENCIA en acceso {acceso}")

    def _ir_a_reposo(self):
        """CASO 2: Pone todos los semaforos en ROJO."""
        inter = self.interseccion
        for a in inter.accesos:
            inter.semaforos[a].cambiar_estado(Semaforo.ROJO)
        inter.acceso_verde = None
        self.maquina.volver_a_reposo()

    def _primer_acceso_con_vehiculos(self, inter, accesos_data):
        """Encuentra el primer acceso con vehiculos (para salir de reposo)."""
        for a in inter.accesos:
            data = accesos_data.get(a, {})
            if data.get("conteo", 0) > 0:
                return a
        return None
