require('dotenv').config();

const settings = {
    port: parseInt(process.env.PORT || '3000', 10),
    dbUser: process.env.DB_USER || 'admin_master',
    dbPass: process.env.DB_PASS || 'change-me-in-production',
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || 'pk_test_change-me',
    smtpUser: process.env.SMTP_USER || 'no-reply@example.com',
};

module.exports = settings;
