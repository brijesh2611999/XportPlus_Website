const express = require('express');
const router = express.Router();
const mscController = require('../controllers/mscController');

// Route for getting MSC quotes
router.post('/get-quotes', mscController.getMscQuotes);

module.exports = router;
