import os

class Config:
    SECRET_KEY = 'your_key'

    # Настройки MySQL
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://user:password$@localhost/dbname'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_TIME_LIMIT = 10800  # 3 часа на заполнение формы
