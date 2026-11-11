import io
import os
import sys
from datetime import date

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.models import Application
from app.services.application_service import ApplicationService
from app.blueprints.apply.forms import ApplicationForm, StudentForm

app = create_app()
app.config["WTF_CSRF_ENABLED"] = False
client = app.test_client()

print("--- ТЕСТИРОВАНИЕ ПОСЛЕДНИХ ДОРАБОТОК ---\n")

# 1. Проверка формата наименования заявок с типом обучения
print("1. Проверка системы генерации номеров заявок (ГО-Д-, ПБ-О- и т.д.):")
with app.app_context():
    num_go_dist = ApplicationService.generate_app_number("gochs", "distant")
    assert num_go_dist.startswith("ГО-Д-2026-"), f"Ожидался номер ГО-Д-2026-..., получен: {num_go_dist}"
    print(f"   [OK] gochs + distant -> {num_go_dist}")

    num_pb_ochno = ApplicationService.generate_app_number("fire", "ochno")
    assert num_pb_ochno.startswith("ПБ-О-2026-"), f"Ожидался номер ПБ-О-2026-..., получен: {num_pb_ochno}"
    print(f"   [OK] fire + ochno -> {num_pb_ochno}")

    num_at_dist = ApplicationService.generate_app_number("antiterror", "distant")
    assert num_at_dist.startswith("АТ-Д-2026-"), f"Ожидался номер АТ-Д-2026-..., получен: {num_at_dist}"
    print(f"   [OK] antiterror + distant -> {num_at_dist}")

    num_112_ochno = ApplicationService.generate_app_number("call112", "ochno")
    assert num_112_ochno.startswith("112-О-2026-"), f"Ожидался номер 112-О-2026-..., получен: {num_112_ochno}"
    print(f"   [OK] call112 + ochno -> {num_112_ochno}")


# 2. Проверка выпадающего списка "Уровень базового образования"
print("\n2. Проверка выпадающего списка уровня образования:")
with app.app_context():
    s_form = StudentForm()
    choices = [c[0] for c in s_form.education.choices]
    assert "" not in choices, "В списке не должно быть пустого варианта!"
    assert choices[0] == "Высшее образование", f"Первым должен быть 'Высшее образование', но получили: {choices[0]}"
    assert s_form.education.default == "Высшее образование", "Дефолтное значение должно быть 'Высшее образование'!"
    print("   [OK] Пустой пункт 'Выберите уровень образования' исключен, дефолтное значение: 'Высшее образование'.")


# 3. Проверка формы пожарной безопасности (обязательность образовательного учреждения и верстка)
print("\n3. Проверка валидации профильного пожарного образования:")
with app.test_request_context():
    fire_form_get = client.get("/apply/distant/fire?category=fulltime_fire_cat27")
    assert fire_form_get.status_code == 200
    html_form = fire_form_get.get_data(as_text=True)

    # Проверка разметки: учреждение со звездочкой и required
    assert 'name="students-0-fire_institution"' in html_form
    assert 'placeholder="Полное наименование образовательного учреждения, выдавшего документ"' in html_form
    print("   [OK] Поле 'Образовательное учреждение, выдавшее документ' выведено в отдельной строке с подсказкой.")

    # Проверка отправки без fire_institution: должна быть ошибка
    invalid_fire_data = {
        "fixed_category_code": "fulltime_fire_cat27",
        "organization_full_name": "ООО Пожарная Безопасность",
        "organization_short_name": "ООО ПБ",
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
        "email": "fire@test.ru",
        "fio_executor": "Петров П.П.",
        "doljnost_executor": "Кадровик",
        "telephone_executor": "+7 (3952) 99-88-77",
        "students-0-student_lastname": "Орлов",
        "students-0-student_firstname": "Олег",
        "students-0-student_birthdate": "1988-03-12",
        "students-0-citizenship": "РФ",
        "students-0-student_position": "Инженер ПБ",
        "students-0-education": "Высшее образование",
        "students-0-institute_name": "ИРНИТУ",
        "students-0-diploma_seriesnumber": "1234 567890",
        "students-0-diploma_date": "2015-06-20",
        "students-0-diploma_lastname": "Орлов",
        "students-0-snils": "333-444-555 66",
        "students-0-student_telephone": "+7 (999) 333-44-55",
        "students-0-student_email": "orlov@fire.ru",
        "students-0-diploma_delivery": "personal",
        "students-0-fire_safety_document_type": "specialty",
        "students-0-fire_institution": "",  # ПУСТОЕ УЧРЕЖДЕНИЕ!
        "students-0-fire_series": "ПБ",
        "students-0-fire_number": "123456",
        "students-0-fire_date": "2016-05-10",
        "students-0-student_categories-0-category": "fulltime_fire_cat27",
        "students-0-student_categories-0-start_date": "2026-11-10",
        "students-0-student_categories-0-end_date": "2026-11-20"
    }

    res_fire_invalid = client.post("/apply/distant/fire?category=fulltime_fire_cat27", data=invalid_fire_data)
    assert res_fire_invalid.status_code == 200, "Форма с пустым пожарным учреждением не должна сохраняться!"
    html_err = res_fire_invalid.get_data(as_text=True)
    assert "Укажите образовательное учреждение, выдавшее документ" in html_err
    print("   [OK] Пустое поле 'Образовательное учреждение, выдавшее документ' успешно блокируется сервером!")

    # Теперь отправляем с заполненным fire_institution
    valid_fire_data = dict(invalid_fire_data)
    valid_fire_data["students-0-fire_institution"] = "Академия ГПС МЧС России"
    res_fire_valid = client.post("/apply/distant/fire?category=fulltime_fire_cat27", data=valid_fire_data, follow_redirects=False)
    assert res_fire_valid.status_code == 302
    token_fire = res_fire_valid.headers["Location"].split("/apply/status/")[1].split("?")[0]
    print(f"   [OK] Заявка ПБ с указанным учреждением успешно создана! Токен: {token_fire}")

    with app.app_context():
        app_to_approve = Application.query.filter_by(secret_token=token_fire).first()
        ApplicationService.approve_application(app_to_approve.id)


# 4. Проверка экрана успеха (наличие ссылки для редактирования и предупреждения)
print("\n4. Проверка карточки успеха (/apply/success/<token>):")
# Прикрепляем тестовый скан к заявке, чтобы перейти на /success
pdf_bytes = b"%PDF-1.4 test success page"
res_up = client.post(
    f"/apply/status/{token_fire}",
    data={"scan_file": (io.BytesIO(pdf_bytes), "Zayavleniye.pdf")},
    content_type="multipart/form-data",
    follow_redirects=False
)
assert res_up.status_code == 302
assert f"/apply/status/{token_fire}" in res_up.headers["Location"]

res_success = client.get(f"/apply/success/{token_fire}", follow_redirects=True)
assert res_success.status_code == 200
html_success = res_success.get_data(as_text=True)

# Проверяем наличие всех требуемых элементов на единой странице статуса
assert "Ваша персональная ссылка на заявку" in html_success
assert "Скан заявления успешно прикреплен" in html_success
assert "id=\"status-token-link\"" in html_success
assert f"/apply/edit/{token_fire}" in html_success
assert "copyStatusTokenLink()" in html_success
assert "Редактировать заявку" in html_success
print("   [OK] На экране успеха присутствует блок с персональной ссылкой на редактирование.")
print("   [OK] Присутствует предупреждающий текст о необходимости сохранить ссылку.")
print("   [OK] Присутствует поле с ссылкой, кнопка копирования в буфер и кнопка перехода к редактированию.")

# Удаляем тестовый файл с диска
with app.app_context():
    app_f = Application.query.filter_by(secret_token=token_fire).first()
    if app_f and app_f.signed_scan_path and os.path.exists(app_f.signed_scan_path):
        os.remove(app_f.signed_scan_path)

print("\n--- ВСЕ ТЕСТЫ НОВЫХ ДОРАБОТОК УСПЕШНО ПРОЙДЕНЫ! ---")
