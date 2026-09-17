const express = require('express');
const adminController = require('../controllers/adminController');

const router = express.Router();

router.get('/admin/financial-report', adminController.financialReport);

module.exports = router;
