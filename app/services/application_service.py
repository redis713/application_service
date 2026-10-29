import os
import re
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from werkzeug.utils import secure_filename
from app.extensions import db
from app.constants import ApplicationStatus, StudyForm, TrainingDirection
from app.models.organization import Organization
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
    def save_or_update_organization(cls, org_data: Dict[str, Any]) -> Organization:
        """Находит существующую организацию по ИНН/ОГРН или создает новую."""
        inn = cls.clean_digits(org_data.get("inn"))
        ogrn = cls.clean_digits(org_data.get("ogrn"))

        org = Organization.query.filter(
            (Organization.inn == inn) | (Organization.ogrn == ogrn)
        ).first()

        _s = cls._s
        if not org:
            org = Organization(
                full_name=_s(org_data.get("organization_full_name")),
                short_name=_s(org_data.get("organization_short_name")),
                inn=inn,
                kpp=cls.clean_digits(org_data.get("kpp")),
                ogrn=ogrn,
                bank_name=_s(org_data.get("bank_name")),
                bik=cls.clean_digits(org_data.get("bik")),
                account_number=cls.clean_digits(org_data.get("rasch_schot")),
                boss_lastname=_s(org_data.get("boss_lastname")),
                boss_firstname=_s(org_data.get("boss_firstname")),
                boss_patronymic=_s(org_data.get("boss_patronymic")) or None,
                boss_position=_s(org_data.get("doljnost_boss")),
                boss_authority=_s(org_data.get("polnamochia_boss")),
                legal_address=_s(org_data.get("yur_address")),
                actual_address=_s(org_data.get("fakt_address")),
                phone=_s(org_data.get("telephone")),
                email=_s(org_data.get("email")),
                executor_fio=_s(org_data.get("fio_executor")),
                executor_position=_s(org_data.get("doljnost_executor")),
                executor_phone=_s(org_data.get("telephone_executor")),
                executor_email=_s(org_data.get("email"))
            )
            db.session.add(org)
        else:
            # Обновляем реквизиты и контактные данные
            org.full_name = _s(org_data.get("organization_full_name")) or org.full_name
            org.short_name = _s(org_data.get("organization_short_name")) or org.short_name
            org.bank_name = _s(org_data.get("bank_name")) or org.bank_name
            org.bik = cls.clean_digits(org_data.get("bik")) or org.bik
            org.account_number = cls.clean_digits(org_data.get("rasch_schot")) or org.account_number
            org.boss_position = _s(org_data.get("doljnost_boss")) or org.boss_position
            org.boss_authority = _s(org_data.get("polnamochia_boss")) or org.boss_authority
            org.actual_address = _s(org_data.get("fakt_address")) or org.actual_address
            org.phone = _s(org_data.get("telephone")) or org.phone
            org.email = _s(org_data.get("email")) or org.email
            org.executor_fio = _s(org_data.get("fio_executor")) or org.executor_fio
            org.executor_position = _s(org_data.get("doljnost_executor")) or org.executor_position
            org.executor_phone = _s(org_data.get("telephone_executor")) or org.executor_phone

        db.session.flush()
        return org

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

        if not person:
            person = Person(
                snils=clean_snils,
                lastname=_s(student_data.get("student_lastname")),
                firstname=_s(student_data.get("student_firstname")),
                patronymic=_s(student_data.get("student_patronymic")) or None,
                birthdate=birthdate,
                citizenship=_s(student_data.get("citizenship")) or "РФ",
                phone=_s(student_data.get("student_telephone")),
                email=_s(student_data.get("student_email")),
                education_level=_s(student_data.get("education")),
                institute_name=_s(student_data.get("institute_name")),
                diploma_series_number=_s(student_data.get("diploma_seriesnumber")) or None,
                diploma_date=diploma_date,
                diploma_lastname=_s(student_data.get("diploma_lastname")) or None,
                fire_safety_document_type=_s(student_data.get("fire_safety_document_type")) or None,
                fire_institution=_s(student_data.get("fire_institution")) or None,
                fire_series=_s(student_data.get("fire_series")) or None,
                fire_number=_s(student_data.get("fire_number")) or None,
                fire_date=_s(student_data.get("fire_date")) or None
            )
            db.session.add(person)
        else:
            # Обновляем контактные данные и образование
            person.lastname = _s(student_data.get("student_lastname")) or person.lastname
            person.firstname = _s(student_data.get("student_firstname")) or person.firstname
            person.patronymic = _s(student_data.get("student_patronymic")) or person.patronymic
            person.phone = _s(student_data.get("student_telephone")) or person.phone
            person.email = _s(student_data.get("student_email")) or person.email
            person.education_level = _s(student_data.get("education")) or person.education_level
            person.institute_name = _s(student_data.get("institute_name")) or person.institute_name
            person.diploma_series_number = _s(student_data.get("diploma_seriesnumber")) or person.diploma_series_number
            person.diploma_date = diploma_date
            person.diploma_lastname = _s(student_data.get("diploma_lastname")) or person.diploma_lastname
            if student_data.get("fire_safety_document_type"):
                person.fire_safety_document_type = _s(student_data.get("fire_safety_document_type"))
                person.fire_institution = _s(student_data.get("fire_institution")) or None
                person.fire_series = _s(student_data.get("fire_series")) or None
                person.fire_number = _s(student_data.get("fire_number")) or None
                person.fire_date = _s(student_data.get("fire_date")) or None

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
                position=_s(s_data.get("student_position")),
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

                if isinstance(start_d, str):
                    start_d = datetime.strptime(start_d, "%Y-%m-%d").date()
                if isinstance(end_d, str):
                    end_d = datetime.strptime(end_d, "%Y-%m-%d").date()

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
        Возвращает объект Application с уникальным app_number и secret_token.
        """
        try:
            # 1. Организация
            org = cls.save_or_update_organization(org_data)

            # 2. Номер заявки
            app_number = cls.generate_app_number(direction)

            application = Application(
                app_number=app_number,
                organization=org,
                direction=direction,
                study_form=study_form,
                status=ApplicationStatus.DRAFT.value
            )
            db.session.add(application)
            db.session.flush()

            # 3. Слушатели и их курсы
            cls._save_application_listeners(application, students_data)

            db.session.commit()
            return application
        except Exception:
            db.session.rollback()
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
        """
        application = Application.query.filter_by(secret_token=token).first()
        if not application:
            raise ValueError("Заявка с указанным токеном не найдена.")

        try:
            # 1. Обновляем организацию
            cls.save_or_update_organization(org_data)

            # 2. Удаляем старых слушателей (курсы удалятся каскадно)
            for old_listener in list(application.listeners):
                db.session.delete(old_listener)
            db.session.flush()

            # 3. Добавляем обновленный список слушателей и их курсов
            cls._save_application_listeners(application, students_data)

            application.updated_at = datetime.now(timezone.utc)
            db.session.commit()
            return application
        except Exception:
            db.session.rollback()
            raise

    @classmethod
    def get_application_form_data(cls, application: Application) -> Dict[str, Any]:
        """Формирует словарь начальных данных для предзаполнения формы редактирования."""
        org = application.organization
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
            "organization_full_name": org.full_name,
            "organization_short_name": org.short_name,
            "inn": org.inn,
            "kpp": org.kpp or "",
            "ogrn": org.ogrn,
            "bank_name": org.bank_name,
            "bik": org.bik,
            "rasch_schot": org.account_number,
            "boss_lastname": org.boss_lastname,
            "boss_firstname": org.boss_firstname,
            "boss_patronymic": org.boss_patronymic or "",
            "doljnost_boss": org.boss_position,
            "polnamochia_boss": org.boss_authority,
            "yur_address": org.legal_address,
            "fakt_address": org.actual_address,
            "telephone": org.phone,
            "email": org.email,
            "fio_executor": org.executor_fio,
            "doljnost_executor": org.executor_position,
            "telephone_executor": org.executor_phone,
            "students": students,
        }

    @classmethod
    def attach_signed_scan(cls, token: str, file_storage, upload_folder: str) -> Application:
        """
        Сохраняет скан подписанной заявки, прикрепляет его к Application
        и переводит заявку в статус SUBMITTED.
        """
        application = Application.query.filter_by(secret_token=token).first()
        if not application:
            raise ValueError("Заявка с указанным токеном не найдена.")

        if not file_storage or not file_storage.filename:
            raise ValueError("Файл не выбран.")

        orig_filename = secure_filename(file_storage.filename)
        ext = orig_filename.rsplit(".", 1)[-1].lower() if "." in orig_filename else ""

        os.makedirs(upload_folder, exist_ok=True)

        unique_name = f"{application.app_number}_{uuid.uuid4().hex[:8]}.{ext}"
        target_path = os.path.join(upload_folder, unique_name)

        file_storage.save(target_path)
        file_size = os.path.getsize(target_path) if os.path.exists(target_path) else 0

        # Обновляем заявку
        application.signed_scan_filename = orig_filename
        application.signed_scan_path = target_path
        application.status = ApplicationStatus.SUBMITTED.value
        application.submitted_at = datetime.now(timezone.utc)

        attachment = ApplicationAttachment(
            application=application,
            file_type="signed_scan",
            original_filename=orig_filename,
            stored_filename=unique_name,
            file_path=target_path,
            file_size=file_size
        )
        db.session.add(attachment)
        db.session.commit()

        return application
