import io
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from datetime import date
from app import create_app
from app.models import Application, Organization, Person
from app.services.docx_service import DocxService
from app.services.application_service import ApplicationService

app = create_app()
app.config["WTF_CSRF_ENABLED"] = False
client = app.test_client()

print("1. Тестирование основных роутов:")
assert client.get("/").status_code == 200
assert client.get("/distant").status_code == 200
assert client.get("/ochno").status_code == 200
assert client.get("/apply/distant/gochs").status_code == 200
print("   [OK] Все маршруты возвращают HTTP 200 OK")

print("\n2. Тестирование генератора Word (.docx) в памяти:")
org_sample = {
    "full_name": "ООО «Байкальские Системы»",
    "short_name": "ООО «БС»",
    "inn": "3808123456",
    "kpp": "380801001",
    "ogrn": "1023800000000",
    "bank_name": "ПАО Сбербанк",
    "bik": "042520607",
    "account_number": "40702810000000000001",
    "boss_lastname": "Иванов",
    "boss_firstname": "Иван",
    "boss_patronymic": "Иванович",
    "boss_position": "Генеральный директор",
    "boss_authority": "Устава",
    "legal_address": "г. Иркутск, ул. Ленина, д. 1",
    "actual_address": "г. Иркутск, ул. Ленина, д. 1",
    "phone": "+7 (3952) 11-22-33",
    "email": "info@baikal.ru",
    "executor_fio": "Петров Петр Петрович",
    "executor_position": "Специалист по охране труда",
    "executor_phone": "+7 (3952) 99-88-77",
    "executor_email": "petrov@baikal.ru"
}

listeners_sample = [{
    "lastname": "Сидоров",
    "firstname": "Алексей",
    "patronymic": "Сергеевич",
    "birthdate": "15.04.1985",
    "citizenship": "РФ",
    "education_level": "Высшее образование",
    "institute_name": "Иркутский государственный университет",
    "diploma_series_number": "103804 1234567",
    "diploma_date": "25.06.2007",
    "diploma_lastname": "Сидоров",
    "snils": "123-456-789 01",
    "position": "Инженер по безопасности",
    "phone": "+7 902 555-44-33",
    "email": "sidorov@mail.ru",
    "diploma_delivery": "personal",
    "courses": [{
        "title": "Руководители организаций",
        "start_date": "01.11.2026",
        "end_date": "10.11.2026"
    }]
}]

stream_dist = DocxService.generate_docx_stream(org_sample, listeners_sample, study_form="distant")
assert stream_dist.getbuffer().nbytes > 1000
print(f"   [OK] Сгенерирован дистанционный Word: {stream_dist.getbuffer().nbytes} байт")

stream_ochno = DocxService.generate_docx_stream(org_sample, listeners_sample, study_form="ochno")
assert stream_ochno.getbuffer().nbytes > 1000
print(f"   [OK] Сгенерирован очно-заочный Word: {stream_ochno.getbuffer().nbytes} байт")

print("\n3. Тестирование создания черновика заявки в базе данных:")
with app.app_context():
    app_draft = ApplicationService.create_application_draft(
        org_data=org_sample,
        students_data=[{
            "student_lastname": "Кузнецов",
            "student_firstname": "Дмитрий",
            "student_patronymic": "Олегович",
            "student_birthdate": date(1990, 5, 20),
            "citizenship": "РФ",
            "student_position": "Главный энергетик",
            "education": "Высшее образование",
            "institute_name": "ИРНИТУ",
            "diploma_seriesnumber": "038101 987654",
            "diploma_date": "18.06.2012",
            "diploma_lastname": "Кузнецов",
            "snils": "999-888-777 66",
            "student_telephone": "+79140001122",
            "student_email": "kuznetsov@baikal.ru",
            "diploma_delivery": "personal",
            "delivery_address": "",
            "student_categories": [{
                "category": "fulltime_cat2",
                "start_date": date(2026, 11, 1),
                "end_date": date(2026, 11, 10),
            }]
        }],
        direction="gochs",
        study_form="distant"
    )
    print(f"   [OK] Заявка успешно сохранена в БД с номером: {app_draft.app_number}")
    print(f"   [OK] Секретный токен для доступа: {app_draft.secret_token}")
    print(f"   [OK] Статус заявки: {app_draft.status_label}")
    token = app_draft.secret_token

print("\n4. Тестирование эндпоинта скачивания бланка (.docx) по токену:")
res_download = client.get(f"/apply/download/{token}")
assert res_download.status_code == 200
assert res_download.mimetype == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
print(f"   [OK] Бланк успешно скачан через GET /apply/download/{token} ({len(res_download.data)} байт)")

print("\n5. Тестирование прикрепления подписанного скана (Шаг 3):")
fake_pdf = io.BytesIO(b"%PDF-1.4 test scan content of signed document")
res_upload = client.post(
    f"/apply/status/{token}",
    data={"scan_file": (fake_pdf, "signed_application.pdf")},
    content_type="multipart/form-data",
    follow_redirects=True
)
assert res_upload.status_code == 200
assert "успешно прикреплен" in res_upload.get_data(as_text=True)
print("   [OK] Скан успешно загружен, заявка переведена в статус 'Подана (на проверке)'")

with app.app_context():
    saved_app = Application.query.filter_by(secret_token=token).first()
    assert saved_app.status == "submitted"
    assert saved_app.signed_scan_filename == "signed_application.pdf"
    assert os.path.exists(saved_app.signed_scan_path)
    print(f"   [OK] Файл физически сохранен на диск: {saved_app.signed_scan_path}")

print("\nВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО! СИСТЕМА ПОЛНОСТЬЮ РАБОТАЕТ!")
