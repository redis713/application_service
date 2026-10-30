import os
import re
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from werkzeug.utils import secure_filename
from app.extensions import db
from app.constants import ApplicationStatus, StudyForm, TrainingDirection
from app.models.person import Person
from app.models.program import Program
from app.models.application import (
    Application,
    ApplicationListener,
    ListenerCourse,
    ApplicationAttachment,
)

class ApplicationService:
    @staticmethod
    def _s(val: Any) -> str:
        """Безопасная очистка строкового значения (защита от None)."""
        return str(val).strip() if val is not None else ""

    @staticmethod
    def clean_digits(value: Optional[str]) -> str:
        """Очищает строку, оставляя только цифры (для СНИЛС, ИНН, ОГРН, телефонов)."""
        if not value:
            return ""
        return re.sub(r"\D", "", str(value))

    @classmethod
    def generate_app_number(cls, direction: str) -> str:
        """
        Генерирует уникальный удобочитаемый номер заявки, например:
        ГО-2026-0001, ПБ-2026-0002
        """
        prefix_map = {
            TrainingDirection.GOCHS.value: "ГО",
            TrainingDirection.FIRE.value: "ПБ",
            TrainingDirection.CALL112.value: "112",
            TrainingDirection.ANTITERROR.value: "АТ",
            TrainingDirection.SPECIALIST.value: "СПГО",
        }
        prefix = prefix_map.get(direction, "ЗЯВ")
        year = datetime.now().year

        # Считаем количество заявок за текущий год
        current_year_count = Application.query.filter(
            Application.created_at >= datetime(year, 1, 1)
        ).count()
        next_num = current_year_count + 1

        candidate = f"{prefix}-{year}-{next_num:04d}"
        # Проверяем на случай коллизий
        while Application.query.filter_by(app_number=candidate).first() is not None:
            next_num += 1
            candidate = f"{prefix}-{year}-{next_num:04d}"

        return candidate

    @classmethod
    def save_or_update_person(cls, student_data: Dict[str, Any]) -> Person:
        """Находит гражданина по СНИЛС или создает нового."""
        _s = cls._s
        clean_snils = cls.clean_digits(student_data.get("snils"))

        person = Person.query.filter_by(snils=clean_snils).first()

        raw_birth = student_data.get("student_birthdate")
        birthdate = raw_birth
        if isinstance(raw_birth, str) and raw_birth:
            try:
                birthdate = datetime.strptime(raw_birth, "%Y-%m-%d").date()
            except ValueError:
                try:
                    birthdate = datetime.strptime(raw_birth, "%d.%m.%Y").date()
                except ValueError:
                    birthdate = datetime.now().date()

        raw_diploma = student_data.get("diploma_date")
        diploma_date = raw_diploma
        if isinstance(raw_diploma, str) and raw_diploma.strip():
            diploma_date = None
            for fmt in ("%Y-%m-%d", "%d.%m.%Y"):
                try:
                    diploma_date = datetime.strptime(raw_diploma.strip(), fmt).date()
                    break
                except ValueError:
                    pass
        elif not raw_diploma:
            diploma_date = None

        raw_fire = student_data.get("fire_date")
        fire_date = raw_fire
        if isinstance(raw_fire, str) and raw_fire.strip():
            fire_date = None
            for fmt in ("%Y-%m-%d", "%d.%m.%Y"):
                try:
                    fire_date = datetime.strptime(raw_fire.strip(), fmt).date()
                    break
                except ValueError:
                    pass
        elif not raw_fire:
            fire_date = None

        phone_val = _s(student_data.get("student_telephone") or student_data.get("phone"))
        email_val = _s(student_data.get("student_email") or student_data.get("email"))
        edu_val = _s(student_data.get("education") or student_data.get("education_level"))
        dip_num = _s(student_data.get("diploma_seriesnumber") or student_data.get("diploma_series_number"))

        if not person:
            person = Person(
                snils=clean_snils,
                lastname=_s(student_data.get("student_lastname")),
                firstname=_s(student_data.get("student_firstname")),
                patronymic=_s(student_data.get("student_patronymic")) or None,
                birthdate=birthdate,
                citizenship=_s(student_data.get("citizenship")) or "РФ",
                phone=phone_val,
                email=email_val,
                education_level=edu_val,
                institute_name=_s(student_data.get("institute_name")),
                diploma_series_number=dip_num or None,
                diploma_date=diploma_date,
                diploma_lastname=_s(student_data.get("diploma_lastname")) or None,
                fire_safety_document_type=_s(student_data.get("fire_safety_document_type")) or None,
                fire_institution=_s(student_data.get("fire_institution")) or None,
                fire_series=_s(student_data.get("fire_series")) or None,
                fire_number=_s(student_data.get("fire_number")) or None,
                fire_date=fire_date
            )
            db.session.add(person)
        else:
            # Обновляем данные гражданина
            person.lastname = _s(student_data.get("student_lastname")) or person.lastname
            person.firstname = _s(student_data.get("student_firstname")) or person.firstname
            person.patronymic = _s(student_data.get("student_patronymic")) or None
            if birthdate:
                person.birthdate = birthdate
            if student_data.get("citizenship"):
                person.citizenship = _s(student_data.get("citizenship"))
            if phone_val:
                person.phone = phone_val
            if email_val:
                person.email = email_val
            if edu_val:
                person.education_level = edu_val
            if student_data.get("institute_name"):
                person.institute_name = _s(student_data.get("institute_name"))

            if edu_val == "Неоконченное высшее (студент)":
                person.diploma_series_number = None
                person.diploma_date = None
                person.diploma_lastname = None
            else:
                if dip_num:
                    person.diploma_series_number = dip_num
                person.diploma_date = diploma_date
                person.diploma_lastname = _s(student_data.get("diploma_lastname")) or None

            if student_data.get("fire_safety_document_type"):
                person.fire_safety_document_type = _s(student_data.get("fire_safety_document_type"))
                person.fire_institution = _s(student_data.get("fire_institution")) or None
                person.fire_series = _s(student_data.get("fire_series")) or None
                person.fire_number = _s(student_data.get("fire_number")) or None
                person.fire_date = fire_date

        db.session.flush()
        return person

    @classmethod
    def _save_application_listeners(cls, application: Application, students_data: List[Dict[str, Any]]):
        """Сохраняет слушателей и их курсы для заявки."""
        _s = cls._s
        for s_data in students_data:
            person = cls.save_or_update_person(s_data)

            listener = ApplicationListener(
                application=application,
                person=person,
                position=_s(s_data.get("student_position") or s_data.get("position")),
                diploma_delivery=s_data.get("diploma_delivery") or "personal",
                delivery_address=_s(s_data.get("delivery_address")) or None
            )
            db.session.add(listener)
            db.session.flush()

            categories = s_data.get("student_categories", [])
            for cat_item in categories:
                cat_code = cat_item.get("category")
                if not cat_code:
                    continue

                prog = Program.query.filter_by(code=cat_code).first()
                if not prog:
                    prog = Program.query.first()

                start_d = cat_item.get("start_date")
                end_d = cat_item.get("end_date")

                if isinstance(start_d, str) and start_d.strip():
                    parsed_s = None
                    for fmt in ("%Y-%m-%d", "%d.%m.%Y"):
                        try:
                            parsed_s = datetime.strptime(start_d.strip(), fmt).date()
                            break
                        except ValueError:
                            pass
                    start_d = parsed_s

                if isinstance(end_d, str) and end_d.strip():
                    parsed_e = None
                    for fmt in ("%Y-%m-%d", "%d.%m.%Y"):
                        try:
                            parsed_e = datetime.strptime(end_d.strip(), fmt).date()
                            break
                        except ValueError:
                            pass
                    end_d = parsed_e

                if not start_d or not end_d:
                    continue

                course = ListenerCourse(
                    listener=listener,
                    program=prog,
                    start_date=start_d,
                    end_date=end_d
                )
                db.session.add(course)

    @classmethod
    def create_application_draft(
        cls,
        org_data: Dict[str, Any],
        students_data: List[Dict[str, Any]],
        direction: str = TrainingDirection.GOCHS.value,
        study_form: str = StudyForm.DISTANT.value
    ) -> Application:
        """
        Создает черновик заявки со всеми слушателями и программами в базе данных.
        Реквизиты организации сохраняются непосредственно внутри самой заявки.
        Возвращает объект Application с уникальным app_number и secret_token.
        """
        _s = cls._s
        max_retries = 5
        for attempt in range(max_retries):
            try:
                app_number = cls.generate_app_number(direction)

                application = Application(
                    app_number=app_number,
                    direction=direction,
                    study_form=study_form,
                    status=ApplicationStatus.DRAFT.value,
                    # Данные организации в заявке (поддерживаем оба формата ключей)
                    org_full_name=_s(org_data.get("organization_full_name") or org_data.get("full_name")),
                    org_short_name=_s(org_data.get("organization_short_name") or org_data.get("short_name")),
                    inn=cls.clean_digits(org_data.get("inn")),
                    kpp=cls.clean_digits(org_data.get("kpp")),
                    ogrn=cls.clean_digits(org_data.get("ogrn")),
                    bank_name=_s(org_data.get("bank_name")),
                    bik=cls.clean_digits(org_data.get("bik")),
                    account_number=cls.clean_digits(org_data.get("rasch_schot") or org_data.get("account_number")),
                    boss_lastname=_s(org_data.get("boss_lastname")),
                    boss_firstname=_s(org_data.get("boss_firstname")),
                    boss_patronymic=_s(org_data.get("boss_patronymic")) or None,
                    boss_position=_s(org_data.get("doljnost_boss") or org_data.get("boss_position")),
                    boss_authority=_s(org_data.get("polnamochia_boss") or org_data.get("boss_authority")),
                    legal_address=_s(org_data.get("yur_address") or org_data.get("legal_address")),
                    actual_address=_s(org_data.get("fakt_address") or org_data.get("actual_address")),
                    phone=_s(org_data.get("telephone") or org_data.get("phone")),
                    email=_s(org_data.get("email")),
                    executor_fio=_s(org_data.get("fio_executor") or org_data.get("executor_fio")),
                    executor_position=_s(org_data.get("doljnost_executor") or org_data.get("executor_position")),
                    executor_phone=_s(org_data.get("telephone_executor") or org_data.get("executor_phone")),
                    executor_email=_s(org_data.get("executor_email") or org_data.get("email")),
                    last_edited_by=None
                )
                db.session.add(application)
                db.session.flush()

                # Слушатели и их курсы
                cls._save_application_listeners(application, students_data)

                db.session.commit()
                return application
            except Exception as e:
                db.session.rollback()
                if "app_number" in str(e) and attempt < max_retries - 1:
                    continue
                raise

    @classmethod
    def update_application_draft(
        cls,
        token: str,
        org_data: Dict[str, Any],
        students_data: List[Dict[str, Any]]
    ) -> Application:
        """
        Обновляет существующий черновик заявки (организацию, слушателей, курсы),
        сохраняя тот же номер заявки и секретный токен.
        Ставит отметку о редактировании пользователем и обновляет timestamp.
        """
        application = Application.query.filter_by(secret_token=token).first()
        if not application:
            raise ValueError("Заявка с указанным токеном не найдена.")

        try:
            _s = cls._s
            # Обновляем организацию прямо в заявке
            application.org_full_name = _s(org_data.get("organization_full_name") or org_data.get("full_name"))
            application.org_short_name = _s(org_data.get("organization_short_name") or org_data.get("short_name"))
            application.inn = cls.clean_digits(org_data.get("inn"))
            application.kpp = cls.clean_digits(org_data.get("kpp"))
            application.ogrn = cls.clean_digits(org_data.get("ogrn"))
            application.bank_name = _s(org_data.get("bank_name"))
            application.bik = cls.clean_digits(org_data.get("bik"))
            application.account_number = cls.clean_digits(org_data.get("rasch_schot") or org_data.get("account_number"))
            application.boss_lastname = _s(org_data.get("boss_lastname"))
            application.boss_firstname = _s(org_data.get("boss_firstname"))
            application.boss_patronymic = _s(org_data.get("boss_patronymic")) or None
            application.boss_position = _s(org_data.get("doljnost_boss") or org_data.get("boss_position"))
            application.boss_authority = _s(org_data.get("polnamochia_boss") or org_data.get("boss_authority"))
            application.legal_address = _s(org_data.get("yur_address") or org_data.get("legal_address"))
            application.actual_address = _s(org_data.get("fakt_address") or org_data.get("actual_address"))
            application.phone = _s(org_data.get("telephone") or org_data.get("phone"))
            application.email = _s(org_data.get("email"))
            application.executor_fio = _s(org_data.get("fio_executor") or org_data.get("executor_fio"))
            application.executor_position = _s(org_data.get("doljnost_executor") or org_data.get("executor_position"))
            application.executor_phone = _s(org_data.get("telephone_executor") or org_data.get("executor_phone"))
            application.executor_email = _s(org_data.get("executor_email") or org_data.get("email"))
            application.last_edited_by = "пользователь"
            application.updated_at = datetime.now(timezone.utc)

            # Если заявка была подана со сканом или отправлена на доработку,
            # изменение данных требует повторного подписания и нового скана
            if application.status in (ApplicationStatus.SUBMITTED.value, ApplicationStatus.NEEDS_CORRECTION.value):
                application.status = ApplicationStatus.DRAFT.value
                application.signed_scan_filename = None
                application.signed_scan_path = None
                application.submitted_at = None

            # Удаляем старых слушателей (курсы удалятся каскадно)
            for old_listener in list(application.listeners):
                db.session.delete(old_listener)
            db.session.flush()

            # Добавляем обновленный список слушателей и их курсов
            cls._save_application_listeners(application, students_data)

            db.session.commit()
            return application
        except Exception:
            db.session.rollback()
            raise

    @classmethod
    def get_application_form_data(cls, application: Application) -> Dict[str, Any]:
        """Формирует словарь начальных данных для предзаполнения формы редактирования."""
        students = []
        for l in application.listeners:
            p = l.person
            categories = []
            for c in l.courses:
                categories.append({
                    "category": c.program.code if c.program else "",
                    "start_date": c.start_date,
                    "end_date": c.end_date,
                })
            if not categories:
                categories.append({"category": "", "start_date": None, "end_date": None})

            students.append({
                "student_lastname": p.lastname,
                "student_firstname": p.firstname,
                "student_patronymic": p.patronymic or "",
                "student_birthdate": p.birthdate,
                "citizenship": p.citizenship,
                "student_position": l.position,
                "education": p.education_level,
                "institute_name": p.institute_name,
                "diploma_seriesnumber": p.diploma_series_number,
                "diploma_date": p.diploma_date,
                "diploma_lastname": p.diploma_lastname,
                "snils": p.formatted_snils,
                "student_telephone": p.phone,
                "student_email": p.email,
                "diploma_delivery": l.diploma_delivery,
                "delivery_address": l.delivery_address or "",
                "fire_safety_document_type": p.fire_safety_document_type or "",
                "fire_institution": p.fire_institution or "",
                "fire_series": p.fire_series or "",
                "fire_number": p.fire_number or "",
                "fire_date": p.fire_date or "",
                "student_categories": categories,
            })

        return {
            "organization_full_name": application.org_full_name,
            "organization_short_name": application.org_short_name,
            "inn": application.inn,
            "kpp": application.kpp or "",
            "ogrn": application.ogrn,
            "bank_name": application.bank_name,
            "bik": application.bik,
            "rasch_schot": application.account_number,
            "boss_lastname": application.boss_lastname,
            "boss_firstname": application.boss_firstname,
            "boss_patronymic": application.boss_patronymic or "",
            "doljnost_boss": application.boss_position,
            "polnamochia_boss": application.boss_authority,
            "yur_address": application.legal_address,
            "fakt_address": application.actual_address,
            "telephone": application.phone,
            "email": application.email,
            "fio_executor": application.executor_fio,
            "doljnost_executor": application.executor_position,
            "telephone_executor": application.executor_phone,
            "students": students,
        }

    @classmethod
    def attach_signed_scan(cls, token: str, file_storage, upload_folder: str) -> Application:
        """
        Сохраняет скан подписанной заявки, прикрепляет его к Application
        и переводит заявку в статус SUBMITTED.
        Безопасно сохраняет кириллическое имя файла для отображения и создает ASCII-имя на диске.
        """
        application = Application.query.filter_by(secret_token=token).first()
        if not application:
            raise ValueError("Заявка с указанным токеном не найдена.")

        if not file_storage or not file_storage.filename:
            raise ValueError("Файл не выбран.")

        raw_filename = file_storage.filename or ""
        ext = raw_filename.rsplit(".", 1)[-1].lower() if "." in raw_filename else ""
        allowed = {"pdf", "jpg", "jpeg", "png", "tif", "tiff"}
        if ext not in allowed:
            raise ValueError(f"Недопустимый формат файла (.{ext}). Разрешены только: {', '.join(allowed)}")

        # Очистка имени от path traversal и спецсимволов с сохранением русских букв
        clean_name = os.path.basename(raw_filename).replace("\x00", "").strip()
        clean_name = re.sub(r'[\\/:*?"<>|]', "", clean_name).strip()
        if not clean_name:
            clean_name = f"scan.{ext}"

        os.makedirs(upload_folder, exist_ok=True)

        # ASCII-безопасное уникальное имя для сохранения на диске
        safe_num = re.sub(r"[^a-zA-Z0-9_\-]", "_", application.app_number).strip("_")
        unique_name = f"{safe_num}_{uuid.uuid4().hex[:8]}.{ext}"
        target_path = os.path.join(upload_folder, unique_name)

        file_storage.save(target_path)
        file_size = os.path.getsize(target_path) if os.path.exists(target_path) else 0

        # Обновляем заявку
        application.signed_scan_filename = clean_name
        application.signed_scan_path = target_path
        application.status = ApplicationStatus.SUBMITTED.value
        application.submitted_at = datetime.now(timezone.utc)

        attachment = ApplicationAttachment(
            application=application,
            file_type="signed_scan",
            original_filename=clean_name,
            stored_filename=unique_name,
            file_path=target_path,
            file_size=file_size
        )
        db.session.add(attachment)
        db.session.commit()

        return application
