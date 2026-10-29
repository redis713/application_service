import os
import sys
from datetime import date
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.models import Application, Person
from app.services.docx_service import DocxService
from app.blueprints.apply.forms import validate_fio
from wtforms.validators import ValidationError

app = create_app()
app.config["WTF_CSRF_ENABLED"] = False
client = app.test_client()

print("--- ТЕСТИРОВАНИЕ НОВЫХ ТРЕБОВАНИЙ (АРХИТЕКТУРА И ДОРАБОТКИ) ---\n")

# 1. Проверка валидации ФИО (двойные имена, составные части, регистр)
print("1. Проверка расширенной валидации ФИО:")
class DummyField:
    def __init__(self, data):
        self.data = data

valid_names = [
    "Иванов",
    "Салтыков-Щедрин",
    "Анна-Мария",
    "Мамед оглы",
    "Али-кызы",
    "Бонч-Бруевич",
    "О'Коннор",
    "Жан Поль",
    "Ян",
    "Ли"
]
for name in valid_names:
    try:
        validate_fio(None, DummyField(name))
    except ValidationError as e:
        assert False, f"Валидное имя '{name}' было отклонено: {e}"
print(f"   [OK] Все {len(valid_names)} вариантов сложных/двойных имен успешно прошли валидацию")

invalid_names = [
    "иванов",      # со строчной буквы
    "Ivanov",      # латиница
    "Иванов123",   # цифры
    "Иванов@",     # спецсимвол
    "Иванов-",     # дефис на конце
    "-Иванов",     # дефис в начале
]
for name in invalid_names:
    try:
        validate_fio(None, DummyField(name))
        assert False, f"Невалидное имя '{name}' не было отклонено"
    except ValidationError:
        pass
print(f"   [OK] Все {len(invalid_names)} невалидных вариантов корректно отклонены")

# 2. Проверка независимости заявок (отказ от отдельной сущности Организации)
print("\n2. Проверка хранения данных организации в заявке и их независимости:")
app_data_1 = {
    "organization_full_name": "ООО «Первая Компания»",
    "organization_short_name": "ООО «ПК»",
    "inn": "7701122334",
    "ogrn": "1027700000000",
    "bank_name": "ПАО Сбербанк",
    "bik": "044525225",
    "rasch_schot": "40702810100000000001",
    "boss_lastname": "Салтыков-Щедрин",
    "boss_firstname": "Михаил",
    "boss_patronymic": "Евграфович",
    "doljnost_boss": "Генеральный директор",
    "polnamochia_boss": "Устава",
    "yur_address": "г. Москва, ул. Арбат, 1",
    "fakt_address": "г. Москва, ул. Арбат, 1",
    "telephone": "+7 (495) 111-22-33",
    "email": "org1@test.ru",
    "fio_executor": "Мамин-Сибиряк Д.Н.",
    "doljnost_executor": "Секретарь",
    "telephone_executor": "+7 (495) 999-88-77",
    "students-0-student_lastname": "Бонч-Бруевич",
    "students-0-student_firstname": "Владимир",
    "students-0-student_birthdate": "1990-01-01",
    "students-0-citizenship": "РФ",
    "students-0-student_position": "Инженер",
    "students-0-education": "Высшее образование",
    "students-0-institute_name": "МГУ",
    "students-0-diploma_seriesnumber": "107701 123456",
    "students-0-diploma_date": "2015-06-20",
    "students-0-diploma_lastname": "Бонч-Бруевич",
    "students-0-snils": "111-222-333 44",
    "students-0-student_telephone": "+7 (999) 111-22-33",
    "students-0-student_email": "bonch@test.ru",
    "students-0-diploma_delivery": "personal",
    "students-0-student_categories-0-category": "fulltime_cat1",
    "students-0-student_categories-0-start_date": "2026-11-01",
    "students-0-student_categories-0-end_date": "2026-11-05",
}

# Подаем 1-ю заявку с ИНН 7701122334
res1 = client.post("/apply/distant/gochs", data=app_data_1, follow_redirects=False)
assert res1.status_code == 302
token1 = res1.headers["Location"].split("/apply/status/")[1].split("?")[0]

# Подаем 2-ю заявку с ТЕМ ЖЕ ИНН 7701122334, но другими контактами и директором
app_data_2 = dict(app_data_1)
app_data_2["organization_full_name"] = "ООО «Первая Компания Филиал 2»"
app_data_2["boss_lastname"] = "Анна-Мария"
app_data_2["boss_firstname"] = "Жанна"
app_data_2["email"] = "filial2@test.ru"
app_data_2["students-0-snils"] = "555-666-777 88"

res2 = client.post("/apply/distant/gochs", data=app_data_2, follow_redirects=False)
assert res2.status_code == 302
token2 = res2.headers["Location"].split("/apply/status/")[1].split("?")[0]

with app.app_context():
    app1 = Application.query.filter_by(secret_token=token1).first()
    app2 = Application.query.filter_by(secret_token=token2).first()

    assert app1.inn == "7701122334"
    assert app2.inn == "7701122334"

    # Заявка 1 НЕ была перезаписана Заявкой 2!
    assert app1.org_full_name == "ООО «Первая Компания»"
    assert app1.boss_lastname == "Салтыков-Щедрин"
    assert app1.email == "org1@test.ru"
    assert app1.last_edited_by is None

    assert app2.org_full_name == "ООО «Первая Компания Филиал 2»"
    assert app2.boss_lastname == "Анна-Мария"
    assert app2.email == "filial2@test.ru"

    print("   [OK] Данные организаций изолированы в заявках и не перезаписывают друг друга по ИНН!")

# 3. Проверка отметки редактирования пользователем
print("\n3. Проверка отметки последнего редактирования:")
edit_data = dict(app_data_1)
edit_data["doljnost_boss"] = "Президент компании"
res_edit = client.post(f"/apply/edit/{token1}", data=edit_data, follow_redirects=False)
assert res_edit.status_code == 302

with app.app_context():
    app1_updated = Application.query.filter_by(secret_token=token1).first()
    assert app1_updated.boss_position == "Президент компании"
    assert app1_updated.last_edited_by == "пользователь"
    assert app1_updated.updated_at is not None
    print(f"   [OK] Отметка редактирования установлена: last_edited_by='{app1_updated.last_edited_by}', updated_at={app1_updated.updated_at}")

# 4. Проверка даты выдачи пожарного диплома как Date
print("\n4. Проверка даты выдачи специального пожарного документа:")
fire_data = {
    "organization_full_name": "ООО Пожарная Охрана",
    "organization_short_name": "ООО ПО",
    "inn": "3808999888",
    "ogrn": "1023800000000",
    "bank_name": "ПАО ВТБ",
    "bik": "042520607",
    "rasch_schot": "40702810000000000002",
    "boss_lastname": "Петров",
    "boss_firstname": "Петр",
    "doljnost_boss": "Начальник",
    "polnamochia_boss": "Устава",
    "yur_address": "г. Иркутск, ул. Советская, 1",
    "fakt_address": "г. Иркутск, ул. Советская, 1",
    "telephone": "+7 (3952) 22-33-44",
    "email": "fire@ohrana.ru",
    "fio_executor": "Сидоров С.С.",
    "doljnost_executor": "Инженер",
    "telephone_executor": "+7 (3952) 88-77-66",
    "students-0-student_lastname": "Мамед оглы",
    "students-0-student_firstname": "Рашид",
    "students-0-student_birthdate": "1988-12-10",
    "students-0-citizenship": "РФ",
    "students-0-student_position": "Специалист ПБ",
    "students-0-education": "Высшее образование",
    "students-0-institute_name": "ИРНИТУ",
    "students-0-diploma_seriesnumber": "103824 555666",
    "students-0-diploma_date": "2010-06-18",
    "students-0-diploma_lastname": "Мамед оглы",
    "students-0-fire_safety_document_type": "specialty",
    "students-0-fire_institution": "СПбУ ГПС МЧС России",
    "students-0-fire_series": "77ПБ",
    "students-0-fire_number": "123456",
    "students-0-fire_date": "2020-04-15",
    "students-0-snils": "333-444-555 66",
    "students-0-student_telephone": "+7 (999) 333-44-55",
    "students-0-student_email": "mamed@ohrana.ru",
    "students-0-diploma_delivery": "personal",
    "students-0-student_categories-0-category": "fulltime_fire_cat27",
    "students-0-student_categories-0-start_date": "2026-11-01",
    "students-0-student_categories-0-end_date": "2026-11-05",
}
res_fire = client.post("/apply/distant/fire?category=fulltime_fire_cat27", data=fire_data, follow_redirects=False)
assert res_fire.status_code == 302
token_fire = res_fire.headers["Location"].split("/apply/status/")[1].split("?")[0]

with app.app_context():
    app_f = Application.query.filter_by(secret_token=token_fire).first()
    p_f = app_f.listeners[0].person
    assert isinstance(p_f.fire_date, date), f"Ожидался date, получено {type(p_f.fire_date)}"
    assert p_f.fire_date == date(2020, 4, 15)
    print("   [OK] Дата выдачи пожарного документа сохранена как Date:", p_f.fire_date)

# 5. Проверка наличия "Фамилия в дипломе" в сгенерированном контексте docx
print("\n5. Проверка вывода 'Фамилия в дипломе' в Word docx:")
context = DocxService.build_context(
    org_data={"full_name": "Тест", "short_name": "Т", "inn": "1", "ogrn": "2"},
    listeners_data=[{
        "lastname": "Петрова",
        "firstname": "Анна",
        "patronymic": "Ивановна",
        "birthdate": date(1992, 1, 1),
        "education": "Высшее образование",
        "institute_name": "ИГУ",
        "diploma_seriesnumber": "1038 999",
        "diploma_date": date(2014, 6, 20),
        "diploma_lastname": "Сидорова",  # Девичья фамилия в дипломе
        "snils": "111-222-333 44",
        "student_position": "Бухгалтер",
        "courses": []
    }]
)
edu_text = context["data"][0]["education"]
assert "Фамилия в дипломе: Сидорова" in edu_text
print("   [OK] В ячейку образования включена 'Фамилия в дипломе':\n" + "-"*40 + f"\n{edu_text}\n" + "-"*40)

# 6. Проверка наличия защиты от случайного ухода со страницы (beforeunload) в шаблоне
print("\n6. Проверка скрипта beforeunload в form.html:")
with open("app/templates/apply/form.html", "r", encoding="utf-8") as f:
    form_html = f.read()
assert "beforeunload" in form_html
assert "isFormDirty" in form_html
assert "isSubmitting" in form_html
print("   [OK] Предупреждение о несохраненных данных (beforeunload) интегрировано в шаблон формы")

print("\n--- ВСЕ НОВЫЕ ТРЕБОВАНИЯ УСПЕШНО РЕАЛИЗОВАНЫ И ПРОТЕСТИРОВАНЫ! ---")
