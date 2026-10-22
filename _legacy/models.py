from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date


db = SQLAlchemy()

class Person(db.Model):
    __tablename__ = "person"

    id = db.Column(db.Integer, primary_key=True)

    firstname = db.Column(db.String(100), nullable=False)
    lastname = db.Column(db.String(100), nullable=False)
    patronymic = db.Column(db.String(100))

    birthdate = db.Column(db.Date)

    citizenship = db.Column(db.String(255), unique=False, nullable=False)
    education = db.Column(db.String(255), unique=False, nullable=False)
    institute_name = db.Column(db.String(255), unique=False, nullable=False)
    diploma_seriesnumber = db.Column(db.String(255), unique=False, nullable=False)
    diploma_date = db.Column(db.String(255), unique=False, nullable=False)
    diploma_lastname = db.Column(db.String(255), unique=False, nullable=False)
    snils = db.Column(db.String(255), unique=False, nullable=False)
    # student_category = db.Column(db.String(255), unique=False, nullable=False)
    fire_safety_document_type = db.Column(db.String(255), unique=False, nullable=False)
    certificate_institution = db.Column(db.String(255), unique=False, nullable=False)
    diploma_series = db.Column(db.String(255), unique=False, nullable=False)
    certificate_number = db.Column(db.String(255), unique=False, nullable=False)
    certificate_date = db.Column(db.String(255), unique=False, nullable=False)
    # start_date = db.Column(db.String(255), unique=False, nullable=False)
    # end_date = db.Column(db.String(255), unique=False, nullable=False)
    student_telephone = db.Column(db.String(255), unique=False, nullable=False)
    email = db.Column(db.String(255), unique=False, nullable=False)
    phone = db.Column(db.String(50))

    # Один человек -> много участий в заявках
    listeners = db.relationship("Listener", back_populates="person", cascade="all, delete-orphan")


class Organization(db.Model):
    __tablename__ = "organization"

    id = db.Column(db.Integer, primary_key=True)

    organization_full_name = db.Column(db.String(255), unique=False, nullable=False)
    organization_short_name = db.Column(db.String(255), unique=False, nullable=False)
    boss_firstname = db.Column(db.String(255), unique=False, nullable=False)
    boss_lastname = db.Column(db.String(255), unique=False, nullable=False)
    boss_patronymic = db.Column(db.String(255), unique=False, nullable=False)
    doljnost_boss = db.Column(db.String(255), unique=False, nullable=False)
    polnamochia_boss = db.Column(db.String(255), unique=False, nullable=False)
    ogrn = db.Column(db.String(255), unique=False, nullable=False)
    inn = db.Column(db.String(255), unique=False, nullable=False)
    kpp = db.Column(db.String(255), unique=False, nullable=False)
    bank_name = db.Column(db.String(255), unique=False, nullable=False)
    rasch_schot = db.Column(db.String(255), unique=False, nullable=False)
    bik = db.Column(db.String(255), unique=False, nullable=False)
    fakt_address = db.Column(db.String(255), unique=False, nullable=False)
    yur_address = db.Column(db.String(255), unique=False, nullable=False)
    telephone = db.Column(db.String(255), unique=False, nullable=False)
    email = db.Column(db.String(255), unique=False, nullable=False)
    doljnost_executor = db.Column(db.String(255), unique=False, nullable=False)
    fio_executor = db.Column(db.String(255), unique=False, nullable=False)
    telephone_executor = db.Column(db.String(255), unique=False, nullable=False)

    # Организация > заявки
    applications = db.relationship("Application", back_populates="organization", cascade="all, delete-orphan")


class Application(db.Model):
    __tablename__ = "application"

    id = db.Column(db.Integer, primary_key=True)

    organization_id = db.Column(db.Integer, db.ForeignKey("organization.id"), nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50))

    # Заявка > организация
    organization = db.relationship("Organization", back_populates="applications")

    # Заявка > строки слушателей
    listeners = db.relationship("Listener", back_populates="application", cascade="all, delete-orphan")


class Listener(db.Model):
    __tablename__ = "listener"

    id = db.Column(db.Integer, primary_key=True)

    application_id = db.Column(db.Integer, db.ForeignKey("application.id"), nullable=False)
    person_id = db.Column(db.Integer, db.ForeignKey("person.id"), nullable=False)

    # <-- Добавленное поле: должность слушателя в этой заявке
    position = db.Column(db.String(255))
    diploma_delivery = db.Column(db.String(255), unique=False, nullable=False)
    delivery_address = db.Column(db.String(255), unique=False, nullable=False)

    application = db.relationship("Application", back_populates="listeners")
    person = db.relationship("Person", back_populates="listeners")

    # ВАЖНО:
    # Listener > ВСЕ программы, которые этот слушатель проходил (в этой заявке)
    programs = db.relationship("ListenerProgram", back_populates="listener", cascade="all, delete-orphan")


class Program(db.Model):
    __tablename__ = "program"

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(255), nullable=False)
    hours = db.Column(db.Integer)
    study_form = db.Column(db.String(100), unique=False, nullable=False)

    # Program > все случаи, когда люди проходили эту программу
    listeners = db.relationship("ListenerProgram", back_populates="program", cascade="all, delete-orphan")


class ListenerProgram(db.Model):
    __tablename__ = "listener_program"

    id = db.Column(db.Integer, primary_key=True)

    listener_id = db.Column(db.Integer, db.ForeignKey("listener.id"), nullable=False)
    program_id = db.Column(db.Integer, db.ForeignKey("program.id"), nullable=False)

    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)

    # Нахождение обратных объектов
    listener = db.relationship("Listener", back_populates="programs")
    program = db.relationship("Program", back_populates="listeners")