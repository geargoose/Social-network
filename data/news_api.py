from flask import jsonify, request, Blueprint

from . import db_session
from .news import News

API_KEY = '1fg8-8723-n58e-k2m9-d9ei'  # Ключ API.

blueprint = Blueprint(  # Подключаем API к проекту посредством Blueprint
    'news_api',
    __name__,
    template_folder='templates'
)


@blueprint.route('/api/news')  # Получение всех новостей
def get_news():
    if dict(request.args.to_dict())['api_key'] != API_KEY:  # Проверяем API-ключ
        return jsonify({'error': 'Invalid API-key'})
    db_sess = db_session.create_session()
    news = db_sess.query(News).all()
    return jsonify(
        {
            'news':
                [item.to_dict(only=('title', 'content', 'user.name'))
                 for item in news]
        }
    )


@blueprint.route('/api/news/<int:news_id>', methods=['GET'])  # Получение новости с конкретным ID
def get_one_news(news_id):
    if dict(request.args.to_dict())['api_key'] != API_KEY:  # Проверяем API-ключ
        return jsonify({'error': 'Invalid API-key'})
    db_sess = db_session.create_session()
    news = db_sess.query(News).get(news_id)
    if not news:  # Проверка наличия новости с конкретным ID
        return jsonify({'error': 'Not found'})
    return jsonify(
        {
            'news': news.to_dict(only=(
                'title', 'content', 'user_id', 'is_private'))
        }
    )


@blueprint.route('/api/news', methods=['POST'])  # Добавление новости
def create_news():
    if not request.json:  # Если параметры не были отправлены (пустой запрос)
        return jsonify({'error': 'Empty request'})  # Empty request (англ.) - пустой запрос
    elif not all(key in request.json for key in ['api_key', 'title', 'content', 'user_id', 'is_private']):
        # Проверка наличия нужных параметров и отсутствия лишних
        return jsonify({'error': 'Bad request'})  # Bad request (англ.) - неправильный, плохой запрос
    if request.json['api_key'] != API_KEY:  # Проверяем API-ключ
        return jsonify({'error': 'Invalid API-key'})  # Invalid API-key (англ.) - неверный ключ API
    db_sess = db_session.create_session()
    news = News(
        title=request.json['title'],
        content=request.json['content'],
        user_id=request.json['user_id'],
        is_private=request.json['is_private']
    )
    db_sess.add(news)
    db_sess.commit()
    return jsonify({'success': 'OK'})  # Если всё хорошо - даём об этом знать :-)


@blueprint.route('/api/news/<int:news_id>', methods=['DELETE'])  # Удаление новости с определённым ID
def delete_news(news_id):
    if dict(request.args.to_dict())['api_key'] != API_KEY:  # Проверяем API-ключ
        return jsonify({'error': 'Invalid API-key'})
    db_sess = db_session.create_session()
    news = db_sess.query(News).get(news_id)
    if not news:  # Проверка наличия новости с конкретным ID
        return jsonify({'error': 'Not found'})
    db_sess.delete(news)
    db_sess.commit()
    return jsonify({'success': 'OK'})


@blueprint.route('/api/news/<int:news_id>', methods=['PUT'])  # Изменение новости с определённым ID
def edit_news(news_id):
    db_sess = db_session.create_session()
    news = db_sess.query(News).get(news_id)
    if not news:
        return jsonify({'error': 'Not found'})
    if not request.json:
        return jsonify({'error': 'Empty request'})
    elif not all(key in request.json for key in  # Проверка наличия нужных параметров и отсутствия лишних
                 ['api_key', 'title', 'content', 'user_id', 'is_private']):
        return jsonify({'error': 'Bad request'})
    if request.json['api_key'] != API_KEY:  # Проверяем API-ключ
        return jsonify({'error': 'Invalid API-key'})
    db_sess = db_session.create_session()
    news = News(
        id=news_id,
        title=request.json['title'],
        content=request.json['content'],
        user_id=request.json['user_id'],
        is_private=request.json['is_private']
    )
    db_sess.merge(news)
    db_sess.commit()
    return jsonify({'success': 'OK'})
