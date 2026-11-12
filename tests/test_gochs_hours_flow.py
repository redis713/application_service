import os
import sys
import io
import docx

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.extensions import db
from app.models.program import Program
from app.models.application import Application
from app.constants import TrainingDirection, StudyForm, ApplicationStatus
from app.services.docx_service import DocxService
from app.data.programs_seed import seed_programs

app = create_app()
app.config["WTF_CSRF_ENABLED"] = False
client = app.test_client()

print("=" * 70)
print("ТЕСТИРОВАНИЕ ГРУППИРОВКИ ПРОГРАММ ГОЧС (ОЧНО-ЗАОЧНО) ПО ЧАСАМ")
print("=" * 70)

with app.app_context():
    seed_programs()

# -------------------------------------------------------------
# ТЕСТ 1: Страница /ochno и переход к /apply/programs/ochno/gochs
# -------------------------------------------------------------
print("\n1. Проверка: Раздел /ochno и ссылка на ГОЧС:")
res_ochno = client.get("/ochno")
assert res_ochno.status_code == 200
html_ochno = res_ochno.get_data(as_text=True)
assert "/apply/programs/ochno/gochs" in html_ochno
print("   [OK] В разделе /ochno присутствует ссылка на /apply/programs/ochno/gochs")

# -------------------------------------------------------------
# ТЕСТ 2: Страница выбора расчасовки ГОЧС
# -------------------------------------------------------------
print("\n2. Проверка: Страница выбора расчасовки ГОЧС (/apply/programs/ochno/gochs):")
res_hours = client.get("/apply/programs/ochno/gochs")
assert res_hours.status_code == 200
html_hours = res_hours.get_data(as_text=True)

# Проверяем наличие разделов по часам: 36, 40, 72
assert "36 часов" in html_hours
assert "40 часов" in html_hours
assert "72 часа" in html_hours
assert "/apply/ochno/gochs?hours=36" in html_hours
assert "/apply/ochno/gochs?hours=40" in html_hours
assert "/apply/ochno/gochs?hours=72" in html_hours
assert "14 программ" in html_hours
assert "2 программы" in html_hours
assert "10 программ" in html_hours
print("   [OK] На странице присутствуют все три раздела: 36, 40 и 72 часа!")
print("   [OK] Ссылки ведут в форму с соответствующим параметром hours.")

# -------------------------------------------------------------
# ТЕСТ 3: Переход в форму без указания часов -> редирект
# -------------------------------------------------------------
print("\n3. Проверка: Защита формы очно-заочного ГОЧС без указания часов:")
res_no_hours = client.get("/apply/ochno/gochs", follow_redirects=False)
assert res_no_hours.status_code == 302
assert "/apply/programs/ochno/gochs" in res_no_hours.headers["Location"]
print("   [OK] GET /apply/ochno/gochs без hours редиректит на выбор расчасовки.")

# -------------------------------------------------------------
# ТЕСТ 4: Открытие формы с hours=36, 40, 72 и проверка набора программ
# -------------------------------------------------------------
print("\n4. Проверка: Открытие формы и фильтрация программ по часам:")

# 4.1 Форма для 36 часов
res_form_36 = client.get("/apply/ochno/gochs?hours=36")
assert res_form_36.status_code == 200
html_36 = res_form_36.get_data(as_text=True)
assert "36 ч." in html_36
assert 'value="fulltime_cat1"' in html_36  # Руководители ОМСУ (36 ч.)
assert 'value="fulltime_cat2"' in html_36  # Руководители организаций (36 ч.)
assert 'value="fulltime_cat3"' not in html_36  # fulltime_cat3 теперь 72 часа, её НЕ должно быть в 36!
assert 'value="fulltime_cat24"' not in html_36  # fulltime_cat24 - 40 часов, её НЕ должно быть в 36!
print("   [OK] В форме для 36 часов присутствуют только программы на 36 часов!")

# 4.2 Форма для 40 часов
res_form_40 = client.get("/apply/ochno/gochs?hours=40")
assert res_form_40.status_code == 200
html_40 = res_form_40.get_data(as_text=True)
assert "40 ч." in html_40
assert 'value="fulltime_cat24"' in html_40  # Руководители УКП (40 ч.)
assert 'value="fulltime_cat26"' in html_40  # Руководители занятий по ГОЧС (40 ч.)
assert 'value="fulltime_cat1"' not in html_40  # 36 ч.
assert 'value="fulltime_cat3"' not in html_40  # 72 ч.
print("   [OK] В форме для 40 часов присутствуют только программы на 40 часов!")

# 4.3 Форма для 72 часов
res_form_72 = client.get("/apply/ochno/gochs?hours=72")
assert res_form_72.status_code == 200
html_72 = res_form_72.get_data(as_text=True)
assert "72 ч." in html_72
assert 'value="fulltime_cat3"' in html_72  # 72 ч.
assert 'value="fulltime_cat4"' in html_72  # 72 ч.
assert 'value="fulltime_cat8"' in html_72  # 72 ч.
assert 'value="fulltime_cat1"' not in html_72  # 36 ч.
assert 'value="fulltime_cat24"' not in html_72  # 40 ч.
print("   [OK] В форме для 72 часов присутствуют только программы на 72 часа!")

# -------------------------------------------------------------
# ТЕСТ 5: Отправка заявки очно-заочного ГОЧС (36 часов) с 2 слушателями
#         (разные программы по 36 часов для каждого слушателя)
# -------------------------------------------------------------
print("\n5. Проверка: Оформление заявки на 36 часов с несколькими слушателями:")

valid_org = {
    "hours": "36",
    "organization_full_name": "ООО «Байкал Энерго Сервис»",
    "organization_short_name": "ООО «БЭС»",
    "inn": "3808123456",
    "kpp": "380801001",
    "ogrn": "1023800000000",
    "bank_name": "ПАО Сбербанк",
    "bik": "042520607",
    "rasch_schot": "40702810900000001234",
    "boss_lastname": "Иванов",
    "boss_firstname": "Иван",
    "boss_patronymic": "Иванович",
    "doljnost_boss": "Генеральный директор",
    "polnamochia_boss": "Устава",
    "yur_address": "г. Иркутск, ул. Ленина, д. 1",
    "fakt_address": "г. Иркутск, ул. Ленина, д. 1",
    "telephone": "+7 (3952) 11-22-33",
    "email": "bes@example.ru",
    "fio_executor": "Сидорова Анна Павловна",
    "doljnost_executor": "Специалист по кадрам",
    "telephone_executor": "+7 (3952) 44-55-66",

    # Слушатель 1: программа fulltime_cat1 (36 ч.)
    "students-0-student_lastname": "Смирнов",
    "students-0-student_firstname": "Алексей",
    "students-0-student_patronymic": "Петрович",
    "students-0-student_birthdate": "1985-04-12",
    "students-0-citizenship": "РФ",
    "students-0-student_position": "Руководитель ОМСУ",
    "students-0-education": "Высшее образование",
    "students-0-institute_name": "ИГУ",
    "students-0-diploma_seriesnumber": "1038 123456",
    "students-0-diploma_date": "2008-06-20",
    "students-0-diploma_lastname": "Смирнов",
    "students-0-snils": "111-222-333 44",
    "students-0-student_telephone": "+7 (914) 111-22-33",
    "students-0-student_email": "smirnov@example.ru",
    "students-0-diploma_delivery": "personal",
    "students-0-student_categories-0-category": "fulltime_cat1",
    "students-0-student_categories-0-start_date": "2026-12-01",
    "students-0-student_categories-0-end_date": "2026-12-10",

    # Слушатель 2: программа fulltime_cat2 (36 ч.)
    "students-1-student_lastname": "Кузнецов",
    "students-1-student_firstname": "Дмитрий",
    "students-1-student_patronymic": "Сергеевич",
    "students-1-student_birthdate": "1990-08-25",
    "students-1-citizenship": "РФ",
    "students-1-student_position": "Директор филиала",
    "students-1-education": "Высшее образование",
    "students-1-institute_name": "ИРНИТУ",
    "students-1-diploma_seriesnumber": "1038 654321",
    "students-1-diploma_date": "2013-06-25",
    "students-1-diploma_lastname": "Кузнецов",
    "students-1-snils": "222-333-444 55",
    "students-1-student_telephone": "+7 (914) 222-33-44",
    "students-1-student_email": "kuznetsov@example.ru",
    "students-1-diploma_delivery": "mail",
    "students-1-delivery_address": "664003, г. Иркутск, ул. Карла Маркса, д. 5",
    "students-1-student_categories-0-category": "fulltime_cat2",
    "students-1-student_categories-0-start_date": "2026-12-01",
    "students-1-student_categories-0-end_date": "2026-12-10",
}

res_submit = client.post("/apply/ochno/gochs", data=valid_org, follow_redirects=False)
assert res_submit.status_code == 302
assert "/apply/status/" in res_submit.headers["Location"]
token_created = res_submit.headers["Location"].split("/apply/status/")[-1]

with app.app_context():
    app_obj = Application.query.filter_by(secret_token=token_created).first()
    assert app_obj is not None
    assert app_obj.study_form == StudyForm.OCHNO.value
    assert app_obj.direction == TrainingDirection.GOCHS.value
    assert app_obj.status == ApplicationStatus.IN_REVIEW.value
    assert len(app_obj.listeners) == 2

    # Проверяем, что у каждого слушателя своя выбранная программа на 36 часов
    l1_course = app_obj.listeners[0].courses[0]
    l2_course = app_obj.listeners[1].courses[0]
    assert l1_course.program.code == "fulltime_cat1"
    assert l1_course.program.hours == 36
    assert l2_course.program.code == "fulltime_cat2"
    assert l2_course.program.hours == 36
    print(f"   [OK] Заявка № {app_obj.app_number} успешно сохранена со статусом 'in_review'!")
    print(f"   [OK] Слушатель 1: {l1_course.program.title} ({l1_course.program.hours} ч.)")
    print(f"   [OK] Слушатель 2: {l2_course.program.title} ({l2_course.program.hours} ч.)")

    # -------------------------------------------------------------
    # ТЕСТ 6: Генерация docx заявления
    # -------------------------------------------------------------
    print("\n6. Проверка: Генерация Word docx бланка (gochs-ochno.docx):")
    docx_stream, dl_filename = DocxService.generate_docx_for_application(app_obj)
    assert len(docx_stream.getvalue()) > 10000
    doc = docx.Document(docx_stream)
    table = doc.tables[0]
    assert len(table.rows) == 3  # заголовок + 2 слушателя
    row1_text = [c.text for c in table.rows[1].cells]
    row2_text = [c.text for c in table.rows[2].cells]
    assert "Руководители органов местного самоуправления" in row1_text[4]
    assert "Руководители организаций" in row2_text[4]
    print(f"   [OK] Word docx успешно сформирован на базе gochs-ochno.docx ({len(docx_stream.getvalue())} байт)")
    print("   [OK] В строке 1 колонка 5 содержит 'Руководители органов местного самоуправления'")
    print("   [OK] В строке 2 колонка 5 содержит 'Руководители организаций'")

# -------------------------------------------------------------
# ТЕСТ 7: Редактирование заявки (/apply/edit/<token>)
# -------------------------------------------------------------
print("\n7. Проверка: Страница редактирования заявки (/apply/edit/<token>):")
res_edit_get = client.get(f"/apply/edit/{token_created}")
assert res_edit_get.status_code == 200
html_edit = res_edit_get.get_data(as_text=True)
assert "Редактирование заявки" in html_edit
assert "36 ч." in html_edit
assert "fulltime_cat1" in html_edit
assert "fulltime_cat2" in html_edit
assert "fulltime_cat3" not in html_edit  # 72 ч. недоступна при редактировании 36 ч.
print("   [OK] Форма редактирования автоматически определяет 36 часов и предлагает только 36ч программы!")

# Обновляем программу второго слушателя на fulltime_cat5 (Члены КЧС, 36 ч.)
edit_data = dict(valid_org)
edit_data["students-1-student_categories-0-category"] = "fulltime_cat5"
res_edit_post = client.post(f"/apply/edit/{token_created}", data=edit_data, follow_redirects=False)
assert res_edit_post.status_code == 302
assert f"/apply/status/{token_created}" in res_edit_post.headers["Location"]

with app.app_context():
    app_updated = Application.query.filter_by(secret_token=token_created).first()
    assert app_updated.listeners[1].courses[0].program.code == "fulltime_cat5"
    assert app_updated.listeners[1].courses[0].program.hours == 36
    print("   [OK] Редактирование успешно сохранило новую программу на 36 часов: fulltime_cat5")

print("\n" + "=" * 70)
print("ВСЕ ТЕСТЫ ГРУППИРОВКИ ГОЧС ПО ЧАСАМ УСПЕШНО ПРОЙДЕНЫ!")
print("=" * 70)
