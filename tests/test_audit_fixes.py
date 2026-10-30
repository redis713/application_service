import io
import os
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.models import Application
from app.services.application_service import ApplicationService
from app.blueprints.apply.forms import ApplicationForm

app = create_app()
app.config["WTF_CSRF_ENABLED"] = False
client = app.test_client()

print("--- ТЕСТИРОВАНИЕ НОВЫХ ИСПРАВЛЕНИЙ И БЕЗОПАСНОСТИ ---\n")

# 1. Проверка валидации почтового адреса при доставке 'mail'
print("1. Проверка обязательности адреса доставки при выборе 'Почтой России':")
with app.test_request_context():
    invalid_delivery_data = {
        "organization_full_name": "ООО Доставка Почтой",
        "organization_short_name": "ООО Почта",
        "inn": "3808123456",
        "ogrn": "1023800000000",
        "bank_name": "ПАО Сбербанк",
        "bik": "042520607",
        "rasch_schot": "40702810000000000001",
        "boss_lastname": "Иванов",
        "boss_firstname": "Иван",
        "doljnost_boss": "Директор",
        "polnamochia_boss": "Устава",
        "yur_address": "г. Иркутск, ул. Ленина, 1",
        "fakt_address": "г. Иркутск, ул. Ленина, 1",
        "telephone": "+7 (3952) 11-22-33",
        "email": "post@test.ru",
        "fio_executor": "Петров П.П.",
        "doljnost_executor": "Кадровик",
        "telephone_executor": "+7 (3952) 99-88-77",
        "students-0-student_lastname": "Сидоров",
        "students-0-student_firstname": "Петр",
        "students-0-student_birthdate": "1990-01-01",
        "students-0-citizenship": "РФ",
        "students-0-student_position": "Специалист",
        "students-0-education": "Неоконченное высшее (студент)",
        "students-0-institute_name": "ИГУ",
        "students-0-snils": "111-222-333 44",
        "students-0-student_telephone": "+7 (999) 111-22-33",
        "students-0-student_email": "sidorov@test.ru",
        "students-0-diploma_delivery": "mail",
        "students-0-delivery_address": "",  # Пустой адрес при доставке почтой
        "students-0-student_categories-0-category": "fulltime_cat1",
        "students-0-student_categories-0-start_date": "2026-11-01",
        "students-0-student_categories-0-end_date": "2026-11-05"
    }
    res_mail = client.post("/apply/distant/gochs", data=invalid_delivery_data)
    assert res_mail.status_code == 200, "Форма с пустым адресом не должна сохраняться!"
    html = res_mail.get_data(as_text=True)
    assert "Укажите почтовый адрес" in html
    print("   [OK] Пустой адрес при 'Почтой России' успешно блокируется валидатором!")

# 2. Проверка блокировки даты рождения в будущем
print("\n2. Проверка валидации даты рождения в будущем:")
with app.test_request_context():
    future_data = dict(invalid_delivery_data)
    future_data["students-0-diploma_delivery"] = "personal"
    future_data["students-0-student_birthdate"] = (date.today() + timedelta(days=10)).strftime("%Y-%m-%d")
    res_future = client.post("/apply/distant/gochs", data=future_data)
    assert res_future.status_code == 200
    html = res_future.get_data(as_text=True)
    assert "Дата рождения не может быть в будущем" in html
    print("   [OK] Дата рождения в будущем успешно блокируется валидатором!")

# 3. Проверка загрузки скана с русским именем файла
print("\n3. Проверка загрузки скана с русским именем файла:")
valid_data = dict(invalid_delivery_data)
valid_data["students-0-diploma_delivery"] = "personal"
valid_data["students-0-student_birthdate"] = "1990-01-01"

res_create = client.post("/apply/distant/gochs", data=valid_data, follow_redirects=False)
assert res_create.status_code == 302
token = res_create.headers["Location"].split("/apply/status/")[1].split("?")[0]

pdf_content = b"%PDF-1.4 test cyrillic upload"
res_up = client.post(
    f"/apply/status/{token}",
    data={"scan_file": (io.BytesIO(pdf_content), "Заявление с подписью и печатью.pdf")},
    content_type="multipart/form-data",
    follow_redirects=False
)
assert res_up.status_code == 302
assert f"/apply/success/{token}" in res_up.headers["Location"]

with app.app_context():
    app_saved = Application.query.filter_by(secret_token=token).first()
    assert app_saved.signed_scan_filename == "Заявление с подписью и печатью.pdf"
    assert os.path.exists(app_saved.signed_scan_path)
    assert app_saved.signed_scan_path.endswith(".pdf")
    print("   [OK] Русское имя файла корректно сохранено в БД:", app_saved.signed_scan_filename)
    print("   [OK] Физический файл имеет безопасное имя и расширение:", os.path.basename(app_saved.signed_scan_path))

# 4. Проверка эндпоинта просмотра скана /apply/scan/<token>
print("\n4. Проверка эндпоинта /apply/scan/<token>:")
res_scan = client.get(f"/apply/scan/{token}")
assert res_scan.status_code == 200
assert res_scan.content_type == "application/pdf"
assert res_scan.data == pdf_content
res_scan.close()
print("   [OK] Эндпоинт /apply/scan/<token> возвращает файл с правильным MIME-типом application/pdf!")

# 5. Проверка защиты от повторного открытия формы скана при уже поданной заявке
print("\n5. Проверка перенаправления со /status/<token> на /success/<token> для поданной заявки:")
res_status = client.get(f"/apply/status/{token}", follow_redirects=False)
assert res_status.status_code == 302
assert f"/apply/success/{token}" in res_status.headers["Location"]
print("   [OK] Поданная заявка автоматически перенаправляется на карточку успеха!")

# 6. Очистка временного файла
if os.path.exists(app_saved.signed_scan_path):
    os.remove(app_saved.signed_scan_path)

print("\n--- ВСЕ ТЕСТЫ АУДИТА И БЕЗОПАСНОСТИ УСПЕШНО ПРОЙДЕНЫ! ---")
