import random
import threading
import time
from flask import Flask, send_from_directory
from flask_socketio import SocketIO, emit
from interseccion import Interseccion, ACCESOS_4, ACCESOS_T, NORTE, SUR
from semaforo import Semaforo
from controlador import Controlador

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins='*')

int_4 = Interseccion(ACCESOS_4)
ctrl_4 = Controlador(ACCESOS_4)
int_t = Interseccion(ACCESOS_T)
ctrl_t = Controlador(ACCESOS_T)

DT = 0.5
PROBABILIDAD_SPAWN = 0.05
TASA_LIBERACION = 1
DURACION_AMARILLO = 2.0

int_4.semaforos[NORTE].cambiar_estado(Semaforo.VERDE)
int_4.acceso_verde = NORTE
int_t.semaforos[SUR].cambiar_estado(Semaforo.VERDE)
int_t.acceso_verde = SUR

def ejecutar_tick(interseccion, controlador):
    for a in interseccion.accesos:
        if random.random() < PROBABILIDAD_SPAWN:
            interseccion.agregar_vehiculo(a)

    interseccion.actualizar(DT)

    acceso_actual = interseccion.acceso_verde
    if acceso_actual is None:
        return

    semaforo_actual = interseccion.semaforos[acceso_actual]

    if semaforo_actual.estado == Semaforo.AMARILLO:
        if semaforo_actual.tiempo_en_estado >= DURACION_AMARILLO:
            semaforo_actual.cambiar_estado(Semaforo.ROJO)
            nuevo_acceso = interseccion.acceso_proximo
            interseccion.semaforos[nuevo_acceso].cambiar_estado(Semaforo.VERDE)
            interseccion.acceso_verde = nuevo_acceso
            interseccion.acceso_proximo = None
    elif semaforo_actual.estado == Semaforo.VERDE:
        for _ in range(TASA_LIBERACION):
            cola = interseccion.carriles[acceso_actual]
            if cola:
                cola.popleft()
                otros = [a for a in interseccion.accesos if a != acceso_actual]
                interseccion.agregar_vehiculo(random.choice(otros))

        decision = controlador.decidir(interseccion)
        if decision != acceso_actual:
            semaforo_actual.cambiar_estado(Semaforo.AMARILLO)
            interseccion.acceso_proximo = decision

def simulation_loop():
    while True:
        time.sleep(DT)
        ejecutar_tick(int_4, ctrl_4)
        ejecutar_tick(int_t, ctrl_t)
        socketio.emit('estado_4', int_4.obtener_estado())
        socketio.emit('estado_t', int_t.obtener_estado())

@app.route('/')
def index():
    return send_from_directory('..', 'frontend/index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('..', f'frontend/{path}')

if __name__ == '__main__':
    thread = threading.Thread(target=simulation_loop, daemon=True)
    thread.start()
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
