"""
Скрипт проверки всех внесенных изменений:
1. Отсутствие категорий-заглушек в дистанционном ГОЧС
2. Форматирование часов ('ч.' вместо 'ак. ч.')
3. Заполнение данных для 'Неоконченное высшее (студент)' без полей диплома
4. Обязательность и заполнение пожарного образования при direction='fire'
5. Генерация документов Word с новыми полями
"""
import io
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.models.program import Program
from app.models.application import Application
from app.models.person import Person
from app.services.docx_service import DocxService
from app.constants import StudyForm, TrainingDirection, FIRE_DOCUMENT_LABELS

app = create_app()
app.config["WTF_CSRF_ENABLED"] = False
client = app.test_client()

print("--- ТЕСТИРОВАНИЕ ОБНОВЛЕНИЙ И НОВЫХ ТРЕБОВАНИЙ ---")

# 1. Проверка отсутствия категорий-заглушек
print("\n1. Проверка отсутствия категорий-заглушек в БД:")
with app.app_context():
    dummy_progs = Program.query.filter(Program.code.in_(["distance_cat1", "distance_cat2", "distance_cat3"])).all()
    assert len(dummy_progs) == 0, f"Заглушки все еще присутствуют: {dummy_progs}"
    print("   [OK] Заглушки Заочная программа по ГОЧС 1, 2, 3 успешно удалены из БД")

# 2. Проверка отображения часов на страницах
print("\n2. Проверка отображения часов ('ч.' вместо 'ак. ч.'):")
res_prog_page = client.get("/apply/programs/distant/fire")
assert res_prog_page.status_code == 200
html_prog = res_prog_page.get_data(as_text=True)
assert "ак. ч" not in html_prog, "Найдено 'ак. ч' на странице выбора программ"
assert " ч." in html_prog, "Отсутствует ' ч.' на странице программ"
print("   [OK] На странице выбора категорий отображается 'ч.' без 'ак.'")

res_form = client.get("/apply/ochno/specialist")
assert res_form.status_code == 200
html_form = res_form.get_data(as_text=True)
assert "ак. ч" not in html_form, "Найдено 'ак. ч' в форме"
assert "250 ч." in html_form, "Отсутствует '250 ч.' в форме"
print("   [OK] В форме зафиксированной программы отображается '250 ч.' без 'ак.'")

# 3. Тестирование 'Неоконченное высшее (студент)' (без диплома)
print("\n3. Тестирование подачи заявки со статусом 'Неоконченное высшее (студент)':")
post_data_student = {
    "organization_full_name": "ООО Студенческие Инициативы",
    "organization_short_name": "ООО СтудИниц",
    "inn": "3808123456",
    "kpp": "380801001",
    "ogrn": "1023800000000",
    "bank_name": "ПАО Сбербанк",
    "bik": "042520607",
    "rasch_schot": "40702810000000000001",
    "boss_lastname": "Иванов",
    "boss_firstname": "Иван",
    "boss_patronymic": "Иванович",
    "doljnost_boss": "Генеральный директор",
    "polnamochia_boss": "Устава",
    "yur_address": "г. Иркутск, ул. Ленина, 1",
    "fakt_address": "г. Иркутск, ул. Ленина, 1",
    "telephone": "+7 (3952) 11-22-33",
    "email": "org@stud.ru",
    "fio_executor": "Петров П.П.",
    "doljnost_executor": "Кадровик",
    "telephone_executor": "+7 (3952) 99-88-77",
    # Слушатель - студент с неоконченным высшим
    "students-0-student_lastname": "Смирнов",
    "students-0-student_firstname": "Алексей",
    "students-0-student_patronymic": "Сергеевич",
    "students-0-student_birthdate": "2003-05-15",
    "students-0-citizenship": "РФ",
    "students-0-student_position": "Стажер-спасатель",
    "students-0-education": "Неоконченное высшее (студент)",
    "students-0-institute_name": "ФГБОУ ВО ИГУ",
    "students-0-diploma_seriesnumber": "",  # пусто, так как диплома еще нет
    "students-0-diploma_date": "",          # пусто
    "students-0-diploma_lastname": "",      # пусто
    "students-0-snils": "999-888-777 66",
    "students-0-student_telephone": "+7 (999) 111-22-33",
    "students-0-student_email": "smirnov@stud.ru",
    "students-0-diploma_delivery": "personal",
    "students-0-student_categories-0-category": "fulltime_cat1",
    "students-0-student_categories-0-start_date": "2026-11-10",
    "students-0-student_categories-0-end_date": "2026-11-20"
}
res_sub1 = client.post(
    "/apply/distant/gochs",
    data=post_data_student,
    follow_redirects=False
)
assert res_sub1.status_code == 302, f"Ожидался редирект, получен {res_sub1.status_code}"
assert "/apply/status/" in res_sub1.headers["Location"]
token1 = res_sub1.headers["Location"].split("/apply/status/")[1].split("?")[0]
print("   [OK] Заявка со студентом без диплома успешно создана! Токен:", token1)

# Проверяем скачивание документа Word
res_doc1 = client.get(f"/apply/download/{token1}")
assert res_doc1.status_code == 200
print(f"   [OK] Бланк Word успешно сгенерирован ({len(res_doc1.data)} байт)")

# 4. Тестирование пожарной безопасности (обязательность пожарного образования)
print("\n4. Тестирование валидации пожарного образования (direction='fire'):")
post_data_fire_invalid = {
    "organization_full_name": "ООО Пожарный Надзор",
    "organization_short_name": "ООО Пожнадзор",
    "inn": "3808123456",
    "ogrn": "1023800000000",
    "bank_name": "ПАО Сбербанк",
    "bik": "042520607",
    "rasch_schot": "40702810000000000001",
    "boss_lastname": "Иванов",
    "boss_firstname": "Иван",
    "boss_patronymic": "Иванович",
    "doljnost_boss": "Директор",
    "polnamochia_boss": "Устава",
    "yur_address": "г. Иркутск, ул. Ленина, 1",
    "fakt_address": "г. Иркутск, ул. Ленина, 1",
    "telephone": "+7 (3952) 11-22-33",
    "email": "fire@org.ru",
    "fio_executor": "Петров П.П.",
    "doljnost_executor": "Инженер",
    "telephone_executor": "+7 (3952) 99-88-77",
    "students-0-student_lastname": "Кузнецов",
    "students-0-student_firstname": "Дмитрий",
    "students-0-student_patronymic": "Олегович",
    "students-0-student_birthdate": "1990-01-01",
    "students-0-citizenship": "РФ",
    "students-0-student_position": "Начальник караула",
    "students-0-education": "Высшее образование",
    "students-0-institute_name": "ИРНИТУ",
    "students-0-diploma_seriesnumber": "103824 000123",
    "students-0-diploma_date": "20.06.2012",
    "students-0-diploma_lastname": "Кузнецов",
    "students-0-snils": "111-222-333 44",
    "students-0-student_telephone": "+7 (999) 777-66-55",
    "students-0-student_email": "kuznetsov@fire.ru",
    "students-0-diploma_delivery": "personal",
    "students-0-student_categories-0-category": "fulltime_fire_cat27",
    "students-0-student_categories-0-start_date": "2026-11-01",
    "students-0-student_categories-0-end_date": "2026-11-05",
    # Поля пожарной безопасности НЕ заполнены!
    "students-0-fire_safety_document_type": "",
    "students-0-fire_series": "",
    "students-0-fire_number": "",
    "students-0-fire_date": ""
}
res_fire_invalid = client.post(
    "/apply/distant/fire?category=fulltime_fire_cat27",
    data=post_data_fire_invalid,
    follow_redirects=True
)
html_fire_inv = res_fire_invalid.get_data(as_text=True)
assert "Выберите основание пожарного образования" in html_fire_inv or "Укажите серию" in html_fire_inv
print("   [OK] Валидация сработала: отправка заявки по ПБ без сведений о пожарном образовании заблокирована")

# 5. Тестирование успешной отправки заявки по ПБ с заполнением пожарного образования
print("\n5. Тестирование успешной заявки по ПБ со сведениями о пожарном дипломе:")
post_data_fire_valid = dict(post_data_fire_invalid)
post_data_fire_valid["students-0-fire_safety_document_type"] = "specialty"
post_data_fire_valid["students-0-fire_institution"] = "ФГБОУ ВО ИРНИТУ"
post_data_fire_valid["students-0-fire_series"] = "103824"
post_data_fire_valid["students-0-fire_number"] = "987654"
post_data_fire_valid["students-0-fire_date"] = "15.06.2018"

res_fire_valid = client.post(
    "/apply/distant/fire?category=fulltime_fire_cat27",
    data=post_data_fire_valid,
    follow_redirects=False
)
assert res_fire_valid.status_code == 302, f"Ожидался редирект, код {res_fire_valid.status_code}"
token_fire = res_fire_valid.headers["Location"].split("/apply/status/")[1].split("?")[0]
print("   [OK] Заявка по ПБ успешно создана! Токен:", token_fire)

# Проверяем генерацию pb-dist.docx
res_doc_fire = client.get(f"/apply/download/{token_fire}")
assert res_doc_fire.status_code == 200
print(f"   [OK] Бланк Word по ПБ успешно сгенерирован ({len(res_doc_fire.data)} байт)")

with app.app_context():
    app_fire = Application.query.filter_by(secret_token=token_fire).first()
    p = app_fire.listeners[0].person
    assert p.fire_safety_document_type == "specialty"
    assert p.fire_series == "103824"
    assert p.fire_number == "987654"
    print("   [OK] Данные о пожарном образовании сохранены в БД:", p.fire_safety_document_type, p.fire_series, p.fire_number)

print("\n--- ВСЕ ТЕСТЫ ОБНОВЛЕНИЙ ПРОЙДЕНЫ УСПЕШНО! ---")
