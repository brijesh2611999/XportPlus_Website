const express = require('express');
const router = express.Router();
const cmaController = require('../controllers/cmaController');

// Route for getting CMA CGM quotes
router.post('/get-quotes', cmaController.getCmaQuotes);

module.exports = router;
