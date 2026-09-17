import logging
from datetime import datetime, timedelta, timezone

import jwt
from flask import request, jsonify

from config.settings import Settings
from database import db
from models.user import User
from models.task import Task
from utils.helpers import VALID_ROLES, MIN_PASSWORD_LENGTH, validate_email

logger = logging.getLogger(__name__)


def _generate_token(user):
    payload = {
        'sub': user.id,
        'role': user.role,
        'exp': datetime.now(timezone.utc) + timedelta(hours=8),
    }
    return jwt.encode(payload, Settings.SECRET_KEY, algorithm='HS256')


def get_users():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', type=int)

    query = User.query
    if per_page:
        query = query.limit(per_page).offset((page - 1) * per_page)

    users = query.all()
    result = []
    for u in users:
        user_data = u.to_dict()
        user_data['task_count'] = len(u.tasks)
        result.append(user_data)
    return jsonify(result), 200


def get_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404

    data = user.to_dict()
    data['tasks'] = [t.to_dict() for t in Task.query.filter_by(user_id=user_id).all()]
    return jsonify(data), 200


def create_user():
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400

    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'user')

    if not name:
        return jsonify({'error': 'Nome é obrigatório'}), 400
    if not email:
        return jsonify({'error': 'Email é obrigatório'}), 400
    if not password:
        return jsonify({'error': 'Senha é obrigatória'}), 400
    if not validate_email(email):
        return jsonify({'error': 'Email inválido'}), 400
    if len(password) < MIN_PASSWORD_LENGTH:
        return jsonify({'error': f'Senha deve ter no mínimo {MIN_PASSWORD_LENGTH} caracteres'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email já cadastrado'}), 409
    if role not in VALID_ROLES:
        return jsonify({'error': 'Role inválido'}), 400

    user = User()
    user.name = name
    user.email = email
    user.set_password(password)
    user.role = role

    try:
        db.session.add(user)
        db.session.commit()
        logger.info("Usuário criado: %s - %s", user.id, user.name)
        return jsonify(user.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        logger.exception("Erro ao criar usuário")
        return jsonify({'error': 'Erro ao criar usuário'}), 500


def update_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400

    if 'name' in data:
        user.name = data['name']

    if 'email' in data:
        if not validate_email(data['email']):
            return jsonify({'error': 'Email inválido'}), 400
        existing = User.query.filter_by(email=data['email']).first()
        if existing and existing.id != user_id:
            return jsonify({'error': 'Email já cadastrado'}), 409
        user.email = data['email']

    if 'password' in data:
        if len(data['password']) < MIN_PASSWORD_LENGTH:
            return jsonify({'error': 'Senha muito curta'}), 400
        user.set_password(data['password'])

    if 'role' in data:
        if data['role'] not in VALID_ROLES:
            return jsonify({'error': 'Role inválido'}), 400
        user.role = data['role']

    if 'active' in data:
        user.active = data['active']

    try:
        db.session.commit()
        return jsonify(user.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        logger.exception("Erro ao atualizar usuário")
        return jsonify({'error': 'Erro ao atualizar'}), 500


def delete_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404

    tasks = Task.query.filter_by(user_id=user_id).all()
    for t in tasks:
        db.session.delete(t)

    try:
        db.session.delete(user)
        db.session.commit()
        logger.info("Usuário deletado: %s", user_id)
        return jsonify({'message': 'Usuário deletado com sucesso'}), 200
    except Exception as e:
        db.session.rollback()
        logger.exception("Erro ao deletar usuário")
        return jsonify({'error': 'Erro ao deletar'}), 500


def get_user_tasks(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404

    tasks = Task.query.filter_by(user_id=user_id).all()
    result = [t.to_dict() for t in tasks]
    return jsonify(result), 200


def login():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400

    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'Email e senha são obrigatórios'}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({'error': 'Credenciais inválidas'}), 401

    if not user.active:
        return jsonify({'error': 'Usuário inativo'}), 403

    return jsonify({
        'message': 'Login realizado com sucesso',
        'user': user.to_dict(),
        'token': _generate_token(user)
    }), 200
