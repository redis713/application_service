from datetime import datetime, timezone
from app.extensions import db

def utc_now():
    return datetime.now(timezone.utc)

class Person(db.Model):
    __tablename__ = "persons"

    id = db.Column(db.Integer, primary_key=True)

    # Уникальный идентификатор гражданина в РФ
    snils = db.Column(db.String(11), unique=True, nullable=False, index=True)

    # ФИО
    lastname = db.Column(db.String(100), nullable=False)
    firstname = db.Column(db.String(100), nullable=False)
    patronymic = db.Column(db.String(100), nullable=True)

    birthdate = db.Column(db.Date, nullable=False)
    citizenship = db.Column(db.String(100), default="РФ", nullable=False)

    phone = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), nullable=False)

    # Базовое профессиональное образование (для ФИС ФРДО)
    education_level = db.Column(db.String(100), nullable=False)  # Высшее, СПО и т.д.
    institute_name = db.Column(db.String(500), nullable=False)
    diploma_series_number = db.Column(db.String(100), nullable=False)
    diploma_date = db.Column(db.String(50), nullable=False)
    diploma_lastname = db.Column(db.String(100), nullable=False)  # Фамилия в дипломе

    # Поля пожарной безопасности (заполняются только при обучении на ПБ)
    fire_safety_document_type = db.Column(db.String(100), nullable=True)
    fire_institution = db.Column(db.String(500), nullable=True)
    fire_series = db.Column(db.String(50), nullable=True)
    fire_number = db.Column(db.String(50), nullable=True)
    fire_date = db.Column(db.String(50), nullable=True)

    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)

    # Связи
    listeners = db.relationship("ApplicationListener", back_populates="person", cascade="all, delete-orphan")

    @property
    def full_name(self) -> str:
        parts = [self.lastname, self.firstname, self.patronymic]
        return " ".join(p for p in parts if p)

    @property
    def formatted_snils(self) -> str:
        s = self.snils or ""
        if len(s) == 11:
            return f"{s[:3]}-{s[3:6]}-{s[6:9]} {s[9:]}"
        return s

    def __repr__(self):
        return f"<Person {self.id}: {self.full_name} ({self.formatted_snils})>"
