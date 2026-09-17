const db = require('../config/database');

async function create(enrollmentId, amount, status) {
    const { lastID } = await db.run(
        'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
        [enrollmentId, amount, status]
    );
    return lastID;
}

async function removeByEnrollmentIds(enrollmentIds) {
    if (!enrollmentIds.length) return;
    const placeholders = enrollmentIds.map(() => '?').join(', ');
    return db.run(`DELETE FROM payments WHERE enrollment_id IN (${placeholders})`, enrollmentIds);
}

async function findByEnrollmentId(enrollmentId) {
    return db.get('SELECT amount, status FROM payments WHERE enrollment_id = ?', [enrollmentId]);
}

module.exports = { create, removeByEnrollmentIds, findByEnrollmentId };
