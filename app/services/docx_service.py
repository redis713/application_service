import io
import os
from typing import Dict, Any, List, Tuple, Optional
from docxtpl import DocxTemplate
from app.constants import StudyForm, TrainingDirection, DeliveryType

class DocxService:
    @staticmethod
    def _format_date(d) -> str:
        if not d:
            return ""
        if hasattr(d, "strftime"):
            return d.strftime("%d.%m.%Y")
        return str(d)

    @classmethod
    def build_context(cls, org_data: Dict[str, Any], listeners_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Формирует универсальный словарь контекста для Jinja-шаблонов docx.
        Поддерживает переменные обоих шаблонов (дистанционного и очного).
        """
        org_full = org_data.get("full_name") or org_data.get("organization_full_name", "")
        org_short = org_data.get("short_name") or org_data.get("organization_short_name", "")
        org_display_name = f"{org_full}, {org_short}".strip(", ")

        # Руководитель
        boss_fio = " ".join(filter(None, [
            org_data.get("boss_lastname"),
            org_data.get("boss_firstname"),
            org_data.get("boss_patronymic")
        ]))
        boss_pos = org_data.get("boss_position") or org_data.get("doljnost_boss", "")
        boss_auth = org_data.get("boss_authority") or org_data.get("polnamochia_boss", "")
        if boss_auth:
            boss_display = f"{boss_fio}, {boss_pos}, действующий(ая) на основании: {boss_auth}".strip(", ")
        else:
            boss_display = f"{boss_fio}, {boss_pos}".strip(", ")

        # Реквизиты
        ogrn = org_data.get("ogrn", "")
        inn = org_data.get("inn", "")
        kpp = org_data.get("kpp", "")
        bank_name = org_data.get("bank_name", "")
        rs = org_data.get("account_number") or org_data.get("rasch_schot", "")
        bik = org_data.get("bik", "")

        req_lines = [f"ОГРН: {ogrn}", f"ИНН: {inn}"]
        if kpp:
            req_lines.append(f"КПП: {kpp}")
        req_lines.extend([
            f"Банк: {bank_name}",
            f"р/с: {rs}",
            f"БИК: {bik}"
        ])
        requisites_block = "\n".join(req_lines)

        fakt_addr = org_data.get("actual_address") or org_data.get("fakt_address", "")
        yur_addr = org_data.get("legal_address") or org_data.get("yur_address", "")
        phone = org_data.get("phone") or org_data.get("telephone", "")
        email = org_data.get("email", "")

        # Исполнитель
        exec_fio = org_data.get("executor_fio") or org_data.get("fio_executor", "")
        exec_pos = org_data.get("executor_position") or org_data.get("doljnost_executor", "")
        exec_phone = org_data.get("executor_phone") or org_data.get("telephone_executor", "")
        exec_email = org_data.get("executor_email", "")

        exec_parts = [f"{exec_pos}: {exec_fio}", f"тел: {exec_phone}"]
        if exec_email:
            exec_parts.append(f"email: {exec_email}")
        executor_block = ", ".join(exec_parts)

        # Таблица слушателей
        table_rows = []
        for index, item in enumerate(listeners_data, start=1):
            fio = " ".join(filter(None, [
                item.get("lastname") or item.get("student_lastname"),
                item.get("firstname") or item.get("student_firstname"),
                item.get("patronymic") or item.get("student_patronymic")
            ]))
            birth = cls._format_date(item.get("birthdate") or item.get("student_birthdate"))
            citizenship = item.get("citizenship", "РФ")
            name_cell = f"{fio}\n\n{birth}\n\n{citizenship}"

            edu_level = item.get("education_level") or item.get("education", "")
            institute = item.get("institute_name", "")
            diploma_num = item.get("diploma_series_number") or item.get("diploma_seriesnumber", "")
            diploma_date = cls._format_date(item.get("diploma_date"))
            diploma_lastname = item.get("diploma_lastname", "")
            snils = item.get("snils", "")

            if edu_level == "Неоконченное высшее (студент)":
                edu_cell = (
                    f"{edu_level}\n\n"
                    f"{institute}\n\n"
                    f"СНИЛС: {snils}"
                )
            else:
                edu_parts = [edu_level]
                if institute:
                    edu_parts.append(institute)
                edu_dip_parts = []
                if diploma_num:
                    edu_dip_parts.append(f"диплом: {diploma_num}")
                if diploma_date:
                    edu_dip_parts.append(f"выдан {diploma_date}")
                if edu_dip_parts:
                    edu_parts.append(", ".join(edu_dip_parts))

                # Фамилия в дипломе (при заполнении или фамилия слушателя по умолчанию)
                dip_lastname = diploma_lastname or item.get("lastname") or item.get("student_lastname") or ""
                if dip_lastname:
                    edu_parts.append(f"Фамилия в дипломе: {dip_lastname}")
                if snils:
                    edu_parts.append(f"СНИЛС: {snils}")
                edu_cell = "\n\n".join(edu_parts)

            # Формирование сведений о пожарном образовании для соответствующих бланков
            fire_doc_type = item.get("fire_safety_document_type")
            if fire_doc_type:
                from app.constants import FIRE_DOCUMENT_LABELS
                doc_title = FIRE_DOCUMENT_LABELS.get(fire_doc_type, fire_doc_type)
                fire_inst = item.get("fire_institution") or institute
                f_series = item.get("fire_series") or ""
                f_number = item.get("fire_number") or ""
                f_date = cls._format_date(item.get("fire_date"))

                parts = []
                if fire_inst:
                    parts.append(fire_inst)
                if doc_title:
                    parts.append(doc_title)

                num_parts = []
                if f_series:
                    num_parts.append(f"серия {f_series}")
                if f_number:
                    num_parts.append(f"№ {f_number}")
                if f_date:
                    num_parts.append(f"дата выдачи {f_date}")
                if num_parts:
                    parts.append(", ".join(num_parts))

                pb_edu_cell = "\n\n".join(parts) if parts else "-"
            else:
                pb_edu_cell = item.get("pb_education", "") or "-"

            position = item.get("position") or item.get("student_position", "")

            # Программы и даты
            courses = item.get("courses") or item.get("student_categories", [])
            cat_titles = []
            cat_dates = []

            for c in courses:
                cat_titles.append(c.get("title") or c.get("category_title") or c.get("category", ""))
                s_date = cls._format_date(c.get("start_date"))
                e_date = cls._format_date(c.get("end_date"))
                cat_dates.append(f"{s_date} - {e_date}")

            category_cell = "\n\n".join(cat_titles)
            date_cell = "\n\n".join(cat_dates)

            # Телефон и доставка
            tel = item.get("phone") or item.get("student_telephone", "")
            delivery_mode = item.get("diploma_delivery", "personal")
            delivery_text = DeliveryType.label(delivery_mode) if delivery_mode in DeliveryType._value2member_map_ else delivery_mode
            phone_cell = f"{tel}\n\n{delivery_text}"
            if delivery_mode == "mail":
                addr = item.get("delivery_address", "")
                if addr:
                    phone_cell += f"\nАдрес: {addr}"

            student_email = item.get("email") or item.get("student_email", "")

            table_rows.append({
                "num": index,
                "name": name_cell,
                "education": edu_cell,
                "pb_education": pb_edu_cell,
                "position": position,
                "category": category_cell,
                "date": date_cell,
                "phone": phone_cell,
                "email": student_email
            })

        # Универсальный словарь для всех 7 утвержденных шаблонов:
        context = {
            # Ключи для dist, pb, 112, antiterror, specialist:
            "organization_name": org_display_name,
            "fio_boss": boss_display,
            "boss_position": boss_pos,
            "ogrn": requisites_block,
            "fakt_address": fakt_addr,
            "yur_address": yur_addr,
            "telephone": phone,
            "email": email,
            "doljnost_executor": executor_block,
            # Ключи для gochs-ochno:
            "org_name": org_display_name,
            "director_name": boss_display,
            "org_requisites": requisites_block,
            "actual_address": fakt_addr,
            "legal_address": yur_addr,
            "org_phone": phone,
            "org_email": email,
            "executor_name": executor_block,
            # Общие:
            "people_kol": len(listeners_data),
            "data": table_rows
        }
        return context

    @classmethod
    def generate_docx_stream(
        cls,
        org_data: Dict[str, Any],
        listeners_data: List[Dict[str, Any]],
        study_form: str = "distant",
        direction: str = "gochs",
        templates_dir: str = None,
        program_code: Optional[str] = None
    ) -> io.BytesIO:
        """
        Генерирует готовый файл .docx в памяти (io.BytesIO) на основе формы и направления обучения.
        """
        if not templates_dir:
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            templates_dir = os.path.join(base_dir, "docx_templates")

        template_map = {
            (StudyForm.DISTANT.value, TrainingDirection.GOCHS.value): "gochs-dist.docx",
            (StudyForm.DISTANT.value, TrainingDirection.FIRE.value): "pb-dist.docx",
            (StudyForm.DISTANT.value, TrainingDirection.ANTITERROR.value): "antiterror.docx",
            (StudyForm.OCHNO.value, TrainingDirection.GOCHS.value): "gochs-ochno.docx",
            (StudyForm.OCHNO.value, TrainingDirection.FIRE.value): "pb-ochno.docx",
            (StudyForm.OCHNO.value, TrainingDirection.CALL112.value): "112.docx",
            (StudyForm.OCHNO.value, TrainingDirection.SPECIALIST.value): "specialist.docx",
        }
        template_name = template_map.get((study_form, direction), "gochs-dist.docx")

        # Для очно-заочной формы программы "Специалист по пожарной профилактике (250 часов)"
        # используется специализированный шаблон без колонки о пожарном образовании
        if study_form == StudyForm.OCHNO.value and direction == TrainingDirection.FIRE.value:
            is_fire_250 = False
            if program_code == "fulltime_fire_cat31":
                is_fire_250 = True
            else:
                for l in (listeners_data or []):
                    for c in l.get("courses", []):
                        c_code = c.get("code") or c.get("program_code") or ""
                        c_title = (c.get("title") or "").lower()
                        c_hours = c.get("hours") or 0
                        if c_code == "fulltime_fire_cat31" or (c_hours == 250 and "профилактик" in c_title):
                            is_fire_250 = True
                            break
                    for c in l.get("student_categories", []):
                        if c.get("category") == "fulltime_fire_cat31":
                            is_fire_250 = True
                            break
            if is_fire_250:
                template_name = "pb-ochno-250.docx"

        template_path = os.path.join(templates_dir, template_name)

        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Шаблон документа не найден: {template_path}")

        context = cls.build_context(org_data, listeners_data)

        doc = DocxTemplate(template_path)
        doc.render(context)

        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer

    @classmethod
    def generate_docx_for_application(cls, application, templates_dir: str = None) -> Tuple[io.BytesIO, str]:
        """
        Генерирует официальный .docx документ для переданной модели Application.
        Возвращает кортеж (BytesIO поток, рекомендуемое имя файла для скачивания).
        """
        org_data = {
            "full_name": application.org_full_name,
            "short_name": application.org_short_name,
            "inn": application.inn,
            "kpp": application.kpp,
            "ogrn": application.ogrn,
            "bank_name": application.bank_name,
            "bik": application.bik,
            "account_number": application.account_number,
            "boss_lastname": application.boss_lastname,
            "boss_firstname": application.boss_firstname,
            "boss_patronymic": application.boss_patronymic,
            "boss_position": application.boss_position,
            "boss_authority": application.boss_authority,
            "legal_address": application.legal_address,
            "actual_address": application.actual_address,
            "phone": application.phone,
            "email": application.email,
            "executor_fio": application.executor_fio,
            "executor_position": application.executor_position,
            "executor_phone": application.executor_phone,
            "executor_email": application.executor_email,
        }

        listeners_data = []
        for l in application.listeners:
            p = l.person
            courses = []
            for c in l.courses:
                courses.append({
                    "code": c.program.code if c.program else "",
                    "title": c.program.title if c.program else "",
                    "hours": c.program.hours if c.program else 0,
                    "start_date": c.start_date,
                    "end_date": c.end_date,
                })
            listeners_data.append({
                "lastname": p.lastname,
                "firstname": p.firstname,
                "patronymic": p.patronymic,
                "birthdate": p.birthdate,
                "citizenship": p.citizenship,
                "education_level": p.education_level,
                "institute_name": p.institute_name,
                "diploma_series_number": p.diploma_series_number,
                "diploma_date": p.diploma_date,
                "diploma_lastname": p.diploma_lastname,
                "snils": p.formatted_snils,
                "position": l.position,
                "phone": p.phone,
                "email": p.email,
                "diploma_delivery": l.diploma_delivery,
                "delivery_address": l.delivery_address or "",
                "fire_safety_document_type": p.fire_safety_document_type,
                "fire_institution": p.fire_institution,
                "fire_series": p.fire_series,
                "fire_number": p.fire_number,
                "fire_date": p.fire_date,
                "courses": courses,
            })

        program_code = None
        if application.direction == TrainingDirection.FIRE.value and application.study_form == StudyForm.OCHNO.value:
            for l in application.listeners:
                for c in l.courses:
                    if c.program and (c.program.code == "fulltime_fire_cat31" or (c.program.hours == 250 and "профилактик" in (c.program.title or "").lower())):
                        program_code = "fulltime_fire_cat31"
                        break

        stream = cls.generate_docx_stream(
            org_data=org_data,
            listeners_data=listeners_data,
            study_form=application.study_form,
            direction=application.direction,
            templates_dir=templates_dir,
            program_code=program_code
        )

        clean_org = (application.short_name or "").replace('"', '').replace("'", "").strip()
        download_filename = f"Заявка_{application.app_number}_{clean_org}.docx"
        return stream, download_filename

    @classmethod
    def get_boss_genitive_fio(cls, lastname: str, firstname: str, patronymic: str) -> str:
        """Склоняет ФИО руководителя в родительный падеж с помощью библиотеки pytrovich."""
        if not lastname and not firstname:
            return ""
        try:
            from pytrovich.detector import PetrovichGenderDetector
            from pytrovich.maker import PetrovichDeclinationMaker
            from pytrovich.enums import Case, Gender, NamePart

            detector = PetrovichGenderDetector()
            maker = PetrovichDeclinationMaker()

            gender = detector.detect(firstname=firstname, lastname=lastname, middlename=patronymic)
            if gender == Gender.ANDROGYNOUS or not gender:
                if patronymic and (patronymic.endswith("ич") or patronymic.endswith("ыч")):
                    gender = Gender.MALE
                elif patronymic and patronymic.endswith("на"):
                    gender = Gender.FEMALE
                else:
                    gender = Gender.MALE

            ln = maker.make(NamePart.LASTNAME, gender, Case.GENITIVE, lastname) if lastname else ""
            fn = maker.make(NamePart.FIRSTNAME, gender, Case.GENITIVE, firstname) if firstname else ""
            pn = maker.make(NamePart.MIDDLENAME, gender, Case.GENITIVE, patronymic) if patronymic else ""
            return " ".join(filter(None, [ln, fn, pn]))
        except Exception:
            return " ".join(filter(None, [lastname, firstname, patronymic]))

    @classmethod
    def get_boss_initials_fio(cls, lastname: str, firstname: str, patronymic: str) -> str:
        """Форматирует инициалы и фамилию руководителя, например: И.И. Иванов."""
        initials = []
        if firstname:
            initials.append(f"{firstname[0]}.")
        if patronymic:
            initials.append(f"{patronymic[0]}.")
        init_str = "".join(initials)
        if init_str:
            return f"{init_str} {lastname}".strip()
        return lastname or ""

    @classmethod
    def calculate_contract_price(cls, application) -> Tuple[int, str, str]:
        """
        Считает общую стоимость обучения по заявке исходя из всех слушателей,
        их выбранных программ и цен в базе данных (модель Program).
        Возвращает (число, строка с пробелами-разделителями, сумма прописью).
        """
        from num2words import num2words

        is_ochno = (application.study_form == StudyForm.OCHNO.value)

        total = 0
        for l in (application.listeners or []):
            for c in (l.courses or []):
                if c.program:
                    # Основной источник - цены из базы данных (модель Program)
                    price = c.program.price_ochno if is_ochno else c.program.price_dist
                    if price is None:
                        # Запасной источник из programs_seed.py на случай, если база еще не обновлена
                        from app.data.programs_seed import PROGRAMS_DATA
                        programs_by_code = {p["code"]: p for p in PROGRAMS_DATA}
                        p_data = programs_by_code.get(c.program.code)
                        if p_data:
                            price = p_data.get("price_ochno") if is_ochno else p_data.get("price_dist")
                    if price is not None:
                        total += int(price)

        formatted_num = f"{total:,}".replace(",", " ")
        try:
            words = num2words(total, lang="ru")
        except Exception:
            words = str(total)

        return total, formatted_num, words

    @classmethod
    def get_contract_template_name(cls, application) -> str:
        """
        Определяет имя файла шаблона договора в папке docx_templates/dogovor
        на основе направления, формы обучения и выбранных программ/часов.
        """
        direction = application.direction
        study_form = application.study_form

        program_code = None
        program_title = ""
        hours = 0
        is_glav_spec = False

        if application.listeners:
            for l in application.listeners:
                for c in l.courses:
                    if c.program:
                        program_code = c.program.code
                        program_title = (c.program.title or "").lower()
                        hours = c.program.hours or 0
                        if "главных специалистов" in program_title or program_code == "fulltime_fire_cat29":
                            is_glav_spec = True
                        break
                if program_code:
                    break

        # 1. Антитеррор (16ч, distant)
        if direction == TrainingDirection.ANTITERROR.value:
            return "dogovor-antiterror-16h.docx"

        # 2. Специалист ГО (250ч, ochno)
        if direction == TrainingDirection.SPECIALIST.value:
            return "dogovor-specgo-250h.docx"

        # 3. Система 112 (250ч, 76ч, 40ч)
        if direction == TrainingDirection.CALL112.value:
            if hours == 250 or program_code == "fulltime_cat32":
                return "dogovor-112-250h.docx"
            elif hours == 76 or program_code == "fulltime_cat33":
                return "dogovor-112-76h.docx"
            elif hours == 40 or program_code == "fulltime_cat34":
                return "dogovor-112-40h.docx"
            return "dogovor-112-250h.docx"

        # 4. ГОЧС (дистанционно: 72ч; очно: 36ч, 40ч, 72ч)
        if direction == TrainingDirection.GOCHS.value:
            if study_form == StudyForm.DISTANT.value:
                return "dogovor-gochs-dist-72h.docx"
            else:
                if hours == 36:
                    return "dogovor-gochs-ochno-36h.docx"
                elif hours == 40:
                    return "dogovor-gochs-ochno-40h.docx"
                elif hours == 72:
                    return "dogovor-gochs-ochno-72h.docx"
                return "dogovor-gochs-ochno-36h.docx"

        # 5. Пожарная безопасность (fire)
        if direction == TrainingDirection.FIRE.value:
            if study_form == StudyForm.DISTANT.value:
                if hours == 18 or program_code == "fulltime_fire_cat30":
                    return "dogovor-pb-dist-18h.docx"
                elif hours == 20 or program_code == "fulltime_fire_cat28":
                    return "dogovor-pb-dist-20h.docx"
                elif hours == 30:
                    if is_glav_spec:
                        return "dogovor-pb-dist-30(gs)h.docx"
                    else:
                        return "dogovor-pb-dist-30h.docx"
                return "dogovor-pb-dist-30h.docx"
            else:
                if hours == 250 or program_code == "fulltime_fire_cat31":
                    return "dogovor-pb-ochno-250h.docx"
                elif hours == 18 or program_code == "fulltime_fire_cat30":
                    return "dogovor-pb-ochno-18h.docx"
                elif hours == 20 or program_code == "fulltime_fire_cat28":
                    return "dogovor-pb-ochno-20h.docx"
                elif hours == 30:
                    if is_glav_spec:
                        return "dogovor-pb-ochno-30(gs)h.docx"
                    else:
                        return "dogovor-pb-ochno-30h.docx"
                return "dogovor-pb-ochno-30h.docx"

        return "dogovor-gochs-dist-72h.docx"

    @classmethod
    def build_contract_context(cls, application) -> Dict[str, Any]:
        """Формирует контекст для шаблона договора."""
        boss_genitive = cls.get_boss_genitive_fio(
            application.boss_lastname,
            application.boss_firstname,
            application.boss_patronymic
        )
        boss_initials = cls.get_boss_initials_fio(
            application.boss_lastname,
            application.boss_firstname,
            application.boss_patronymic
        )
        _, total_str, total_words = cls.calculate_contract_price(application)
        kpp_line = application.kpp or "-"

        table_rows = []
        for index, l in enumerate(application.listeners, start=1):
            p = l.person
            fio = p.full_name
            birth = cls._format_date(p.birthdate)
            citizenship = p.citizenship or "РФ"
            name_cell = f"{fio}\n\n{birth}\n\n{citizenship}"

            edu_level = p.education_level or ""
            institute = p.institute_name or ""
            diploma_num = p.diploma_series_number or ""
            diploma_date = cls._format_date(p.diploma_date)
            diploma_lastname = p.diploma_lastname or ""
            snils = p.formatted_snils or ""

            if edu_level == "Неоконченное высшее (студент)":
                edu_cell = f"{edu_level}\n\n{institute}\n\nСНИЛС: {snils}"
            else:
                edu_parts = [edu_level]
                if institute:
                    edu_parts.append(institute)
                edu_dip_parts = []
                if diploma_num:
                    edu_dip_parts.append(f"диплом: {diploma_num}")
                if diploma_date:
                    edu_dip_parts.append(f"выдан {diploma_date}")
                if edu_dip_parts:
                    edu_parts.append(", ".join(edu_dip_parts))
                dip_lastname = diploma_lastname or p.lastname or ""
                if dip_lastname:
                    edu_parts.append(f"Фамилия в дипломе: {dip_lastname}")
                if snils:
                    edu_parts.append(f"СНИЛС: {snils}")
                edu_cell = "\n\n".join(edu_parts)

            fire_doc_type = p.fire_safety_document_type
            if fire_doc_type:
                from app.constants import FIRE_DOCUMENT_LABELS
                doc_title = FIRE_DOCUMENT_LABELS.get(fire_doc_type, fire_doc_type)
                fire_inst = p.fire_institution or institute
                f_series = p.fire_series or ""
                f_number = p.fire_number or ""
                f_date = cls._format_date(p.fire_date)
                parts = []
                if fire_inst:
                    parts.append(fire_inst)
                if doc_title:
                    parts.append(doc_title)
                num_parts = []
                if f_series:
                    num_parts.append(f"серия {f_series}")
                if f_number:
                    num_parts.append(f"№ {f_number}")
                if f_date:
                    num_parts.append(f"дата выдачи {f_date}")
                if num_parts:
                    parts.append(", ".join(num_parts))
                pb_edu_cell = "\n\n".join(parts) if parts else "-"
            else:
                pb_edu_cell = "-"

            position = l.position or ""

            cat_titles = []
            cat_dates = []
            hours = 0
            for c in l.courses:
                if c.program:
                    cat_titles.append(c.program.title or "")
                    hours = c.program.hours or hours
                s_date = cls._format_date(c.start_date)
                e_date = cls._format_date(c.end_date)
                cat_dates.append(f"с {s_date} по {e_date} г.")

            category_cell = "\n\n".join(cat_titles)
            date_cell = "\n\n".join(cat_dates)

            table_rows.append({
                "num": index,
                "name": name_cell,
                "fio": fio,
                "education": edu_cell,
                "pb_education": pb_edu_cell,
                "position": position,
                "category": category_cell,
                "date": date_cell,
                "hours": hours,
                "phone": p.phone or "",
                "email": p.email or "",
            })

        context = {
            "organization_name": application.org_full_name,
            "org_name": application.org_full_name,
            "boss_fio_genitive": boss_genitive,
            "boss_authority": application.boss_authority or "",
            "people_kol": len(application.listeners),
            "total_price": total_str,
            "total_price_words": total_words,
            "actual_address": application.actual_address,
            "legal_address": application.legal_address,
            "inn": application.inn,
            "kpp": application.kpp or "-",
            "kpp_line": kpp_line,
            "bank_name": application.bank_name,
            "account_number": application.account_number,
            "bik": application.bik,
            "ogrn": application.ogrn,
            "phone": application.phone,
            "email": application.email,
            "boss_position": application.boss_position or "",
            "boss_fio_initials": boss_initials,
            "data": table_rows
        }
        return context

    @classmethod
    def generate_contract_for_application(cls, application, templates_dir: str = None) -> Tuple[io.BytesIO, str]:
        """
        Генерирует договор на оказание платных образовательных услуг (.docx)
        для переданной модели Application.
        Возвращает кортеж (BytesIO поток, рекомендуемое имя файла для скачивания).
        """
        if not templates_dir:
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            templates_dir = os.path.join(base_dir, "docx_templates")

        template_name = cls.get_contract_template_name(application)
        dogovor_dir = os.path.join(templates_dir, "dogovor")
        template_path = os.path.join(dogovor_dir, template_name)

        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Шаблон договора не найден: {template_path}")

        context = cls.build_contract_context(application)

        doc = DocxTemplate(template_path)
        doc.render(context)

        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)

        clean_org = (application.short_name or "").replace('"', '').replace("'", "").strip()
        download_filename = f"Договор_{application.app_number}_{clean_org}.docx"
        return buffer, download_filename
