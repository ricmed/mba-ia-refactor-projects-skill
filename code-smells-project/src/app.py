import logging

from flask import Flask
from flask_cors import CORS

from config.database import get_db
from config.settings import Settings
from middlewares.error_handler import register_error_handlers
from views.general_routes import general_bp
from views.pedido_routes import pedido_bp
from views.produto_routes import produto_bp
from views.usuario_routes import usuario_bp

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def create_app():
    app = Flask(__name__)
    app.config.from_object(Settings)

    CORS(app, origins=Settings.CORS_ORIGINS)

    register_error_handlers(app)

    app.register_blueprint(general_bp)
    app.register_blueprint(produto_bp)
    app.register_blueprint(usuario_bp)
    app.register_blueprint(pedido_bp)

    return app


app = create_app()

if __name__ == "__main__":
    get_db()
    logger.info("=" * 50)
    logger.info("SERVIDOR INICIADO")
    logger.info("Rodando em http://%s:%s", Settings.HOST, Settings.PORT)
    logger.info("=" * 50)

    app.run(host=Settings.HOST, port=Settings.PORT, debug=Settings.DEBUG)
