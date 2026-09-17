from werkzeug.security import check_password_hash, generate_password_hash

from config.database import get_db


def _row_to_dict_public(row):
    """Serialização segura: nunca inclui o hash de senha."""
    return {
        "id": row["id"],
        "nome": row["nome"],
        "email": row["email"],
        "tipo": row["tipo"],
        "criado_em": row["criado_em"],
    }


def get_all(limit=None, offset=0):
    db = get_db()
    cursor = db.cursor()
    if limit is not None:
        cursor.execute("SELECT * FROM usuarios LIMIT ? OFFSET ?", (limit, offset))
    else:
        cursor.execute("SELECT * FROM usuarios")
    return [_row_to_dict_public(row) for row in cursor.fetchall()]


def get_by_id(usuario_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,))
    row = cursor.fetchone()
    return _row_to_dict_public(row) if row else None


def get_by_email(email):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
    return cursor.fetchone()


def create(nome, email, senha, tipo="cliente"):
    db = get_db()
    cursor = db.cursor()
    senha_hash = generate_password_hash(senha)
    cursor.execute(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
        (nome, email, senha_hash, tipo),
    )
    db.commit()
    return cursor.lastrowid


def authenticate(email, senha):
    row = get_by_email(email)
    if row and check_password_hash(row["senha"], senha):
        return {"id": row["id"], "nome": row["nome"], "email": row["email"], "tipo": row["tipo"]}
    return None
