import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from datetime import date
from app import create_app
from app.extensions import db
from app.models.application import Application
from app.models.person import Person

app = create_app()
client = app.test_client()

print("--- ТЕСТИРОВАНИЕ ВАЛИДАЦИИ И ИСПРАВЛЕНИЙ ---\n")

# 1. Проверка времени жизни CSRF токена
print("1. Проверка времени жизни CSRF токена:")
assert app.config["WTF_CSRF_TIME_LIMIT"] == 10800, f"Ожидалось 10800, получено {app.config.get('WTF_CSRF_TIME_LIMIT')}"
print("   [OK] WTF_CSRF_TIME_LIMIT установлен на 10800 секунд (3 часа)")

app.config["WTF_CSRF_ENABLED"] = False

# 2. Проверка валидации БИК (слишком длинный БИК не должен ронять БД)
print("\n2. Проверка валидации БИК:")
invalid_bik_data = {
    "organization_full_name": "ООО Валидация БИК Тест",
    "organization_short_name": "ООО БИК",
    "inn": "3808111222",
    "ogrn": "1023800000000",
    "bank_name": "ПАО Сбербанк",
    "bik": "0425206079999",  # 13 цифр вместо 9
    "rasch_schot": "40702810000000000001",
    "boss_lastname": "Иванов",
    "boss_firstname": "Иван",
    "doljnost_boss": "Директор",
    "polnamochia_boss": "Устава",
    "yur_address": "г. Иркутск, ул. Ленина, 1",
    "fakt_address": "г. Иркутск, ул. Ленина, 1",
    "telephone": "+7 (3952) 11-22-33",
    "email": "bik@test.ru",
    "fio_executor": "Петров П.П.",
    "doljnost_executor": "Инженер",
    "telephone_executor": "+7 (3952) 99-88-77",
    "students-0-student_lastname": "Смирнов",
    "students-0-student_firstname": "Алексей",
    "students-0-student_birthdate": "1995-05-15",
    "students-0-citizenship": "РФ",
    "students-0-student_position": "Специалист",
    "students-0-education": "Высшее образование",
    "students-0-institute_name": "ИГУ",
    "students-0-diploma_seriesnumber": "103801 123456",
    "students-0-diploma_date": "2018-06-25",
    "students-0-diploma_lastname": "Смирнов",
    "students-0-snils": "999-888-777 66",
    "students-0-student_telephone": "+7 (999) 111-22-33",
    "students-0-student_email": "smirnov@test.ru",
    "students-0-diploma_delivery": "personal",
    "students-0-student_categories-0-category": "fulltime_cat1",
    "students-0-student_categories-0-start_date": "2026-11-01",
    "students-0-student_categories-0-end_date": "2026-11-05",
}

res_bik = client.post("/apply/distant/gochs", data=invalid_bik_data, follow_redirects=True)
html_bik = res_bik.get_data(as_text=True)
assert "БИК должен содержать ровно 9 цифр" in html_bik
assert "Data too long" not in html_bik
print("   [OK] Слишком длинный БИК корректно отловлен формой с понятным сообщением")

# 3. Проверка валидации расчетного счета (20 цифр)
print("\n3. Проверка валидации расчетного счета:")
invalid_rs_data = dict(invalid_bik_data)
invalid_rs_data["bik"] = "042520607"
invalid_rs_data["rasch_schot"] = "407028100"  # 9 цифр вместо 20

res_rs = client.post("/apply/distant/gochs", data=invalid_rs_data, follow_redirects=True)
html_rs = res_rs.get_data(as_text=True)
assert "Расчетный счет должен содержать ровно 20 цифр" in html_rs
print("   [OK] Некорректный расчетный счет отловлен формой с понятным сообщением")

# 4. Проверка валидации уровня образования и видимости диплома
print("\n4. Проверка валидации уровня образования:")
no_edu_data = dict(invalid_bik_data)
no_edu_data["bik"] = "042520607"
no_edu_data["rasch_schot"] = "40702810000000000001"
no_edu_data["students-0-education"] = ""  # Не выбрано ничего

res_no_edu = client.post("/apply/distant/gochs", data=no_edu_data, follow_redirects=True)
html_no_edu = res_no_edu.get_data(as_text=True)
assert "Выберите уровень образования" in html_no_edu
print("   [OK] Пустой уровень образования блокирует отправку с ошибкой")

# 5. Проверка сохранения диплома как Date и успешного создания заявки
print("\n5. Проверка сохранения даты выдачи диплома как Date:")
valid_data = dict(invalid_bik_data)
valid_data["bik"] = "042520607"
valid_data["rasch_schot"] = "40702810000000000001"
valid_data["students-0-diploma_date"] = "2018-06-25"

res_valid = client.post("/apply/distant/gochs", data=valid_data, follow_redirects=False)
assert res_valid.status_code == 302, f"Ожидался редирект, код {res_valid.status_code}"
token = res_valid.headers["Location"].split("/apply/status/")[1].split("?")[0]

with app.app_context():
    app_obj = Application.query.filter_by(secret_token=token).first()
    p = app_obj.listeners[0].person
    assert isinstance(p.diploma_date, date), f"Ожидался date, получено {type(p.diploma_date)}"
    assert p.diploma_date == date(2018, 6, 25)
    print("   [OK] Дата выдачи диплома успешно сохранена в типе Date:", p.diploma_date)

# 6. Проверка редактирования с датой диплома
print("\n6. Проверка предзаполнения даты диплома при редактировании:")
res_edit_get = client.get(f"/apply/edit/{token}")
assert res_edit_get.status_code == 200
html_edit = res_edit_get.get_data(as_text=True)
assert 'value="2018-06-25"' in html_edit
print("   [OK] Дата диплома корректно предзаполняется в input type=date")

print("\n--- ВСЕ ТЕСТЫ ВАЛИДАЦИИ И ИСПРАВЛЕНИЙ УСПЕШНО ПРОЙДЕНЫ! ---")
