import logging

from flask import jsonify, request

from models import usuario_model

logger = logging.getLogger(__name__)


def listar_usuarios():
    limit = request.args.get("limit", type=int)
    offset = request.args.get("offset", 0, type=int)
    usuarios = usuario_model.get_all(limit=limit, offset=offset)
    return jsonify({"dados": usuarios, "sucesso": True}), 200


def buscar_usuario(id):
    usuario = usuario_model.get_by_id(id)
    if usuario:
        return jsonify({"dados": usuario, "sucesso": True}), 200
    return jsonify({"erro": "Usuário não encontrado", "sucesso": False}), 404


def criar_usuario():
    dados = request.get_json(silent=True)

    if not dados:
        return jsonify({"erro": "Dados inválidos", "sucesso": False}), 400

    nome = dados.get("nome", "")
    email = dados.get("email", "")
    senha = dados.get("senha", "")

    if not nome or not email or not senha:
        return jsonify({"erro": "Nome, email e senha são obrigatórios", "sucesso": False}), 400

    novo_id = usuario_model.create(nome, email, senha)
    logger.info("Usuário criado: %s", email)
    return jsonify({"dados": {"id": novo_id}, "sucesso": True}), 201


def login():
    dados = request.get_json(silent=True) or {}
    email = dados.get("email", "")
    senha = dados.get("senha", "")

    if not email or not senha:
        return jsonify({"erro": "Email e senha são obrigatórios", "sucesso": False}), 400

    usuario = usuario_model.authenticate(email, senha)
    if usuario:
        logger.info("Login bem-sucedido: %s", email)
        return jsonify({"dados": usuario, "sucesso": True, "mensagem": "Login OK"}), 200

    logger.warning("Login falhou: %s", email)
    return jsonify({"erro": "Email ou senha inválidos", "sucesso": False}), 401
