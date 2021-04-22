from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FileField, MultipleFileField
from wtforms import BooleanField, SubmitField
from wtforms.validators import DataRequired

#
# Заготовки Flask-WTF для создания/изменения новостей.
#

class NewsForm(FlaskForm):
    title = StringField('Заголовок', validators=[DataRequired()])
    content = TextAreaField("Содержание")
    is_private = BooleanField("Скрыть новость")
    submit = SubmitField('Сохранить')
    file = MultipleFileField('Вложения')
