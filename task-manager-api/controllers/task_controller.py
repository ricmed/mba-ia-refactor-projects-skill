import logging

from flask import request, jsonify

from database import db
from models.task import Task
from models.user import User
from models.category import Category
from datetime import datetime
from utils.helpers import VALID_STATUSES, MIN_TITLE_LENGTH, MAX_TITLE_LENGTH, parse_date

logger = logging.getLogger(__name__)


def get_tasks():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', type=int)

        query = Task.query.options(db.joinedload(Task.user), db.joinedload(Task.category))
        if per_page:
            query = query.limit(per_page).offset((page - 1) * per_page)

        tasks = query.all()
        result = [t.to_dict(include_relations=True) for t in tasks]
        return jsonify(result), 200
    except Exception as e:
        logger.exception("Erro ao listar tasks")
        return jsonify({'error': 'Erro interno'}), 500


def get_task(task_id):
    task = db.session.get(Task, task_id)
    if not task:
        return jsonify({'error': 'Task não encontrada'}), 404
    return jsonify(task.to_dict()), 200


def create_task():
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400

    title = data.get('title')
    if not title:
        return jsonify({'error': 'Título é obrigatório'}), 400
    if len(title) < MIN_TITLE_LENGTH:
        return jsonify({'error': 'Título muito curto'}), 400
    if len(title) > MAX_TITLE_LENGTH:
        return jsonify({'error': 'Título muito longo'}), 400

    description = data.get('description', '')
    status = data.get('status', 'pending')
    priority = data.get('priority', 3)
    user_id = data.get('user_id')
    category_id = data.get('category_id')
    due_date = data.get('due_date')
    tags = data.get('tags')

    if status not in VALID_STATUSES:
        return jsonify({'error': 'Status inválido'}), 400
    if priority < 1 or priority > 5:
        return jsonify({'error': 'Prioridade deve ser entre 1 e 5'}), 400

    if user_id and not db.session.get(User, user_id):
        return jsonify({'error': 'Usuário não encontrado'}), 404
    if category_id and not db.session.get(Category, category_id):
        return jsonify({'error': 'Categoria não encontrada'}), 404

    task = Task()
    task.title = title
    task.description = description
    task.status = status
    task.priority = priority
    task.user_id = user_id
    task.category_id = category_id

    if due_date:
        parsed = parse_date(due_date)
        if not parsed:
            return jsonify({'error': 'Formato de data inválido. Use YYYY-MM-DD'}), 400
        task.due_date = parsed

    if tags:
        task.tags = ','.join(tags) if isinstance(tags, list) else tags

    try:
        db.session.add(task)
        db.session.commit()
        logger.info("Task criada: %s - %s", task.id, task.title)
        return jsonify(task.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        logger.exception("Erro ao criar task")
        return jsonify({'error': 'Erro ao criar task'}), 500


def update_task(task_id):
    task = db.session.get(Task, task_id)
    if not task:
        return jsonify({'error': 'Task não encontrada'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400

    if 'title' in data:
        if len(data['title']) < MIN_TITLE_LENGTH:
            return jsonify({'error': 'Título muito curto'}), 400
        if len(data['title']) > MAX_TITLE_LENGTH:
            return jsonify({'error': 'Título muito longo'}), 400
        task.title = data['title']

    if 'description' in data:
        task.description = data['description']

    if 'status' in data:
        if data['status'] not in VALID_STATUSES:
            return jsonify({'error': 'Status inválido'}), 400
        task.status = data['status']

    if 'priority' in data:
        if data['priority'] < 1 or data['priority'] > 5:
            return jsonify({'error': 'Prioridade deve ser entre 1 e 5'}), 400
        task.priority = data['priority']

    if 'user_id' in data:
        if data['user_id'] and not db.session.get(User, data['user_id']):
            return jsonify({'error': 'Usuário não encontrado'}), 404
        task.user_id = data['user_id']

    if 'category_id' in data:
        if data['category_id'] and not db.session.get(Category, data['category_id']):
            return jsonify({'error': 'Categoria não encontrada'}), 404
        task.category_id = data['category_id']

    if 'due_date' in data:
        if data['due_date']:
            parsed = parse_date(data['due_date'])
            if not parsed:
                return jsonify({'error': 'Formato de data inválido'}), 400
            task.due_date = parsed
        else:
            task.due_date = None

    if 'tags' in data:
        task.tags = ','.join(data['tags']) if isinstance(data['tags'], list) else data['tags']

    task.updated_at = datetime.utcnow()

    try:
        db.session.commit()
        logger.info("Task atualizada: %s", task.id)
        return jsonify(task.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        logger.exception("Erro ao atualizar task")
        return jsonify({'error': 'Erro ao atualizar'}), 500


def delete_task(task_id):
    task = db.session.get(Task, task_id)
    if not task:
        return jsonify({'error': 'Task não encontrada'}), 404

    try:
        db.session.delete(task)
        db.session.commit()
        logger.info("Task deletada: %s", task_id)
        return jsonify({'message': 'Task deletada com sucesso'}), 200
    except Exception as e:
        db.session.rollback()
        logger.exception("Erro ao deletar task")
        return jsonify({'error': 'Erro ao deletar'}), 500


def search_tasks():
    query_text = request.args.get('q', '')
    status = request.args.get('status', '')
    priority = request.args.get('priority', '')
    user_id = request.args.get('user_id', '')

    tasks = Task.query

    if query_text:
        tasks = tasks.filter(
            db.or_(
                Task.title.like(f'%{query_text}%'),
                Task.description.like(f'%{query_text}%')
            )
        )
    if status:
        tasks = tasks.filter(Task.status == status)
    if priority:
        tasks = tasks.filter(Task.priority == int(priority))
    if user_id:
        tasks = tasks.filter(Task.user_id == int(user_id))

    output = [t.to_dict() for t in tasks.all()]
    return jsonify(output), 200


def task_stats():
    total = Task.query.count()
    pending = Task.query.filter_by(status='pending').count()
    in_progress = Task.query.filter_by(status='in_progress').count()
    done = Task.query.filter_by(status='done').count()
    cancelled = Task.query.filter_by(status='cancelled').count()

    overdue_count = sum(1 for t in Task.query.all() if t.is_overdue())

    stats = {
        'total': total,
        'pending': pending,
        'in_progress': in_progress,
        'done': done,
        'cancelled': cancelled,
        'overdue': overdue_count,
        'completion_rate': round((done / total) * 100, 2) if total > 0 else 0
    }

    return jsonify(stats), 200
