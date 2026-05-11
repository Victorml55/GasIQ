const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
require('dotenv').config();

const estacionesRouter = require('./routes/estaciones');
const preciosRouter = require('./routes/precios');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());

// Conexión MongoDB
mongoose.connect(process.env.MONGO_URI)
  .then(() => console.log('✅ MongoDB conectado'))
  .catch(err => console.error('❌ Error MongoDB:', err));

// Rutas
app.use('/api/estaciones', estacionesRouter);
app.use('/api/precios', preciosRouter);

// Ruta raíz
app.get('/', (req, res) => {
  res.json({
    message: '🔥 GasolinaIQ API funcionando',
    version: '1.0.0',
    endpoints: {
      estaciones: '/api/estaciones',
      precios: '/api/precios'
    }
  });
});

app.listen(PORT, () => {
  console.log(`🚀 Servidor corriendo en http://localhost:${PORT}`);
});