from app.models.program import Program
from app.extensions import db

PROGRAMS_DATA = [
    {"code": "fulltime_cat1", "title": "Руководители органов местного самоуправления", "hours": 36, "direction": "gochs", "study_form": "both"},
    {"code": "fulltime_cat2", "title": "Руководители организаций", "hours": 36, "direction": "gochs", "study_form": "both"},
    {"code": "fulltime_cat3", "title": "Руководители (работники) органов, уполномоченных на решение задач в области защиты населения и территорий от чрезвычайных ситуаций и (или) гражданской обороны муниципальных образований", "hours": 36, "direction": "gochs", "study_form": "both"},
    {"code": "fulltime_cat4", "title": "Руководители (работники) структурных подразделений, уполномоченных на решение задач в области защиты населения и территорий от чрезвычайных ситуаций и (или) гражданской обороны в организациях", "hours": 36, "direction": "gochs", "study_form": "both"},
    {"code": "fulltime_cat5", "title": "Члены комиссии по предупреждению и ликвидации чрезвычайных ситуаций и обеспечению пожарной безопасности Иркутской области", "hours": 36, "direction": "gochs", "study_form": "both"},
    {"code": "fulltime_cat6", "title": "Председатели и члены комиссий по предупреждению и ликвидации чрезвычайных ситуаций и обеспечению пожарной безопасности муниципальных образований", "hours": 36, "direction": "gochs", "study_form": "both"},
    {"code": "fulltime_cat7", "title": "Председатели и члены комиссий по предупреждению и ликвидации чрезвычайных ситуаций и обеспечению пожарной безопасности организаций", "hours": 36, "direction": "gochs", "study_form": "both"},
    {"code": "fulltime_cat8", "title": "Руководители и специалисты единых дежурно-диспетчерских служб муниципальных образований", "hours": 36, "direction": "gochs", "study_form": "both"},
    {"code": "fulltime_cat9", "title": "Руководители и специалисты дежурно-диспетчерских служб организаций", "hours": 36, "direction": "gochs", "study_form": "both"},
    {"code": "fulltime_cat10", "title": "Должностные лица, входящие в состав эвакуационной комиссии Иркутской области", "hours": 36, "direction": "gochs", "study_form": "both"},
    {"code": "fulltime_cat11", "title": "Должностные лица, входящие в составы эвакуационных комиссий органов местного самоуправления", "hours": 36, "direction": "gochs", "study_form": "both"},
    {"code": "fulltime_cat12", "title": "Должностные лица, входящие в составы эвакоприемных комиссий органов местного самоуправления", "hours": 36, "direction": "gochs", "study_form": "both"},
    {"code": "fulltime_cat13", "title": "Должностные лица, входящие в составы сборных и приемных эвакуационных пунктов, промежуточных пунктов эвакуации органов местного самоуправления", "hours": 36, "direction": "gochs", "study_form": "both"},
    {"code": "fulltime_cat14", "title": "Должностные лица, входящие в составы эвакуационных комиссий организаций", "hours": 36, "direction": "gochs", "study_form": "both"},
    {"code": "fulltime_cat15", "title": "Должностные лица, входящие в составы сборных и приемных эвакуационных пунктов, промежуточных пунктов эвакуации организаций", "hours": 36, "direction": "gochs", "study_form": "both"},
    {"code": "fulltime_cat16", "title": "Должностные лица, входящие в состав комиссии по повышению устойчивого функционирования объектов экономики Иркутской области", "hours": 36, "direction": "gochs", "study_form": "both"},
    {"code": "fulltime_cat17", "title": "Должностные лица, входящие в составы комиссий по повышению устойчивости функционирования органов местного самоуправления", "hours": 36, "direction": "gochs", "study_form": "both"},
    {"code": "fulltime_cat18", "title": "Должностные лица, входящие в составы комиссий по повышению устойчивости функционирования организаций, отнесенных к категориям по гражданской обороне, а также продолжающих работу в военное время", "hours": 36, "direction": "gochs", "study_form": "both"},
    {"code": "fulltime_cat19", "title": "Руководители спасательных служб муниципальных образований", "hours": 36, "direction": "gochs", "study_form": "both"},
    {"code": "fulltime_cat20", "title": "Руководители спасательных служб, нештатных формирований гражданской обороны, нештатных аварийно-спасательных формирований организаций", "hours": 36, "direction": "gochs", "study_form": "both"},
    {"code": "fulltime_cat21", "title": "Преподаватели учебного предмета «Основы безопасности и защиты Родины»", "hours": 36, "direction": "gochs", "study_form": "both"},
    {"code": "fulltime_cat22", "title": "Преподаватели дисциплины «Безопасность жизнедеятельности»", "hours": 36, "direction": "gochs", "study_form": "both"},
    {"code": "fulltime_cat23", "title": "Руководители, педагогические работники и инструкторы гражданской обороны курсов гражданской обороны муниципальных образований", "hours": 36, "direction": "gochs", "study_form": "both"},
    {"code": "fulltime_cat24", "title": "Руководители, инструкторы гражданской обороны, консультанты учебно-консультационных пунктов муниципальных образований", "hours": 36, "direction": "gochs", "study_form": "both"},
    {"code": "fulltime_cat25", "title": "Руководители и педагогические работники, осуществляющие обучение по дополнительным профессиональным программам в области гражданской обороны, организаций, осуществляющих образовательную деятельность по дополнительным профессиональным программам в области гражданской обороны", "hours": 36, "direction": "gochs", "study_form": "both"},
    {"code": "fulltime_cat26", "title": "Руководители занятий по ГОЧС", "hours": 36, "direction": "gochs", "study_form": "both"},
    {"code": "fulltime_fire_cat27", "title": "ДПП повышения квалификации для руководителей организаций, лиц, назначенных руководителем организации ответственными за обеспечение пожарной безопасности на объектах защиты, в которых могут одновременно находиться 50 и более человек, объектах защиты, отнесенных к категориям повышенной взрывопожароопасности, взрывопожароопасности, пожароопасности (30 часов)", "hours": 30, "direction": "fire", "study_form": "both"},
    {"code": "fulltime_fire_cat28", "title": "ДПП повышения квалификации для руководителей эксплуатирующих и управляющих организаций, осуществляющих хозяйственную деятельность, связанную с обеспечением пожарной безопасности на объектах защиты, лиц, назначенных ими ответственными за обеспечение пожарной безопасности (20 часов)", "hours": 20, "direction": "fire", "study_form": "both"},
    {"code": "fulltime_fire_cat29", "title": "ДПП повышения квалификации для ответственных должностных лиц, занимающих должности главных специалистов технического и производственного профиля, должностных лиц, исполняющих их обязанности, на объектах защиты, в которых могут одновременно находиться 50 и более человек, объектах защиты, отнесенных к категориям повышенной взрывопожароопасности, взрывопожароопасности, пожароопасности (30 часов)", "hours": 30, "direction": "fire", "study_form": "both"},
    {"code": "fulltime_fire_cat30", "title": "ДПП повышения квалификации для лиц, на которых возложена трудовая функция по проведению противопожарного инструктажа (18 часов)", "hours": 18, "direction": "fire", "study_form": "both"},
    {"code": "fulltime_fire_cat31", "title": "ДПП профессиональной переподготовки для получения квалификации \"Специалист по пожарной профилактике\" (250 часов)", "hours": 250, "direction": "fire", "study_form": "ochno"},
    {"code": "fulltime_cat32", "title": "ДПП профессиональной переподготовки операторского персонала системы обеспечения вызова экстренных оперативных служб по единому номеру «112» для получения квалификации «Специалист по приему и обработке экстренных вызовов» (250 часов)", "hours": 250, "direction": "112", "study_form": "ochno"},
    {"code": "fulltime_cat33", "title": "ДПП повышения квалификации «Подготовка операторского персонала системы обеспечения вызова экстренных оперативных служб по единому номеру «112» (76 часов)", "hours": 76, "direction": "112", "study_form": "ochno"},
    {"code": "fulltime_cat34", "title": "ДПП повышения квалификации «Подготовка персонала дежурно-диспетчерских служб в рамках функционирования системы обеспечения вызова экстренных оперативных служб по единому номеру «112» (40 часов)", "hours": 40, "direction": "112", "study_form": "ochno"},
    {"code": "antiterror", "title": "ДПП повышения квалификации «Антитеррористическая защищенность» (36 часов)", "hours": 36, "direction": "antiterror", "study_form": "distant"},
    {"code": "specialist_go", "title": "ДПП профессиональной переподготовки «Специалист по гражданской обороне» (250 часов)", "hours": 250, "direction": "specialist", "study_form": "ochno"},
]

def ensure_schema_updates():
    """Проверяет и обновляет схему таблиц при необходимости (миграция организации в заявку, даты в DATE)."""
    try:
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        table_names = inspector.get_table_names()

        # 1. Обновление дат в таблице persons (diploma_date, fire_date -> DATE)
        if "persons" in table_names:
            columns = {col["name"].lower(): str(col["type"]).upper() for col in inspector.get_columns("persons")}
            from datetime import datetime

            for date_col in ("diploma_date", "fire_date"):
                col_type = columns.get(date_col, "")
                if "VARCHAR" in col_type or "CHAR" in col_type:
                    rows = db.session.execute(db.text(f"SELECT id, {date_col} FROM persons WHERE {date_col} IS NOT NULL")).fetchall()
                    for r_id, d_val in rows:
                        valid_date = None
                        if d_val:
                            for fmt in ("%Y-%m-%d", "%d.%m.%Y"):
                                try:
                                    valid_date = datetime.strptime(str(d_val).strip(), fmt).date()
                                    break
                                except ValueError:
                                    pass
                        db.session.execute(
                            db.text(f"UPDATE persons SET {date_col} = :d WHERE id = :id"),
                            {"d": valid_date, "id": r_id}
                        )
                    db.session.commit()
                    db.session.execute(db.text(f"ALTER TABLE persons MODIFY COLUMN {date_col} DATE NULL"))
                    db.session.commit()

        # 2. Перенос данных организации непосредственно в таблицу applications
        if "applications" in table_names:
            app_cols = [c["name"].lower() for c in inspector.get_columns("applications")]
            if "org_full_name" not in app_cols:
                cols_to_add = [
                    "org_full_name VARCHAR(500) NULL",
                    "org_short_name VARCHAR(255) NULL",
                    "inn VARCHAR(12) NULL",
                    "kpp VARCHAR(9) NULL",
                    "ogrn VARCHAR(15) NULL",
                    "bank_name VARCHAR(255) NULL",
                    "bik VARCHAR(9) NULL",
                    "account_number VARCHAR(30) NULL",
                    "boss_lastname VARCHAR(100) NULL",
                    "boss_firstname VARCHAR(100) NULL",
                    "boss_patronymic VARCHAR(100) NULL",
                    "boss_position VARCHAR(255) NULL",
                    "boss_authority VARCHAR(255) NULL",
                    "legal_address VARCHAR(500) NULL",
                    "actual_address VARCHAR(500) NULL",
                    "phone VARCHAR(50) NULL",
                    "email VARCHAR(100) NULL",
                    "executor_fio VARCHAR(255) NULL",
                    "executor_position VARCHAR(255) NULL",
                    "executor_phone VARCHAR(50) NULL",
                    "executor_email VARCHAR(100) NULL",
                    "last_edited_by VARCHAR(100) NULL",
                ]
                for col_def in cols_to_add:
                    db.session.execute(db.text(f"ALTER TABLE applications ADD COLUMN {col_def}"))
                db.session.commit()

            if "organizations" in table_names and "organization_id" in app_cols:
                copy_sql = """
                    UPDATE applications a
                    JOIN organizations o ON a.organization_id = o.id
                    SET a.org_full_name = o.full_name,
                        a.org_short_name = o.short_name,
                        a.inn = o.inn,
                        a.kpp = o.kpp,
                        a.ogrn = o.ogrn,
                        a.bank_name = o.bank_name,
                        a.bik = o.bik,
                        a.account_number = o.account_number,
                        a.boss_lastname = o.boss_lastname,
                        a.boss_firstname = o.boss_firstname,
                        a.boss_patronymic = o.boss_patronymic,
                        a.boss_position = o.boss_position,
                        a.boss_authority = o.boss_authority,
                        a.legal_address = o.legal_address,
                        a.actual_address = o.actual_address,
                        a.phone = o.phone,
                        a.email = o.email,
                        a.executor_fio = o.executor_fio,
                        a.executor_position = o.executor_position,
                        a.executor_phone = o.executor_phone,
                        a.executor_email = o.executor_email
                """
                db.session.execute(db.text(copy_sql))
                db.session.commit()

                # Удаление внешних ключей на organization_id
                for fk in inspector.get_foreign_keys("applications"):
                    if "organization_id" in fk.get("constrained_columns", []):
                        db.session.execute(db.text(f"ALTER TABLE applications DROP FOREIGN KEY {fk['name']}"))
                        db.session.commit()

                # Удаление колонки organization_id
                db.session.execute(db.text("ALTER TABLE applications DROP COLUMN organization_id"))
                db.session.commit()

                # Удаление старой таблицы organizations
                db.session.execute(db.text("DROP TABLE organizations"))
                db.session.commit()
    except Exception:
        db.session.rollback()


def seed_programs():
    """Заполняет или обновляет базу данных утвержденными программами обучения."""
    ensure_schema_updates()
    # Удаляем устаревшие программы-заглушки, если они присутствуют
    Program.query.filter(Program.code.in_(["distance_cat1", "distance_cat2", "distance_cat3"])).delete(synchronize_session=False)

    count = 0
    for p_data in PROGRAMS_DATA:
        prog = Program.query.filter_by(code=p_data["code"]).first()
        if not prog:
            prog = Program(
                code=p_data["code"],
                title=p_data["title"],
                hours=p_data["hours"],
                direction=p_data["direction"],
                study_form=p_data["study_form"],
                is_active=True
            )
            db.session.add(prog)
            count += 1
        else:
            prog.title = p_data["title"]
            prog.hours = p_data["hours"]
            prog.direction = p_data["direction"]
            prog.study_form = p_data["study_form"]
    db.session.commit()
    return count
