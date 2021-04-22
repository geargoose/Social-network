import datetime

import sqlalchemy
from flask_login import UserMixin
from sqlalchemy import orm
from sqlalchemy_serializer import SerializerMixin
from werkzeug.security import generate_password_hash, check_password_hash

from .db_session import SqlAlchemyBase


#
# Определяем класс пользователя: таблица "users", определяем поля,
# создаём отношения к таблицам новотей, сообщений и комментариев. Добавляем функции
# set_password(password) для присваивания/изменения и check_password(password) для проверки пароля.
#


class User(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    about = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    email = sqlalchemy.Column(sqlalchemy.String,
                              index=True, unique=True, nullable=True)
    hashed_password = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    created_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    is_admin = sqlalchemy.Column(sqlalchemy.Boolean, default=0)
    is_group = sqlalchemy.Column(sqlalchemy.Boolean, default=0)
    is_confirmed = sqlalchemy.Column(sqlalchemy.Boolean, default=0)
    news = orm.relation("News", back_populates='user')
    msg = orm.relation("Message", back_populates='user', lazy='subquery')
    comm = orm.relation("Comment", back_populates='user')
    friends = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    f_request = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)
