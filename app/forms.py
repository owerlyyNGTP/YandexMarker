from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, FloatField, FileField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length
from app.models import User

class RegistrationForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    confirm_password = PasswordField('Подтвердите пароль', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Зарегистрироваться')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Это имя уже занято.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Этот email уже зарегистрирован.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')

class MarkerForm(FlaskForm):
    title = StringField('Название', validators=[DataRequired()])
    description = TextAreaField('Описание')
    latitude = FloatField('Широта', validators=[DataRequired()])
    longitude = FloatField('Долгота', validators=[DataRequired()])
    image = FileField('Фотография')
    is_public = BooleanField('Публичная метка', default=True)
    submit = SubmitField('Сохранить')

class GPXUploadForm(FlaskForm):
    gpx_file = FileField('Выберите GPX файл', validators=[DataRequired()])
    submit = SubmitField('Загрузить')