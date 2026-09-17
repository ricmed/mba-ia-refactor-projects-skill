const db = require('../config/database');
const settings = require('../config/settings');
const cache = require('../config/cache');
const userModel = require('../models/userModel');
const courseModel = require('../models/courseModel');
const enrollmentModel = require('../models/enrollmentModel');
const paymentModel = require('../models/paymentModel');
const auditLogModel = require('../models/auditLogModel');

/**
 * Simulação de autorização de gateway de pagamento. Nunca loga o número do
 * cartão nem a chave do gateway (ver anti-pattern "log de dados sensíveis").
 */
function authorizePayment(cardNumber) {
    return cardNumber.startsWith('4') ? 'PAID' : 'DENIED';
}

/**
 * Orquestra a regra de negócio de checkout (validação, criação de usuário,
 * autorização de pagamento, matrícula e log de auditoria) fora do handler de
 * rota, dentro de uma transação — resolve o God Class / callback-hell / falta
 * de transação do AppManager original.
 */
async function checkout({ usr, eml, pwd, c_id, card }) {
    if (!usr || !eml || !c_id || !card) {
        return { error: 'Bad Request', status: 400 };
    }

    const course = await courseModel.getActiveById(c_id);
    if (!course) {
        return { error: 'Curso não encontrado', status: 404 };
    }

    const existingUser = await userModel.findByEmail(eml);

    await db.run('BEGIN TRANSACTION');
    try {
        const userId = existingUser ? existingUser.id : await userModel.create(usr, eml, pwd);

        const status = authorizePayment(card);
        if (status === 'DENIED') {
            await db.run('ROLLBACK');
            return { error: 'Pagamento recusado', status: 400 };
        }

        const enrollmentId = await enrollmentModel.create(userId, c_id);
        await paymentModel.create(enrollmentId, course.price, status);
        await auditLogModel.record(`Checkout curso ${c_id} por ${userId} via gateway ${settings.paymentGatewayKey.slice(0, 7)}***`);

        await db.run('COMMIT');
        cache.set(`last_checkout_${userId}`, course.title);

        return { data: { msg: 'Sucesso', enrollment_id: enrollmentId } };
    } catch (err) {
        await db.run('ROLLBACK');
        throw err;
    }
}

module.exports = { checkout };
