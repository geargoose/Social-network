import os
import time
from urllib.parse import unquote

from flask import *
from flask_login import login_user, LoginManager, current_user, login_required, logout_user
from flask_ngrok import run_with_ngrok
from flask_socketio import SocketIO
from werkzeug.utils import secure_filename

from data import db_session, news_api, users_api
from data.comms import Comment
from data.msg import Message
from data.news import News
from data.users import User
from forms.comms import *
from forms.news import *
from forms.user import *

db_session.global_init("db/blogs.db")

app = Flask(__name__)
app.config['SECRET_KEY'] = 'meow'  # Секретный ключ на то и секретный, что знает его только разработчик.

socketio = SocketIO(app)  # Запускаем SocketIO, который позволяет получать информацию о новых сообщениях "на лету".

login_manager = LoginManager()  # LoginManager для авторизации пользователей.
login_manager.init_app(app)


@login_manager.user_loader  # Определяем, авторизован ли пользователь в системе или он на сайте как гость.
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@login_manager.unauthorized_handler  # Если гость хочет залезть на страничку только для зарегистрированных - запрещаем!
def unauthorized_callback():
    return redirect('/login')  # Отправляем гостя на авторизацию.


@app.route("/<int:prof_id>", methods=['GET', 'POST'])  # Профиль
@login_required  # Только для авторизованных!
def index(prof_id):
    session['from_page'] = f'/{prof_id}'  # Объявляем переменные, подключаем базу данных, собираем данные
    form = NewsForm()
    commsform = CommsForm()
    db_sess = db_session.create_session()
    comms = db_sess.query(Comment).all()
    prof_user = db_sess.query(User).filter(User.id == prof_id)  # Получаем ИД пользователя, в профиль которого мы зашли
    if current_user.is_authenticated:  # Если пользователь аутентифицирован
        news = db_sess.query(News).filter(
            News.user.has(id=prof_id)).order_by(News.created_date.desc())
        if form.validate_on_submit():  # Форма для создания новости
            attachments = []
            f = request.files['file']
            if f:  # Работаем с вложениями: называем каждое вложение, сохраняем в папку
                # print(request.files.to_dict(flat=False)['file'])
                files = request.files.to_dict(flat=False)['file']
                for file in files:
                    filename = secure_filename(
                        f'{str(time.time()).replace(".", "-")}.png')
                    attachments.append(filename)
                    # print(filename)
                    file.save('static/attachments/' + filename)
            db_sess = db_session.create_session()
            news = News()  # Добавляем данные к экземпляру класса News данные и сохраняем
            news.title = form.title.data
            news.content = form.content.data
            news.is_private = form.is_private.data
            news.attach = '|'.join(attachments)
            current_user.news.append(news)
            db_sess.merge(current_user)
            db_sess.commit()
            return redirect(f'/{prof_id}')
        if commsform.validate_on_submit():  # Форма для комментариев
            db_sess = db_session.create_session()
            comm = Comment()  # Добавляем данные к экземпляру класса Comment данные и сохраняем
            comm.to = commsform.to.data
            comm.content = commsform.content.data
            current_user.comm.append(comm)
            db_sess.merge(current_user)
            db_sess.commit()
            return redirect(f'/{prof_id}')
    else:  # Иначе отправляем все новости
        news = db_sess.query(News).filter(
            News.is_private != True).order_by(News.created_date.desc())
    return render_template("profile.html",
                           news=news, form=form,
                           profile_id=prof_id, profile_user=prof_user,
                           comments=comms, commsform=commsform
                           )


@app.route('/uploader', methods=['GET', 'POST'])  # Загрузка аватара пользователя
def uploader():
    if request.method == 'POST':  # Если отправлено изображение, называем и сохраняем сохраняем его.
        f = request.files['file']
        # ext = f.filename.split('.')[-1]
        f.save('static/userpics/' + secure_filename(f'{current_user.id}.png'))
        return redirect(f'/{current_user.id}')


@app.route("/", methods=['GET', 'POST'])  # Домашняя страница
@app.route("/feed", methods=['GET', 'POST'])  # Альтернативный адрес к странице
def feed():
    session['from_page'] = f'/feed'
    form = NewsForm()  # Подключаем нужные формы
    commsform = CommsForm()
    db_sess = db_session.create_session()
    comms = db_sess.query(Comment).all()

    if current_user.is_authenticated:
        news = db_sess.query(News).filter(
            (News.user == current_user) | (News.is_private != True)).order_by(
            News.created_date.desc())  # Достаём новости из БД
        if form.validate_on_submit():  # Форма добавления новости
            attachments = []
            f = request.files['file']
            if f:
                files = request.files.to_dict(flat=False)['file']
                for file in files:
                    print(file.filename)
                    filename = secure_filename(
                        f'{str(time.time()).replace(".", "-")}-{file.filename}')
                    ftype = ''
                    if filename.endswith('png') or filename.endswith('jpg') \
                            or filename.endswith('jpeg') or filename.endswith('bmp') \
                            or filename.endswith('mp4') or filename.endswith('mov') \
                            or filename.endswith('avi') or filename.endswith('wav') \
                            or filename.endswith('mp3'):
                        ftype = 'media'
                    attachments.append(f'{ftype}{filename}')
                    # print(filename)
                    file.save('static/attachments/' + f'{ftype}{filename}')
            db_sess = db_session.create_session()
            news = News()
            news.title = form.title.data
            news.content = form.content.data
            news.is_private = form.is_private.data
            news.attach = '|'.join(attachments)
            current_user.news.append(news)
            db_sess.merge(current_user)
            db_sess.commit()
            return redirect('/feed')
        if commsform.validate_on_submit():  # Отправка комментария
            db_sess = db_session.create_session()
            comm = Comment()
            comm.to = commsform.to.data
            comm.content = commsform.content.data
            current_user.comm.append(comm)
            db_sess.merge(current_user)
            db_sess.commit()
            return redirect(f'/feed#{comm.to}')
    else:
        news = db_sess.query(News).filter(
            News.is_private != True).order_by(News.created_date.desc())
    return render_template("feed.html",
                           news=news,
                           form=form,
                           comments=comms,
                           commsform=commsform)


@app.route('/register', methods=['GET', 'POST'])  # Регистрация
def reqister():
    form = RegisterForm()  # Подключаем форму
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:  # Совпадает ли пароль
            return render_template(
                'register.html',
                title='Регистрация',
                form=form,
                message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():  # Проверка на дубликат - двух одинаковых
            # пользователей быть не должно!
            return render_template(
                'register.html',
                title='Регистрация',
                form=form,
                message="Такой пользователь уже есть")
        user = User(  # Добавляем,сохраняем
            name=form.name.data,
            email=form.email.data,
            about=form.about.data
        )
        user.set_password(form.password.data)  # Сохраняем пароль
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация',
                           form=form)


@app.route('/login/change', methods=['GET', 'POST'])  # Изменение пароля
@login_required
def ch_pass():
    form = ChangePassForm()  # Форма и принцип работы сходны со страницей регистрации.
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.id == current_user.id).first()
        print(user.check_password(form.password_old.data))
        if form.password.data != form.password_again.data:
            return render_template(
                'ch_pass.html',
                title='Смена пароля',
                form=form,
                message="Пароли не совпадают")
        if user and not user.check_password(form.password_old.data):
            return render_template(
                'ch_pass.html',
                title='Смена пароля',
                form=form,
                message="Неверный текущий пароль")
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect(f'/{current_user.id}')
    return render_template('ch_pass.html', title='Смена пароля',
                           form=form)


@app.route('/login', methods=['GET', 'POST'])  # Авторизация
def login():
    form = LoginForm()  # Форма авторизации
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(
            User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',  # Если логин или пароль неверные - говорим об этом
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Изменение пароля',
                           form=form)


@app.route('/logout')  # Выход из учётной записи
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/news', methods=['GET', 'POST'])  # Редактор новостей
@login_required
def add_news():
    form = NewsForm()
    if form.validate_on_submit():
        attachments = []
        f = request.files['file']
        if f:
            files = request.files.to_dict(flat=False)['file']
            for file in files:
                print(file.filename)  # Обработка приложенных файлов
                filename = secure_filename(
                    f'{str(time.time()).replace(".", "-")}-{file.filename}')
                attachments.append(filename)
                # print(filename)
                file.save('static/attachments/' + filename)
        db_sess = db_session.create_session()  # Сохранение и отправка
        news = News()
        news.title = form.title.data
        news.content = form.content.data
        news.is_private = form.is_private.data
        news.attach = '|'.join(attachments)
        current_user.news.append(news)
        db_sess.merge(current_user)
        db_sess.commit()
        return redirect('/feed')
    return render_template('news.html',
                           title='Добавление новости',
                           form=form)


@app.route('/news/delete/<int:id>', methods=['GET', 'POST'])  # Удаление новости
@login_required
def news_delete(id):
    db_sess = db_session.create_session()
    news = db_sess.query(News).filter(
        News.id == id, ((News.user == current_user) | current_user.is_admin)).first()
    if news:
        # print(news.attach)
        try:
            for i in news.attach.split('|'):
                os.remove(f'static/attachments/{i}')  # Удаляем вложения, которые больше не нужны
        except Exception as e:
            str(e)
        db_sess.delete(news)
        db_sess.commit()
    else:
        # abort(403)
        redirect('/login')
    if session.get('from_page', None) == '/feed':
        return redirect(f'/feed#{id - 1}')  # Возвращаемся к моменту, на котором остановились
    else:
        return redirect(session.get('from_page', f'/feed#{id - 1}'))


@app.route('/comments/delete/<int:id>', methods=['GET', 'POST'])  # Удаление комментария
@login_required
def comms_delete(id):
    db_sess = db_session.create_session()
    comms = db_sess.query(Comment).filter(Comment.id == id,
                                          ((Comment.user == current_user)
                                           | current_user.is_admin)).first()
    if comms:
        db_sess.delete(comms)
        db_sess.commit()
    else:
        # abort(403)
        redirect('/login')
    if session.get('from_page', None) == '/feed':
        return redirect(f'/feed#{comms.to}')  # Возвращаемся к моменту, на котором остановились
    else:
        return redirect(session.get('from_page', f'/feed#{comms.to}'))


@app.route('/news/like/<int:id>', methods=['GET', 'POST'])  # "лайкаем" новости
@login_required
def news_like(id):
    db_sess = db_session.create_session()
    news = db_sess.query(News).filter(News.id == id).first()
    if news:
        if news.liked_by:  # Добавляем имя пользователя к списку лайкнувших новость
            if current_user.name not in news.liked_by.split('|'):
                news.liked_by += '|' + current_user.name
        else:
            news.liked_by = current_user.name

        news.likes = len(news.liked_by.split('|'))  # Обновляем кол-во лайков
        db_sess.commit()
    else:
        # abort(403)
        redirect('/login')
    if session.get('from_page', None) == '/feed':
        return redirect(f'/feed#{id}')
    else:
        return redirect(session.get('from_page', f'/feed#{id}'))


@app.route('/news/unlike/<int:id>', methods=['GET', 'POST'])  # Отменить лайк
@login_required
def news_unlike(id):
    db_sess = db_session.create_session()
    news = db_sess.query(News).filter(News.id == id).first()
    if news:
        if news.liked_by:  # Удаляем имя пользователя из списка людей, отметивших новость
            a = news.liked_by.split('|')
            if current_user.name in a:
                a.pop(a.index(current_user.name))
                # print(a)
                news.liked_by = '|'.join(a)
        else:
            pass

        news.likes = len(news.liked_by.split('|'))  # Обновляем кол-во лайков
        db_sess.commit()
    else:
        # abort(403)
        redirect('/login')
    if session.get('from_page', None) == '/feed':
        return redirect(f'/feed#{id}')
    else:
        return redirect(session.get('from_page', f'/feed#{id}'))


@app.route('/news/<int:id>', methods=['GET', 'POST'])  # Редактирование новости. Всё почти так же как и добавление.
@login_required
def edit_news(id):
    form = NewsForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        news = db_sess.query(News).filter(
            News.id == id, ((News.user == current_user) | current_user.is_admin)).first()
        if news:
            form.title.data = news.title
            form.content.data = news.content
            form.is_private.data = news.is_private
        else:
            # abort(403)
            redirect('/login')
    if form.validate_on_submit():
        attachments = []
        f = request.files['file']
        if f:
            # print(request.files.to_dict(flat=False)['file'])
            files = request.files.to_dict(flat=False)['file']
            for file in files:
                filename = secure_filename(
                    f'{str(time.time()).replace(".", "-")}.png')
                attachments.append(filename)
                # print(filename)
                file.save('static/attachments/' + filename)
        db_sess = db_session.create_session()
        news = db_sess.query(News).filter(
            News.id == id, ((News.user == current_user) | current_user.is_admin)).first()
        if news:
            news.title = form.title.data
            news.content = form.content.data
            news.is_private = form.is_private.data
            try:
                for i in news.attach.split('|'):
                    os.remove(f'static/attachments/{i}')
            except Exception as e:
                str(e)
            news.attach = '|'.join(attachments)
            db_sess.commit()
            if session.get('from_page', None) == '/feed':
                return redirect(f'/feed#{id}')
            else:
                return redirect(session.get('from_page', f'/feed#{id}'))
        else:
            # abort(403)
            redirect('/login')
    return render_template('news.html', title='Редактирование новости',
                           form=form)


@app.route('/msg')  # Сообщения
@login_required
def messages():
    if current_user.is_authenticated:
        db_sess = db_session.create_session()
        messages = db_sess.query(Message).filter(
            Message.title.like(
                f'{current_user.id}_%') | Message.title.like(f'%_{current_user.id}')).order_by(
            # В начале загружаем сохранённые в базе данных сообщения
            Message.created_date.desc()).all()  # Сортируем по дате/времени
        dialogs = []
        users = []
        for i in messages:
            # После определения, есть ли текущий пользователь в спике отправителей/получателей сообщений
            a = i.title.split('_')
            for k in a:
                if k != str(current_user.id):
                    # print(k)
                    if k not in dialogs:
                        dialogs.append(k)
        # Формируем список людей, с которыми контактировал текущий пользователь
        for i in dialogs:
            user = db_sess.query(User).filter(User.id == i).first()
            message = db_sess.query(Message).filter(
                Message.title.like(
                    f'{current_user.id}_{i}') | Message.title.like(f'{i}_{current_user.id}')).order_by(
                Message.created_date.desc()).first()
            users.append([user, message])
    else:
        return redirect(f'/login')
    return render_template('dialogs.html', title='Мессенджер',
                           friends=users)  # Выводим список диалогов, в которых есть сообщения


@app.route('/msg/<int:to>', methods=['GET', 'POST'])  # Диалог (чат)
@login_required
def add_msg(to):
    db_sess = db_session.create_session()
    who = db_sess.query(User).filter(User.id == to).first()  # Определяем, с кем пользователь переписывается
    if current_user.is_authenticated:
        message = db_sess.query(Message).filter(
            Message.title.like(
                f'{current_user.id}_{to}') | Message.title.like(
                f'{to}_{current_user.id}')).all()  # Загрузка сообщений из базы данных
    else:
        return redirect('/login')
    if current_user.id > to:
        title = f'{current_user.id}_{to}'
    else:
        title = f'{to}_{current_user.id}'
    return render_template('dialog.html', title=f'Чат с пользователем {who.name}',  # Немного красоты на странице
                           messages=message, to=to,
                           header=title)


@socketio.on('message')  # Отслеживаем событие SocketIO
@login_required  # Получаем JSON с сообщением
def handle_my_custom_event(json):
    db_sess = db_session.create_session()
    msg = Message()
    msg.title = str(json['user_name'])

    # При получении сообщения нужно сохранить его в базе данных.
    msg.content = unquote(json['message'])
    current_user.msg.append(msg)
    db_sess.merge(current_user)
    db_sess.expire_on_commit = False
    db_sess.commit()
    socketio.emit('my response', json)


def main():  # Запуск сервера
    # Подключаем API
    db_session.global_init("db/blogs.db")
    app.register_blueprint(news_api.blueprint)
    app.register_blueprint(users_api.blueprint)
    # Запускаем Ngrok
    run_with_ngrok(app)
    # Запускаем сервер
    app.run()


if __name__ == '__main__':
    main()  # Поехали!
