from flask_mysqldb import MySQL
from dotenv import load_dotenv
import os

# MySQL 객체 생성
mysql = MySQL()

def init_db(app):
    load_dotenv()  # .env 로드

    app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
    app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
    app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
    app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')

    mysql.init_app(app)  # Flask 앱과 MySQL 연결
