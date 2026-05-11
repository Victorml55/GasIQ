const mongoose = require('mongoose');
const fs = require('fs');
const path = require('path');
require('dotenv').config();

const Estacion = require('./models/estacion');

// Centroides de estados (igual que el script de Victor)
const CENTROIDES = {
  "Aguascalientes":      [21.8853, -102.2916],
  "Baja California":     [30.8406, -115.2838],
  "Baja California Sur": [26.0444, -111.6661],
  "Campeche":            [19.8301,  -90.5349],
  "Chiapas":             [16.7569,  -93.1292],
  "Chihuahua":           [28.6353, -106.0889],
  "Ciudad de Mexico":    [19.4326,  -99.1332],
  "Coahuila":            [27.0587, -101.7068],
  "Colima":              [19.2452, -103.7241],
  "Durango":             [24.5593, -104.6588],
  "Guanajuato":          [21.0190, -101.2574],
  "Guerrero":            [17.4392,  -99.5451],
  "Hidalgo":             [20.0911,  -98.7624],
  "Jalisco":             [20.6595, -103.3494],
  "Mexico":              [19.4969,  -99.7233],
  "Michoacan":           [19.5665, -101.7068],
  "Morelos":             [18.6813,  -99.1013],
  "Nayarit":             [21.7514, -104.8455],
  "Nuevo Leon":          [25.5922,  -99.9962],
  "Oaxaca":              [17.0732,  -96.7266],
  "Puebla":              [19.0414,  -98.2063],
  "Queretaro":           [20.5888, -100.3899],
  "Quintana Roo":        [19.1817,  -88.4791],
  "San Luis Potosi":     [22.1565, -100.9855],
  "Sinaloa":             [25.1721, -107.4795],
  "Sonora":              [29.2972, -110.3309],
  "Tabasco":             [17.8409,  -92.6189],
  "Tamaulipas":          [24.2669,  -98.8363],
  "Tlaxcala":            [19.3139,  -98.2400],
  "Veracruz":            [19.1738,  -96.1342],
  "Yucatan":             [20.7099,  -89.0943],
  "Zacatecas":           [22.7709, -102.5832],
};

function nearestEstado(lat, lon) {
  let best = null, bestD = Infinity;
  for (const [estado, [la, lo]] of Object.entries(CENTROIDES)) {
    const d = (lat - la) ** 2 + (lon - lo) ** 2;
    if (d < bestD) { bestD = d; best = estado; }
  }
  return best;
}

function toFloat(x) {
  if (x === null || x === undefined) return null;
  if (typeof x === 'number') return x;
  if (typeof x === 'object') {
    for (const k of ['$numberDouble','$numberInt','$numberLong','$numberDecimal']) {
      if (k in x) return parseFloat(x[k]);
    }
  }
  const f = parseFloat(x);
  return isNaN(f) ? null : f;
}

async function cargarDatos() {
  try {
    await mongoose.connect(process.env.MONGO_URI);
    console.log('✅ MongoDB conectado');

    const rutaJson = path.join(__dirname, '../data/raw/precios_mongo.json');
    const raw = fs.readFileSync(rutaJson, 'utf-8');
    
    let docs = [];
    const txt = raw.trim();
    if (txt.startsWith('[')) {
      docs = JSON.parse(txt);
    } else {
      docs = txt.split('\n').filter(l => l.trim()).map(l => JSON.parse(l));
    }

    console.log(`📦 Documentos encontrados: ${docs.length}`);

    await Estacion.deleteMany({});
    console.log('🗑️ Colección limpiada');

    const estaciones = [];
    let errores = 0;

    for (const d of docs) {
      try {
        const lat = toFloat(d.latitud);
        const lng = toFloat(d.longitud);
        if (!lat || !lng) { errores++; continue; }
        if (!(14 <= lat && lat <= 33 && -120 <= lng && lng <= -86)) { errores++; continue; }

        // Asignar estado por coordenadas igual que Victor
        const estado = nearestEstado(lat, lng);

        estaciones.push({
          id_cre: d.cre_id || d.place_id || String(Math.random()),
          nombre: d.nombre || '',
          estado: estado,
          municipio: d.municipio || '',
          direccion: d.direccion || '',
          marca: d.marca || '',
          coordenadas: { lat, lng },
          calidad: {
            nom005: d.nom005 || false,
            servicio_completo: d.servicio_completo || false,
            aire: d.aire || false,
            agua: d.agua || false,
            bano: d.bano || false,
            cajero: d.cajero || false,
            tienda: d.tienda || false,
            rating_google: toFloat(d.rating),
            num_resenas: parseInt(d.num_resenas) || 0
          },
          precios: [{
            semana: d.semana || new Date().toISOString().split('T')[0],
            magna: toFloat(d.precio_regular),
            premium: toFloat(d.precio_premium),
            diesel: toFloat(d.precio_diesel)
          }]
        });
      } catch (e) {
        errores++;
      }
    }

    console.log(`📝 Preparados: ${estaciones.length} documentos`);

    const LOTE = 500;
    let cargados = 0;
    for (let i = 0; i < estaciones.length; i += LOTE) {
      const lote = estaciones.slice(i, i + LOTE);
      await Estacion.insertMany(lote, { ordered: false });
      cargados += lote.length;
      console.log(`⬆️  ${cargados}/${estaciones.length} cargados...`);
    }

    console.log(`\n✅ Cargados: ${cargados} estaciones`);
    console.log(`❌ Errores: ${errores}`);
    mongoose.disconnect();

  } catch (err) {
    console.error('Error:', err.message);
    process.exit(1);
  }
}

cargarDatos();