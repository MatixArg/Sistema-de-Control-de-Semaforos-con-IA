# Sistema de Control de Semáforos con IA

Sistema inteligente que optimiza el flujo vehicular mediante inteligencia artificial y visión por computadora.

## Descripción

Los semáforos tradicionales funcionan con tiempos fijos, lo que genera congestión innecesaria:
carriles con pocos vehículos permanecen en verde mientras otros con largas filas siguen esperando.

Este sistema analiza en tiempo real la cantidad de vehículos en cada acceso de una intersección
y ajusta dinámicamente los tiempos de los semáforos para reducir la congestión.

## Objetivos

- Detectar vehículos mediante visión por computadora
- Contabilizar vehículos por carril
- Analizar nivel de congestión
- Determinar qué semáforo debe recibir prioridad
- Evitar que un carril quede esperando indefinidamente (anti-starvation)

## Tecnologías

- **Backend**: Python, Flask, Flask-SocketIO
- **Frontend**: HTML5, CSS3, JavaScript (Canvas)
- **Visión**: OpenCV, YOLO (en desarrollo)
- **Control**: Algoritmo de priorización con anti-starvation

## Requisitos

- Python 3.8 o superior
- pip

## Instalación

```bash
pip install -r requirements.txt
```

## Uso

```bash
python simulador/backend/app.py
```

Abrir [http://localhost:5000](http://localhost:5000) en el navegador.

## Estructura del proyecto

```
sistema-inteligente/
├── simulador/
│   ├── backend/
│   │   ├── __init__.py
│   │   ├── semaforo.py       # Estados y temporización
│   │   ├── vehiculo.py       # Modelo de vehículo
│   │   ├── interseccion.py   # Gestión del cruce
│   │   ├── controlador.py    # Algoritmo de decisión
│   │   └── app.py            # Servidor web + loop simulación
│   └── frontend/
│       ├── index.html        # Interfaz web
│       ├── style.css         # Estilos
│       └── app.js            # Lógica cliente (Canvas + WebSocket)
├── deteccion/                # Visión por computadora (próximamente)
├── LICENSE
├── requirements.txt
└── README.md
```

## Algoritmo de control

La prioridad se calcula como:

```
prioridad = (cantidad_vehiculos * 2) + (tiempo_espera_maximo * 1.5)
```

- Mínimo de 5 segundos en verde por ciclo
- Máximo de 30 segundos en verde por ciclo
- Si un carril supera los 45 segundos de espera, recibe prioridad absoluta (anti-starvation)

## Roadmap

- [x] Estructura del proyecto y planificación
- [ ] Simulador base con semáforos y vehículos
- [ ] Algoritmo de priorización
- [ ] Visualización web en tiempo real
- [ ] Detección de vehículos con OpenCV + YOLO
- [ ] Integración con controladores reales

## Licencia

Todos los derechos reservados. Ver [LICENSE](LICENSE) para más información.
