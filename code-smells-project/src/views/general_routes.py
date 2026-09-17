from flask import Blueprint, jsonify

from config.database import get_db

general_bp = Blueprint("general", __name__)


@general_bp.route("/")
def index():
    return jsonify(
        {
            "mensagem": "Bem-vindo à API da Loja",
            "versao": "1.0.0",
            "endpoints": {
                "produtos": "/produtos",
                "usuarios": "/usuarios",
                "pedidos": "/pedidos",
                "login": "/login",
                "relatorios": "/relatorios/vendas",
                "health": "/health",
            },
        }
    )


@general_bp.route("/health")
def health_check():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) FROM produtos")
    produtos = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    usuarios = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM pedidos")
    pedidos = cursor.fetchone()[0]

    return (
        jsonify(
            {
                "status": "ok",
                "database": "connected",
                "counts": {"produtos": produtos, "usuarios": usuarios, "pedidos": pedidos},
                "versao": "1.0.0",
            }
        ),
        200,
    )
