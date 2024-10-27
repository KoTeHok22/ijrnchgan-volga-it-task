from flask import Flask, request, g, flash, url_for, redirect, jsonify, make_response, Blueprint
from utils import requires_auth, requires_admin, generate_refresh_token, generate_access_token, before_request, is_api_request

import jwt
from functools import wraps
import os
from dotenv import load_dotenv
import re
from werkzeug.security import generate_password_hash, check_password_hash
import pathlib

from werkzeug.utils import secure_filename
from forms import HospitalForm

hos_bp = Blueprint('hospitals', __name__)

database = None
@hos_bp.before_request
def app_before_request():
    global database
    database = before_request()

#----------Обработка API----------

@hos_bp.route('/Hospitals', methods=['GET', 'POST'])
@requires_auth
def api_hospitals():
    if request.method == 'GET':
        from_param = request.args.get('from', default=0, type=int)
        count_param = request.args.get('count', default=1000, type=int)

        hospitals = database.get_all_hospitals(deleted=False, _from=from_param, _count=count_param)
        hospital_list = []
        print(hospitals)
        for hospital in hospitals:
            hospital_list.append({
                'id': hospital.id,
                'hospital_name': hospital.hospital_name,
                'cabinets': hospital.cabinets,
                'phone': hospital.phone,
                'email': hospital.email,
                'hospital_address': hospital.hospital_address,
            })
        return jsonify(hospital_list), 200

    if request.method == 'POST':
        form = HospitalForm()
        if form.validate_on_submit():
            data = request.get_json()

            hospital_name = data.get('hospital_name')
            cabinets = data.get('cabinets')
            phone = data.get('phone')
            email = data.get('email')
            hospital_address = data.get('hospital_address')

            if database.create_hospital(hospital_name, cabinets, phone, email, hospital_address):

                if is_api_request():
                    return jsonify({'message': 'Hospital created successfully'}), 201
                flash('Больница успешно создана!', 'success')
                return redirect(url_for('profile'))
            else:
                if is_api_request():
                    return jsonify({'message': 'Failed to create hospital'}), 500
                flash('Ошибка при создании больницы!', 'error')
        else:
             if is_api_request():
                 print(form.errors)
                 return jsonify({'message': 'Missing required fields'}), 400
             flash('Ошибка в форме', 'error')       
        return redirect(url_for('profile'))
    
@hos_bp.route('/Hospitals/<int:id>', methods=['GET'])
@requires_auth
def api_hospital(id):
    hospital = database.get_all_hospitals(deleted=False, _from=0, _count=1, hospital_id=id)[0]

    if not hospital:
        return jsonify({'message': 'Hospital not found'}), 404

    hospital_data = {
        'id': hospital.id,
        'hospital_name': hospital.hospital_name,
        'cabinets': hospital.cabinets,
        'phone': hospital.phone,
        'email': hospital.email,
        'hospital_address': hospital.hospital_address,
    }
    return jsonify(hospital_data), 200

@hos_bp.route('/Hospitals/<int:id>', methods=['PUT', 'DELETE'])
@requires_auth
@requires_admin
def api_hospital_admin(id):
    if request.method == 'PUT':
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No data provided'}), 400

        hospital_name = data.get('hospital_name')
        cabinets = data.get('cabinets')
        phone = data.get('phone')
        email = data.get('email')
        hospital_address = data.get('hospital_address')
        deleted = data.get('deleted')

        if database.update_hospital(id, hospital_name, cabinets, phone, email, hospital_address, deleted):
            return jsonify({'message': 'Hospital updated successfully'}), 200
        else:
            return jsonify({'message': 'Failed to update hospital'}), 500

    elif request.method == 'DELETE':
        if database.soft_delete_hospital(id):
            return jsonify({'message': 'Hospital deleted successfully'}), 200
        else:
            return jsonify({'message': 'Failed to delete hospital'}), 500

@hos_bp.route('/Hospitals/<int:id>/Rooms', methods=['GET'])
@requires_auth
def api_hospital_rooms(id):
    hospital = database.get_all_hospitals(deleted=False, _from=0, _count=1, hospital_id=id)[0]
    if not hospital:
        return jsonify({'message': 'Hospital not found'}), 404

    rooms = hospital.cabinets
    return jsonify(rooms), 200