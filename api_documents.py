from flask import Flask, request, g, flash, url_for, redirect, jsonify, make_response, Blueprint
from utils import requires_auth, requires_admin, generate_refresh_token, generate_access_token, before_request, is_api_request, requires_manager_admin, requires_doctor_manager_admin

import jwt
from functools import wraps
import os
from dotenv import load_dotenv
import re
from werkzeug.security import generate_password_hash, check_password_hash
import pathlib

from werkzeug.utils import secure_filename
from datetime import datetime, timedelta

doc_bp = Blueprint('documents', __name__)

database = None
@doc_bp.before_request
def app_before_request():
    global database
    database = before_request()

#----------Обработка API----------

@doc_bp.route('/History/Account/<int:id>', methods=['GET'])
@requires_auth
def get_account_history(id):
    """
    Возвращает историю болезни аккаунта по ID.

    Параметры запроса:
        id: ID аккаунта (целое число, обязательно).

    Возвращает:
        JSON ответ с кодом состояния 200 и историей болезни, если найдена и у пользователя есть доступ.
        JSON ответ с кодом состояния 404, если история болезни не найдена.
        JSON ответ с кодом состояния 403, если у пользователя нет доступа к истории болезни.
    """
    user = database.getuserdata(g.current_user_id)
    if int(id) == int(g.current_user_id) or user.user_role in ('doctor', 'admin'):
        history = database.get_account_history(id)
        if history:
            return jsonify(history), 200
        else:
            return jsonify({'message': 'History not found'}), 404
    else:
        return jsonify({'message': 'Access denied'}), 403

@doc_bp.route('/History', methods=['POST'])
@requires_auth
@requires_doctor_manager_admin
def create_history():
    """
    Создает новую запись в истории болезни.

    Параметры запроса (JSON):
        date: Дата записи (строка, обязательно).
        pacientId: ID пациента (целое число, обязательно).
        hospitalId: ID больницы (целое число, обязательно).
        doctorId: ID врача (целое число, обязательно).
        room: Кабинет (строка, обязательно).
        data: Данные истории болезни (строка, обязательно).

    Возвращает:
        JSON ответ с кодом состояния 201 и ID созданной записи, если создание успешно.
        JSON ответ с кодом состояния 500, если произошла ошибка при создании.
    """
    data = request.get_json()
    history_id = database.create_history(data.get('date'), data.get('pacientId'), data.get('hospitalId'), data.get('doctorId'), data.get('room'), data.get('data'))
    if history_id:
        return jsonify({'id': history_id, 'message': 'History created successfully'}), 201
    else:
        return jsonify({'message': 'Failed to create history'}), 500

@doc_bp.route('/History/<int:id>', methods=['GET'])
@requires_auth
def get_history(id):
    """
    Возвращает запись истории болезни по ID.

    Параметры запроса:
        id: ID записи истории болезни (целое число, обязательно).

    Возвращает:
        JSON ответ с кодом состояния 200 и данными истории болезни, если найдена и у пользователя есть доступ.
        JSON ответ с кодом состояния 404, если запись не найдена.
        JSON ответ с кодом состояния 403, если у пользователя нет доступа к записи.
    """
    user = database.getuserdata(g.current_user_id)
    history = database.get_history(id)
    if history:
        history_pacient_id = history[2]
        if int(history_pacient_id) == int(g.current_user_id) or user.user_role in ('doctor', 'admin'):
            return jsonify(history), 200
        else:
             return jsonify({'message': 'Access denied'}), 403
    else:
        return jsonify({'message': 'History not found'}), 404

@doc_bp.route('/History/<int:id>', methods=['PUT'])
@requires_auth
@requires_doctor_manager_admin
def update_history(id):
    """
    Обновляет запись истории болезни по ID.

    Параметры запроса (JSON):
        date: Дата записи (строка, обязательно).
        pacientId: ID пациента (целое число, обязательно).
        hospitalId: ID больницы (целое число, обязательно).
        doctorId: ID врача (целое число, обязательно).
        room: Кабинет (строка, обязательно).
        data: Данные истории болезни (строка, обязательно).

    Возвращает:
        JSON ответ с кодом состояния 200, если обновление успешно.
        JSON ответ с кодом состояния 500, если произошла ошибка при обновлении.
    """
    data = request.get_json()

    if database.update_history(id, data.get('date'), data.get('pacientId'), data.get('hospitalId'), data.get('doctorId'), data.get('room'), data.get('data')):
        return jsonify({'message': 'History updated successfully'}), 200
    else:
        return jsonify({'message': 'Failed to update history'}), 500