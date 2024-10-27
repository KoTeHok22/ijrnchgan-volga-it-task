from flask import Flask, render_template, request, g, flash, url_for, redirect, jsonify, make_response
from functools import wraps
import os
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from api_account import acc_bp
from api_hospitals import hos_bp
from api_timetable import time_bp
from api_documents import doc_bp

from forms import SettingsForm, SignUpForm, SignInForm, SettingsFormAdmin
from utils import requires_auth, requires_admin, check_token, before_request

load_dotenv()
secret_key = os.getenv("SECRET_KEY")

app = Flask(__name__)
app.config.from_object(__name__)
app.config['SECRET_KEY'] = secret_key

app.register_blueprint(acc_bp, url_prefix='/api')
app.register_blueprint(hos_bp, url_prefix='/api')
app.register_blueprint(time_bp, url_prefix='/api')
app.register_blueprint(doc_bp, url_prefix='/api')

database = None

@app.before_request
def app_before_request():
    global database
    database = before_request()

#----------Обработка запросов----------

@app.route('/')
def index():
    return render_template('index.html')

#-----Запросы для  модуля аккаунта-----

@app.route('/signin')
def signin():
    token = request.cookies.get('access_token')
    if check_token(token):
        return redirect(url_for('profile'))
    else:
        form = SignInForm()
        return render_template('signin.html', form=form)

@app.route('/signup')
def signup():
    token = request.cookies.get('access_token')
    if check_token(token):
        return redirect(url_for('profile'))
    else:
        form = SignUpForm()
        return render_template('signup.html', form=form)

@app.route('/profile/signup')
@requires_auth
@requires_admin
def signup_admin():
    form = SignUpForm()
    return render_template('profile/admin/signup.html', form=form)

@app.route('/profile')
@requires_auth
def profile():
    actual = database.get_all_actual_items()
    print(actual)

    actual = [{'title': item[1], 'icon': url_for('static', filename=item[2]), 'link': item[3], 'color': item[4], 'border-color': item[5]} for item in actual]

    recommendations = database.get_recommendations_for_user(g.current_user_id)
    recommendations = [{'title': item[2], 'text': item[3], 'link': url_for('recommendation_details', recommendation_id=item[0]), 'color': '#95c9ff', 'border-color': '#71a8e8'} for item in recommendations]

    appointments = database.get_appointments_for_user(g.current_user_id)
    appointments = [{'time': f"{item.appointment_time.strftime('%d.%m.%Y %H:%M')}", 
                     'full_name': f'{item.first_name} {item.last_name} {item.middle_name}',
                     'cabinet': f'{item.room}',
                     'link': '#',
                     'color': '#a0f1b9', 
                     'border-color': '#66d686'} for item in appointments]
    print(appointments)

    return render_template('profile/profile.html', actual=actual, recommendations=recommendations, appointments=appointments)

@app.route('/profile/accounts', methods=['GET'])
@requires_auth
@requires_admin
def accounts():
    all_accounts = database.get_all_accounts()
    return render_template('profile/admin/users.html', accounts=all_accounts)

@app.route('/profile/settings', methods=['GET'])
@requires_auth
def settings():
    user = database.getuserdata(g.current_user_id)
    form = SettingsForm(obj=user)
    return render_template('profile/settings.html', form=form, user=user)

@app.route('/profile/accounts/<int:id>', methods=['GET'])
@requires_auth
@requires_admin
def user(id):
    user = database.getuserdata(id)
    form = SettingsFormAdmin(obj=user)
    return render_template('profile/admin/user.html', form=form, user=user)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)