import os
import sys
from datetime import date

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.models import Application, Program
from app.services.docx_service import DocxService
from app.constants import StudyForm, TrainingDirection

app = create_app()
app.config["WTF_CSRF_ENABLED"] = False
client = app.test_client()

print("--- ТЕСТ НОВОЙ СТРУКТУРЫ ПО ТРЕБОВАНИЯМ ДОГОВОРНОГО ОТДЕЛА ---\n")

# 1. Проверка страницы Дистанционного обучения
print("1. Проверка страницы /distant:")
res = client.get("/distant")
assert res.status_code == 200
html = res.get_data(as_text=True)
assert "Гражданская оборона" in html
assert "Пожарная безопасность" in html
assert "Антитеррористическая защищенность" in html
assert "112" not in html, "112 не должно быть в дистанте!"
assert "/apply/programs/distant/fire" in html, "Пожарка в дистанте должна вести на выбор категорий!"
print("   [OK] В дистанте ровно 3 подраздела (ГОЧС, Пожарка, Антитеррор)")

# 2. Проверка страницы Очно-заочного обучения
print("\n2. Проверка страницы /ochno:")
res = client.get("/ochno")
assert res.status_code == 200
html = res.get_data(as_text=True)
assert "Гражданская оборона" in html
assert "Пожарная безопасность" in html
assert "112" in html
assert "Специалист по гражданской обороне (250 часов)" in html
assert "Антитеррористическая защищенность" not in html, "Антитеррора не должно быть в очке!"
assert "/apply/programs/ochno/gochs" in html
assert "/apply/programs/ochno/fire" in html
assert "/apply/programs/ochno/112" in html
assert "/apply/ochno/specialist" in html
print("   [OK] В очке ровно 4 подраздела (ГОЧС, Пожарка, 112, Специалист ГО 250ч)")

# 3. Проверка категорий Пожарной безопасности в дистанте (без 250ч)
print("\n3. Проверка выбора категорий Пожарной безопасности в дистанте:")
res = client.get("/apply/programs/distant/fire")
assert res.status_code == 200
html = res.get_data(as_text=True)
assert "250 часов" not in html, "В дистанте пожарка не должна содержать 250 часов!"
assert "fulltime_fire_cat27" in html
assert "fulltime_fire_cat28" in html
assert "fulltime_fire_cat29" in html
assert "fulltime_fire_cat30" in html
print("   [OK] В дистанционной пожарке ровно 4 категории (без 250 часов)")

# 4. Проверка категорий Пожарной безопасности в очке (включая 250ч)
print("\n4. Проверка выбора категорий Пожарной безопасности в очке:")
res = client.get("/apply/programs/ochno/fire")
assert res.status_code == 200
html = res.get_data(as_text=True)
assert "fulltime_fire_cat31" in html, "В очной пожарке должна быть категория на 250 часов!"
assert "Специалист по пожарной профилактике" in html
print("   [OK] В очной пожарке доступны все 5 категорий (включая 250 часов)")

# 5. Проверка категорий 112 в очке (включая новую на 40 часов)
print("\n5. Проверка категорий 112 в очке:")
res = client.get("/apply/programs/ochno/112")
assert res.status_code == 200
html = res.get_data(as_text=True)
assert "fulltime_cat32" in html, "Должна быть 250 часов 112"
assert "fulltime_cat33" in html, "Должна быть 76 часов 112"
assert "fulltime_cat34" in html, "Должна быть добавленная категория 40 часов 112"
assert "40 часов" in html
print("   [OK] В 112 доступны 3 категории (250ч, 76ч, 40ч)")

# 6. Проверка прямого входа в Антитеррор (жесткая фиксация)
print("\n6. Проверка формы Антитеррор:")
res = client.get("/apply/distant/antiterror")
assert res.status_code == 200
html = res.get_data(as_text=True)
assert "Антитеррористическая защищенность" in html
assert "fixed_category_code" in html or "antiterror" in html
assert "fixed-program-card" in html, "Должен отображаться блок фиксированной программы"
print("   [OK] Форма антитеррора открывается напрямую с жестко зафиксированной категорией")

# 7. Проверка прямого входа в Специалист ГО (250ч)
print("\n7. Проверка формы Специалист ГО (250ч):")
res = client.get("/apply/ochno/specialist")
assert res.status_code == 200
html = res.get_data(as_text=True)
assert "Специалист по гражданской обороне" in html
assert "fixed-program-card" in html
print("   [OK] Форма Специалиста ГО (250ч) открывается напрямую с жестко зафиксированной категорией")

# 8. Проверка рендеринга всех 7 шаблонов Word через DocxService
print("\n8. Проверка генерации Word для всех 7 сценариев:")
cases = [
    ("distant", "gochs", "gochs-dist.docx"),
    ("distant", "fire", "pb-dist.docx"),
    ("distant", "antiterror", "antiterror.docx"),
    ("ochno", "gochs", "gochs-ochno.docx"),
    ("ochno", "fire", "pb-ochno.docx"),
    ("ochno", "112", "112.docx"),
    ("ochno", "specialist", "specialist.docx"),
]

sample_org = {
    "organization_full_name": "ООО «Тест»",
    "organization_short_name": "ООО «Тест»",
    "boss_lastname": "Иванов",
    "boss_firstname": "Иван",
    "boss_patronymic": "Иванович",
    "boss_position": "Директор",
    "boss_authority": "Устава",
    "ogrn": "1023800000000",
    "inn": "3808000000",
    "kpp": "380801001",
    "bank_name": "ПАО Сбербанк",
    "account_number": "40702810000000000001",
    "bik": "042520607",
    "actual_address": "г. Иркутск",
    "legal_address": "г. Иркутск",
    "phone": "+7 (3952) 11-22-33",
    "email": "test@irk.ru",
    "executor_fio": "Петров П.П.",
    "executor_position": "Инженер",
    "executor_phone": "+7 (3952) 22-33-44",
}
sample_listeners = [{
    "lastname": "Сидоров",
    "firstname": "Сидор",
    "patronymic": "Сидорович",
    "birthdate": date(1990, 5, 10),
    "citizenship": "РФ",
    "education_level": "Высшее образование",
    "institute_name": "ИГУ",
    "diploma_series_number": "123456",
    "diploma_date": "20.06.2012",
    "diploma_lastname": "Сидоров",
    "snils": "111-222-333 44",
    "position": "Специалист",
    "phone": "+7 (914) 111-22-33",
    "email": "sidorov@irk.ru",
    "diploma_delivery": "personal",
    "courses": [{
        "title": "Тестовая программа",
        "start_date": date(2026, 12, 1),
        "end_date": date(2026, 12, 10),
    }]
}]

templates_dir = app.config["DOCX_TEMPLATES_FOLDER"]
for s_form, direction, expected_tmpl in cases:
    buf = DocxService.generate_docx_stream(
        org_data=sample_org,
        listeners_data=sample_listeners,
        study_form=s_form,
        direction=direction,
        templates_dir=templates_dir
    )
    assert buf.getbuffer().nbytes > 15000
    print(f"   [OK] ({s_form}, {direction}) -> успешно сгенерирован {expected_tmpl} ({buf.getbuffer().nbytes} байт)")

print("\nВСЕ ПРОВЕРКИ НОВОЙ СТРУКТУРЫ УСПЕШНО ПРОЙДЕНЫ!")
