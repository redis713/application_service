import os

class Config:
    SECRET_KEY = 'your_key'

    # Настройки MySQL
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://user:password$@localhost/dbname'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

