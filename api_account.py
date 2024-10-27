from flask import Flask, request, g, flash, url_for, redirect, jsonify, make_response, Blueprint
from utils import requires_auth, requires_admin, generate_refresh_token, generate_access_token, before_request, is_api_request, requires_doctor_manager_admin, requires_manager_admin

import jwt
from functools import wraps
import os
from dotenv import load_dotenv
import re
from werkzeug.security import generate_password_hash, check_password_hash
import pathlib

from werkzeug.utils import secure_filename
from forms import SettingsForm, SignUpForm, SignInForm, SettingsFormAdmin

acc_bp = Blueprint('accounts', __name__)

database = None
@acc_bp.before_request
def app_before_request():
    global database
    database = before_request()

#----------Обработка API----------

@acc_bp.route('/Authentication/SignUp', methods=['POST'])
def api_signup():
    """
    Регистрирует нового пользователя.

    Тело запроса (form-data):
        username: Имя пользователя (строка, обязательно, мин. длина 4)
        first_name: Имя (строка, обязательно, мин. длина 4)
        last_name: Фамилия (строка, обязательно, мин. длина 4)
        middle_name: Отчество (строка, обязательно, мин. длина 4)
        email: Адрес электронной почты (строка, обязательно, корректный формат email)
        password: Пароль (строка, обязательно, мин. длина 4, буквенно-цифровые символы и спецсимволы)
        r_password: Повтор пароля (строка, обязательно, должен совпадать с паролем)

    Возвращает:
        Перенаправление на /signin в случае успеха с flash-сообщением.
        Перенаправление на /signup в случае ошибки с flash-сообщением, указывающим на ошибку.
    """
    form = SignUpForm()
    if form.validate_on_submit():
        if len(form.username.data) >= 4 and len(form.first_name.data) >= 4 and len(form.last_name.data) >= 4 and len(form.middle_name.data) >= 4:
            if bool(re.match(r'^[^.+@]+@[^@]+\.[^@]+$', form.email.data)):
                if len(form.password.data) >= 4 and bool(re.match(r'^[A-Za-z0-9!@#$%^&*(),.?":{}|<>]+$', form.password.data)):
                    if form.password.data == form.r_password.data:
                        pass_hash = generate_password_hash(form.password.data)
                        result, status, log = database.add_user(form.username.data, 
                                                                form.first_name.data, 
                                                                form.last_name.data, 
                                                                form.middle_name.data,
                                                                form.email.data,
                                                                pass_hash)
                        if isinstance(result, str):
                            if log:
                                message = {'message': result, 'status': status}
                                if is_api_request():
                                    return jsonify(message), 200 if status == 'success' else 400
                                flash(result, status)
                                return redirect(url_for('signin'))
                            else:
                                message = {'message': result, 'status': status}
                                if is_api_request():
                                    return jsonify(message), 400
                                flash(result, status)
                        else:
                            message = {'message': 'Непредвиденная ситуация...', 'status': 'error'}
                            if is_api_request():
                                return jsonify(message), 500
                            flash('Непредвиденная ситуация...', 'error')
                    else:
                        message = {'message': 'Пароли не совпадают!', 'status': 'error'}
                        if is_api_request():
                            return jsonify(message), 400
                        flash('Пароли не совпадают!', 'error')
                else:
                    message = {'message': 'Пароль должен быть более 4 символов и содержать только англ. буквы, спец. символы и цифры', 'status': 'error'}
                    if is_api_request():
                        return jsonify(message), 400
                    flash('Пароль должен быть более 4 символов и содержать только англ. буквы, спец. символы и цифры', 'error')
            else:
                message = {'message': 'Некорректный email!', 'status': 'error'}
                if is_api_request():
                    return jsonify(message), 400
                flash('Некорректный email!', 'error')
        else:
            message = {'message': 'У ФИО или имени пользователя должно быть более 3 букв и минимум 1 англ. буква.', 'status': 'error'}
            if is_api_request():
                return jsonify(message), 400
            flash('У ФИО или имени пользователя должно быть более 3 букв и минимум 1 англ. буква.', 'error')
    elif is_api_request():
        return jsonify({'errors': form.errors}), 400

    return redirect(url_for('signup'))

@acc_bp.route('/Authentication/SignIn', methods=['POST'])
def api_signin():
    """
    Авторизует существующего пользователя.

    Тело запроса (form-data):
        usermail: Адрес электронной почты или имя пользователя (строка, обязательно)
        password: Пароль (строка, обязательно)

    Возвращает:
        Перенаправление на /profile в случае успеха с access и refresh токенами в cookies.
        JSON ответ с кодом состояния 400, если refresh token отсутствует (не должно происходить в этой конечной точке).
        Перенаправление на /signin в случае ошибки с flash-сообщением, указывающим на ошибку.
    """
    form = SignInForm()
    if form.validate_on_submit():
        user = database.login_getuserdata(form.usermail.data)
        if user[2] == False:
            message = {'message': user[0], 'status': user[1]}
            if is_api_request():
                return jsonify(message), 400
            flash(user[0], user[1])
            return redirect(url_for('signin'))
        else:
            if user and check_password_hash(user.pass_hash, form.password.data):
                access_token = generate_access_token(user.id)
                refresh_token = generate_refresh_token(user.id)
                database.save_refresh_token(user.id, refresh_token)
                resp = make_response(redirect(url_for('profile')))
                resp.set_cookie('access_token', access_token)
                resp.set_cookie('refresh_token', refresh_token, httponly=True)
                return resp

            message = {'message': 'Invalid username or password', 'status': 'error'}
            if is_api_request():
                return jsonify(message), 401
            flash('Invalid username or password', 'error')
            return redirect(url_for('signin'))
    elif is_api_request():
        return jsonify({'errors': form.errors}), 400
    return redirect(url_for('signin'))

@acc_bp.route('/Authentication/SignOut', methods=['POST'])
def api_signout():
    """
    Выход текущего пользователя из системы.

    Тело запроса: Нет (ожидает refresh token в cookies)

    Возвращает:
        Перенаправление на /signin с удалением access и refresh токенов из cookies.
        Flash-сообщение об успешном выходе.
    """
    refresh_token = request.cookies.get('refresh_token')
    if refresh_token:
        database.delete_refresh_token(refresh_token)
    flash('Выход из аккаунта успешен', 'success')
    resp = make_response(redirect(url_for('signin')))
    resp.delete_cookie('access_token')
    resp.delete_cookie('refresh_token')
    return resp

@acc_bp.route('/Authentication/Validate', methods=['GET'])
def api_validate():
    """
    Проверяет access token.

    Параметры запроса:
        accessToken: Access token для проверки (строка, обязательно)

    Возвращает:
        JSON ответ с кодом состояния 200 и {'valid': True, 'user_id': user_id}, если токен действителен.
        JSON ответ с кодом состояния 401 и сообщением об ошибке, если токен недействителен или просрочен.
        JSON ответ с кодом состояния 400, если токен отсутствует.
    """
    token = request.args.get('accessToken')
    if not token:
        return jsonify({'message': 'Token is missing'}), 400

    try:
        data = jwt.decode(token, acc_bp.config['SECRET_KEY'], algorithms=['HS256'])
        if data.get('type') != 'access':
            raise jwt.InvalidTokenError
        return jsonify({'valid': True, 'user_id': data['sub']}), 200
    except jwt.ExpiredSignatureError:
        return jsonify({'valid': False, 'message': 'Token expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'valid': False, 'message': 'Invalid token'}), 401

@acc_bp.route('/Authentication/Refresh', methods=['POST'])
def api_refresh():
    """
    Обновляет access token с помощью refresh token.

    Тело запроса: Нет (ожидает refresh token в cookies)

    Возвращает:
        JSON ответ с кодом состояния 200 и новым access token в поле 'access_token' и в cookie.
        JSON ответ с кодом состояния 401 и сообщением об ошибке, если refresh token недействителен или просрочен.
        JSON ответ с кодом состояния 400, если refresh token отсутствует.
    """
    refresh_token = request.cookies.get('refresh_token')
    if not refresh_token:
        return jsonify({'message': 'Refresh token is missing'}), 400

    try:
        data = jwt.decode(refresh_token, acc_bp.config['SECRET_KEY'], algorithms=['HS256'])
        if data.get('type') != 'refresh':
            raise jwt.InvalidTokenError

        if not database.is_refresh_token_valid(refresh_token):
            return jsonify({'message': 'Invalid refresh token'}), 401

        access_token = generate_access_token(data['sub'])

        resp = make_response(jsonify({'access_token': access_token}), 200)
        resp.set_cookie('access_token', access_token)
        return resp

    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Refresh token expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'message': 'Invalid refresh token'}), 401
    
@acc_bp.route('/Accounts/Me', methods=['GET'])
@requires_auth
def api_me():
    """
    Возвращает информацию о текущем пользователе.

    Тело запроса: Нет (требуется аутентификация)

    Возвращает:
        JSON ответ с кодом состояния 200 и данными пользователя.
        JSON ответ с кодом состояния 404, если пользователь не найден.
    """
    user = database.getuserdata(g.current_user_id)
    if user:
        return jsonify({
            'id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'middle_name': user.middle_name,
            'email': user.email,
            'hospital_id': user.hospital_id,
            'doctor_id': user.doctor_id,
            'user_role': user.user_role,
            'reg_time': user.reg_time,
            'avatar': url_for('static', filename=user.avatar)
        })
    else:
        return jsonify({'message': 'User not found'}), 404
    
@acc_bp.route('/Accounts/Update', methods=['PUT'])
@requires_auth
def api_update():
    """
    Обновляет информацию о текущем пользователе.

    Тело запроса (form-data):
        current_password: Текущий пароль (строка, обязательно)
        last_name: Новая фамилия (строка, необязательно)
        first_name: Новое имя (строка, необязательно)
        middle_name: Новое отчество (строка, необязательно)
        email: Новый адрес электронной почты (строка, необязательно)
        password: Новый пароль (строка, необязательно)
        avatar: Новое изображение аватара (файл, необязательно)

    Возвращает:
        JSON ответ с кодом состояния 200 в случае успеха.
        JSON ответ с кодом состояния 400 и ошибками валидации, если данные формы недействительны.
        JSON ответ с кодом состояния 401, если текущий пароль неверен.
        JSON ответ с кодом состояния 405, если метод запроса не PUT.
    """
    if request.method == 'PUT':
        form = SettingsForm()
        if form.validate():
            last_name = request.form.get('last_name')
            first_name = request.form.get('first_name')
            middle_name = request.form.get('middle_name')
            email = request.form.get('email')
            password = request.form.get('password')
            avatar = request.files.get('avatar')

            user = database.getuserdata(g.current_user_id)
            if not check_password_hash(user.pass_hash, request.form.get('current_password')):
                flash('Неверный текущий пароль', 'error')
                return jsonify({'error': 'Incorrect current password'}), 401

            if password:
                pass_hash = generate_password_hash(password)
                database.update_user(g.current_user_id, last_name, first_name, middle_name, email, pass_hash)
            else:
                database.update_user(g.current_user_id, last_name, first_name, middle_name, email)

            if avatar:
                filename = secure_filename(avatar.filename)
                extension = pathlib.Path(filename).suffix
                avatar_path = f"images/users/avatars/{g.current_user_id}{extension}"
                avatar.save(os.path.join(acc_bp.root_path, "static", avatar_path))
                database.update_avatar(g.current_user_id, avatar_path)


            flash('Настройки успешно сохранены', 'success')
            return jsonify({'message': 'Account updated successfully'}), 200
        else:
            return jsonify({'errors': form.errors}), 400
    return jsonify({'message': 'Invalid request method'}), 405

@acc_bp.route('/Accounts/<int:id>', methods=['PUT', 'DELETE'])
@requires_auth
@requires_admin
def api_update_account(id):
    """
    Обновляет или удаляет учетную запись пользователя по ID (только для администратора).

    Тело запроса (form-data для PUT):
        last_name: Новая фамилия (строка, необязательно)
        first_name: Новое имя (строка, необязательно)
        middle_name: Новое отчество (строка, необязательно)
        email: Новый адрес электронной почты (строка, необязательно)
        password: Новый пароль (строка, необязательно)
        avatar: Новое изображение аватара (файл, необязательно)
        user_role: Новая роль пользователя (строка, необязательно)

    Параметры запроса:
        id: ID пользователя (целое число, обязательно)

    Возвращает:
        PUT:
            JSON ответ с кодом состояния 200 в случае успеха.
            JSON ответ с кодом состояния 400 и ошибками валидации, если данные формы недействительны.

        DELETE:
            JSON ответ с кодом состояния 200 в случае успеха.
            JSON ответ с кодом состояния 500 в случае ошибки.
    """
    if request.method == 'PUT':
        form = SettingsFormAdmin()
        if form.validate():
            last_name = request.form.get('last_name')
            first_name = request.form.get('first_name')
            middle_name = request.form.get('middle_name')
            email = request.form.get('email')
            password = request.form.get('password')
            avatar = request.files.get('avatar')
            user_role = request.form.get('user_role')

            if password:
                pass_hash = generate_password_hash(password)
                database.update_user(id, last_name, first_name, middle_name, email, pass_hash)
            else:
                database.update_user(id, last_name, first_name, middle_name, email)

            if avatar:
                filename = secure_filename(avatar.filename)
                extension = pathlib.Path(filename).suffix
                avatar_path = f"images/users/avatars/{id}{extension}"
                avatar.save(os.path.join(acc_bp.root_path, "static", avatar_path))
                database.update_avatar(id, avatar_path)

            if user_role:
                database.update_user_role(id, user_role)

            return jsonify({'message': 'Account updated successfully'}), 200
        else:
            return jsonify({'errors': form.errors}), 400
    elif request.method == 'DELETE':
        success = database.soft_delete_user(id)

        if success:
            return jsonify({'message': 'Account deleted successfully'}), 200
        else:
            return jsonify({'message': 'Failed to delete account'}), 500

@acc_bp.route('/Accounts', methods=['POST', 'GET'])
@requires_auth
@requires_admin
def api_accounts():
    """
    Возвращает все учетные записи пользователей или создает новую учетную запись (только для администратора).

    Параметры GET запроса:
        from: Смещение для пагинации (целое число, необязательно, по умолчанию=0)
        count: Количество учетных записей для извлечения (целое число, необязательно, по умолчанию=1000)

    Тело POST запроса (form-data):
        username: Имя пользователя (строка, обязательно, мин. длина 4)
        first_name: Имя (строка, обязательно, мин. длина 4)
        last_name: Фамилия (строка, обязательно, мин. длина 4)
        middle_name: Отчество (строка, обязательно, мин. длина 4)
        email: Адрес электронной почты (строка, обязательно, корректный формат email)
        password: Пароль (строка, обязательно, мин. длина 4, буквенно-цифровые символы и спецсимволы)
        r_password: Повтор пароля (строка, обязательно, должен совпадать с паролем)

    Возвращает:
        GET:
            JSON ответ с кодом состояния 200 и списком учетных записей пользователей.
        POST:
            Перенаправление на /signup_admin в случае успеха с flash-сообщением.
            Перенаправление на /signup_admin в случае ошибки с flash-сообщением, указывающим на ошибку.
    """
    if request.method == 'GET':
        from_param = request.args.get('from', default=0, type=int)
        count_param = request.args.get('count', default=1000, type=int)

        accounts = database.get_all_accounts(deleted=False, _from=from_param, _count=count_param)
        account_list = []
        for account in accounts:
            account_list.append({
                'id': account.id,
                'username': account.username,
                'first_name': account.first_name,
                'last_name': account.last_name,
                'middle_name': account.middle_name,
                'email': account.email,
                'hospital_id': account.hospital_id,
                'doctor_id': account.doctor_id,
                'user_role': account.user_role,
                'reg_time': account.reg_time,
                'avatar': url_for('static', filename=account.avatar)
            })
        return jsonify(account_list), 200
    
    if request.method == 'POST':
        form = SignUpForm()
        if form.validate_on_submit():
            if form.password.data == form.r_password.data:
                pass_hash = generate_password_hash(form.password.data)
                result, status, log = database.add_user(form.username.data, 
                                                        form.first_name.data, 
                                                        form.last_name.data, 
                                                        form.middle_name.data,
                                                        form.email.data,
                                                        pass_hash)
                if isinstance(result, str):
                    message = {'message': result, 'status': status}
                    if is_api_request():
                        return jsonify(message), 200 if status == 'success' else 400
                    if log:
                        flash(result, status)
                        return redirect(url_for('signup_admin'))
                    else:
                        flash(result, status)
                else:
                    message = {'message': 'Непредвиденная ситуация...', 'status': 'error'}
                    if is_api_request():
                        return jsonify(message), 500
                    flash('Непредвиденная ситуация...', 'error')
            else:
                message = {'message': 'Пароли не совпадают!', 'status': 'error'}
                if is_api_request():
                    return jsonify(message), 400
                flash('Пароли не совпадают!', 'error')
        elif is_api_request():
            return jsonify({'errors': form.errors}), 400
        return redirect(url_for('signup_admin'))

@acc_bp.route('/Accounts/Search', methods=['GET'])
@requires_auth
@requires_admin
def api_search_accounts():
    """
    Ищет учетные записи пользователей (только для администратора).

    Параметры запроса:
        q: Поисковый запрос (строка, необязательно)

    Возвращает:
        JSON ответ с кодом состояния 200 и списком совпадающих учетных записей пользователей.
        Возвращает пустой список, если запрос не предоставлен.
    """
    search_query = request.args.get('q')
    if not search_query:
        return jsonify([]), 200

    accounts = database.search_accounts(search_query)
    account_list = []
    for account in accounts:
        account_list.append({
            'id': account.id,
            'username': account.username,
            'first_name': account.first_name,
            'last_name': account.last_name,
            'middle_name': account.middle_name,
            'email': account.email,
            'hospital_id': account.hospital_id,
            'doctor_id': account.doctor_id,
            'reg_time': account.reg_time
        })
    return jsonify(account_list), 200

@acc_bp.route('/Doctors', methods=['GET'])
@requires_auth
def api_doctors():
    """
    Возвращает список врачей.

    Параметры запроса:
        nameFilter: Фильтр врачей по имени (строка, необязательно)
        from: Смещение для пагинации (целое число, необязательно, по умолчанию=0)
        count: Количество врачей для извлечения (целое число, необязательно, по умолчанию=1000)
        h_id: Фильтр врачей по ID больницы (целое число, необязательно)

    Возвращает:
        JSON ответ с кодом состояния 200 и списком врачей.
    """
    name_filter = request.args.get('nameFilter')
    from_param = request.args.get('from', default=0, type=int)
    count_param = request.args.get('count', default=1000, type=int)
    hospital_id = request.args.get('h_id', default=None, type=int)

    doctors = database.get_doctors(name_filter, hospital_id, from_param, count_param)
    doctor_list = []
    for doctor in doctors:
        doctor_list.append({
            'id': doctor.id,
            'username': doctor.username,
            'first_name': doctor.first_name,
            'last_name': doctor.last_name,
            'middle_name': doctor.middle_name,
            'email': doctor.email,
            'hospital_id': doctor.hospital_id,
            'doctor_id': doctor.doctor_id,
            'user_role': doctor.user_role,
            'reg_time': doctor.reg_time,
            'avatar': url_for('static', filename=doctor.avatar)
        })
    return jsonify(doctor_list), 200

@acc_bp.route('/Doctors/<int:id>', methods=['GET'])
@requires_auth
def api_doctor(id):
    """
    Возвращает врача по ID.

    Параметры запроса:
        id: ID врача (целое число, обязательно)

    Возвращает:
        JSON ответ с кодом состояния 200 и данными врача, если найден.
        JSON ответ с кодом состояния 404, если пользователь не найден или не имеет роли врача.
    """
    doctor = database.getuserdata(id)
    if doctor and doctor.user_role == 'doctor':
        return jsonify({
            'id': doctor.id,
            'username': doctor.username,
            'first_name': doctor.first_name,
            'last_name': doctor.last_name,
            'middle_name': doctor.middle_name,
            'email': doctor.email,
            'hospital_id': doctor.hospital_id,
            'doctor_id': doctor.doctor_id,
            'user_role': doctor.user_role,
            'reg_time': doctor.reg_time,
            'avatar': url_for('static', filename=doctor.avatar)
        })
    else:
        return jsonify({'message': 'Doctor not found'}), 404

#----------Обработка новых API (не по заданию)----------

@acc_bp.route('/recommendations', methods=['POST'])
@requires_auth
@requires_doctor_manager_admin
def create_recommendation():
    """
    Создает новую рекомендацию.

    Параметры запроса (JSON):
        title: Заголовок рекомендации (строка, обязательно).
        text: Текст рекомендации (строка, обязательно).
        user_id: ID пользователя, которому адресована рекомендация (целое число, обязательно).

    Возвращает:
        JSON ответ с кодом состояния 201, если рекомендация создана успешно.
        JSON ответ с кодом состояния 400, если не предоставлены необходимые данные.
        JSON ответ с кодом состояния 500, если произошла ошибка при создании рекомендации.
    """
    data = request.get_json()
    if not data:
        return jsonify({'message': 'No data provided'}), 400
    title = data.get('title')
    text = data.get('text')
    user_id = data.get('user_id')
    if not all([title, text, user_id]):
        return jsonify({'message': 'Missing required fields'}), 400

    if database.create_recommendation(user_id, title, text):
        return jsonify({'message': 'Recommendation created'}), 201
    else:
        return jsonify({'message': 'Failed to create recommendation'}), 500

@acc_bp.route('/recommendations/<int:user_id>', methods=['GET'])
@requires_auth
def get_recommendations(user_id):
    """
    Возвращает рекомендации для пользователя по ID.

    Параметры запроса:
        user_id: ID пользователя (целое число, обязательно).

    Возвращает:
        JSON ответ с кодом состояния 200 и списком рекомендаций.
    """
    recommendations = database.get_recommendations_for_user(user_id)
    return jsonify(recommendations), 200

@acc_bp.route('/recommendations/<int:id>', methods=['PUT', 'DELETE'])
@requires_auth
@requires_doctor_manager_admin
def update_delete_recommendation(id):
    """
    Обновляет или удаляет рекомендацию по ID.

    Параметры запроса:
        id: ID рекомендации (целое число, обязательно).

    Для метода PUT:
        Параметры запроса (JSON):
            title: Заголовок рекомендации (строка, обязательно).
            text: Текст рекомендации (строка, обязательно).

    Возвращает:
        Для метода PUT:
            JSON ответ с кодом состояния 200, если рекомендация обновлена успешно.
            JSON ответ с кодом состояния 400, если не предоставлены необходимые данные.
            JSON ответ с кодом состояния 500, если произошла ошибка при обновлении.
        Для метода DELETE:
            JSON ответ с кодом состояния 200, если рекомендация удалена успешно.
            JSON ответ с кодом состояния 500, если произошла ошибка при удалении.
    """
    if request.method == 'PUT':
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No data provided'}), 400

        if database.update_recommendation(id, data.get('title'), data.get('text')):
            return jsonify({'message': 'Recommendation updated'}), 200
        else:
            return jsonify({'message': 'Failed to update recommendation'}), 500
    elif request.method == 'DELETE':
        if database.delete_recommendation(id):
            return jsonify({'message': 'Recommendation deleted'}), 200
        else:
            return jsonify({'message': 'Failed to delete recommendation'}), 500

@acc_bp.route('/actual', methods=['POST'])
@requires_auth
@requires_manager_admin
def create_actual_item():
    """
    Создает новую актуальную запись.
    
    Параметры запроса (JSON):
        Произвольные данные для актуальной записи.

    Возвращает:
        JSON ответ с кодом состояния 201, если запись создана.
        JSON ответ с кодом состояния 400, если данные не предоставлены.
        JSON ответ с кодом состояния 500, если произошла ошибка при создании.
    """
    data = request.get_json()
    if not data:
        return jsonify({'message': 'No data provided'}), 400

    if database.create_actual_item(data):
        return jsonify({'message': 'Actual item created'}), 201
    else:
        return jsonify({'message': 'Failed to create actual item'}), 500

@acc_bp.route('/actual', methods=['GET'])
def get_actual_items():
    """
    Возвращает все актуальные записи.

    Возвращает:
        JSON ответ с кодом состояния 200 и списком актуальных записей.
    """
    actual_items = database.get_all_actual_items()
    return jsonify(actual_items), 200

@acc_bp.route('/actual/<int:id>', methods=['PUT', 'DELETE'])
@requires_auth
@requires_manager_admin
def update_delete_actual_item(id):
    """
    Обновляет или удаляет актуальную запись по ID.

    Параметры запроса:
        id: ID актуальной записи (целое число, обязательно).

    Для метода PUT:
        Параметры запроса (JSON):
            Произвольные данные для обновления записи.

    Возвращает:
        Для метода PUT:
            JSON ответ с кодом состояния 200, если обновление успешно.
            JSON ответ с кодом состояния 500, если произошла ошибка при обновлении.
        Для метода DELETE:
            JSON ответ с кодом состояния 200, если удаление успешно.
            JSON ответ с кодом состояния 500, если произошла ошибка при удалении.
    """
    if request.method == 'PUT':
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No data provided'}), 400

        if database.update_actual_item(id, data):
            return jsonify({'message': 'Actual item updated'}), 200
        else:
            return jsonify({'message': 'Failed to update actual item'}), 500
    elif request.method == 'DELETE':
        if database.delete_actual_item(id):
            return jsonify({'message': 'Actual item deleted'}), 200
        else:
            return jsonify({'message': 'Failed to delete actual item'}), 500