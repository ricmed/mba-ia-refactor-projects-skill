import logging

from flask import jsonify, request

from models import pedido_model

logger = logging.getLogger(__name__)


def criar_pedido():
    dados = request.get_json(silent=True)

    if not dados:
        return jsonify({"erro": "Dados inválidos", "sucesso": False}), 400

    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])

    if not usuario_id:
        return jsonify({"erro": "Usuario ID é obrigatório", "sucesso": False}), 400
    if not itens:
        return jsonify({"erro": "Pedido deve ter pelo menos 1 item", "sucesso": False}), 400

    resultado = pedido_model.create(usuario_id, itens)

    if "erro" in resultado:
        return jsonify({"erro": resultado["erro"], "sucesso": False}), 400

    logger.info("Pedido %s criado para usuário %s — notificações enfileiradas", resultado["pedido_id"], usuario_id)

    return jsonify({"dados": resultado, "sucesso": True, "mensagem": "Pedido criado com sucesso"}), 201


def listar_pedidos_usuario(usuario_id):
    pedidos = pedido_model.get_by_user(usuario_id)
    return jsonify({"dados": pedidos, "sucesso": True}), 200


def listar_todos_pedidos():
    limit = request.args.get("limit", type=int)
    offset = request.args.get("offset", 0, type=int)
    pedidos = pedido_model.get_all(limit=limit, offset=offset)
    return jsonify({"dados": pedidos, "sucesso": True}), 200


def atualizar_status_pedido(pedido_id):
    dados = request.get_json(silent=True) or {}
    novo_status = dados.get("status", "")

    if novo_status not in pedido_model.STATUS_VALIDOS:
        return jsonify({"erro": "Status inválido", "sucesso": False}), 400

    pedido_model.update_status(pedido_id, novo_status)

    if novo_status == "aprovado":
        logger.info("Pedido %s aprovado — preparar envio", pedido_id)
    elif novo_status == "cancelado":
        logger.info("Pedido %s cancelado — devolver estoque", pedido_id)

    return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200


def relatorio_vendas():
    relatorio = pedido_model.relatorio_vendas()
    return jsonify({"dados": relatorio, "sucesso": True}), 200
