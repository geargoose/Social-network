from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FileField, MultipleFileField
from wtforms import BooleanField, SubmitField, HiddenField
from wtforms.validators import DataRequired


#
# Заготовка Flask-WTF для добавления комментария.
#


class CommsForm(FlaskForm):
    to = StringField("ToNewsId")
    content = TextAreaField("Содержание", validators=[DataRequired()])
    submit = SubmitField('Сохранить')
