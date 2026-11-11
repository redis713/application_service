import io
import os
import sys
from datetime import date

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.models import Application, Program
from app.constants import ApplicationStatus, StudyForm, TrainingDirection
from app.services.application_service import ApplicationService
from app.services.docx_service import DocxService

app = create_app()
app.config["WTF_CSRF_ENABLED"] = False
client = app.test_client()

print("=" * 70)
print("ТЕСТИРОВАНИЕ НОВЫХ ТРЕБОВАНИЙ ДОГОВОРНОГО ОТДЕЛА")
print("=" * 70)

# -------------------------------------------------------------
# ТЕСТ 1: Сокращенное наименование организации необязательное
# -------------------------------------------------------------
print("\n1. Проверка: Сокращенное название организации необязательно:")

data_no_short_name = {
    "organization_full_name": "Акционерное общество «Байкал Энерго Сервис»",
    "organization_short_name": "",  # Пустое сокращенное наименование
    "inn": "3808111222",
    "kpp": "380801001",
    "ogrn": "1023801112223",
    "bank_name": "ПАО Сбербанк",
    "bik": "042520607",
    "rasch_schot": "40702810999990000001",
    "boss_lastname": "Иванов",
    "boss_firstname": "Иван",
    "boss_patronymic": "Иванович",
    "doljnost_boss": "Генеральный директор",
    "polnamochia_boss": "Устава",
    "yur_address": "г. Иркутск, ул. Ленина, д. 1",
    "fakt_address": "г. Иркутск, ул. Ленина, д. 1",
    "telephone": "+7 (3952) 11-22-33",
    "email": "info@baikal-energo.ru",
    "fio_executor": "Петров П.П.",
    "doljnost_executor": "Специалист по кадрам",
    "telephone_executor": "+7 (3952) 44-55-66",
    "students-0-student_lastname": "Сидоров",
    "students-0-student_firstname": "Сидор",
    "students-0-student_patronymic": "Сидорович",
    "students-0-student_birthdate": "1985-05-15",
    "students-0-citizenship": "РФ",
    "students-0-student_position": "Энергетик",
    "students-0-education": "Высшее образование",
    "students-0-institute_name": "ИРНИТУ",
    "students-0-diploma_seriesnumber": "103804 778899",
    "students-0-diploma_date": "2010-06-20",
    "students-0-diploma_lastname": "Сидоров",
    "students-0-snils": "111-222-333 99",
    "students-0-student_telephone": "+7 (914) 111-22-33",
    "students-0-student_email": "sidorov@baikal-energo.ru",
    "students-0-diploma_delivery": "personal",
    "students-0-delivery_address": "",
    "students-0-student_categories-0-category": "fulltime_cat1",
    "students-0-student_categories-0-start_date": "2026-11-20",
    "students-0-student_categories-0-end_date": "2026-11-30",
}

res_post = client.post("/apply/distant/gochs", data=data_no_short_name, follow_redirects=False)
assert res_post.status_code == 302, f"Ожидался редирект 302, получен {res_post.status_code}"
assert "/apply/status/" in res_post.headers["Location"]
token_no_short = res_post.headers["Location"].split("/apply/status/")[1].split("?")[0]

with app.app_context():
    app1 = Application.query.filter_by(secret_token=token_no_short).first()
    assert app1 is not None
    assert app1.org_short_name is None or app1.org_short_name == ""
    assert app1.short_name == "Акционерное общество «Байкал Энерго Сервис»"
    print("   [OK] Заявка успешно создана без краткого наименования!")
    print(f"   [OK] Свойство short_name корректно вернуло полное наименование: {app1.short_name}")

    # Проверка генерации Word для заявки без краткого наименования
    templates_dir = app.config["DOCX_TEMPLATES_FOLDER"]
    stream, filename = DocxService.generate_docx_for_application(app1, templates_dir)
    assert stream.getvalue()
    print("   [OK] Генерация .docx документа прошла успешно (размер:", len(stream.getvalue()), "байт)")


# -------------------------------------------------------------
# ТЕСТ 2: Проверка почтового индекса при доставке почтой
# -------------------------------------------------------------
print("\n2. Проверка: Валидация почтового индекса при доставке почтой:")

# 2.1 Попытка отправить без индекса
data_mail_no_index = dict(data_no_short_name)
data_mail_no_index["students-0-snils"] = "222-333-444 01"
data_mail_no_index["students-0-diploma_delivery"] = "mail"
data_mail_no_index["students-0-delivery_address"] = "г. Иркутск, ул. Советская, д. 25, кв. 10"  # Нет 6 цифр индекса

res_invalid_mail = client.post("/apply/distant/gochs", data=data_mail_no_index, follow_redirects=True)
assert res_invalid_mail.status_code == 200
html_invalid = res_invalid_mail.get_data(as_text=True)
assert "почтовый индекс" in html_invalid
print("   [OK] Адрес без 6-значного индекса успешно отклонен валидатором!")

# 2.2 Отправка с корректным 6-значным индексом
data_mail_valid = dict(data_no_short_name)
data_mail_valid["students-0-snils"] = "222-333-444 02"
data_mail_valid["students-0-diploma_delivery"] = "mail"
data_mail_valid["students-0-delivery_address"] = "664003, г. Иркутск, ул. Советская, д. 25, кв. 10"  # Есть 664003

res_valid_mail = client.post("/apply/distant/gochs", data=data_mail_valid, follow_redirects=False)
assert res_valid_mail.status_code == 302
print("   [OK] Адрес с 6-значным индексом '664003' успешно принят!")


# -------------------------------------------------------------
# ТЕСТ 3: Очно-заочная форма для программы "Специалист по пожарной профилактике (250 часов)"
# -------------------------------------------------------------
print("\n3. Проверка: Программа переподготовки 250ч в очно-заочной форме НЕ требует пожарного образования:")

data_fire_specialist_250 = dict(data_no_short_name)
data_fire_specialist_250["students-0-snils"] = "333-444-555 03"
data_fire_specialist_250["fixed_category_code"] = "fulltime_fire_cat31"
data_fire_specialist_250["students-0-student_categories-0-category"] = "fulltime_fire_cat31"
# Не заполняем поля пожарного образования (fire_safety_document_type и т.д.)

res_fire_250 = client.post(
    "/apply/ochno/fire?category=fulltime_fire_cat31",
    data=data_fire_specialist_250,
    follow_redirects=False
)
assert res_fire_250.status_code == 302, f"Ожидался редирект 302, получен {res_fire_250.status_code}"
token_fire_250 = res_fire_250.headers["Location"].split("/apply/status/")[1].split("?")[0]

with app.app_context():
    app_f250 = Application.query.filter_by(secret_token=token_fire_250).first()
    assert app_f250 is not None
    assert app_f250.direction == "fire"
    assert app_f250.study_form == "ochno"
    stream_f250, filename_f250 = DocxService.generate_docx_for_application(app_f250, app.config["DOCX_TEMPLATES_FOLDER"])
    assert stream_f250.getvalue()
    # Проверяем, что в документе использован шаблон pb-ochno-250.docx (в нем 8 колонок в таблице слушателей, без пожарного образования)
    import docx
    rendered_doc = docx.Document(stream_f250)
    assert len(rendered_doc.tables[0].rows[0].cells) == 8, "Таблица должна содержать ровно 8 колонок (без пожарного образования)"
    print("   [OK] Заявка на 'Специалист по пожарной профилактике (250 часов)' создана БЕЗ пожарного образования!")
    print(f"   [OK] Использован новый шаблон pb-ochno-250.docx: таблица содержит 8 колонок вместо 9 ({len(stream_f250.getvalue())} байт)")

# 3.2 Проверяем, что для ДРУГОЙ программы ПБ (напр. fulltime_fire_cat27) пожарное образование по-прежнему ТРЕБУЕТСЯ:
data_fire_other = dict(data_no_short_name)
data_fire_other["students-0-snils"] = "333-444-555 04"
data_fire_other["fixed_category_code"] = "fulltime_fire_cat27"
data_fire_other["students-0-student_categories-0-category"] = "fulltime_fire_cat27"

res_fire_other_invalid = client.post(
    "/apply/ochno/fire?category=fulltime_fire_cat27",
    data=data_fire_other,
    follow_redirects=True
)
assert res_fire_other_invalid.status_code == 200
html_other = res_fire_other_invalid.get_data(as_text=True)
assert "Выберите основание пожарного образования" in html_other
print("   [OK] Для других программ ПБ (30ч) проверка пожарного образования по-прежнему строго работает!")


# -------------------------------------------------------------
# ТЕСТ 4: Новый бизнес-процесс работы с заявками
# -------------------------------------------------------------
print("\n4. Проверка: Новый порядок работы с заявками:")

# 4.1. После подачи заявки создается заявка со статусом 'in_review'
with app.app_context():
    app_flow = Application.query.filter_by(secret_token=token_no_short).first()
    assert app_flow.status == ApplicationStatus.IN_REVIEW.value
    print(f"   [OK] Начальный статус заявки: '{app_flow.status_label}' (in_review)")

# 4.2. На странице статуса отображается сообщение об ожидании рассмотрения и ссылка-токен для копирования
res_status_page = client.get(f"/apply/status/{token_no_short}")
assert res_status_page.status_code == 200
html_status = res_status_page.get_data(as_text=True)
assert "ожидает рассмотрения договорным отделом" in html_status
assert "Ваша персональная ссылка на заявку" in html_status
assert token_no_short in html_status
assert "Скопировать ссылку" in html_status
assert "Форма загрузки скана станет активна сразу после того, как договорной отдел проверит и одобрит" in html_status
print("   [OK] На странице заявителя отображается сообщение о рассмотрении и блок ссылки-токена")

# 4.3. Попытка загрузить скан до одобрения блокируется
fake_pdf = io.BytesIO(b"%PDF-1.4 unauthorized scan")
res_premature_scan = client.post(
    f"/apply/status/{token_no_short}",
    data={"scan_file": (fake_pdf, "scan.pdf")},
    follow_redirects=True
)
assert res_premature_scan.status_code == 200
assert "Прикрепление скан-копии станет доступно после того, как договорной отдел проверит и одобрит" in res_premature_scan.get_data(as_text=True)
print("   [OK] Загрузка скана до одобрения договорным отделом заблокирована!")

# 4.4. Договорной отдел: отправка на доработку с замечаниями
app_id = app_flow.id
res_return = client.post(
    f"/applications/{app_id}/return_for_correction",
    data={"comment": "Неверно указан КПП. Проверьте дату выдачи диплома слушателя Сидорова."},
    headers={"Host": "contractmaker.umcgochs.local"},
    follow_redirects=True
)
assert res_return.status_code == 200

with app.app_context():
    app_flow = Application.query.get(app_id)
    assert app_flow.status == ApplicationStatus.NEEDS_CORRECTION.value
    assert "Неверно указан КПП" in app_flow.review_comment
    print("   [OK] Договорной отдел перевел заявку в статус 'correction' с замечаниями:", app_flow.review_comment)

# 4.5. Заявитель видит статус возврата и замечания на уникальной странице
res_status_corr = client.get(f"/apply/status/{token_no_short}")
html_corr = res_status_corr.get_data(as_text=True)
assert "возвращена договорным отделом на доработку" in html_corr
assert "Неверно указан КПП" in html_corr
assert "Редактировать заявку и устранить замечания" in html_corr
print("   [OK] Заявитель видит замечания договорного отдела на персональной странице")

# 4.6. Заявитель исправляет данные на /apply/edit/<token>
edit_data = dict(data_no_short_name)
edit_data["kpp"] = "380801002"  # Исправили КПП
res_edit_post = client.post(
    f"/apply/edit/{token_no_short}",
    data=edit_data,
    follow_redirects=True
)
assert res_edit_post.status_code == 200

with app.app_context():
    app_flow = Application.query.get(app_id)
    assert app_flow.kpp == "380801002"
    assert app_flow.status == ApplicationStatus.IN_REVIEW.value
    assert app_flow.review_comment is None
    print("   [OK] Заявитель отредактировал заявку, статус сбросился обратно в 'in_review'")

# 4.7. Договорной отдел одобряет исправленную заявку
res_approve = client.post(
    f"/applications/{app_id}/approve",
    headers={"Host": "contractmaker.umcgochs.local"},
    follow_redirects=True
)
assert res_approve.status_code == 200

with app.app_context():
    app_flow = Application.query.get(app_id)
    assert app_flow.status == ApplicationStatus.APPROVED.value
    print("   [OK] Договорной отдел одобрил заявку (статус: 'approved')")

# 4.8. На уникальной странице заявитель видит одобрение и активную форму загрузки скана
res_status_approved = client.get(f"/apply/status/{token_no_short}")
html_approved = res_status_approved.get_data(as_text=True)
assert "Заявка успешно одобрена договорным отделом!" in html_approved
assert "Шаг 3. Прикрепление скан-копии с печатью" in html_approved
assert "Отправить подписанную заявку в УМЦ" in html_approved
print("   [OK] На странице заявителя отображается подтверждение одобрения и форма прикрепления скана")

# 4.9. Заявитель загружает подписанный скан
approved_pdf = io.BytesIO(b"%PDF-1.4 official approved scan")
res_upload_scan = client.post(
    f"/apply/status/{token_no_short}",
    data={"scan_file": (approved_pdf, "signed_app_stamped.pdf")},
    follow_redirects=True
)
assert res_upload_scan.status_code == 200

with app.app_context():
    app_flow = Application.query.get(app_id)
    assert app_flow.status == ApplicationStatus.SUBMITTED.value
    assert app_flow.signed_scan_filename == "signed_app_stamped.pdf"
    assert os.path.exists(app_flow.signed_scan_path)
    print("   [OK] Скан успешно загружен, заявка переведена в 'submitted'!")

# 4.10. Проверка отсутствия отдельной success страницы и единой ссылки status:
res_old_success = client.get(f"/apply/success/{token_no_short}", follow_redirects=False)
assert res_old_success.status_code == 302
assert f"/apply/status/{token_no_short}" in res_old_success.headers["Location"]

res_final_status = client.get(f"/apply/status/{token_no_short}")
assert res_final_status.status_code == 200
html_final = res_final_status.get_data(as_text=True)
assert "Скан заявления успешно прикреплен" in html_final
assert "signed_app_stamped.pdf" in html_final
assert "Редактировать заявку" in html_final
print("   [OK] Маршрут /apply/success перенаправляет на единый /apply/status/<token>")
print("   [OK] На единой странице статуса отображается вся информация о прикрепленном скане")


# -------------------------------------------------------------
# ТЕСТ 5: Иркутское время (+8 часов)
# -------------------------------------------------------------
print("\n5. Проверка: Отображение времени в Иркутском часовом поясе (UTC+8):")

with app.app_context():
    from datetime import datetime, timezone
    utc_test_dt = datetime(2026, 11, 11, 2, 0, 0, tzinfo=timezone.utc)
    # Через Jinja filter irkutsk_time
    rendered_time = app.jinja_env.filters["irkutsk_time"](utc_test_dt)
    assert rendered_time == "11.11.2026 10:00", f"Ожидалось 11.11.2026 10:00, получено {rendered_time}"
    print(f"   [OK] UTC 02:00 успешно конвертируется в Иркутское время (+8ч): {rendered_time}")

    # Через свойство модели
    app_check = Application.query.get(app_id)
    assert app_check.created_at_local.utcoffset().total_seconds() == 8 * 3600
    print(f"   [OK] Свойство created_at_local имеет смещение +08:00: {app_check.created_at_local}")

print("\n" + "=" * 70)
print("ВСЕ ТЕСТЫ НОВЫХ ТРЕБОВАНИЙ ДОГОВОРНОГО ОТДЕЛА УСПЕШНО ПРОЙДЕНЫ!")
print("=" * 70)
