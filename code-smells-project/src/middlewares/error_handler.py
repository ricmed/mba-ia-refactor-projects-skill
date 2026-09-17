import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        return jsonify({"erro": error.description, "sucesso": False}), error.code

    @app.errorhandler(Exception)
    def handle_unexpected(error):
        logger.exception("Erro não tratado")
        return jsonify({"erro": str(error), "sucesso": False}), 500
