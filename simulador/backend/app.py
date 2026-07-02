import random
import threading
import time
from flask import Flask, send_from_directory
from flask_socketio import SocketIO, emit
from interseccion import Interseccion, CARRIL_NORTE, CARRIL_SUR, CARRIL_ESTE, CARRIL_OESTE, TODOS_CARRILES
from semaforo import Semaforo
from controlador import Controlador

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins='*')

interseccion = Interseccion()
controlador = Controlador()

DT = 0.5
PROBABILIDAD_SPAWN = 0.3
TASA_LIBERACION = 2
DURACION_AMARILLO = 2.0

interseccion.semaforo_ns.cambiar_estado(Semaforo.VERDE)
interseccion.grupo_verde = "NS"

def simulation_loop():
    while True:
        time.sleep(DT)

        for carril in TODOS_CARRILES:
            if random.random() < PROBABILIDAD_SPAWN:
                interseccion.agregar_vehiculo(carril)

        interseccion.actualizar(DT)

        grupo_actual = interseccion.grupo_verde
        semaforo_actual = interseccion.semaforo_ns if grupo_actual == "NS" else interseccion.semaforo_ew
        semaforo_otro = interseccion.semaforo_ew if grupo_actual == "NS" else interseccion.semaforo_ns

        if semaforo_actual.estado == Semaforo.AMARILLO:
            if semaforo_actual.tiempo_en_estado >= DURACION_AMARILLO:
                semaforo_actual.cambiar_estado(Semaforo.ROJO)
                semaforo_otro.cambiar_estado(Semaforo.VERDE)
                nuevo_grupo = "EW" if grupo_actual == "NS" else "NS"
                interseccion.grupo_verde = nuevo_grupo
        elif semaforo_actual.estado == Semaforo.VERDE:
            for carril in interseccion.obtener_carriles_grupo(grupo_actual):
                for _ in range(TASA_LIBERACION):
                    if interseccion.carriles[carril]:
                        interseccion.carriles[carril].popleft()

            decision = controlador.decidir(interseccion)
            if decision != grupo_actual:
                semaforo_actual.cambiar_estado(Semaforo.AMARILLO)

        socketio.emit('estado', interseccion.obtener_estado())

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
