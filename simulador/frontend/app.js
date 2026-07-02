const socket = io();

const canvas4 = document.getElementById('canvas-4');
const ctx4 = canvas4.getContext('2d');
const canvasT = document.getElementById('canvas-t');
const ctxT = canvasT.getContext('2d');

const CX = 300, CY = 300;
const ANCHO_CALLE = 80;
const MITAD = ANCHO_CALLE / 2;
const RS = 12;
const SEP = 22;

let estado4 = null;
let estadoT = null;

socket.on('connect', () => {
    document.getElementById('status').textContent = 'Conectado';
    document.getElementById('status').className = 'status-conectado';
});

socket.on('disconnect', () => {
    document.getElementById('status').textContent = 'Desconectado';
    document.getElementById('status').className = 'status-desconectado';
});

socket.on('estado_4', (data) => {
    if (!estado4) crearPanel('panel-4', Object.keys(data.accesos));
    estado4 = data;
    actualizarPanel(data, 'panel-4');
    dibujar4();
});

socket.on('estado_t', (data) => {
    if (!estadoT) crearPanel('panel-t', Object.keys(data.accesos));
    estadoT = data;
    actualizarPanel(data, 'panel-t');
    dibujarT();
});

function crearPanel(id, accesos) {
    const p = document.getElementById(id);
    const nom = { N: 'Norte', S: 'Sur', E: 'Este', O: 'Oeste' };
    let html = '<h3>Panel de Control</h3>';
    accesos.forEach(a => {
        html += `<div class="grupo-acceso" data-acceso="${a}">`;
        html += `<h4>${nom[a]} (${a})</h4>`;
        html += `<div class="indicador"><span class="etiqueta">Estado:</span><span class="valor estado" data-id="${id}-${a}-estado">--</span></div>`;
        html += `<div class="indicador"><span class="etiqueta">Vehículos:</span><span class="valor" data-id="${id}-${a}-vehiculos">0</span></div>`;
        html += `<div class="indicador"><span class="etiqueta">Espera máx:</span><span class="valor" data-id="${id}-${a}-espera-max">0s</span></div>`;
        html += `<div class="indicador"><span class="etiqueta">Espera prom:</span><span class="valor" data-id="${id}-${a}-espera-prom">0s</span></div>`;
        html += `<div class="indicador"><span class="etiqueta">Tiempo verde:</span><span class="valor" data-id="${id}-${a}-tiempo-estado">0s</span></div>`;
        html += `</div>`;
    });
    html += `<div class="resumen">`;
    html += `<h4>Resumen</h4>`;
    html += `<div class="indicador"><span class="etiqueta">Total:</span><span class="valor" data-id="${id}-total">0</span></div>`;
    html += `<div class="indicador"><span class="etiqueta">Tiempo:</span><span class="valor" data-id="${id}-tiempo">0s</span></div>`;
    html += `<div class="indicador"><span class="etiqueta">En verde:</span><span class="valor" data-id="${id}-verde">--</span></div>`;
    html += `</div>`;
    p.innerHTML = html;
}

function actualizarPanel(data, id) {
    for (const [a, d] of Object.entries(data.accesos)) {
        const el = (key) => document.querySelector(`[data-id="${id}-${a}-${key}"]`);
        el('estado').textContent = d.estado;
        el('estado').className = 'valor estado ' + d.estado.toLowerCase();
        el('vehiculos').textContent = d.vehiculos;
        el('espera-max').textContent = d.espera_max + 's';
        el('espera-prom').textContent = d.espera_prom + 's';
        el('tiempo-estado').textContent = d.tiempo_estado + 's';
    }
    document.querySelector(`[data-id="${id}-total"]`).textContent = data.total_vehiculos;
    document.querySelector(`[data-id="${id}-tiempo"]`).textContent = data.tiempo + 's';
    document.querySelector(`[data-id="${id}-verde"]`).textContent = data.acceso_verde || '--';
}

function dibujarSemaforo(ctx, x, y, data, vertical) {
    ctx.strokeStyle = '#444';
    ctx.lineWidth = 2;
    ctx.fillStyle = '#222';
    ctx.beginPath();
    if (vertical) {
        ctx.roundRect(x - RS, y - RS * 3 - 4, RS * 2, RS * 6 + 8, 4);
    } else {
        ctx.roundRect(x - RS * 3 - 4, y - RS, RS * 6 + 8, RS * 2, 4);
    }
    ctx.fill();
    ctx.stroke();

    const colores = [
        data.estado === 'ROJO' ? '#ff3333' : '#330000',
        data.estado === 'AMARILLO' ? '#ffcc00' : '#332200',
        data.estado === 'VERDE' ? '#33ff33' : '#003300'
    ];

    if (vertical) {
        for (let i = 0; i < 3; i++) {
            const yy = y + (i - 1) * RS * 2;
            ctx.beginPath();
            ctx.arc(x, yy, RS - 2, 0, Math.PI * 2);
            ctx.fillStyle = colores[i];
            ctx.fill();
            if (i === 0 && data.estado === 'ROJO' || i === 1 && data.estado === 'AMARILLO' || i === 2 && data.estado === 'VERDE') {
                ctx.shadowColor = colores[i];
                ctx.shadowBlur = 8;
                ctx.fill();
                ctx.shadowBlur = 0;
            }
        }
    } else {
        for (let i = 0; i < 3; i++) {
            const xx = x + (i - 1) * RS * 2;
            ctx.beginPath();
            ctx.arc(xx, y, RS - 2, 0, Math.PI * 2);
            ctx.fillStyle = colores[i];
            ctx.fill();
            if (i === 0 && data.estado === 'ROJO' || i === 1 && data.estado === 'AMARILLO' || i === 2 && data.estado === 'VERDE') {
                ctx.shadowColor = colores[i];
                ctx.shadowBlur = 8;
                ctx.fill();
                ctx.shadowBlur = 0;
            }
        }
    }
    ctx.shadowBlur = 0;
}

function dibujarFondo(ctx, norte) {
    ctx.fillStyle = '#3d3d5c';
    ctx.fillRect(0, 0, 600, 600);
    ctx.fillStyle = '#2d2d44';
    if (norte) {
        ctx.fillRect(CX - MITAD, 0, ANCHO_CALLE, CY - MITAD);
    }
    ctx.fillRect(CX - MITAD, CY + MITAD, ANCHO_CALLE, 600 - CY - MITAD);
    ctx.fillRect(0, CY - MITAD, CX - MITAD, ANCHO_CALLE);
    ctx.fillRect(CX + MITAD, CY - MITAD, 600 - CX - MITAD, ANCHO_CALLE);
}

function dibujarMarcas(ctx, norte) {
    ctx.strokeStyle = '#5a5a7a';
    ctx.lineWidth = 2;
    ctx.setLineDash([8, 6]);
    if (norte) {
        ctx.beginPath(); ctx.moveTo(CX, 0); ctx.lineTo(CX, CY - MITAD); ctx.stroke();
    }
    ctx.beginPath(); ctx.moveTo(CX, CY + MITAD); ctx.lineTo(CX, 600); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(0, CY); ctx.lineTo(CX - MITAD, CY); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(CX + MITAD, CY); ctx.lineTo(600, CY); ctx.stroke();
    ctx.setLineDash([]);
}

function dibujarVehiculosCarril(ctx, cantidad, sx, sy, dx, dy, girar) {
    const maxVis = Math.min(cantidad, 8);
    for (let i = 0; i < maxVis; i++) {
        const off = (i + 1) * SEP;
        const x = sx + dx * off;
        const y = sy + dy * off;
        ctx.save();
        ctx.translate(x, y);
        if (girar) ctx.rotate(Math.PI / 2);
        ctx.fillStyle = '#e94560';
        ctx.fillRect(-6, -4, 12, 8);
        ctx.fillStyle = '#ff6b81';
        ctx.fillRect(-4, -3, 8, 6);
        ctx.restore();
        if (i === maxVis - 1 && cantidad > maxVis) {
            ctx.fillStyle = '#aaa';
            ctx.font = '10px sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText('+' + (cantidad - maxVis), x + dx * 10, y + dy * 10 + 4);
        }
    }
}

function dibujarRotulos(ctx, items) {
    ctx.fillStyle = '#a0a0c0';
    ctx.font = 'bold 14px sans-serif';
    items.forEach(item => {
        if (item.align) ctx.textAlign = item.align;
        else ctx.textAlign = 'center';
        ctx.fillText(item.text, item.x, item.y);
    });
}

function dibujar4() {
    if (!estado4) return;
    const ctx = ctx4, d = estado4;
    ctx.clearRect(0, 0, 600, 600);
    dibujarFondo(ctx, true);
    dibujarMarcas(ctx, true);

    ctx.fillStyle = '#3d3d5c';
    ctx.fillRect(CX - MITAD, CY - MITAD, ANCHO_CALLE, ANCHO_CALLE);
    ctx.strokeStyle = '#5a5a7a';
    ctx.lineWidth = 2;
    ctx.strokeRect(CX - MITAD, CY - MITAD, ANCHO_CALLE, ANCHO_CALLE);

    const semPos = {
        N: { x: CX, y: CY - MITAD - 15, v: true },
        S: { x: CX, y: CY + MITAD + 15, v: true },
        E: { x: CX + MITAD + 15, y: CY, v: false },
        W: { x: CX - MITAD - 15, y: CY, v: false }
    };
    for (const [a, p] of Object.entries(semPos)) {
        if (d.accesos[a]) dibujarSemaforo(ctx, p.x, p.y, d.accesos[a], p.v);
    }

    const vehCfg = {
        N: { sx: CX, sy: CY - MITAD, dx: 0, dy: -1, girar: false },
        S: { sx: CX, sy: CY + MITAD, dx: 0, dy: 1, girar: false },
        E: { sx: CX + MITAD, sy: CY, dx: 1, dy: 0, girar: true },
        W: { sx: CX - MITAD, sy: CY, dx: -1, dy: 0, girar: true }
    };
    for (const [a, c] of Object.entries(vehCfg)) {
        if (d.accesos[a]) dibujarVehiculosCarril(ctx, d.accesos[a].vehiculos, c.sx, c.sy, c.dx, c.dy, c.girar);
    }

    dibujarRotulos(ctx, [
        { text: 'NORTE (' + (d.accesos.N ? d.accesos.N.vehiculos : 0) + ')', x: CX, y: 20 },
        { text: 'SUR (' + (d.accesos.S ? d.accesos.S.vehiculos : 0) + ')', x: CX, y: 590 },
        { text: 'OESTE (' + (d.accesos.W ? d.accesos.W.vehiculos : 0) + ')', x: 10, y: CY + 5, align: 'left' },
        { text: 'ESTE (' + (d.accesos.E ? d.accesos.E.vehiculos : 0) + ')', x: 590, y: CY + 5, align: 'right' }
    ]);
}

function dibujarT() {
    if (!estadoT) return;
    const ctx = ctxT, d = estadoT;
    ctx.clearRect(0, 0, 600, 600);
    dibujarFondo(ctx, false);
    dibujarMarcas(ctx, false);

    ctx.fillStyle = '#3d3d5c';
    ctx.fillRect(CX - MITAD, CY - MITAD, ANCHO_CALLE, ANCHO_CALLE);
    ctx.strokeStyle = '#5a5a7a';
    ctx.lineWidth = 2;
    ctx.strokeRect(CX - MITAD, CY - MITAD, ANCHO_CALLE, ANCHO_CALLE);

    const semPos = {
        S: { x: CX, y: CY + MITAD + 15, v: true },
        E: { x: CX + MITAD + 15, y: CY, v: false },
        W: { x: CX - MITAD - 15, y: CY, v: false }
    };
    for (const [a, p] of Object.entries(semPos)) {
        if (d.accesos[a]) dibujarSemaforo(ctx, p.x, p.y, d.accesos[a], p.v);
    }

    const vehCfg = {
        S: { sx: CX, sy: CY + MITAD, dx: 0, dy: 1, girar: false },
        E: { sx: CX + MITAD, sy: CY, dx: 1, dy: 0, girar: true },
        W: { sx: CX - MITAD, sy: CY, dx: -1, dy: 0, girar: true }
    };
    for (const [a, c] of Object.entries(vehCfg)) {
        if (d.accesos[a]) dibujarVehiculosCarril(ctx, d.accesos[a].vehiculos, c.sx, c.sy, c.dx, c.dy, c.girar);
    }

    dibujarRotulos(ctx, [
        { text: 'SUR (' + d.accesos.S.vehiculos + ')', x: CX, y: 590 },
        { text: 'OESTE (' + d.accesos.W.vehiculos + ')', x: 10, y: CY + 5, align: 'left' },
        { text: 'ESTE (' + d.accesos.E.vehiculos + ')', x: 590, y: CY + 5, align: 'right' }
    ]);
}
