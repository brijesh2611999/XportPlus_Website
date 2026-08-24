const express = require('express');
const router = express.Router();
const icegateProxy = require('../middlewares/proxyMiddleware');

// Route all requests starting with /icegate_api through the proxy middleware
router.use('/', icegateProxy);

module.exports = router;
