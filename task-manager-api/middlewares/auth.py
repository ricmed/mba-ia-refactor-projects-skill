from functools import wraps

import jwt
from flask import jsonify, request

from config.settings import Settings


def require_auth(fn):
    """Decorator pronto para proteger rotas com o JWT real emitido em /login.

    Não aplicado a nenhuma rota nesta refatoração para não quebrar o contrato
    de API existente (nenhum endpoint exigia token antes) — ver finding HIGH
    "Autenticação Falsa" em reports/audit-project-3.md. Fica disponível para
    ser adotado incrementalmente rota a rota.
    """

    @wraps(fn)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Token ausente'}), 401
        token = auth_header.split(' ', 1)[1]
        try:
            jwt.decode(token, Settings.SECRET_KEY, algorithms=['HS256'])
        except jwt.PyJWTError:
            return jsonify({'error': 'Token inválido ou expirado'}), 401
        return fn(*args, **kwargs)

    return wrapper
