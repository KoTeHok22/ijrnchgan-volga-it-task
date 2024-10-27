from flask import current_app, g, redirect, url_for, jsonify, make_response, request
from functools import wraps
import jwt
import uuid
from datetime import datetime, timedelta, timezone
import psycopg2
import os
from dotenv import load_dotenv
from db import MainDataBase
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()
DB_URL = os.getenv("DB_URL")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

database = None

def is_api_request():
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json'

def get_db():
    if 'db' not in g:
        g.db = psycopg2.connect(database=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_URL, port=5432, client_encoding='utf8')
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db(app):
    with app.app_context():
        db = get_db()
        with current_app.open_resource('data.sql', mode='r') as f:
            db.cursor().execute(f.read())
        db.commit()

def generate_access_token(user_id):
    payload = {
        'exp': datetime.now(tz=timezone.utc) + timedelta(minutes=15),
        'iat': datetime.now(tz=timezone.utc),
        'sub': user_id,
        'type': 'access'
    }
    return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')

def generate_refresh_token(user_id):
    payload = {
        'exp': datetime.now(tz=timezone.utc) + timedelta(days=30),
        'iat': datetime.now(tz=timezone.utc),
        'sub': user_id,
        'type': 'refresh',
        'jti': str(uuid.uuid4())
    }
    return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')

def generate_permanent_access_token(user_id):
    payload = {
        'iat': datetime.now(tz=timezone.utc),
        'sub': user_id,
        'type': 'permanent_access'
    }
    return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')

def before_request():
    global database
    db = get_db()
    database = MainDataBase(db)
    return database

def refresh_access_token():
    refresh_token = request.cookies.get('refresh_token')
    if not refresh_token:
        return redirect(url_for('signin'))

    try:
        data = jwt.decode(refresh_token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        if data.get('type') != 'refresh':
            raise jwt.InvalidTokenError
        if not database.is_refresh_token_valid(refresh_token):
            return False

        access_token = generate_access_token(data['sub'])
        resp = make_response(redirect(request.url))
        resp.set_cookie('access_token', access_token)
        return resp

    except jwt.ExpiredSignatureError:
        return redirect(url_for('signin'))
    except jwt.InvalidTokenError:
        return redirect(url_for('signin'))

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get('access_token')
        if not token:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'message': 'Authentication required'}), 401
            else:
                return redirect(url_for('signin'))

        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            token_type = data.get('type')
            if token_type not in ('access', 'permanent_access'):
                raise jwt.InvalidTokenError
            g.current_user_id = data['sub']
        except jwt.ExpiredSignatureError:
            refresh_result = refresh_access_token()
            if refresh_result is False:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'message': 'Token refresh failed'}), 401
                else:
                    return redirect(url_for('signin'))
            else:
                return refresh_result
        except jwt.InvalidTokenError:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'message': 'Invalid token'}), 401
            else:
                return redirect(url_for('signin'))
        return f(*args, **kwargs)

    return decorated

def requires_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = database.getuserdata(g.current_user_id)
        if not user or user.user_role != 'admin':
            return jsonify({'message': 'Internal server error'}), 500
        return f(*args, **kwargs)
        
    return decorated

def requires_manager_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = database.getuserdata(g.current_user_id)
        if not user or user.user_role not in ('admin', 'manager'):
            return jsonify({'message': 'Internal server error'}), 500
        return f(*args, **kwargs)

    return decorated

def requires_doctor_manager_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = database.getuserdata(g.current_user_id)
        if not user or user.user_role not in ('admin', 'manager', 'doctor'):
            return jsonify({'message': 'Internal server error'}), 500
        return f(*args, **kwargs)

    return decorated

def check_token(token):
    if token:
        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            if data.get('type') != 'access':
                raise jwt.InvalidTokenError
            return True
        except jwt.ExpiredSignatureError:
            return False
        except jwt.InvalidTokenError:
            return False
        
def create_tabl():
    try:
        conn = psycopg2.connect(
            host=DB_URL,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        conn.autocommit = True
        cursor = conn.cursor()

        with open('data.sql', 'r') as f:
            sql = f.read()
        cursor.execute(sql)

        database = MainDataBase(conn)

        pass_hash = generate_password_hash('user')
        database.add_user('user', 'Иванов', 'Иван', 'Иванович', 'user@user.ru', pass_hash)
        database.update_user_role(1, 'user')

        pass_hash = generate_password_hash('doctor')
        database.add_user('doctor', 'Иванов', 'Иван', 'Иванович', 'doctor@doctor.ru', pass_hash)
        database.update_user_role(2, 'doctor')

        pass_hash = generate_password_hash('manager')
        database.add_user('manager', 'Иванов', 'Иван', 'Иванович', 'manager@manager.ru', pass_hash)
        database.update_user_role(3, 'manager')

        pass_hash = generate_password_hash('admin')
        database.add_user('admin', 'Иванов', 'Иван', 'Иванович', 'admin@admin.ru', pass_hash)
        database.update_user_role(4, 'admin')

        data = {
            "hospital_name": "Больница 1",
            "cabinets": {"1": "Заведующий", "2": "ГлавВрач", "3": "Окулист"},
            "phone": {"ГлавВрач": "+7 (123) 456-78-90", "Секретарь": "+7 (987) 654-32-10"},
            "email": {"Общая": "test1@email.com", "Секретарь": "test2@email.com"},
            "hospital_address": "Адрес"
        }
        data2 = {
            "hospital_name": "Больница 2",
            "cabinets": {"11": "Заведующий", "22": "ГлавВрач", "33": "Окулист"},
            "phone": {"ГлавВрач": "+7 (123) 411-78-90", "Секретарь": "+7 (944) 654-32-10"},
            "email": {"Общая": "test11@email.ru", "Секретарь": "test22@email.ru"},
            "hospital_address": "Адресс"
        }

        database.create_hospital(data['hospital_name'], data['cabinets'], data['phone'], data['email'], data['hospital_address'])
        database.create_hospital(data2['hospital_name'], data2['cabinets'], data2['phone'], data2['email'], data2['hospital_address'])

        data = {
            'title': 'Запись на прием',
            'icon': 'images/actual/doctor.png', 
            'link': '#',
            'color': '#b0e0e6',
            'border': '#6bacb4'
        }
        data2 = {
            'title': 'Заказ лекарств',
            'icon': 'images/actual/medicines.png', 
            'link': '#',
            'color': '#e6e6fa',
            'border': '#c9c9e3'
        }
        data3 = {
            'title': 'Статус анализов',
            'icon': 'images/actual/microscope.png', 
            'link': '#',
            'color': '#ffdab9',
            'border': '#ffc194'
        }

        database.create_actual_item(data)
        database.create_actual_item(data2)
        database.create_actual_item(data3)

        conn.close()
    except psycopg2.Error as e:
        print(f"Ошибка создания таблиц: {e}")