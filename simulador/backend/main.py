import random
import threading
import time
from flask import Flask, send_from_directory
from flask_socketio import SocketIO, emit

import config
from interseccion import Interseccion, ACCESOS_4, ACCESOS_T, NORTE, SUR
from semaforo import Semaforo
from maquina_estados import MaquinaEstados
from modulo_ia_simulado import ModuloIASimulado
from monitor_obstruccion import MonitorObstruccion
from detector_emergencia import DetectorEmergencia
from controlador_logico import ControladorLogico

# ---- INICIALIZACION ----

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins='*')

# Intersecciones
int_4 = Interseccion(ACCESOS_4)
int_t = Interseccion(ACCESOS_T)

# Maquinas de estado
mq_4 = MaquinaEstados()
mq_t = MaquinaEstados()

# Monitores de obstruccion
mon_4 = MonitorObstruccion()
mon_t = MonitorObstruccion()

# Modulos de IA simulados
ia_4 = ModuloIASimulado(int_4)
ia_t = ModuloIASimulado(int_t)

# Detectores de emergencia
det_4 = DetectorEmergencia(None)
det_t = DetectorEmergencia(None)

# Controladores logicos
ctrl_4 = ControladorLogico(int_4, mq_4, mon_4, det_4)
ctrl_t = ControladorLogico(int_t, mq_t, mon_t, det_t)

# Vincular detectores con sus controladores
det_4.controlador = ctrl_4
det_t.controlador = ctrl_t

# Estado inicial: NORTE en verde para 4-vias, SUR en verde para T
int_4.semaforos[NORTE].cambiar_estado(Semaforo.VERDE)
int_4.acceso_verde = NORTE
int_t.semaforos[SUR].cambiar_estado(Semaforo.VERDE)
int_t.acceso_verde = SUR

# Inicializar maquinas de estado
mq_4.iniciar(NORTE)
mq_t.iniciar(SUR)


# ---- FUNCIONES AUXILIARES ----

def log_separador(titulo):
    print(f"\n{'='*70}")
    print(f"  {titulo}")
    print(f"{'='*70}")


def ejecutar_tick(interseccion, ia, controlador, nombre):
    """Ejecuta un tick completo de simulacion para una interseccion."""
    # 1. Spawn vehiculos
    ia.spawn_vehiculos()

    # 2. Simular fallo de camara (CASO 7)
    ia.simular_fallo_camara()

    # 3. Obtener frame de IA
    frame = ia.detectar()

    # 4. Procesar frame en el controlador logico (aplica todas las reglas)
    controlador.procesar_frame(frame, config.DT)

    # 5. Simular paso de vehiculos por el carril en verde
    acceso_verde = interseccion.acceso_verde
    if acceso_verde and interseccion.semaforos[acceso_verde].es_verde():
        for _ in range(config.TASA_LIBERACION):
            cola = interseccion.carriles[acceso_verde]
            if cola:
                cola.popleft()
                otros = [a for a in interseccion.accesos if a != acceso_verde]
                if otros:
                    interseccion.agregar_vehiculo(random.choice(otros), tipo="auto")

    return frame


# ---- LOOP DE SIMULACION ----

def simulation_loop():
    while True:
        time.sleep(config.DT)

        log_separador(f"TICK - Tiempo: {int_4.tiempo_simulacion:.0f}s")

        # Ejecutar tick para 4-vias
        print(f"\n  📍 Interseccion 4 Vías:")
        frame_4 = ejecutar_tick(int_4, ia_4, ctrl_4, "4V")

        # Ejecutar tick para T
        print(f"\n  📍 Interseccion T (3 Vías):")
        frame_t = ejecutar_tick(int_t, ia_t, ctrl_t, "T")

        # Mostrar estado resumido
        print(f"\n  📊 Estado 4V: Verde={int_4.acceso_verde} | "
              f"Total={int_4.contar_vehiculos()} | "
              f"Fase={mq_4.fase}")
        print(f"  📊 Estado T:  Verde={int_t.acceso_verde} | "
              f"Total={int_t.contar_vehiculos()} | "
              f"Fase={mq_t.fase}")

        # Emitir a traves de WebSocket
        socketio.emit('estado_4', int_4.obtener_estado())
        socketio.emit('estado_t', int_t.obtener_estado())


# ---- RUTAS FLASK ----

@app.route('/')
def index():
    return send_from_directory('..', 'frontend/index.html')


@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('..', f'frontend/{path}')


# ---- ENTRY POINT ----

if __name__ == '__main__':
    print(f"\n{'='*70}")
    print(f"  SISTEMA INTELIGENTE DE CONTROL DE SEMAFOROS")
    print(f"  Modo: Simulacion con 2 intersecciones")
    print(f"  DT: {config.DT}s | Max Green: {config.MAX_GREEN}s | Min Green: {config.MIN_GREEN}s")
    print(f"{'='*70}\n")

    thread = threading.Thread(target=simulation_loop, daemon=True)
    thread.start()
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
