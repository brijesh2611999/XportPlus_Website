// require('dotenv').config();

// module.exports = {
//     PORT: process.env.PORT || 5000,
//     ICEGATE_BASE_URL: process.env.ICEGATE_BASE_URL || 'https://foservices.icegate.gov.in',
//     ALLOWED_ORIGINS: ['http://localhost:5173', 'https://xport-plus.com'] // Add your frontend domains here
// };


require('dotenv').config();

const defaultOrigins = ['http://localhost:5173', 'https://xport-plus.com'];

module.exports = {
    PORT: process.env.PORT || 5000,
    ICEGATE_BASE_URL: process.env.ICEGATE_BASE_URL || 'https://foservices.icegate.gov.in',
    ALLOWED_ORIGINS: process.env.ALLOWED_ORIGINS
        ? process.env.ALLOWED_ORIGINS.split(',').map(o => o.trim())
        : defaultOrigins,
    TOKEN_TTL_MINUTES: parseInt(process.env.TOKEN_TTL_MINUTES || '12', 10),
};