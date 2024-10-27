import psycopg2
from utils import create_tabl
import os
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.getenv("DB_URL")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

def check_tables_exist(db):
    tables_to_check = ["users", "hospitals", "refresh_tokens", "timetable", "appointments", "history", "recommendations", "actual"]
    cursor = db.cursor()
    for table in tables_to_check:
        try:
            cursor.execute(f"SELECT 1 FROM {table} LIMIT 1")
            cursor.fetchone()
        except psycopg2.ProgrammingError:
            return False
    return True


try:
    db = psycopg2.connect(database=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_URL, port=5432, client_encoding='utf8')
    if not check_tables_exist(db):
        create_tabl()
    else:
        pass
except Exception as e:
    print(e)