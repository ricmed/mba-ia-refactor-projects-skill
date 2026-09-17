from flask import jsonify
from sqlalchemy import func

from database import db
from models.task import Task
from models.user import User
from models.category import Category
from datetime import datetime, timedelta


def summary_report():
    total_tasks = Task.query.count()
    total_users = User.query.count()
    total_categories = Category.query.count()

    pending = Task.query.filter_by(status='pending').count()
    in_progress = Task.query.filter_by(status='in_progress').count()
    done = Task.query.filter_by(status='done').count()
    cancelled = Task.query.filter_by(status='cancelled').count()

    priority_counts = dict(
        db.session.query(Task.priority, func.count(Task.id)).group_by(Task.priority).all()
    )

    all_tasks = Task.query.all()
    overdue_list = [
        {
            'id': t.id,
            'title': t.title,
            'due_date': str(t.due_date),
            'days_overdue': (datetime.utcnow() - t.due_date).days,
        }
        for t in all_tasks
        if t.is_overdue()
    ]

    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_tasks = Task.query.filter(Task.created_at >= seven_days_ago).count()
    recent_done = Task.query.filter(
        Task.status == 'done',
        Task.updated_at >= seven_days_ago
    ).count()

    # Agregação em 2 queries (em vez de 1 query de tasks por usuário) — resolve o N+1.
    total_by_user = dict(
        db.session.query(Task.user_id, func.count(Task.id)).group_by(Task.user_id).all()
    )
    completed_by_user = dict(
        db.session.query(Task.user_id, func.count(Task.id))
        .filter(Task.status == 'done')
        .group_by(Task.user_id)
        .all()
    )

    user_stats = []
    for u in User.query.all():
        total = total_by_user.get(u.id, 0)
        completed = completed_by_user.get(u.id, 0)
        user_stats.append({
            'user_id': u.id,
            'user_name': u.name,
            'total_tasks': total,
            'completed_tasks': completed,
            'completion_rate': round((completed / total) * 100, 2) if total > 0 else 0
        })

    report = {
        'generated_at': str(datetime.utcnow()),
        'overview': {
            'total_tasks': total_tasks,
            'total_users': total_users,
            'total_categories': total_categories,
        },
        'tasks_by_status': {
            'pending': pending,
            'in_progress': in_progress,
            'done': done,
            'cancelled': cancelled,
        },
        'tasks_by_priority': {
            'critical': priority_counts.get(1, 0),
            'high': priority_counts.get(2, 0),
            'medium': priority_counts.get(3, 0),
            'low': priority_counts.get(4, 0),
            'minimal': priority_counts.get(5, 0),
        },
        'overdue': {
            'count': len(overdue_list),
            'tasks': overdue_list,
        },
        'recent_activity': {
            'tasks_created_last_7_days': recent_tasks,
            'tasks_completed_last_7_days': recent_done,
        },
        'user_productivity': user_stats,
    }

    return jsonify(report), 200


def user_report(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404

    tasks = Task.query.filter_by(user_id=user_id).all()

    status_counts = {'done': 0, 'pending': 0, 'in_progress': 0, 'cancelled': 0}
    high_priority = 0
    overdue = 0

    for t in tasks:
        if t.status in status_counts:
            status_counts[t.status] += 1
        if t.priority <= 2:
            high_priority += 1
        if t.is_overdue():
            overdue += 1

    total = len(tasks)
    report = {
        'user': {'id': user.id, 'name': user.name, 'email': user.email},
        'statistics': {
            'total_tasks': total,
            **status_counts,
            'overdue': overdue,
            'high_priority': high_priority,
            'completion_rate': round((status_counts['done'] / total) * 100, 2) if total > 0 else 0
        }
    }

    return jsonify(report), 200
