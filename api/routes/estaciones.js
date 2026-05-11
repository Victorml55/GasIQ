 const express = require('express');
const router = express.Router();
const Estacion = require('../models/estacion');

// GET todas las estaciones (con filtros opcionales)
router.get('/', async (req, res) => {
  try {
    const { estado, municipio, marca } = req.query;
    const filtro = {};
    if (estado) filtro.estado = estado;
    if (municipio) filtro.municipio = municipio;
    if (marca) filtro.marca = marca;

    const estaciones = await Estacion.find(filtro).limit(100);
    res.json({ total: estaciones.length, data: estaciones });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// GET una estación por ID CRE
router.get('/:id_cre', async (req, res) => {
  try {
    const estacion = await Estacion.findOne({ id_cre: req.params.id_cre });
    if (!estacion) return res.status(404).json({ error: 'Estación no encontrada' });
    res.json(estacion);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// GET mejores estaciones por estado (precio más bajo)
router.get('/mejores/:estado', async (req, res) => {
  try {
    const estaciones = await Estacion.find({ estado: req.params.estado })
      .sort({ 'precios.0.magna': 1 })
      .limit(10);
    res.json({ estado: req.params.estado, mejores: estaciones });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;

