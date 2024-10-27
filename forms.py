from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, FieldList
from wtforms.validators import DataRequired, EqualTo, Length, Email
from werkzeug.utils import secure_filename

class SettingsForm(FlaskForm):
    last_name = StringField('Фамилия', validators=[DataRequired()])
    first_name = StringField('Имя', validators=[DataRequired()])
    middle_name = StringField('Отчество', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    current_password = PasswordField('Текущий пароль', validators=[DataRequired()])
    password = PasswordField('Новый пароль', validators=[EqualTo('confirm_password', message='Пароли должны совпадать')])
    confirm_password = PasswordField('Подтвердите пароль')
    avatar = FileField('Аватар')
    submit = SubmitField('Сохранить')
    class Meta:
        csrf = False

class SettingsFormAdmin(FlaskForm):
    last_name = StringField('Фамилия', validators=[DataRequired()])
    first_name = StringField('Имя', validators=[DataRequired()])
    middle_name = StringField('Отчество', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    user_role = SelectField('Роль пользователя', choices=[('user', 'Пользователь'), ('doctor', 'Доктор'), ('manager', 'Менеджер'), ('admin', 'Администратор')], validators=[DataRequired()])
    password = PasswordField('Новый пароль', validators=[EqualTo('confirm_password', message='Пароли должны совпадать')])
    confirm_password = PasswordField('Подтвердите пароль')
    avatar = FileField('Аватар')
    submit = SubmitField('Сохранить')
    class Meta:
        csrf = False

class SignInForm(FlaskForm):
    usermail = StringField('Почта/Имя пользователя', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')
    class Meta:
        csrf = False

class SignUpForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=4)])
    last_name = StringField('Фамилия', validators=[DataRequired(), Length(min=4)])
    first_name = StringField('Имя', validators=[DataRequired(), Length(min=4)])
    middle_name = StringField('Отчество', validators=[DataRequired(), Length(min=4)])
    email = StringField('Почта', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=4)])
    r_password = PasswordField('Повторите пароль', validators=[DataRequired(), EqualTo('password', message='Пароли не совпадают')])
    submit = SubmitField('Зарегистрироваться')
    class Meta:
        csrf = False

class HospitalForm(FlaskForm):
    hospital_name = StringField('Название больницы', validators=[DataRequired()])
    cabinets = FieldList(StringField('Кабинет'), min_entries=1)
    phone = FieldList(StringField('Телефон'), min_entries=1)
    email = FieldList(StringField('Email', min_entries=1))
    hospital_address = StringField('Адрес больницы', validators=[DataRequired()])
    submit = SubmitField('Создать')
    class Meta:
        csrf = False