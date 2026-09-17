const express = require('express');
const userController = require('../controllers/userController');

const router = express.Router();

router.delete('/users/:id', userController.remove);

module.exports = router;
