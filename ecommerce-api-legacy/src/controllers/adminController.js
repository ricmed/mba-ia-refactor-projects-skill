const reportModel = require('../models/reportModel');

async function financialReport(req, res, next) {
    try {
        const report = await reportModel.getFinancialReport();
        res.json(report);
    } catch (err) {
        next(err);
    }
}

module.exports = { financialReport };
