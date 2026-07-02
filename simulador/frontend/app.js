const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');

const CX = 300, CY = 300;
const ANCHO_CALLE = 80;
const MITAD_CALLE = ANCHO_CALLE / 2;
const LARGO_CARRIL = 200;
const RADIO_SEMAFORO = 12;
const TAMANO_VEHICULO = 10;

let estado = null;

const socket = io();

socket.on('connect', () => {
    document.getElementById('status').textContent = 'Conectado';
    document.getElementById('status').className = 'status-conectado';
});

socket.on('disconnect', () => {
    document.getElementById('status').textContent = 'Desconectado';
    document.getElementById('status').className = 'status-desconectado';
});

socket.on('estado', (data) => {
    estado = data;
    actualizarPanel(data);
    dibujar();
});

function actualizarPanel(data) {
    document.getElementById('ns-estado').textContent = data.ns.estado;
    document.getElementById('ns-estado').className = 'valor estado ' + data.ns.estado.toLowerCase();
    document.getElementById('ns-vehiculos').textContent = data.ns.vehiculos;
    document.getElementById('ns-espera-max').textContent = data.ns.espera_max + 's';
    document.getElementById('ns-espera-prom').textContent = data.ns.espera_prom + 's';
    document.getElementById('ns-tiempo-verde').textContent = data.ns.tiempo_estado + 's';

    document.getElementById('ew-estado').textContent = data.ew.estado;
    document.getElementById('ew-estado').className = 'valor estado ' + data.ew.estado.toLowerCase();
    document.getElementById('ew-vehiculos').textContent = data.ew.vehiculos;
    document.getElementById('ew-espera-max').textContent = data.ew.espera_max + 's';
    document.getElementById('ew-espera-prom').textContent = data.ew.espera_prom + 's';
    document.getElementById('ew-tiempo-verde').textContent = data.ew.tiempo_estado + 's';

    document.getElementById('total-vehiculos').textContent = data.total_vehiculos;
    document.getElementById('tiempo-simulacion').textContent = data.tiempo + 's';
    document.getElementById('grupo-verde').textContent = data.grupo_verde;
}

function dibujar() {
    ctx.clearRect(0, 0, 600, 600);

    dibujarFondo();
    dibujarCarriles();
    dibujarInterseccion();
    dibujarSemaforos();
    dibujarVehiculos();
    dibujarRotulos();
}

function dibujarFondo() {
    ctx.fillStyle = '#3d3d5c';
    ctx.fillRect(0, 0, 600, 600);

    ctx.fillStyle = '#2d2d44';
    ctx.fillRect(0, CY - MITAD_CALLE, CX - MITAD_CALLE, ANCHO_CALLE);
    ctx.fillRect(CX + MITAD_CALLE, CY - MITAD_CALLE, CX - MITAD_CALLE, ANCHO_CALLE);
    ctx.fillRect(CX - MITAD_CALLE, 0, ANCHO_CALLE, CY - MITAD_CALLE);
    ctx.fillRect(CX - MITAD_CALLE, CY + MITAD_CALLE, ANCHO_CALLE, CY - MITAD_CALLE);
}

function dibujarCarriles() {
    ctx.strokeStyle = '#5a5a7a';
    ctx.lineWidth = 2;
    ctx.setLineDash([8, 6]);

    ctx.beginPath();
    ctx.moveTo(CX, 0);
    ctx.lineTo(CX, CY - MITAD_CALLE);
    ctx.stroke();

    ctx.beginPath();
    ctx.moveTo(CX, CY + MITAD_CALLE);
    ctx.lineTo(CX, 600);
    ctx.stroke();

    ctx.beginPath();
    ctx.moveTo(0, CY);
    ctx.lineTo(CX - MITAD_CALLE, CY);
    ctx.stroke();

    ctx.beginPath();
    ctx.moveTo(CX + MITAD_CALLE, CY);
    ctx.lineTo(600, CY);
    ctx.stroke();

    ctx.setLineDash([]);
}

function dibujarInterseccion() {
    ctx.fillStyle = '#3d3d5c';
    ctx.fillRect(CX - MITAD_CALLE, CY - MITAD_CALLE, ANCHO_CALLE, ANCHO_CALLE);

    ctx.strokeStyle = '#5a5a7a';
    ctx.lineWidth = 2;
    ctx.strokeRect(CX - MITAD_CALLE, CY - MITAD_CALLE, ANCHO_CALLE, ANCHO_CALLE);
}

function dibujarSemaforo(x, y, data, vertical) {
    const cx = vertical ? RADIO_SEMAFORO : 0;
    const cy = vertical ? 0 : RADIO_SEMAFORO;

    ctx.strokeStyle = '#444';
    ctx.lineWidth = 2;
    ctx.fillStyle = '#222';
    ctx.beginPath();
    if (vertical) {
        ctx.roundRect(x - RADIO_SEMAFORO, y - RADIO_SEMAFORO * 3 - 4, RADIO_SEMAFORO * 2, RADIO_SEMAFORO * 6 + 8, 4);
    } else {
        ctx.roundRect(x - RADIO_SEMAFORO * 3 - 4, y - RADIO_SEMAFORO, RADIO_SEMAFORO * 6 + 8, RADIO_SEMAFORO * 2, 4);
    }
    ctx.fill();
    ctx.stroke();

    const colores = [data.estado === 'ROJO' ? '#ff3333' : '#440000',
                     data.estado === 'AMARILLO' ? '#ffcc00' : '#443300',
                     data.estado === 'VERDE' ? '#33ff33' : '#004400'];

    const posiciones = vertical ?
        [y - RADIO_SEMAFORO * 2, y, y + RADIO_SEMAFORO * 2] :
        [x - RADIO_SEMAFORO * 2, x, x + RADIO_SEMAFORO * 2];

    for (let i = 0; i < 3; i++) {
        ctx.beginPath();
        ctx.arc(vertical ? x : posiciones[i], vertical ? posiciones[i] : y, RADIO_SEMAFORO - 2, 0, Math.PI * 2);
        ctx.fillStyle = colores[i];
        ctx.fill();
        if (colores[i] !== '#440000' && colores[i] !== '#443300' && colores[i] !== '#004400') {
            ctx.shadowColor = colores[i];
            ctx.shadowBlur = 8;
            ctx.fill();
            ctx.shadowBlur = 0;
        }
    }
}

function dibujarSemaforos() {
    if (!estado) return;

    const cx = CX, cy = CY;

    dibujarSemaforo(cx, cy - MITAD_CALLE - 10, estado.ns, true);
    dibujarSemaforo(cx, cy + MITAD_CALLE + 10, estado.ns, true);
    dibujarSemaforo(cx - MITAD_CALLE - 10, cy, estado.ew, false);
    dibujarSemaforo(cx + MITAD_CALLE + 10, cy, estado.ew, false);

    ctx.shadowBlur = 0;
}

function dibujarVehiculos() {
    if (!estado) return;

    const separacion = 22;

    function dibujarFila(cx, cy, cantidad, dx, dy, girar) {
        const max_visibles = Math.min(cantidad, 8);
        for (let i = 0; i < max_visibles; i++) {
            const offset = (i + 1) * separacion;
            const x = cx + dx * offset;
            const y = cy + dy * offset;

            ctx.save();
            ctx.translate(x, y);
            if (girar) ctx.rotate(Math.PI / 2);
            ctx.fillStyle = '#e94560';
            ctx.fillRect(-6, -4, 12, 8);
            ctx.fillStyle = '#ff6b81';
            ctx.fillRect(-4, -3, 8, 6);
            ctx.restore();

            if (i === max_visibles - 1 && cantidad > max_visibles) {
                ctx.fillStyle = '#aaa';
                ctx.font = '10px sans-serif';
                ctx.textAlign = 'center';
                ctx.fillText('+' + (cantidad - max_visibles), x + dx * 10, y + dy * 10 + 4);
            }
        }
    }

    dibujarFila(CX, CY - MITAD_CALLE, estado.norte, 0, -1, false);
    dibujarFila(CX, CY + MITAD_CALLE, estado.sur, 0, 1, false);
    dibujarFila(CX - MITAD_CALLE, CY, estado.oeste, -1, 0, true);
    dibujarFila(CX + MITAD_CALLE, CY, estado.este, 1, 0, true);
}

function dibujarRotulos() {
    if (!estado) return;

    ctx.fillStyle = '#a0a0c0';
    ctx.font = 'bold 14px sans-serif';
    ctx.textAlign = 'center';

    ctx.fillText('NORTE (' + estado.norte + ')', CX, 20);
    ctx.fillText('SUR (' + estado.sur + ')', CX, 590);
    ctx.textAlign = 'left';
    ctx.fillText('OESTE (' + estado.oeste + ')', 10, CY + 5);
    ctx.textAlign = 'right';
    ctx.fillText('ESTE (' + estado.este + ')', 590, CY + 5);
}
