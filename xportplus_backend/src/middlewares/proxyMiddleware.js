const { createProxyMiddleware } = require('http-proxy-middleware');
const config = require('../config/config');

const icegateProxy = createProxyMiddleware({
    target: config.ICEGATE_BASE_URL,
    changeOrigin: true,
    pathRewrite: {
        '^/icegate_api': '', 
    },
    headers: {
        'Origin': config.ICEGATE_BASE_URL,
        'Referer': `${config.ICEGATE_BASE_URL}/`,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    },
    onError: (err, req, res) => {
        console.error('Proxy Error:', err);
        res.status(500).json({ success: false, message: 'Proxy Error to Icegate API' });
    }
});

module.exports = icegateProxy;
