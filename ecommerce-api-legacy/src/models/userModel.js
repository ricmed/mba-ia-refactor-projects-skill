const bcrypt = require('bcryptjs');
const db = require('../config/database');

async function findByEmail(email) {
    return db.get('SELECT * FROM users WHERE email = ?', [email]);
}

async function findById(id) {
    return db.get('SELECT id, name, email FROM users WHERE id = ?', [id]);
}

async function create(name, email, plainPassword) {
    const hash = await bcrypt.hash(plainPassword || '123456', 10);
    const { lastID } = await db.run('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)', [
        name,
        email,
        hash,
    ]);
    return lastID;
}

async function remove(id) {
    return db.run('DELETE FROM users WHERE id = ?', [id]);
}

module.exports = { findByEmail, findById, create, remove };
