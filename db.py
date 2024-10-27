import re
import psycopg2
import time
import json
from datetime import datetime, timedelta
from collections import namedtuple
from werkzeug.security import generate_password_hash

class MainDataBase:
    def __init__(self, db):
        self.db = db
        self.cursor = db.cursor()

    def add_user(self, username, F_N, L_N, M_D, email, hash):
        now_utc = datetime.utcnow()
        moscow_offset = timedelta(hours=3)
        now_moscow = now_utc + moscow_offset
        time = now_moscow.strftime("%d.%m.%Y:%H.%M.%S")

        try:
            self.cursor.execute(f'SELECT COUNT(*) as "count" FROM users WHERE email LIKE %s', (email,))
            if self.cursor.fetchall()[0][0] > 0:
                return 'Пользователь с таким email уже существует!', 'error', False
            
            self.cursor.execute(f'SELECT COUNT(*) as "count" FROM users WHERE username LIKE %s', (username,))
            if self.cursor.fetchall()[0][0] > 0:
                return 'Пользователь с таким именем пользователя уже существует!', 'error', False

            self.cursor.execute("INSERT INTO users(username, First_Name, Last_Name, Middle_Name, avatar, email, pass_hash, User_Role, reg_time, deleted) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                                (username, F_N, L_N, M_D, "images/users/avatars/default.jpg", email, hash, 'user', time, False))

            self.db.commit()

            return 'Пользователь успешно зарегистрирован! Войдите в аккаунт!', 'success', True
        except Exception as e:
            return f'{e}', 'error', False

    def update_user_role(self, user_id, user_role):
        try:
            self.cursor.execute("UPDATE users SET user_role = %s WHERE id = %s", (user_role, user_id))
            self.db.commit()
            return True
        except Exception as e:
            print(e)
            self.db.rollback()
            return False

    def login_getuser(self, user_id):
        try:
            self.cursor.execute(f'SELECT * FROM users WHERE id = %s', (user_id,))
            result = self.cursor.fetchone()
            if not result:
                return False
            
            return result
        except Exception as e:
            print(f'{e}')

    def login_getuserdata(self, input):
        sql = f'SELECT * FROM users WHERE username = %s'
        if bool(re.match(r'^[^.+@]+@[^@]+\.[^@]+$', input)):
            sql = f'SELECT * FROM users WHERE email = %s'

        try:
            self.cursor.execute(sql, (input,))
            row = self.cursor.fetchone()

            if not row:
                return 'Пользователь не найден! Зарегистрируйтесь!', 'error', False

            columns = [col[0] for col in self.cursor.description] 
            User = namedtuple("User", columns)
            print(User.deleted)

            if User.deleted == True:
                return 'Пользователь удален!', 'error', False

            result = User(*row)

            return result
        except Exception as e:
            print(e)
            return False

    def getuserdata(self, input):
        sql = f'SELECT * FROM users WHERE id = %s'
        try:
            self.cursor.execute(sql, (input,))
            row = self.cursor.fetchone()

            if not row:
                return False

            columns = [col[0] for col in self.cursor.description] 
            User = namedtuple("User", columns)
            result = User(*row)

            return result
        except Exception as e:
            print(e)
            return False

    def save_refresh_token(self, user_id, token):
        try:
            self.cursor.execute("SELECT 1 FROM refresh_tokens WHERE user_id = %s", (user_id,))
            exists = self.cursor.fetchone()
            if exists:
                self.cursor.execute("UPDATE refresh_tokens SET token = %s WHERE user_id = %s", (token, user_id))
            else:
                self.cursor.execute("INSERT INTO refresh_tokens (user_id, token) VALUES (%s, %s)", (user_id, token))
            self.db.commit()
            return True
        except Exception as e:
            print(e)
            return False

    def is_refresh_token_valid(self, token):
        try:
            self.cursor.execute("SELECT 1 FROM refresh_tokens WHERE token = %s", (token,))
            return self.cursor.fetchone() is not None
        except Exception as e:
            print(e)
            return False

    def delete_refresh_token(self, token):
        try:
            self.cursor.execute("DELETE FROM refresh_tokens WHERE token = %s", (token,))
            self.db.commit()
            return True
        except Exception as e:
            print(e)
            return False
        

    def update_user(self, user_id, last_name, first_name, middle_name, email, pass_hash=None):
        try:
            if pass_hash:
                self.cursor.execute("UPDATE users SET last_name = %s, first_name = %s, middle_name = %s, email = %s, pass_hash = %s WHERE id = %s", (last_name, first_name, middle_name, email, pass_hash, user_id))
            else:
                self.cursor.execute("UPDATE users SET last_name = %s, first_name = %s, middle_name = %s, email = %s WHERE id = %s", (last_name, first_name, middle_name, email, user_id))

            self.db.commit()
            return True
        except Exception as e:
            print(e)
            return False

    def update_avatar(self, user_id, avatar_path):
        try:
            self.cursor.execute("UPDATE users SET avatar = %s WHERE id = %s", (avatar_path, user_id))
            self.db.commit()
            return True
        except Exception as e:
            print(e)
            return False

    def update_user_api(self, user_id, last_name, first_name, password=None):
        try:
            if password:
                pass_hash = generate_password_hash(password)
                self.cursor.execute("UPDATE users SET last_name = %s, first_name = %s, pass_hash = %s WHERE id = %s", (last_name, first_name, pass_hash, user_id))
            else:
                self.cursor.execute("UPDATE users SET last_name = %s, first_name = %s WHERE id = %s", (last_name, first_name, user_id))
            self.db.commit()
            return True
        except Exception as e:
            print(e)
            return False
        
    def update_user_api(self, user_id, last_name, first_name, username, middle_name, pass_hash=None, roles=None):
        try:
            update_fields = []
            update_values = []

            update_fields.append("last_name = %s")
            update_values.append(last_name)

            update_fields.append("first_name = %s")
            update_values.append(first_name)

            update_fields.append("middle_name = %s")
            update_values.append(middle_name)

            update_fields.append("middle_name = %s")
            update_values.append(middle_name)

            update_fields.append("username = %s")
            update_values.append(username)

            if pass_hash:
                update_fields.append("pass_hash = %s")
                update_values.append(pass_hash)
            
            if roles:
                update_fields.append("user_role = %s")
                update_values.append(",".join(roles))

            update_query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = %s"
            update_values.append(user_id)

            self.cursor.execute(update_query, tuple(update_values))

            self.db.commit()
            return True
        except Exception as e:
            print(e)
            return False
        
    def update_user_role(self, user_id, user_role):
            try:
                self.cursor.execute("UPDATE users SET User_Role = %s WHERE id = %s", (user_role, user_id))
                self.db.commit()
                return True
            except Exception as e:
                print(e)
                return False
        
    def soft_delete_user(self, user_id):
        try:
            self.cursor.execute("UPDATE users SET deleted = TRUE WHERE id = %s", (user_id,))
            self.db.commit()
            return True
        except Exception as e:
            print(e)
            return False
        
    def get_all_accounts(self, deleted=False, _from=0, _count=1000):
        where_clause = f"WHERE deleted = {deleted}"

        try:
            self.cursor.execute(f'SELECT * FROM users {where_clause} OFFSET {_from} LIMIT {_count}')

            rows = self.cursor.fetchall()
            if not rows:
                return []

            columns = [col[0] for col in self.cursor.description]
            User = namedtuple("User", columns)
            results = [User(*row) for row in rows]

            return results
        except Exception as e:
            print(e)
            return []
        
    def search_accounts(self, query):
        try:
            self.cursor.execute(
                "SELECT * FROM users WHERE CAST(id AS TEXT) LIKE %s OR username LIKE %s OR first_name LIKE %s OR last_name LIKE %s OR middle_name LIKE %s OR email LIKE %s OR CAST(hospital_id AS TEXT) LIKE %s OR CAST(doctor_id AS TEXT) LIKE %s",
                (f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%")
            )
            rows = self.cursor.fetchall()
            if not rows:
                return []

            columns = [col[0] for col in self.cursor.description]
            User = namedtuple("User", columns)
            results = [User(*row) for row in rows]
            return results

        except Exception as e:
            print(e)
            return []
        
    def get_doctors(self, name_filter=None, hospital_id=None, _from=0, _count=1000):
        try:
            where_clauses = ["User_Role = 'doctor'"]
            query_params = []

            if name_filter:
                where_clauses.append("FullName LIKE %s")
                query_params.append(f"%{name_filter}%")

            if hospital_id:
                where_clauses.append("hospital_id = %s")
                query_params.append(hospital_id)

            where_clause = " AND ".join(where_clauses)
            query = f"SELECT * FROM users WHERE {where_clause} OFFSET {_from} LIMIT {_count}"

            self.cursor.execute(query, tuple(query_params))
            rows = self.cursor.fetchall()

            if not rows:
                return []

            columns = [col[0] for col in self.cursor.description]
            User = namedtuple("User", columns)
            results = [User(*row) for row in rows]

            return results
        except Exception as e:
            print(e)
            return []
        


















    def get_all_hospitals(self, deleted=False, _from=0, _count=1000, hospital_id=None):
            where_clause = f"WHERE deleted = {deleted}"
            if hospital_id:
                where_clause += f" AND id = {hospital_id}"

            try:
                self.cursor.execute(f'SELECT * FROM hospitals {where_clause} OFFSET {_from} LIMIT {_count}')

                rows = self.cursor.fetchall()
                if not rows:
                    return []

                columns = [col[0] for col in self.cursor.description]
                Hospital = namedtuple("Hospital", columns)
                results = []

                for row in rows:
                    results.append(Hospital(*row))

                return results
            except Exception as e:
                print(e)
                return []
        
    def create_hospital(self, hospital_name, cabinets, phone, email, hospital_address):
        try:
            if isinstance(cabinets, list):
                cabinets = {str(i+1): cabinet for i, cabinet in enumerate(cabinets)}
            if isinstance(phone, list):
                phone = {str(i+1): p for i, p in enumerate(phone)}
            if isinstance(email, list):
                email = {str(i+1): e for i, e in enumerate(email)}

            self.cursor.execute("""
                INSERT INTO hospitals (hospital_name, cabinets, phone, email, hospital_address) 
                VALUES (%s, %s, %s, %s, %s)
            """, (hospital_name, json.dumps(cabinets), json.dumps(phone), json.dumps(email), hospital_address))
            self.db.commit()
            return True
        except Exception as e:
            print(f"Error creating hospital: {e}")
            self.db.rollback()
            return False
        
    def update_hospital(self, hospital_id, hospital_name, cabinets, phone, email, hospital_address, deleted):
        try:
            update_fields = []
            update_values = []

            if hospital_name:
                update_fields.append("hospital_name = %s")
                update_values.append(hospital_name)
            if cabinets:
                update_fields.append("cabinets = %s")
                update_values.append(json.dumps(cabinets))
            if phone:
                update_fields.append("phone = %s")
                update_values.append(json.dumps(phone))
            if email:
                update_fields.append("email = %s")
                update_values.append(json.dumps(email))
            if hospital_address:
                update_fields.append("hospital_address = %s")
                update_values.append(hospital_address)
            if deleted is not None:
                update_fields.append("deleted = %s")
                update_values.append(deleted)

            if not update_fields:
                return True

            update_query = f"UPDATE hospitals SET {', '.join(update_fields)} WHERE id = %s"
            update_values.append(hospital_id)

            self.cursor.execute(update_query, tuple(update_values))
            self.db.commit()
            return True
        except Exception as e:
            print(f"Error updating hospital: {e}")
            self.db.rollback()
            return False

    def soft_delete_hospital(self, hospital_id):
        try:
            self.cursor.execute("UPDATE hospitals SET deleted = TRUE WHERE id = %s", (hospital_id,))
            self.db.commit()
            return True
        except Exception as e:
            print(e)
            return False
        





    def create_timetable_entry(self, hospital_id, doctor_id, from_dt_str, to_dt_str, room):
        self.cursor.execute("""
            INSERT INTO timetable (hospital_id, doctor_id, from_dt, to_dt, room) VALUES (%s, %s, %s, %s, %s) RETURNING id;
        """, (hospital_id, doctor_id, from_dt_str, to_dt_str, room))
        self.db.commit()
        return self.cursor.fetchone()[0]

    def update_timetable_entry(self, id, data):
        self.cursor.execute("""
            UPDATE timetable
            SET hospital_id = %s, doctor_id = %s, from_dt = %s, to_dt = %s, room = %sWHERE id = %s;""", 
            (data['hospitalId'], data['doctorId'], data['from'], data['to'], data['room'], id))
        self.db.commit()

    def delete_timetable_entry(self, id):
        self.cursor.execute("""DELETE FROM timetable WHERE id = %s;""", (id,))
        self.db.commit()

    def get_hospital_schedule(self, hospital_id, from_dt_str, to_dt_str):
        from_dt = datetime.fromisoformat(from_dt_str.replace('Z', '+00:00'))
        to_dt = datetime.fromisoformat(to_dt_str.replace('Z', '+00:00'))
        self.cursor.execute("""
            SELECT * FROM timetable
            WHERE hospital_id = %s AND from_dt >= %s AND to_dt <= %s
        """, (hospital_id, from_dt, to_dt))
        return self.cursor.fetchall()

    def get_doctor_schedule(self, doctor_id, from_dt_str, to_dt_str):
        from_dt = datetime.fromisoformat(from_dt_str.replace('Z', '+00:00'))
        to_dt = datetime.fromisoformat(to_dt_str.replace('Z', '+00:00'))
        self.cursor.execute("""
            SELECT * FROM timetable
            WHERE doctor_id = %s AND from_dt >= %s AND to_dt <= %s
        """, (doctor_id, from_dt, to_dt))
        return self.cursor.fetchall()

    def delete_hospital_timetable_entries(self, hospital_id):
        try:
            self.cursor.execute("DELETE FROM timetable WHERE hospital_id = %s", (hospital_id,))
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise e
            

    def delete_doctor_timetable_entries(self, doctor_id):
        try:
            self.cursor.execute("DELETE FROM timetable WHERE doctor_id = %s", (doctor_id,))
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise e
    
    def has_appointments(self, timetable_id):
        self.cursor.execute("""
            SELECT EXISTS(SELECT 1 FROM appointments WHERE timetable_id = %s);
        """, (timetable_id,))
        return self.cursor.fetchone()[0]
    




    def get_hospital_room_schedule(self, hospital_id, room, from_dt_str, to_dt_str):
        cursor = self.db.cursor()
        from_dt = datetime.fromisoformat(from_dt_str.replace('Z', '+00:00'))
        to_dt = datetime.fromisoformat(to_dt_str.replace('Z', '+00:00'))
        cursor.execute("""
            SELECT * FROM timetable
            WHERE hospital_id = %s AND room = %s AND from_dt >= %s AND to_dt <= %s
        """, (hospital_id, room, from_dt, to_dt))

        return cursor.fetchall()

    def get_free_appointment_slots(self, timetable_id):
        cursor = self.db.cursor()
        cursor.execute("SELECT from_dt, to_dt FROM timetable WHERE id = %s", (timetable_id,))
        timetable_entry = cursor.fetchone()
        if not timetable_entry:
            return []

        from_dt, to_dt = timetable_entry
        slots = []
        current_dt = from_dt
        while current_dt < to_dt:
            slots.append(current_dt.isoformat().replace('+00:00', 'Z'))
            current_dt += timedelta(minutes=30)
        return slots

    def create_appointment(self, timetable_id, patient_id, appointment_time_str):
        cursor = self.db.cursor()
        appointment_time = datetime.fromisoformat(appointment_time_str.replace('Z', '+00:00'))
        try:
            cursor.execute("""
                INSERT INTO appointments (timetable_id, patient_id, appointment_time)
                VALUES (%s, %s, %s)
                RETURNING id
            """, (timetable_id, patient_id, appointment_time))
            self.db.commit()
            return cursor.fetchone()[0]
        except Exception as e:
            self.db.rollback()
            raise e

    def get_appointment(self, appointment_id):
        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM appointments WHERE id = %s", (appointment_id,))
        return cursor.fetchone()

    def delete_appointment(self, appointment_id):
        cursor = self.db.cursor()
        try:
            cursor.execute("DELETE FROM appointments WHERE id = %s", (appointment_id,))
            self.db.commit()
        except Exception as e:
            self.db.r








    def create_history(self, date, pacientId, hospitalId, doctorId, room, data):
        try:
            self.cursor.execute("""
                INSERT INTO history (date, pacientId, hospitalId, doctorId, room, data)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (date, pacientId, hospitalId, doctorId, room, data))
            self.db.commit()
            return self.cursor.fetchone()[0]
        except Exception as e:
            self.db.rollback()
            print(f"Error creating history: {e}")
            return False

    def get_history(self, id):
        try:
            self.cursor.execute("SELECT * FROM history WHERE id = %s", (id,))
            return self.cursor.fetchone()
        except Exception as e:
            print(f"Error fetching history: {e}")
            return None

    def get_account_history(self, pacientId):
        try:
            self.cursor.execute("SELECT * FROM history WHERE pacientId = %s", (pacientId,))
            return self.cursor.fetchall()
        except Exception as e:
            print(f"Error fetching account history: {e}")
            return None

    def update_history(self, id, date, pacientId, hospitalId, doctorId, room, data):
        try:
            self.cursor.execute("""
                UPDATE history
                SET date = %s, pacientId = %s, hospitalId = %s, doctorId = %s, room = %s, data = %s
                WHERE id = %s
            """, (date, pacientId, hospitalId, doctorId, room, data, id))
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Error updating history: {e}")
            return False
        












    def create_recommendation(self, user_id, title, text):
        try:
            self.cursor.execute(
                "INSERT INTO recommendations (user_id, title, text) VALUES (%s, %s, %s)",
                (user_id, title, text)
            )
            self.db.commit()
            return True
        except Exception as e:
            print(e)
            self.db.rollback()
            return False

    def get_recommendations_for_user(self, user_id):
        try:
            self.cursor.execute("SELECT * FROM recommendations WHERE user_id = %s", (user_id,))
            return self.cursor.fetchall() 
        except Exception as e:
            print(e)
            return []

    def update_recommendation(self, id, title, text):
        try:
            self.cursor.execute(
                "UPDATE recommendations SET title = %s, text = %s WHERE id = %s",
                (title, text, id)
            )
            self.db.commit()
            return True
        except Exception as e:
            print(e)
            self.db.rollback()
            return False


    def delete_recommendation(self, id):
        try:
            self.cursor.execute("DELETE FROM recommendations WHERE id = %s", (id,))
            self.db.commit()
            return True
        except Exception as e:
            print(e)
            self.db.rollback()
            return False

    def create_actual_item(self, data):
        try:
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['%s'] * len(data))
            query = f"INSERT INTO actual ({columns}) VALUES ({placeholders})"
            self.cursor.execute(query, tuple(data.values()))
            self.db.commit()
            return True
        except Exception as e:
            print(e)
            self.db.rollback()
            return False

    def get_all_actual_items(self):
        try:
            self.cursor.execute("SELECT * FROM actual")
            return self.cursor.fetchall()
        except Exception as e:
            print(e)
            return []

    def update_actual_item(self, id, data):
        try:
            update_fields = [f"{key} = %s" for key in data.keys()]
            query = f"UPDATE actual SET {', '.join(update_fields)} WHERE id = %s"
            self.cursor.execute(query, tuple(data.values()) + (id,))
            self.db.commit()
            return True
        except Exception as e:
            print(e)
            self.db.rollback()
            return False


    def delete_actual_item(self, id):
        try:
            self.cursor.execute("DELETE FROM actual WHERE id = %s", (id,))
            self.db.commit()
            return True
        except Exception as e:
            print(e)
            self.db.rollback()
            return False

    def get_appointments_for_user(self, user_id):
        try:
            self.cursor.execute(
                "SELECT a.*, t.hospital_id, t.doctor_id, t.room, u.first_name, u.last_name, u.middle_name "
                "FROM appointments a "
                "JOIN timetable t ON a.timetable_id = t.id "
                "JOIN users u ON t.doctor_id = u.id "
                "WHERE a.patient_id = %s",
                (user_id,)
            )
            rows = self.cursor.fetchall()
            if not rows:
                return []

            columns = [col[0] for col in self.cursor.description]
            Appointment = namedtuple("Appointment", columns)
            return [Appointment(*row) for row in rows] 

        except Exception as e:
            print(e)
            return []