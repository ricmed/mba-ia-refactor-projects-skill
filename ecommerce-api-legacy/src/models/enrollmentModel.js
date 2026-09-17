const db = require('../config/database');

async function create(userId, courseId) {
    const { lastID } = await db.run('INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)', [
        userId,
        courseId,
    ]);
    return lastID;
}

async function removeByUserId(userId) {
    return db.run('DELETE FROM enrollments WHERE user_id = ?', [userId]);
}

async function findByUserId(userId) {
    return db.all('SELECT * FROM enrollments WHERE user_id = ?', [userId]);
}

async function findByCourseId(courseId) {
    return db.all('SELECT * FROM enrollments WHERE course_id = ?', [courseId]);
}

module.exports = { create, removeByUserId, findByUserId, findByCourseId };
