import io
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.models import Application, Person, ApplicationListener, ListenerCourse
from app.constants import ApplicationStatus, StudyForm, TrainingDirection

app = create_app()
app.config["WTF_CSRF_ENABLED"] = False
client = app.test_client()

print("=" * 60)
print("ТЕСТИРОВАНИЕ ВНУТРЕННЕГО ПОРТАЛА СОТРУДНИКОВ (CONTRACTMAKER)")
print("=" * 60)

# 1. Проверка разделения сайтов и прав доступа
print("\n1. Проверка изоляции двух сайтов (публичного и внутреннего):")

# Запрос к /applications с публичного хоста (192.168.1.21:8009 или X-Site: public)
resp_pub_denied = client.get("/applications", headers={"Host": "192.168.1.21:8009", "X-Site": "public"})
assert resp_pub_denied.status_code == 404, f"Ожидался 404, получено {resp_pub_denied.status_code}"
print("   [OK] Попытка входа в реестр заявок с публичного сайта возвращает HTTP 404 Not Found")

# Запрос к главной странице с публичного хоста
resp_pub_root = client.get("/", headers={"Host": "192.168.1.21:8009", "X-Site": "public"})
assert resp_pub_root.status_code == 200
assert "Дистанционное" in resp_pub_root.get_data(as_text=True)
print("   [OK] Публичный сайт открывает страницу выбора формы обучения")

# Запрос к главной странице с внутреннего хоста contractmaker.umcgochs.local
resp_int_root = client.get("/", headers={"Host": "contractmaker.umcgochs.local"})
assert resp_int_root.status_code in (301, 302), f"Ожидался редирект, получено {resp_int_root.status_code}"
assert "/applications" in resp_int_root.headers.get("Location")
print("   [OK] Внутренний хост contractmaker.umcgochs.local перенаправляет с корня (/) в /applications")

# Запрос к /applications с внутреннего хоста
resp_int_list = client.get("/applications", headers={"Host": "contractmaker.umcgochs.local"})
assert resp_int_list.status_code == 200
html_text = resp_int_list.get_data(as_text=True)
assert "Реестр поступивших заявок на обучение" in html_text
assert "contractmaker.umcgochs.local" in html_text
print("   [OK] Внутренний реестр успешно открывается по адресу contractmaker.umcgochs.local")


# 2. Проверка отображения списка и фильтров
print("\n2. Проверка фильтрации и поиска заявок:")

with app.app_context():
    first_app = Application.query.first()
    assert first_app is not None, "В базе должна быть хотя бы 1 заявка для теста"
    sample_inn = first_app.inn
    sample_num = first_app.app_number
    sample_id = first_app.id

# Поиск по номеру заявки
resp_search = client.get(f"/applications?q={sample_num}", headers={"Host": "contractmaker.umcgochs.local"})
assert resp_search.status_code == 200
assert sample_num in resp_search.get_data(as_text=True)
print(f"   [OK] Поиск по номеру заявки '{sample_num}' работает корректно")

# Поиск по ИНН
resp_inn = client.get(f"/applications?q={sample_inn}", headers={"Host": "contractmaker.umcgochs.local"})
assert resp_inn.status_code == 200
assert sample_inn in resp_inn.get_data(as_text=True)
print(f"   [OK] Поиск по ИНН '{sample_inn}' работает корректно")

# Фильтрация по статусу
resp_status = client.get("/applications?status=submitted", headers={"Host": "contractmaker.umcgochs.local"})
assert resp_status.status_code == 200
print("   [OK] Фильтрация по статусу 'submitted' работает без ошибок")


# 3. Проверка детальной страницы заявки
print(f"\n3. Проверка карточки заявки ID #{sample_id}:")
resp_detail = client.get(f"/applications/{sample_id}", headers={"Host": "contractmaker.umcgochs.local"})
assert resp_detail.status_code == 200
detail_html = resp_detail.get_data(as_text=True)
assert sample_num in detail_html
assert "Направляющая организация" in detail_html
assert "Слушатели на обучение" in detail_html
print(f"   [OK] Карточка заявки #{sample_id} ({sample_num}) успешно загружена")


# 4. Проверка скачивания официального бланка DOCX сотрудником
print(f"\n4. Проверка генерации и скачивания DOCX для заявки #{sample_id}:")
resp_docx = client.get(f"/applications/{sample_id}/docx", headers={"Host": "contractmaker.umcgochs.local"})
assert resp_docx.status_code == 200
assert resp_docx.mimetype == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
assert len(resp_docx.data) > 5000, "Файл docx должен быть сгенерирован и не быть пустым"
print(f"   [OK] Сгенерирован DOCX документ размером {len(resp_docx.data)} байт")


# 5. Проверка просмотра/скачивания прикрепленного скана
print(f"\n5. Проверка работы со сканом заявления:")
with app.app_context():
    apps_with_scan = Application.query.filter(Application.signed_scan_path.isnot(None)).all()
    app_with_scan = next((a for a in apps_with_scan if a.signed_scan_path and os.path.exists(a.signed_scan_path)), None)

if app_with_scan:
    resp_scan_inline = client.get(f"/applications/{app_with_scan.id}/scan", headers={"Host": "contractmaker.umcgochs.local"})
    assert resp_scan_inline.status_code == 200
    print(f"   [OK] Просмотр скана для заявки #{app_with_scan.id} ({app_with_scan.app_number}) (HTTP 200, mime: {resp_scan_inline.mimetype})")

    resp_scan_dl = client.get(f"/applications/{app_with_scan.id}/scan?download=1", headers={"Host": "contractmaker.umcgochs.local"})
    assert resp_scan_dl.status_code == 200
    assert "attachment" in resp_scan_dl.headers.get("Content-Disposition", "")
    print(f"   [OK] Скачивание скана как вложения для заявки #{app_with_scan.id} (Content-Disposition: attachment)")
else:
    print("   [INFO] В тестовой БД пока нет физического файла скана на диске, проверим обработку отсутствующего скана:")
    resp_no_scan = client.get(f"/applications/{sample_id}/scan", headers={"Host": "contractmaker.umcgochs.local"})
    # Должен сделать редирект с предупреждением
    assert resp_no_scan.status_code in (301, 302)
    print("   [OK] При отсутствии файла происходит редирект с флеш-сообщением")

print("\n" + "=" * 60)
print("ВСЕ ТЕСТЫ ВНУТРЕННЕГО ПОРТАЛА СОТРУДНИКА УСПЕШНО ПРОЙДЕНЫ!")
print("=" * 60)
