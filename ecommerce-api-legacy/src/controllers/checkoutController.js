const checkoutService = require('../services/checkoutService');

async function checkout(req, res, next) {
    try {
        const result = await checkoutService.checkout(req.body);
        if (result.error) {
            return res.status(result.status).json({ error: result.error });
        }
        res.status(200).json(result.data);
    } catch (err) {
        next(err);
    }
}

module.exports = { checkout };
