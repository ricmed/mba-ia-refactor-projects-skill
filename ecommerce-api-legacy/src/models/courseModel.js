const db = require('../config/database');

async function getActiveById(id) {
    return db.get('SELECT * FROM courses WHERE id = ? AND active = 1', [id]);
}

async function getAll() {
    return db.all('SELECT * FROM courses');
}

module.exports = { getActiveById, getAll };
