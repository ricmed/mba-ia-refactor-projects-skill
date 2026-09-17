const express = require('express');

const settings = require('./config/settings');
const db = require('./config/database');
const errorHandler = require('./middlewares/errorHandler');
const checkoutRoutes = require('./views/checkoutRoutes');
const adminRoutes = require('./views/adminRoutes');
const userRoutes = require('./views/userRoutes');

const app = express();
app.use(express.json());

app.use('/api', checkoutRoutes);
app.use('/api', adminRoutes);
app.use('/api', userRoutes);

app.use(errorHandler);

async function start() {
    await db.initSchema();
    await db.seed();
    app.listen(settings.port, () => {
        console.log(`LMS API rodando na porta ${settings.port}...`);
    });
}

if (require.main === module) {
    start();
}

module.exports = app;
