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

        if not org:
            org = Organization(
                full_name=org_data.get("organization_full_name", "").strip(),
                short_name=org_data.get("organization_short_name", "").strip(),
                inn=inn,
                kpp=cls.clean_digits(org_data.get("kpp")),
                ogrn=ogrn,
                bank_name=org_data.get("bank_name", "").strip(),
                bik=cls.clean_digits(org_data.get("bik")),
                account_number=cls.clean_digits(org_data.get("rasch_schot", "")),
                boss_lastname=org_data.get("boss_lastname", "").strip(),
                boss_firstname=org_data.get("boss_firstname", "").strip(),
                boss_patronymic=org_data.get("boss_patronymic", "").strip() or None,
                boss_position=org_data.get("doljnost_boss", "").strip(),
                boss_authority=org_data.get("polnamochia_boss", "").strip(),
                legal_address=org_data.get("yur_address", "").strip(),
                actual_address=org_data.get("fakt_address", "").strip(),
                phone=org_data.get("telephone", "").strip(),
                email=org_data.get("email", "").strip(),
                executor_fio=org_data.get("fio_executor", "").strip(),
                executor_position=org_data.get("doljnost_executor", "").strip(),
                executor_phone=org_data.get("telephone_executor", "").strip(),
                executor_email=org_data.get("email", "").strip()
            )
            db.session.add(org)
        else:
            # Обновляем реквизиты и контактные данные
            org.full_name = org_data.get("organization_full_name", "").strip() or org.full_name
            org.short_name = org_data.get("organization_short_name", "").strip() or org.short_name
            org.bank_name = org_data.get("bank_name", "").strip() or org.bank_name
            org.bik = cls.clean_digits(org_data.get("bik")) or org.bik
            org.account_number = cls.clean_digits(org_data.get("rasch_schot", "")) or org.account_number
            org.boss_position = org_data.get("doljnost_boss", "").strip() or org.boss_position
            org.boss_authority = org_data.get("polnamochia_boss", "").strip() or org.boss_authority
            org.actual_address = org_data.get("fakt_address", "").strip() or org.actual_address
            org.phone = org_data.get("telephone", "").strip() or org.phone
            org.email = org_data.get("email", "").strip() or org.email
            org.executor_fio = org_data.get("fio_executor", "").strip() or org.executor_fio
            org.executor_position = org_data.get("doljnost_executor", "").strip() or org.executor_position
            org.executor_phone = org_data.get("telephone_executor", "").strip() or org.executor_phone

        db.session.flush()
        return org

    @classmethod
    def save_or_update_person(cls, student_data: Dict[str, Any]) -> Person:
        """Находит гражданина по СНИЛС или создает нового."""
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

        if not person:
            person = Person(
                snils=clean_snils,
                lastname=student_data.get("student_lastname", "").strip(),
                firstname=student_data.get("student_firstname", "").strip(),
                patronymic=student_data.get("student_patronymic", "").strip() or None,
                birthdate=birthdate,
                citizenship=student_data.get("citizenship", "РФ").strip(),
                phone=student_data.get("student_telephone", "").strip(),
                email=student_data.get("student_email", "").strip(),
                education_level=student_data.get("education", "").strip(),
                institute_name=student_data.get("institute_name", "").strip(),
                diploma_series_number=student_data.get("diploma_seriesnumber", "").strip(),
                diploma_date=str(student_data.get("diploma_date", "")).strip(),
                diploma_lastname=student_data.get("diploma_lastname", "").strip()
            )
            db.session.add(person)
        else:
            # Обновляем контактные данные и образование
            person.lastname = student_data.get("student_lastname", "").strip() or person.lastname
            person.firstname = student_data.get("student_firstname", "").strip() or person.firstname
            person.patronymic = student_data.get("student_patronymic", "").strip() or person.patronymic
            person.phone = student_data.get("student_telephone", "").strip() or person.phone
            person.email = student_data.get("student_email", "").strip() or person.email
            person.education_level = student_data.get("education", "").strip() or person.education_level
            person.institute_name = student_data.get("institute_name", "").strip() or person.institute_name
            person.diploma_series_number = student_data.get("diploma_seriesnumber", "").strip() or person.diploma_series_number
            person.diploma_date = str(student_data.get("diploma_date", "")).strip() or person.diploma_date
            person.diploma_lastname = student_data.get("diploma_lastname", "").strip() or person.diploma_lastname

        db.session.flush()
        return person

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
            for s_data in students_data:
                person = cls.save_or_update_person(s_data)

                listener = ApplicationListener(
                    application=application,
                    person=person,
                    position=s_data.get("student_position", "").strip(),
                    diploma_delivery=s_data.get("diploma_delivery", "personal"),
                    delivery_address=s_data.get("delivery_address", "").strip() or None
                )
                db.session.add(listener)
                db.session.flush()

                # Категории / программы этого слушателя
                categories = s_data.get("student_categories", [])
                for cat_item in categories:
                    cat_code = cat_item.get("category")
                    if not cat_code:
                        continue

                    # Находим программу по коду
                    prog = Program.query.filter_by(code=cat_code).first()
                    if not prog:
                        # Если программа еще не в базе, берем первую подходящую или создаем
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

            db.session.commit()
            return application
        except Exception:
            db.session.rollback()
            raise

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
