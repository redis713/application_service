import unittest
import os
import io
import docx
from datetime import date
from app import create_app, db
from app.models.application import Application, ApplicationListener, ListenerCourse
from app.models.person import Person
from app.models.program import Program
from app.constants import ApplicationStatus, StudyForm, TrainingDirection
from app.services.docx_service import DocxService
from app.services.application_service import ApplicationService


class ContractGenerationTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.app.config["WTF_CSRF_ENABLED"] = False
        cls.client = cls.app.test_client()

    def setUp(self):
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        db.session.rollback()
        self.app_context.pop()

    def test_01_pytrovich_genitive_fio(self):
        """Проверка склонения ФИО руководителя в родительный падеж."""
        print("\n1. Проверка склонения ФИО руководителя в родительный падеж:")
        res_m = DocxService.get_boss_genitive_fio("Иванов", "Иван", "Иванович")
        self.assertEqual(res_m, "Иванова Ивана Ивановича")
        print(f"   [OK] Иванов Иван Иванович -> {res_m}")

        res_f = DocxService.get_boss_genitive_fio("Петрова", "Анна", "Сергеевна")
        self.assertEqual(res_f, "Петровой Анны Сергеевны")
        print(f"   [OK] Петрова Анна Сергеевна -> {res_f}")

        res_initials = DocxService.get_boss_initials_fio("Иванов", "Иван", "Иванович")
        self.assertEqual(res_initials, "И.И. Иванов")
        print(f"   [OK] Инициалы: {res_initials}")

    def test_02_template_selection_all_types(self):
        """Проверка правильности выбора всех 18 шаблонов договоров."""
        print("\n2. Проверка сопоставления заявок с утвержденными шаблонами договоров:")

        class FakeProgram:
            def __init__(self, code, hours, title):
                self.code = code
                self.hours = hours
                self.title = title

        class FakeCourse:
            def __init__(self, p):
                self.program = p

        class FakeListener:
            def __init__(self, p):
                self.courses = [FakeCourse(p)]

        class FakeApp:
            def __init__(self, direction, study_form, p):
                self.direction = direction
                self.study_form = study_form
                self.listeners = [FakeListener(p)]

        cases = [
            (TrainingDirection.ANTITERROR.value, StudyForm.DISTANT.value, FakeProgram("antiterror", 16, "Антитеррор"), "dogovor-antiterror-16h.docx"),
            (TrainingDirection.SPECIALIST.value, StudyForm.OCHNO.value, FakeProgram("specialist_go", 250, "Спец ГО"), "dogovor-specgo-250h.docx"),
            (TrainingDirection.CALL112.value, StudyForm.OCHNO.value, FakeProgram("fulltime_cat32", 250, "112 250ч"), "dogovor-112-250h.docx"),
            (TrainingDirection.CALL112.value, StudyForm.OCHNO.value, FakeProgram("fulltime_cat33", 76, "112 76ч"), "dogovor-112-76h.docx"),
            (TrainingDirection.CALL112.value, StudyForm.OCHNO.value, FakeProgram("fulltime_cat34", 40, "112 40ч"), "dogovor-112-40h.docx"),
            (TrainingDirection.GOCHS.value, StudyForm.DISTANT.value, FakeProgram("fulltime_cat1", 36, "ГОЧС"), "dogovor-gochs-dist-72h.docx"),
            (TrainingDirection.GOCHS.value, StudyForm.OCHNO.value, FakeProgram("fulltime_cat1", 36, "ГОЧС 36ч"), "dogovor-gochs-ochno-36h.docx"),
            (TrainingDirection.GOCHS.value, StudyForm.OCHNO.value, FakeProgram("fulltime_cat24", 40, "ГОЧС 40ч"), "dogovor-gochs-ochno-40h.docx"),
            (TrainingDirection.GOCHS.value, StudyForm.OCHNO.value, FakeProgram("fulltime_cat3", 72, "ГОЧС 72ч"), "dogovor-gochs-ochno-72h.docx"),
            (TrainingDirection.FIRE.value, StudyForm.DISTANT.value, FakeProgram("fulltime_fire_cat30", 18, "ПБ 18ч"), "dogovor-pb-dist-18h.docx"),
            (TrainingDirection.FIRE.value, StudyForm.DISTANT.value, FakeProgram("fulltime_fire_cat28", 20, "ПБ 20ч"), "dogovor-pb-dist-20h.docx"),
            (TrainingDirection.FIRE.value, StudyForm.DISTANT.value, FakeProgram("fulltime_fire_cat29", 30, "ПБ 30ч главных специалистов"), "dogovor-pb-dist-30(gs)h.docx"),
            (TrainingDirection.FIRE.value, StudyForm.DISTANT.value, FakeProgram("fulltime_fire_cat27", 30, "ПБ 30ч руководители"), "dogovor-pb-dist-30h.docx"),
            (TrainingDirection.FIRE.value, StudyForm.OCHNO.value, FakeProgram("fulltime_fire_cat30", 18, "ПБ 18ч очно"), "dogovor-pb-ochno-18h.docx"),
            (TrainingDirection.FIRE.value, StudyForm.OCHNO.value, FakeProgram("fulltime_fire_cat28", 20, "ПБ 20ч очно"), "dogovor-pb-ochno-20h.docx"),
            (TrainingDirection.FIRE.value, StudyForm.OCHNO.value, FakeProgram("fulltime_fire_cat29", 30, "ПБ 30ч очно главных специалистов"), "dogovor-pb-ochno-30(gs)h.docx"),
            (TrainingDirection.FIRE.value, StudyForm.OCHNO.value, FakeProgram("fulltime_fire_cat27", 30, "ПБ 30ч очно руководители"), "dogovor-pb-ochno-30h.docx"),
            (TrainingDirection.FIRE.value, StudyForm.OCHNO.value, FakeProgram("fulltime_fire_cat31", 250, "ПБ 250ч специалист"), "dogovor-pb-ochno-250h.docx"),
        ]

        for direction, study_form, prog, expected_tpl in cases:
            tpl_name = DocxService.get_contract_template_name(FakeApp(direction, study_form, prog))
            self.assertEqual(tpl_name, expected_tpl, f"Не совпал шаблон для {prog.code} ({study_form})")
            print(f"   [OK] {direction} / {study_form} / {prog.code} -> {tpl_name}")

    def test_03_contract_generation_and_content(self):
        """Проверка генерации Word .docx договора и заполнения всех полей."""
        print("\n3. Проверка генерации Word-документа договора:")

        prog_go = Program.query.filter_by(code="fulltime_cat1").first()
        self.assertIsNotNone(prog_go)
        self.assertEqual(prog_go.price_ochno, 7060)
        self.assertEqual(prog_go.price_dist, 7800)

        import random
        r_snils1 = str(random.randint(10000000000, 99999999999))
        r_snils2 = str(random.randint(10000000000, 99999999999))
        r_app_num = f"TEST-DOG-{random.randint(1000, 9999)}"

        # Создаем тестовую заявку на 2 слушателей
        app = Application(
            app_number=r_app_num,
            direction=TrainingDirection.GOCHS.value,
            study_form=StudyForm.OCHNO.value,
            status=ApplicationStatus.APPROVED.value,
            has_contract=True,
            org_full_name="Общество с ограниченной ответственностью «Северный Альянс»",
            org_short_name="ООО «Северный Альянс»",
            inn="3808123456",
            kpp="380801001",
            ogrn="1023800000001",
            bank_name="ПАО Сбербанк",
            bik="042520607",
            account_number="40702810900000001234",
            boss_lastname="Сергеев",
            boss_firstname="Виктор",
            boss_patronymic="Николаевич",
            boss_position="Генеральный директор",
            boss_authority="Устава",
            legal_address="664000, г. Иркутск, ул. Ленина, д. 10",
            actual_address="664000, г. Иркутск, ул. Ленина, д. 10",
            phone="+7 (3952) 20-30-40",
            email="alliance@irkutsk.ru",
            executor_fio="Васильев П.П.",
            executor_position="Юрист",
            executor_phone="+7 (3952) 20-30-41",
        )
        db.session.add(app)
        db.session.flush()

        p1 = Person(
            snils=r_snils1,
            lastname="Ковалев",
            firstname="Михаил",
            patronymic="Алексеевич",
            birthdate=date(1985, 4, 12),
            phone="+79140000001",
            email="kovalev@test.ru",
            education_level="Высшее",
            institute_name="ИрНИТУ",
            diploma_series_number="12345",
            diploma_date=date(2008, 6, 20)
        )
        p2 = Person(
            snils=r_snils2,
            lastname="Дмитриева",
            firstname="Елена",
            patronymic="Игоревна",
            birthdate=date(1990, 8, 25),
            phone="+79140000002",
            email="dmitrieva@test.ru",
            education_level="Высшее",
            institute_name="ИГУ",
            diploma_series_number="67890",
            diploma_date=date(2013, 6, 25)
        )
        db.session.add_all([p1, p2])
        db.session.flush()

        l1 = ApplicationListener(application_id=app.id, person_id=p1.id, position="Главный энергетик")
        l2 = ApplicationListener(application_id=app.id, person_id=p2.id, position="Начальник отдела кадров")
        db.session.add_all([l1, l2])
        db.session.flush()

        c1 = ListenerCourse(listener_id=l1.id, program_id=prog_go.id, start_date=date(2026, 12, 1), end_date=date(2026, 12, 10))
        c2 = ListenerCourse(listener_id=l2.id, program_id=prog_go.id, start_date=date(2026, 12, 1), end_date=date(2026, 12, 10))
        db.session.add_all([c1, c2])
        db.session.commit()

        # Проверяем расчет стоимости: fulltime_cat1 очно = 7060 руб. Для двоих = 14120 руб.
        price_num, price_str, price_words = DocxService.calculate_contract_price(app)
        self.assertEqual(price_num, 14120)
        self.assertEqual(price_str, "14 120")
        self.assertIn("четырнадцать тысяч", price_words)
        print(f"   [OK] Стоимость рассчитана корректно: {price_str} ({price_words})")

        # Генерируем Word документ
        stream, filename = DocxService.generate_contract_for_application(app)
        self.assertTrue(filename.startswith(f"Договор_{app.app_number}"))
        self.assertGreater(len(stream.getvalue()), 10000)
        print(f"   [OK] Документ успешно сгенерирован: {filename} (размер: {len(stream.getvalue())} байт)")

        # Проверяем содержимое сгенерированного документа
        doc = docx.Document(stream)
        all_text = " ".join([p.text for p in doc.paragraphs])
        self.assertIn("Северный Альянс", all_text)
        self.assertIn("Сергеева Виктора Николаевича", all_text)
        self.assertIn("Устава", all_text)
        self.assertIn("в количестве 2 человек", all_text)
        self.assertIn("14 120", all_text)
        self.assertIn("четырнадцать тысяч", all_text)
        print("   [OK] Шапка договора, пункты 1.2 и 3.2 содержат корректные значения")

        # Проверяем таблицу реквизитов (пункт 10)
        cell_req = doc.tables[0].cell(0, 1).text
        self.assertIn("Северный Альянс", cell_req)
        self.assertIn("3808123456", cell_req)
        self.assertIn("КПП 380801001", cell_req)
        self.assertNotIn("КПП КПП", cell_req)
        self.assertIn("Генеральный директор", cell_req)
        self.assertIn("В.Н. Сергеев", cell_req)
        print("   [OK] Таблица реквизитов (пункт 10) содержит реквизиты Заказчика (включая должность руководителя и корректный КПП)")

        # Проверяем таблицу слушателей в приложении
        t_listeners = doc.tables[1]
        self.assertEqual(len(t_listeners.rows), 3)  # 1 заголовок + 2 слушателя
        row1_text = " ".join([c.text for c in t_listeners.rows[1].cells])
        row2_text = " ".join([c.text for c in t_listeners.rows[2].cells])
        self.assertIn("Ковалев Михаил Алексеевич", row1_text)
        self.assertIn("Дмитриева Елена Игоревна", row2_text)
        self.assertIn("Главный энергетик", row1_text)
        self.assertIn("Начальник отдела кадров", row2_text)
        print("   [OK] Таблица приложения заполнена сведениями о 2 слушателях")

    def test_04_approval_workflow_with_contract_choice(self):
        """Проверка процесса одобрения с выбором прикреплять договор или нет."""
        print("\n4. Проверка процесса одобрения заявки с выбором договора:")

        import random
        r_snils = str(random.randint(10000000000, 99999999999))
        r_app_num = f"TEST-APPR-{random.randint(1000, 9999)}"

        prog_go = Program.query.filter_by(code="fulltime_cat1").first()

        app = Application(
            app_number=r_app_num,
            direction=TrainingDirection.GOCHS.value,
            study_form=StudyForm.OCHNO.value,
            status=ApplicationStatus.IN_REVIEW.value,
            has_contract=False,
            org_full_name="ООО «Тест Одобрения»",
            org_short_name="ООО «ТО»",
            inn="3808999999",
            kpp="380801001",
            ogrn="1023800000009",
            bank_name="ПАО Сбербанк",
            bik="042520607",
            account_number="40702810900000009999",
            boss_lastname="Петров",
            boss_firstname="Петр",
            boss_patronymic="Петрович",
            boss_position="Директор",
            boss_authority="Устава",
            legal_address="г. Иркутск, ул. Ленина, 1",
            actual_address="г. Иркутск, ул. Ленина, 1",
            phone="+7 (3952) 99-99-99",
            email="test_approve@irkutsk.ru",
            executor_fio="Петров П.П.",
            executor_position="Директор",
            executor_phone="+7 (3952) 99-99-99",
        )
        db.session.add(app)
        db.session.flush()

        p = Person(
            snils=r_snils,
            lastname="Смирнов",
            firstname="Алексей",
            patronymic="Иванович",
            birthdate=date(1992, 1, 15),
            phone="+79149999999",
            email="smirnov@test.ru",
            education_level="Высшее",
            institute_name="ИГУ",
            diploma_series_number="11111",
            diploma_date=date(2015, 6, 20)
        )
        db.session.add(p)
        db.session.flush()

        l = ApplicationListener(application_id=app.id, person_id=p.id, position="Инженер")
        db.session.add(l)
        db.session.flush()

        c = ListenerCourse(listener_id=l.id, program_id=prog_go.id, start_date=date(2026, 12, 1), end_date=date(2026, 12, 10))
        db.session.add(c)
        db.session.commit()

        # 4.1 Одобрение с прикреплением договора (attach_contract=1)
        res_approve_with = self.client.post(
            f"/applications/{app.id}/approve",
            data={"attach_contract": "1"},
            headers={"Host": "contractmaker.umcgochs.local"},
            follow_redirects=True
        )
        self.assertEqual(res_approve_with.status_code, 200)
        app_updated = Application.query.get(app.id)
        self.assertEqual(app_updated.status, ApplicationStatus.APPROVED.value)
        self.assertTrue(app_updated.has_contract)
        print("   [OK] Одобрение с attach_contract=1 установило has_contract=True")

        # Проверяем персональную страницу слушателя
        res_user_page = self.client.get(f"/apply/status/{app.secret_token}")
        self.assertEqual(res_user_page.status_code, 200)
        html_user = res_user_page.get_data(as_text=True)
        self.assertIn("Скачать договор (.docx)", html_user)
        self.assertIn(f"/apply/download_contract/{app.secret_token}", html_user)
        print("   [OK] На персональной странице заявителя отображается кнопка 'Скачать договор (.docx)'")

        # Проверяем скачивание договора заявителем
        res_contract_dl = self.client.get(f"/apply/download_contract/{app.secret_token}")
        self.assertEqual(res_contract_dl.status_code, 200)
        self.assertEqual(res_contract_dl.headers["Content-Type"], "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        print("   [OK] Эндпоинт /apply/download_contract/<token> успешно отдает .docx файл договора")

        # 4.2 Снятие прикрепления договора (ручной режим / нетиповой договор)
        res_toggle = self.client.post(
            f"/applications/{app.id}/toggle_contract",
            data={"attach_contract": "0"},
            headers={"Host": "contractmaker.umcgochs.local"},
            follow_redirects=True
        )
        self.assertEqual(res_toggle.status_code, 200)
        app_updated = Application.query.get(app.id)
        self.assertFalse(app_updated.has_contract)
        print("   [OK] Открепление договора установило has_contract=False")

        # На персональной странице заявителя кнопка скачивания договора должна исчезнуть
        res_user_page2 = self.client.get(f"/apply/status/{app.secret_token}")
        html_user2 = res_user_page2.get_data(as_text=True)
        self.assertNotIn(f"/apply/download_contract/{app.secret_token}", html_user2)
        print("   [OK] При has_contract=False кнопка договора отсутствует на странице заявителя")

        # Попытка прямого скачивания возвращает редирект с предупреждением
        res_contract_dl2 = self.client.get(f"/apply/download_contract/{app.secret_token}", follow_redirects=True)
        self.assertEqual(res_contract_dl2.status_code, 200)
        self.assertIn("Типовой договор для данной заявки не прикреплен", res_contract_dl2.get_data(as_text=True))
        print("   [OK] Прямой запрос к /apply/download_contract при has_contract=False корректно блокируется")

        # 4.3 Для договорного отдела договор ВСЕГДА доступен для скачивания
        res_internal_contract = self.client.get(
            f"/applications/{app.id}/contract",
            headers={"Host": "contractmaker.umcgochs.local"}
        )
        self.assertEqual(res_internal_contract.status_code, 200)
        self.assertEqual(res_internal_contract.headers["Content-Type"], "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        print("   [OK] Договорной отдел может скачать договор всегда (даже при has_contract=False)")

        # 4.4 Одобрение с attach_contract=0
        app.status = ApplicationStatus.IN_REVIEW.value
        db.session.commit()
        self.client.post(
            f"/applications/{app.id}/approve",
            data={"attach_contract": "0"},
            headers={"Host": "contractmaker.umcgochs.local"},
            follow_redirects=True
        )
        app_after_0 = Application.query.get(app.id)
        self.assertEqual(app_after_0.status, ApplicationStatus.APPROVED.value)
        self.assertFalse(app_after_0.has_contract)
        print("   [OK] Одобрение с attach_contract=0 оставляет has_contract=False")


if __name__ == "__main__":
    unittest.main()
