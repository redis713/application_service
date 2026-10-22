from datetime import datetime, timezone
from app.extensions import db

def utc_now():
    return datetime.now(timezone.utc)

class Organization(db.Model):
    __tablename__ = "organizations"

    id = db.Column(db.Integer, primary_key=True)

    # Наименования
    full_name = db.Column(db.String(500), nullable=False)
    short_name = db.Column(db.String(255), nullable=False)

    # Реквизиты
    inn = db.Column(db.String(12), nullable=False, index=True)
    kpp = db.Column(db.String(9), nullable=True)
    ogrn = db.Column(db.String(15), nullable=False, index=True)
    bank_name = db.Column(db.String(255), nullable=False)
    bik = db.Column(db.String(9), nullable=False)
    account_number = db.Column(db.String(30), nullable=False)  # Расчетный счет

    # Руководство
    boss_lastname = db.Column(db.String(100), nullable=False)
    boss_firstname = db.Column(db.String(100), nullable=False)
    boss_patronymic = db.Column(db.String(100), nullable=True)
    boss_position = db.Column(db.String(255), nullable=False)
    boss_authority = db.Column(db.String(255), nullable=False)  # Основание полномочий

    # Адреса и контакты организации
    legal_address = db.Column(db.String(500), nullable=False)
    actual_address = db.Column(db.String(500), nullable=False)
    phone = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), nullable=False)

    # Ответственный исполнитель (контактное лицо)
    executor_fio = db.Column(db.String(255), nullable=False)
    executor_position = db.Column(db.String(255), nullable=False)
    executor_phone = db.Column(db.String(50), nullable=False)
    executor_email = db.Column(db.String(100), nullable=True)

    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)

    # Связи
    applications = db.relationship("Application", back_populates="organization", cascade="all, delete-orphan")

    @property
    def boss_full_name(self) -> str:
        parts = [self.boss_lastname, self.boss_firstname, self.boss_patronymic]
        return " ".join(p for p in parts if p)

    def __repr__(self):
        return f"<Organization {self.id}: {self.short_name} (ИНН {self.inn})>"
