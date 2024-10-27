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

time_bp = Blueprint('timetable', __name__)

database = None

@time_bp.before_request
def app_before_request():
    global database
    database = before_request()

def is_valid_datetime(dt_str):
    """
    Проверяет, является ли строка допустимым представлением даты и времени в формате ISO 8601
    с нулевыми секундами и минутами, кратными 30.

    Args:
        dt_str: Строка с датой и временем.

    Returns:
        True, если строка является допустимым представлением даты и времени, False в противном случае.
    """
    try:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        if dt.second != 0 or dt.minute % 30 != 0:
            return False
        return True
    except ValueError:
        return False

# ----------Обработка API----------

@time_bp.route('/Timetable', methods=['POST'])
@requires_auth
@requires_manager_admin
def create_timetable_entry():
    """
    Создает новую запись в расписании.

    Параметры запроса (JSON):
        hospitalId: ID больницы (целое число, обязательно).
        doctorId: ID врача (целое число, обязательно).
        from: Дата и время начала приема (строка ISO 8601, обязательно).
        to: Дата и время окончания приема (строка ISO 8601, обязательно).
        room: Номер кабинета (строка, обязательно).

    Возвращает:
        JSON ответ с кодом состояния 201 и ID созданной записи, если создание успешно.
        JSON ответ с кодом состояния 400, если предоставлены неверные данные или отсутствуют обязательные поля.
        JSON ответ с кодом состояния 500, если произошла ошибка при создании записи.
    """
    data = request.get_json()
    if not data:
        return jsonify({'message': 'No data provided'}), 400

    hospital_id = data.get('hospitalId')
    doctor_id = data.get('doctorId')
    from_dt_str = data.get('from')
    to_dt_str = data.get('to')
    room = data.get('room')

    if not all([hospital_id, doctor_id, from_dt_str, to_dt_str, room]):
        return jsonify({'message': 'Missing required fields'}), 400

    if not is_valid_datetime(from_dt_str) or not is_valid_datetime(to_dt_str):
        return jsonify({'message': 'Invalid datetime format'}), 400

    from_dt = datetime.fromisoformat(from_dt_str.replace('Z', '+00:00'))
    to_dt = datetime.fromisoformat(to_dt_str.replace('Z', '+00:00'))

    if from_dt >= to_dt:
        return jsonify({'message': '"from" must be before "to"'}), 400

    if (to_dt - from_dt) > timedelta(hours=12):
        return jsonify({'message': 'Difference between "from" and "to" cannot exceed 12 hours'}), 400

    timetable_id = database.create_timetable_entry(
        hospital_id, doctor_id, from_dt_str, to_dt_str, room)
    return jsonify({'id': timetable_id, 'message': 'Timetable entry created'}), 201

@time_bp.route('/Timetable/<int:id>', methods=['PUT', 'DELETE'])
@requires_auth
@requires_manager_admin
def update_delete_timetable_entry(id):
    """
    Обновляет или удаляет запись в расписании по ID.

    Параметры запроса:
        id: ID записи расписания (целое число, обязательно).

    Для метода PUT:
        Параметры запроса (JSON):
            hospitalId: ID больницы (целое число, обязательно).
            doctorId: ID врача (целое число, обязательно).
            from: Дата и время начала приема (строка ISO 8601, обязательно).
            to: Дата и время окончания приема (строка ISO 8601, обязательно).
            room: Номер кабинета (строка, обязательно).

    Возвращает:
        Для метода PUT:
            JSON ответ с кодом состояния 200, если обновление успешно.
            JSON ответ с кодом состояния 400, если предоставлены неверные данные, отсутствуют обязательные поля, или есть связанные записи.
        Для метода DELETE:
            JSON ответ с кодом состояния 200, если удаление успешно.
            JSON ответ с кодом состояния 400, если есть связанные записи.
            JSON ответ с кодом состояния 500, если произошла ошибка при удалении.
    """
    if request.method == 'PUT':
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No data provided'}), 400
        if database.has_appointments(id):
            return jsonify({'message': "Can't update, appointments exist"}), 400

        hospital_id = data.get('hospitalId')
        doctor_id = data.get('doctorId')
        from_dt_str = data.get('from')
        to_dt_str = data.get('to')
        room = data.get('room')

        if not all([hospital_id, doctor_id, from_dt_str, to_dt_str, room]):
            return jsonify({'message': 'Missing required fields'}), 400

        if not is_valid_datetime(from_dt_str) or not is_valid_datetime(to_dt_str):
            return jsonify({'message': 'Invalid datetime format'}), 400

        from_dt = datetime.fromisoformat(from_dt_str.replace('Z', '+00:00'))
        to_dt = datetime.fromisoformat(to_dt_str.replace('Z', '+00:00'))

        if from_dt >= to_dt:
            return jsonify({'message': '"from" must be before "to"'}), 400

        if (to_dt - from_dt) > timedelta(hours=12):
            return jsonify(
                {'message': 'Difference between "from" and "to" cannot exceed 12 hours'}), 400

        database.update_timetable_entry(id, data)
        return jsonify({'message': 'Timetable entry updated'}), 200

    elif request.method == 'DELETE':
        try:
            if database.has_appointments(id):
                return jsonify(
                    {'message': "Can't delete, appointments exist"}), 400
            database.delete_timetable_entry(id)
            return jsonify({'message': 'Timetable entry deleted'}), 200
        except:
            return jsonify({'message': 'Timetable not deleted'}), 400

@time_bp.route('/Timetable/Hospital/<int:id>', methods=['GET'])
@requires_auth
def hospital_timetable(id):
    """
    Возвращает расписание больницы по ID.

    Параметры запроса:
        id: ID больницы (целое число, обязательно).
        from: Дата и время начала периода (строка ISO 8601, обязательно).
        to: Дата и время окончания периода (строка ISO 8601, обязательно).

    Возвращает:
        JSON ответ с кодом состояния 200 и расписанием больницы, если найдено.
        JSON ответ с кодом состояния 400, если формат даты и времени неверный.

    """
    from_dt_str = request.args.get('from')
    to_dt_str = request.args.get('to')

    if not is_valid_datetime(from_dt_str) or not is_valid_datetime(to_dt_str):
        return jsonify({'message': 'Invalid datetime format'}), 400

    schedule = database.get_hospital_schedule(id, from_dt_str, to_dt_str)
    return jsonify(schedule), 200

@time_bp.route('/Timetable/Hospital/<int:id>', methods=['DELETE'])
@requires_auth
@requires_manager_admin
def hospital_timetable_delete(id):
    """
    Удаляет все записи расписания для больницы по ID.

    Параметры запроса:
        id: ID больницы (целое число, обязательно).

    Возвращает:
        JSON ответ с кодом состояния 200, если удаление успешно.
        JSON ответ с кодом состояния 500, если произошла ошибка при удалении.
    """
    try:
        database.delete_hospital_timetable_entries(id)
        return jsonify({'message': 'Hospital schedule entries deleted'}), 200
    except:
        return jsonify(
            {'message': 'Hospital schedule entries not deleted'}), 500

@time_bp.route('/Timetable/Doctor/<int:id>', methods=['GET'])
@requires_auth
def doctor_timetable(id):
    """
    Возвращает расписание врача по ID.

    Параметры запроса:
        id: ID врача (целое число, обязательно).
        from: Дата и время начала периода (строка ISO 8601, обязательно).
        to: Дата и время окончания периода (строка ISO 8601, обязательно).

    Возвращает:
        JSON ответ с кодом состояния 200 и расписанием врача, если найдено.
        JSON ответ с кодом состояния 400, если формат даты и времени неверный.
    """
    from_dt_str = request.args.get('from')
    to_dt_str = request.args.get('to')

    if not is_valid_datetime(from_dt_str) or not is_valid_datetime(to_dt_str):
        return jsonify({'message': 'Invalid datetime format'}), 400

    schedule = database.get_doctor_schedule(id, from_dt_str, to_dt_str)
    return jsonify(schedule), 200

@time_bp.route('/Timetable/Doctor/<int:id>', methods=['DELETE'])
@requires_auth
@requires_manager_admin
def doctor_timetable_delete(id):
    """
    Удаляет все записи расписания для врача по ID.

    Параметры запроса:
        id: ID врача (целое число, обязательно).

    Возвращает:
        JSON ответ с кодом состояния 200, если удаление успешно.
        JSON ответ с кодом состояния 500, если произошла ошибка при удалении.
    """
    try:
        database.delete_doctor_timetable_entries(id)
        return jsonify({'message': 'Doctor schedule entries deleted'}), 200
    except:
        return jsonify({'message': 'Doctor schedule entries not deleted'}), 500

@time_bp.route('/Timetable/Hospital/<int:id>/Room/<string:room>', methods=['GET'])
@requires_auth
@requires_doctor_manager_admin
def hospital_room_timetable(id, room):
    """
    Возвращает расписание для заданного кабинета в больнице.

    Параметры запроса:
        id: ID больницы (целое число, обязательно).
        room: Номер кабинета (строка, обязательно).
        from: Дата и время начала (строка в формате ISO 8601, обязательно).
        to: Дата и время окончания (строка в формате ISO 8601, обязательно).


    Возвращает:
        JSON ответ с кодом состояния 200 и расписанием, если найдено.
        JSON ответ с кодом состояния 400, если формат даты и времени неверный.
    """
    from_dt_str = request.args.get('from')
    to_dt_str = request.args.get('to')

    if not is_valid_datetime(from_dt_str) or not is_valid_datetime(to_dt_str):
        return jsonify({'message': 'Invalid datetime format'}), 400
    schedule = database.get_hospital_room_schedule(
        id, room, from_dt_str, to_dt_str)
    return jsonify(schedule), 200

@time_bp.route('/Timetable/<int:id>/Appointments', methods=['GET', 'POST'])
@requires_auth
def timetable_appointments(id):
    """
    Обрабатывает запросы, связанные со слотами для записи на прием.

    Параметры запроса:
        id: ID записи расписания (целое число, обязательно).
    
    Для POST запроса:
        time: Время записи (строка ISO 8601, обязательно).
    
    Возвращает:
        Для GET запроса:
            JSON ответ с кодом состояния 200 и списком доступных слотов.
        Для POST запроса:
            JSON ответ с кодом состояния 201 и ID созданной записи, если создание успешно.
            JSON ответ с кодом состояния 400, если формат даты и времени неверный или произошла ошибка при создании записи.
    """
    if request.method == 'GET':
        appointments = database.get_free_appointment_slots(id)
        return jsonify(appointments), 200

    elif request.method == 'POST':
        data = request.get_json()
        appointment_time_str = data.get('time')

        if not is_valid_datetime(appointment_time_str):
            return jsonify({'message': 'Invalid datetime format'}), 400

        try:
            appointment_id = database.create_appointment(
                id, g.current_user_id, appointment_time_str)
            return jsonify(
                {'id': appointment_id, 'message': 'Appointment created'}), 201
        except Exception as e:
            return jsonify({'message': str(e)}), 400

@time_bp.route('/Appointment/<int:id>', methods=['DELETE'])
@requires_auth
def delete_appointment(id):
    """
    Удаляет запись на прием по ID.

    Параметры запроса:
        id: ID записи на прием (целое число, обязательно).

    Возвращает:
        JSON ответ с кодом состояния 200, если удаление успешно.
        JSON ответ с кодом состояния 404, если запись на прием не найдена.
        JSON ответ с кодом состояния 500, если произошла ошибка при удалении.
    """
    appointment = database.get_appointment(id)
    user = database.getuserdata(g.current_user_id)

    if not appointment:
        return jsonify({'message': 'Appointment not found'}), 404

    if g.current_user_id == id or user.user_role not in ('admin', 'manager'):
        try:
            database.delete_appointment(id)
            return jsonify({'message': 'Appointment deleted'}), 200
        except:
            return jsonify({'message': 'Appointment not deleted'}), 500
    else:
        return jsonify(
            {'message': 'You are not the owner of the appointment'}), 500