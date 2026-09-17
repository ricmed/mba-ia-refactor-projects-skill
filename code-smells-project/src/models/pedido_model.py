from config.database import get_db

STATUS_VALIDOS = ["pendente", "aprovado", "enviado", "entregue", "cancelado"]

# (limiar de faturamento, percentual de desconto aplicável)
FAIXAS_DESCONTO = [
    (10000, 0.10),
    (5000, 0.05),
    (1000, 0.02),
]


def _fetch_pedidos(where_clause="", params=()):
    """Busca pedidos + itens + nome do produto em uma única query com JOIN,
    evitando o N+1 do código original (1 query por pedido + 1 por item)."""
    db = get_db()
    cursor = db.cursor()
    query = f"""
        SELECT p.id AS pedido_id, p.usuario_id, p.status, p.total, p.criado_em,
               ip.produto_id, ip.quantidade, ip.preco_unitario, pr.nome AS produto_nome
        FROM pedidos p
        LEFT JOIN itens_pedido ip ON ip.pedido_id = p.id
        LEFT JOIN produtos pr ON pr.id = ip.produto_id
        {where_clause}
        ORDER BY p.id
    """
    cursor.execute(query, params)

    pedidos = {}
    for row in cursor.fetchall():
        pid = row["pedido_id"]
        if pid not in pedidos:
            pedidos[pid] = {
                "id": pid,
                "usuario_id": row["usuario_id"],
                "status": row["status"],
                "total": row["total"],
                "criado_em": row["criado_em"],
                "itens": [],
            }
        if row["produto_id"] is not None:
            pedidos[pid]["itens"].append(
                {
                    "produto_id": row["produto_id"],
                    "produto_nome": row["produto_nome"] or "Desconhecido",
                    "quantidade": row["quantidade"],
                    "preco_unitario": row["preco_unitario"],
                }
            )
    return list(pedidos.values())


def get_by_user(usuario_id):
    return _fetch_pedidos("WHERE p.usuario_id = ?", (usuario_id,))


def get_all(limit=None, offset=0):
    pedidos = _fetch_pedidos()
    if limit is not None:
        return pedidos[offset : offset + limit]
    return pedidos


def create(usuario_id, itens):
    db = get_db()
    cursor = db.cursor()

    total = 0
    produtos_cache = {}
    for item in itens:
        cursor.execute("SELECT * FROM produtos WHERE id = ?", (item["produto_id"],))
        produto = cursor.fetchone()
        if produto is None:
            return {"erro": f"Produto {item['produto_id']} não encontrado"}
        if produto["estoque"] < item["quantidade"]:
            return {"erro": f"Estoque insuficiente para {produto['nome']}"}
        produtos_cache[item["produto_id"]] = produto
        total += produto["preco"] * item["quantidade"]

    cursor.execute(
        "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, 'pendente', ?)",
        (usuario_id, total),
    )
    pedido_id = cursor.lastrowid

    for item in itens:
        produto = produtos_cache[item["produto_id"]]
        cursor.execute(
            "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
            (pedido_id, item["produto_id"], item["quantidade"], produto["preco"]),
        )
        cursor.execute(
            "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
            (item["quantidade"], item["produto_id"]),
        )

    db.commit()
    return {"pedido_id": pedido_id, "total": total}


def update_status(pedido_id, novo_status):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id))
    db.commit()
    return True


def _calcular_desconto(faturamento):
    for limiar, percentual in FAIXAS_DESCONTO:
        if faturamento > limiar:
            return faturamento * percentual
    return 0


def relatorio_vendas():
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT COUNT(*) FROM pedidos")
    total_pedidos = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(total) FROM pedidos")
    faturamento = cursor.fetchone()[0] or 0

    cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status = 'pendente'")
    pendentes = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status = 'aprovado'")
    aprovados = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status = 'cancelado'")
    cancelados = cursor.fetchone()[0]

    desconto = _calcular_desconto(faturamento)

    return {
        "total_pedidos": total_pedidos,
        "faturamento_bruto": round(faturamento, 2),
        "desconto_aplicavel": round(desconto, 2),
        "faturamento_liquido": round(faturamento - desconto, 2),
        "pedidos_pendentes": pendentes,
        "pedidos_aprovados": aprovados,
        "pedidos_cancelados": cancelados,
        "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0,
    }
