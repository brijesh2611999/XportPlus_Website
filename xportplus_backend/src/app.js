// const express = require('express');
// const cors = require('cors');
// const icegateRoutes = require('./routes/icegateRoutes');
// const cmaRoutes = require('./routes/cmaRoutes');
// const mscRoutes = require('./routes/mscRoutes');

// const app = express();

// // Middleware
// app.use(cors()); // Configure CORS options here if needed in production

// // Routes MUST be before express.json() for http-proxy-middleware to work with POST bodies
// app.use('/icegate_api', icegateRoutes);

// app.use(express.json()); // Parse JSON bodies if needed for other routes

// // Other generic routes that need body parsing
// app.use('/cma', cmaRoutes);
// app.use('/msc', mscRoutes);

// // Health check route
// app.get('/', (req, res) => {
//     res.json({
//         success: true,
//         message: 'XPortPlus Backend API is running successfully!',
//         version: '1.0.0'
//     });
// });

// // Error handling middleware
// app.use((err, req, res, next) => {
//     console.error('Unhandled Error:', err);
//     res.status(500).json({ success: false, message: 'Internal Server Error' });
// });

// module.exports = app;
const express = require('express');
const cors = require('cors');
const config = require('./config/config');
const icegateRoutes = require('./routes/icegateRoutes');
const cmaRoutes = require('./routes/cmaRoutes');
const mscRoutes = require('./routes/mscRoutes');

const app = express();
app.use(cors({ origin: config.ALLOWED_ORIGINS }));
app.use('/icegate_api', icegateRoutes);
app.use(express.json());
app.use('/cma', cmaRoutes);
app.use('/msc', mscRoutes);

app.get('/', (req, res) => {
    res.json({ success: true, message: 'XPortPlus Backend API is running successfully!', version: '1.0.0' });
});

app.use((err, req, res, next) => {
    console.error('Unhandled Error:', err);
    res.status(500).json({ success: false, message: 'Internal Server Error' });
});

module.exports = app;