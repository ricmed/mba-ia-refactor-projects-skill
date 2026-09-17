import logging

from flask import jsonify, request

from models import produto_model

logger = logging.getLogger(__name__)


def listar_produtos():
    limit = request.args.get("limit", type=int)
    offset = request.args.get("offset", 0, type=int)
    produtos = produto_model.get_all(limit=limit, offset=offset)
    logger.info("Listando %d produtos", len(produtos))
    return jsonify({"dados": produtos, "sucesso": True}), 200


def buscar_produto(id):
    produto = produto_model.get_by_id(id)
    if produto:
        return jsonify({"dados": produto, "sucesso": True}), 200
    return jsonify({"erro": "Produto não encontrado", "sucesso": False}), 404


def criar_produto():
    dados = request.get_json(silent=True)

    if not dados:
        return jsonify({"erro": "Dados inválidos", "sucesso": False}), 400
    if "nome" not in dados:
        return jsonify({"erro": "Nome é obrigatório", "sucesso": False}), 400
    if "preco" not in dados:
        return jsonify({"erro": "Preço é obrigatório", "sucesso": False}), 400
    if "estoque" not in dados:
        return jsonify({"erro": "Estoque é obrigatório", "sucesso": False}), 400

    nome = dados["nome"]
    descricao = dados.get("descricao", "")
    preco = dados["preco"]
    estoque = dados["estoque"]
    categoria = dados.get("categoria", "geral")

    if preco < 0:
        return jsonify({"erro": "Preço não pode ser negativo", "sucesso": False}), 400
    if estoque < 0:
        return jsonify({"erro": "Estoque não pode ser negativo", "sucesso": False}), 400
    if len(nome) < 2:
        return jsonify({"erro": "Nome muito curto", "sucesso": False}), 400
    if len(nome) > 200:
        return jsonify({"erro": "Nome muito longo", "sucesso": False}), 400
    if categoria not in produto_model.CATEGORIAS_VALIDAS:
        return jsonify(
            {"erro": f"Categoria inválida. Válidas: {produto_model.CATEGORIAS_VALIDAS}", "sucesso": False}
        ), 400

    novo_id = produto_model.create(nome, descricao, preco, estoque, categoria)
    logger.info("Produto criado com ID: %s", novo_id)
    return jsonify({"dados": {"id": novo_id}, "sucesso": True, "mensagem": "Produto criado"}), 201


def atualizar_produto(id):
    dados = request.get_json(silent=True)

    produto_existente = produto_model.get_by_id(id)
    if not produto_existente:
        return jsonify({"erro": "Produto não encontrado", "sucesso": False}), 404

    if not dados:
        return jsonify({"erro": "Dados inválidos", "sucesso": False}), 400
    if "nome" not in dados:
        return jsonify({"erro": "Nome é obrigatório", "sucesso": False}), 400
    if "preco" not in dados:
        return jsonify({"erro": "Preço é obrigatório", "sucesso": False}), 400
    if "estoque" not in dados:
        return jsonify({"erro": "Estoque é obrigatório", "sucesso": False}), 400

    nome = dados["nome"]
    descricao = dados.get("descricao", "")
    preco = dados["preco"]
    estoque = dados["estoque"]
    categoria = dados.get("categoria", "geral")

    if preco < 0:
        return jsonify({"erro": "Preço não pode ser negativo", "sucesso": False}), 400
    if estoque < 0:
        return jsonify({"erro": "Estoque não pode ser negativo", "sucesso": False}), 400

    produto_model.update(id, nome, descricao, preco, estoque, categoria)
    return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200


def deletar_produto(id):
    produto = produto_model.get_by_id(id)
    if not produto:
        return jsonify({"erro": "Produto não encontrado", "sucesso": False}), 404

    produto_model.delete(id)
    logger.info("Produto %s deletado", id)
    return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200


def buscar_produtos():
    termo = request.args.get("q", "")
    categoria = request.args.get("categoria", None)
    preco_min = request.args.get("preco_min", None, type=float)
    preco_max = request.args.get("preco_max", None, type=float)

    resultados = produto_model.search(termo, categoria, preco_min, preco_max)
    return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200
