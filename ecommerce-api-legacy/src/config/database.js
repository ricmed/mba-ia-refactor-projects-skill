const sqlite3 = require('sqlite3').verbose();

/**
 * Fina camada de acesso ao SQLite que expõe Promises em vez de callbacks,
 * eliminando o "callback hell" do driver `sqlite3` cru (ver AP: API deprecated
 * baseada em callback, catálogo de anti-patterns).
 */
class Database {
    constructor() {
        this.raw = new sqlite3.Database(':memory:');
    }

    run(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.raw.run(sql, params, function callback(err) {
                if (err) return reject(err);
                resolve({ lastID: this.lastID, changes: this.changes });
            });
        });
    }

    get(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.raw.get(sql, params, (err, row) => {
                if (err) return reject(err);
                resolve(row);
            });
        });
    }

    all(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.raw.all(sql, params, (err, rows) => {
                if (err) return reject(err);
                resolve(rows);
            });
        });
    }

    async initSchema() {
        await this.run('CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, pass TEXT)');
        await this.run('CREATE TABLE courses (id INTEGER PRIMARY KEY, title TEXT, price REAL, active INTEGER)');
        await this.run('CREATE TABLE enrollments (id INTEGER PRIMARY KEY, user_id INTEGER, course_id INTEGER)');
        await this.run('CREATE TABLE payments (id INTEGER PRIMARY KEY, enrollment_id INTEGER, amount REAL, status TEXT)');
        await this.run('CREATE TABLE audit_logs (id INTEGER PRIMARY KEY, action TEXT, created_at DATETIME)');
    }

    async seed() {
        const bcrypt = require('bcryptjs');
        const hash = await bcrypt.hash('123', 10);

        await this.run('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)', [
            'Leonan',
            'leonan@fullcycle.com.br',
            hash,
        ]);
        await this.run("INSERT INTO courses (title, price, active) VALUES ('Clean Architecture', 997.00, 1)");
        await this.run("INSERT INTO courses (title, price, active) VALUES ('Docker', 497.00, 1)");
        await this.run('INSERT INTO enrollments (user_id, course_id) VALUES (1, 1)');
        await this.run('INSERT INTO payments (enrollment_id, amount, status) VALUES (1, 997.00, ?)', ['PAID']);
    }
}

module.exports = new Database();
