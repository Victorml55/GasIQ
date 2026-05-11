 
const mongoose = require('mongoose');

const estacionSchema = new mongoose.Schema({
  id_cre: { type: String, required: true, unique: true },
  nombre: String,
  razon_social: String,
  estado: String,
  municipio: String,
  direccion: String,
  marca: String,
  coordenadas: {
    lat: Number,
    lng: Number
  },
  calidad: {
    nom005: Boolean,
    servicio_completo: Boolean,
    aire: Boolean,
    agua: Boolean,
    bano: Boolean,
    cajero: Boolean,
    tienda: Boolean,
    rating_google: Number,
    num_resenas: Number
  },
  precios: [{
    semana: String,
    magna: Number,
    premium: Number,
    diesel: Number
  }],
  precio_predicho: {
    semana: String,
    magna: Number,
    premium: Number,
    diesel: Number
  }
});

module.exports = mongoose.model('Estacion', estacionSchema);