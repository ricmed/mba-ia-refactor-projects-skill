const userModel = require('../models/userModel');
const enrollmentModel = require('../models/enrollmentModel');
const paymentModel = require('../models/paymentModel');

/**
 * Ao contrário do AppManager original (que deixava enrollments/payments
 * órfãos de propósito), remove os registros dependentes antes do usuário
 * para preservar integridade referencial.
 */
async function remove(req, res, next) {
    try {
        const userId = req.params.id;
        const enrollments = await enrollmentModel.findByUserId(userId);
        const enrollmentIds = enrollments.map((e) => e.id);

        await paymentModel.removeByEnrollmentIds(enrollmentIds);
        await enrollmentModel.removeByUserId(userId);
        await userModel.remove(userId);

        res.json({ message: 'Usuário e todos os registros associados (matrículas, pagamentos) foram removidos.' });
    } catch (err) {
        next(err);
    }
}

module.exports = { remove };
