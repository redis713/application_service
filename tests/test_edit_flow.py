import os
import sys
from datetime import date

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.models import Application, Program
from app.services.application_service import ApplicationService

app = create_app()
app.config["WTF_CSRF_ENABLED"] = False
client = app.test_client()

print("1. Тестирование создания черновика заявки:")
with app.app_context():
    app_draft = ApplicationService.create_application_draft(
        org_data={
            "organization_full_name": "ООО «Тест Иркутск»",
            "organization_short_name": "ООО «ТИ»",
            "inn": "3808999888",
            "kpp": "380801001",
            "ogrn": "1023800000001",
            "bank_name": "ПАО Сбербанк",
            "bik": "042520607",
            "rasch_schot": "40702810000000000002",
            "boss_lastname": "Сергеев",
            "boss_firstname": "Сергей",
            "boss_patronymic": "Сергеевич",
            "doljnost_boss": "Директор",
            "polnamochia_boss": "Устава",
            "yur_address": "г. Иркутск, ул. Карла Маркса, 10",
            "fakt_address": "г. Иркутск, ул. Карла Маркса, 10",
            "telephone": "+7 (3952) 22-33-44",
            "email": "sergeev@irk.ru",
            "fio_executor": "Антонов А.А.",
            "doljnost_executor": "Инженер",
            "telephone_executor": "+7 (3952) 55-66-77",
        },
        students_data=[{
            "student_lastname": "Васильев",
            "student_firstname": "Василий",
            "student_patronymic": "Васильевич",
            "student_birthdate": date(1988, 3, 10),
            "citizenship": "РФ",
            "student_position": "Мастер цеха",
            "education": "Высшее образование",
            "institute_name": "ИГУ",
            "diploma_seriesnumber": "103801 112233",
            "diploma_date": "20.06.2010",
            "diploma_lastname": "Васильев",
            "snils": "111-222-333 44",
            "student_telephone": "+79141112233",
            "student_email": "vasiliev@irk.ru",
            "diploma_delivery": "personal",
            "delivery_address": "",
            "student_categories": [{
                "category": "fulltime_cat1",
                "start_date": date(2026, 12, 1),
                "end_date": date(2026, 12, 10),
            }]
        }],
        direction="gochs",
        study_form="distant"
    )
    token = app_draft.secret_token
    print(f"   [OK] Создана заявка {app_draft.app_number}, токен: {token}")

print("\n2. Тестирование страницы статуса (Шаг 2):")
res_status = client.get(f"/apply/status/{token}")
assert res_status.status_code == 200
html_status = res_status.get_data(as_text=True)
assert f"/apply/edit/{token}" in html_status
assert "Редактировать заявку" in html_status
print("   [OK] Страница статуса содержит ссылку на редактирование заявки")

print("\n3. Тестирование GET /apply/edit/<token> (Предзаполнение формы):")
res_edit_get = client.get(f"/apply/edit/{token}")
assert res_edit_get.status_code == 200
html_edit = res_edit_get.get_data(as_text=True)
assert "ООО «Тест Иркутск»" in html_edit
assert "3808999888" in html_edit
assert "Васильев" in html_edit
assert "111-222-333 44" in html_edit
print("   [OK] Форма редактирования открылась и успешно предзаполнена данными из БД")

print("\n4. Тестирование POST /apply/edit/<token> (Сохранение изменений):")
# Пользователь исправил фамилию на Васильев-Северный и добавил второго слушателя
edit_form_data = {
    "organization_full_name": "ООО «Тест Иркутск Модифицированный»",
    "organization_short_name": "ООО «ТИМ»",
    "inn": "3808999888",
    "kpp": "380801001",
    "ogrn": "1023800000001",
    "bank_name": "ПАО Сбербанк",
    "bik": "042520607",
    "rasch_schot": "40702810000000000002",
    "boss_lastname": "Сергеев",
    "boss_firstname": "Сергей",
    "boss_patronymic": "Сергеевич",
    "doljnost_boss": "Генеральный директор",
    "polnamochia_boss": "Устава",
    "yur_address": "г. Иркутск, ул. Карла Маркса, 10",
    "fakt_address": "г. Иркутск, ул. Карла Маркса, 10",
    "telephone": "+7 (3952) 22-33-44",
    "email": "sergeev@irk.ru",
    "fio_executor": "Антонов А.А.",
    "doljnost_executor": "Главный инженер",
    "telephone_executor": "+7 (3952) 55-66-77",
    # Слушатель 0 (отредактированный)
    "students-0-student_lastname": "Васильев",
    "students-0-student_firstname": "Василий",
    "students-0-student_patronymic": "Васильевич",
    "students-0-student_birthdate": "1988-03-10",
    "students-0-citizenship": "РФ",
    "students-0-student_position": "Начальник службы безопасности",
    "students-0-education": "Высшее образование",
    "students-0-institute_name": "ИГУ",
    "students-0-diploma_seriesnumber": "103801 112233",
    "students-0-diploma_date": "20.06.2010",
    "students-0-diploma_lastname": "Васильев",
    "students-0-snils": "111-222-333 44",
    "students-0-student_telephone": "+79141112233",
    "students-0-student_email": "vasiliev@irk.ru",
    "students-0-diploma_delivery": "personal",
    "students-0-student_categories-0-category": "fulltime_cat2",
    "students-0-student_categories-0-start_date": "2026-12-01",
    "students-0-student_categories-0-end_date": "2026-12-10",
}

res_edit_post = client.post(
    f"/apply/edit/{token}",
    data=edit_form_data,
    follow_redirects=True
)
assert res_edit_post.status_code == 200
html_post = res_edit_post.get_data(as_text=True)
assert "успешно обновлена" in html_post
print("   [OK] Изменения сохранены, перенаправление на скачивание обновленного бланка отработало")

with app.app_context():
    updated_app = Application.query.filter_by(secret_token=token).first()
    assert updated_app.organization.full_name == "ООО «Тест Иркутск Модифицированный»"
    assert updated_app.listeners[0].position == "Начальник службы безопасности"
    print(f"   [OK] В БД зафиксировано новое наименование организации: {updated_app.organization.full_name}")
    print(f"   [OK] В БД зафиксирована новая должность слушателя: {updated_app.listeners[0].position}")

print("\nТЕСТ РЕДАКТИРОВАНИЯ И ВОЗВРАТА С ШАГА 2 НА ШАГ 1 ПРОЙДЕН УСПЕШНО!")
