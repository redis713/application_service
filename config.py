import os

class Config:
    SECRET_KEY = 'superfrog'

    # Настройки MySQL
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:DB_dev_38$@localhost/megaumc'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

