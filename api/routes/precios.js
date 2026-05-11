 const express = require('express');
const router = express.Router();
const Estacion = require('../models/estacion');

// GET precio promedio por estado
router.get('/promedio/:estado', async (req, res) => {
  try {
    const resultado = await Estacion.aggregate([
      { $match: { estado: req.params.estado } },
      { $unwind: '$precios' },
      { $group: {
        _id: '$precios.semana',
        promedio_magna: { $avg: '$precios.magna' },
        promedio_premium: { $avg: '$precios.premium' },
        promedio_diesel: { $avg: '$precios.diesel' }
      }},
      { $sort: { _id: -1 } },
      { $limit: 12 }
    ]);
    res.json({ estado: req.params.estado, historico: resultado });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// GET predicción de precio por estado
router.get('/prediccion/:estado', async (req, res) => {
  try {
    const estaciones = await Estacion.find(
      { estado: req.params.estado },
      { precio_predicho: 1, nombre: 1, municipio: 1 }
    ).limit(20);
    res.json({ estado: req.params.estado, predicciones: estaciones });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;