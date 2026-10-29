import secrets
from datetime import datetime, timezone
from app.extensions import db
from app.constants import ApplicationStatus, StudyForm, TrainingDirection, DeliveryType

def utc_now():
    return datetime.now(timezone.utc)

def generate_secret_token() -> str:
    return secrets.token_urlsafe(32)


class Application(db.Model):
    __tablename__ = "applications"

    id = db.Column(db.Integer, primary_key=True)

    # Официальный номер заявки (например: 2026-ГО-0001)
    app_number = db.Column(db.String(50), unique=True, nullable=False, index=True)

    # Секретный токен для безопасного доступа заявителя без логина (прикрепить скан, проверить статус)
    secret_token = db.Column(db.String(64), unique=True, nullable=False, default=generate_secret_token, index=True)

    direction = db.Column(db.String(50), nullable=False, default=TrainingDirection.GOCHS.value)
    study_form = db.Column(db.String(50), nullable=False, default=StudyForm.DISTANT.value)

    status = db.Column(db.String(50), nullable=False, default=ApplicationStatus.DRAFT.value, index=True)

    # Данные организации (хранятся непосредственно в заявке)
    org_full_name = db.Column(db.String(500), nullable=False)
    org_short_name = db.Column(db.String(255), nullable=False)
    inn = db.Column(db.String(12), nullable=False, index=True)
    kpp = db.Column(db.String(9), nullable=True)
    ogrn = db.Column(db.String(15), nullable=False, index=True)
    bank_name = db.Column(db.String(255), nullable=False)
    bik = db.Column(db.String(9), nullable=False)
    account_number = db.Column(db.String(30), nullable=False)

    # Руководство организации
    boss_lastname = db.Column(db.String(100), nullable=False)
    boss_firstname = db.Column(db.String(100), nullable=False)
    boss_patronymic = db.Column(db.String(100), nullable=True)
    boss_position = db.Column(db.String(255), nullable=False)
    boss_authority = db.Column(db.String(255), nullable=False)

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

    # Временные метки и аудит
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)
    submitted_at = db.Column(db.DateTime, nullable=True)  # Момент загрузки подписанного скана
    last_edited_by = db.Column(db.String(100), nullable=True)  # "пользователь" или метка сотрудника

    # Подписанный скан документа
    signed_scan_filename = db.Column(db.String(255), nullable=True)
    signed_scan_path = db.Column(db.String(500), nullable=True)

    # Заметки заявителя или методиста
    notes = db.Column(db.Text, nullable=True)

    # Связи
    listeners = db.relationship("ApplicationListener", back_populates="application", cascade="all, delete-orphan")
    attachments = db.relationship("ApplicationAttachment", back_populates="application", cascade="all, delete-orphan")

    @property
    def boss_full_name(self) -> str:
        parts = [self.boss_lastname, self.boss_firstname, self.boss_patronymic]
        return " ".join(p for p in parts if p)

    @property
    def full_name(self) -> str:
        return self.org_full_name

    @property
    def short_name(self) -> str:
        return self.org_short_name

    @property
    def organization(self):
        """Свойство совместимости: возвращает саму заявку с реквизитами организации."""
        return self

    @property
    def status_label(self) -> str:
        return ApplicationStatus.label(self.status)

    @property
    def direction_label(self) -> str:
        return TrainingDirection.label(self.direction)

    @property
    def study_form_label(self) -> str:
        return StudyForm.label(self.study_form)

    def __repr__(self):
        return f"<Application {self.app_number} [{self.status}]: {self.org_short_name}>"


class ApplicationListener(db.Model):
    __tablename__ = "application_listeners"

    id = db.Column(db.Integer, primary_key=True)

    application_id = db.Column(db.Integer, db.ForeignKey("applications.id", ondelete="CASCADE"), nullable=False)
    person_id = db.Column(db.Integer, db.ForeignKey("persons.id"), nullable=False)

    # Должность в направляющей организации
    position = db.Column(db.String(255), nullable=False)

    # Способ доставки документа об образовании
    diploma_delivery = db.Column(db.String(50), default=DeliveryType.PERSONAL.value, nullable=False)
    delivery_address = db.Column(db.String(500), nullable=True)

    # Связи
    application = db.relationship("Application", back_populates="listeners")
    person = db.relationship("Person", back_populates="listeners")
    courses = db.relationship("ListenerCourse", back_populates="listener", cascade="all, delete-orphan")

    @property
    def delivery_label(self) -> str:
        return DeliveryType.label(self.diploma_delivery)


class ListenerCourse(db.Model):
    __tablename__ = "listener_courses"

    id = db.Column(db.Integer, primary_key=True)

    listener_id = db.Column(db.Integer, db.ForeignKey("application_listeners.id", ondelete="CASCADE"), nullable=False)
    program_id = db.Column(db.Integer, db.ForeignKey("programs.id"), nullable=False)

    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)

    # Связи
    listener = db.relationship("ApplicationListener", back_populates="courses")
    program = db.relationship("Program", back_populates="listener_courses")


class ApplicationAttachment(db.Model):
    __tablename__ = "application_attachments"

    id = db.Column(db.Integer, primary_key=True)

    application_id = db.Column(db.Integer, db.ForeignKey("applications.id", ondelete="CASCADE"), nullable=False)
    file_type = db.Column(db.String(50), default="signed_scan", nullable=False)  # signed_scan, payment, etc.

    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, nullable=True)

    uploaded_at = db.Column(db.DateTime, default=utc_now)

    application = db.relationship("Application", back_populates="attachments")
