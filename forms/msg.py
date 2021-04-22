from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms import BooleanField, SubmitField
from wtforms.validators import DataRequired


#
# Заготовка Flask-WTF для отправки сообщения в диалоге.
#


class MsgForm(FlaskForm):
    content = TextAreaField("Текст сообщения", validators=[DataRequired()])
    submit = SubmitField('Отправить')
