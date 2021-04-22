from flask import jsonify, request, Blueprint

from . import db_session
from .users import User

API_KEY = '1fg8-8723-n58e-k2m9-d9ei'  # Ключ API.

blueprint = Blueprint(  # Подключаем API к проекту посредством Blueprint
    'users_api',
    __name__,
    template_folder='templates'
)


@blueprint.route('/api/users')  # Получение всех пользователей
def get_users():
    if dict(request.args.to_dict())['api_key'] != API_KEY:  # Проверяем API-ключ
        return jsonify({'error': 'Invalid API-key'})
    db_sess = db_session.create_session()
    users = db_sess.query(User).all()
    return jsonify(
        {
            'users':
                [item.to_dict(only=('name', 'about', 'email', 'hashed_password'))
                 for item in users]
        }
    )


@blueprint.route('/api/users/<int:users_id>', methods=['GET'])  # Получение пользователя с конкретным ID
def get_one_users(users_id):
    if dict(request.args.to_dict())['api_key'] != API_KEY:  # Проверяем API-ключ
        return jsonify({'error': 'Invalid API-key'})
    db_sess = db_session.create_session()
    users = db_sess.query(User).get(users_id)
    if not users:  # Проверка наличия пользователя с конкретным ID
        return jsonify({'error': 'Not found'})
    return jsonify(
        {
            'users': users.to_dict(only=(
                'name', 'about', 'email', 'hashed_password'))
        }
    )


@blueprint.route('/api/users', methods=['POST'])  # Добавление пользователя
def create_users():
    if not request.json:  # Если параметры не были отправлены (пустой запрос)
        return jsonify({'error': 'Empty request'})  # Empty request (англ.) - пустой запрос
    elif not all(key in request.json for key in ['api_key', 'title', 'content', 'user_id', 'is_private']):
        # Проверка наличия нужных параметров и отсутствия лишних
        return jsonify({'error': 'Bad request'})  # Bad request (англ.) - неправильный, плохой запрос
    if request.json['api_key'] != API_KEY:  # Проверяемп API-ключ
        return jsonify({'error': 'Invalid API-key'})  # Invalid API-key (англ.) - неверный ключ API
    db_sess = db_session.create_session()
    users = User(
        name=request.json['name'],
        about=request.json['about'],
        email=request.json['email'],
        hashed_password=request.json['hashed_password']
    )
    db_sess.add(users)
    db_sess.commit()
    return jsonify({'success': 'OK'})  # Если всё хорошо - даём об этом знать :-)


@blueprint.route('/api/users/<int:users_id>', methods=['DELETE'])  # Удаление пользователя с определённым ID
def delete_users(users_id):
    if dict(request.args.to_dict())['api_key'] != API_KEY:
        return jsonify({'error': 'Invalid API-key'})
    db_sess = db_session.create_session()
    users = db_sess.query(User).get(users_id)
    if not users:
        return jsonify({'error': 'Not found'})
    db_sess.delete(users)
    db_sess.commit()
    return jsonify({'success': 'OK'})


@blueprint.route('/api/users/<int:users_id>', methods=['PUT'])  # Редактирование пользователя с определённым ID
def edit_users(users_id):
    db_sess = db_session.create_session()
    users = db_sess.query(User).get(users_id)
    if not users:
        return jsonify({'error': 'Not found'})
    if not request.json:
        return jsonify({'error': 'Empty request'})
    elif not all(key in request.json for key in
                 ['api_key', 'title', 'content', 'user_id', 'is_private']):
        return jsonify({'error': 'Bad request'})
    if request.json['api_key'] != API_KEY:  # Проверяемп API-ключ
        return jsonify({'error': 'Invalid API-key'})
    db_sess = db_session.create_session()
    users = User(
        id=users_id,
        name=request.json['name'],
        about=request.json['about'],
        email=request.json['email'],
        hashed_password=request.json['hashed_password']
    )
    db_sess.merge(users)
    db_sess.commit()
    return jsonify({'success': 'OK'})
