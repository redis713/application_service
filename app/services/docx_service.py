import io
import os
from typing import Dict, Any, List
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
        boss_display = f"{boss_fio}, {boss_pos}, действующий(ая) на основании: {boss_auth}".strip(", ")

        # Реквизиты
        ogrn = org_data.get("ogrn", "")
        inn = org_data.get("inn", "")
        kpp = org_data.get("kpp", "")
        bank_name = org_data.get("bank_name", "")
        rs = org_data.get("account_number") or org_data.get("rasch_schot", "")
        bik = org_data.get("bik", "")

        requisites_block = (
            f"ОГРН: {ogrn}\n"
            f"ИНН: {inn}\n"
            f"КПП: {kpp}\n"
            f"Банк: {bank_name}\n"
            f"р/с: {rs}\n"
            f"БИК: {bik}"
        )

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

            edu_cell = (
                f"{edu_level}\n\n"
                f"{institute} {diploma_num}, {diploma_date}\n\n"
                f"Фамилия в дипломе: {diploma_lastname}\n\n"
                f"СНИЛС: {snils}"
            )

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
                "pb_education": item.get("pb_education", "") or "-",
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
        templates_dir: str = "docx_templates"
    ) -> io.BytesIO:
        """
        Генерирует готовый файл .docx в памяти (io.BytesIO) на основе формы и направления обучения.
        """
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
