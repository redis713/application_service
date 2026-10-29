import os
from flask import (
    render_template,
    redirect,
    url_for,
    flash,
    request,
    send_file,
    current_app,
    abort,
)
from app.blueprints.apply import apply_bp
from app.blueprints.apply.forms import ApplicationForm, ScanUploadForm
from app.constants import StudyForm, TrainingDirection, ApplicationStatus
from app.models.program import Program
from app.models.application import Application
from app.services.application_service import ApplicationService
from app.services.docx_service import DocxService

def get_programs_list(direction: str, study_form: str):
    """Возвращает список моделей Program для направления и формы обучения."""
    query = Program.query.filter_by(is_active=True)
    if direction in [d.value for d in TrainingDirection]:
        query = query.filter(Program.direction == direction)
    if study_form in [s.value for s in StudyForm]:
        query = query.filter(Program.study_form.in_([study_form, "both"]))
    return query.order_by(Program.id).all()


def get_program_choices(direction: str, study_form: str):
    """Возвращает список доступных программ для выбора в форме с учетом направления и формы обучения."""
    programs = get_programs_list(direction, study_form)
    choices = [("", "Выберите категорию обучения")]
    for p in programs:
        choices.append((p.code, f"{p.title} ({p.hours} ч.)" if p.hours else p.title))
    return choices


def add_field_error(field, message: str):
    """Безопасно добавляет ошибку валидации к полю формы WTForms."""
    field.errors = list(field.errors or ()) + [message]


def extract_form_data(form: ApplicationForm):
    """Извлекает нормализованные словари данных организации и слушателей из формы."""
    org_data = {
        "organization_full_name": form.organization_full_name.data,
        "organization_short_name": form.organization_short_name.data,
        "inn": form.inn.data,
        "kpp": form.kpp.data,
        "ogrn": form.ogrn.data,
        "bank_name": form.bank_name.data,
        "bik": form.bik.data,
        "rasch_schot": form.rasch_schot.data,
        "boss_lastname": form.boss_lastname.data,
        "boss_firstname": form.boss_firstname.data,
        "boss_patronymic": form.boss_patronymic.data,
        "doljnost_boss": form.doljnost_boss.data,
        "polnamochia_boss": form.polnamochia_boss.data,
        "yur_address": form.yur_address.data,
        "fakt_address": form.fakt_address.data,
        "telephone": form.telephone.data,
        "email": form.email.data,
        "fio_executor": form.fio_executor.data,
        "doljnost_executor": form.doljnost_executor.data,
        "telephone_executor": form.telephone_executor.data,
    }

    students_data = []
    for s_form in form.students:
        s_categories = []
        for c_form in s_form.student_categories:
            s_categories.append({
                "category": c_form.category.data,
                "start_date": c_form.start_date.data,
                "end_date": c_form.end_date.data,
            })

        students_data.append({
            "student_lastname": s_form.student_lastname.data,
            "student_firstname": s_form.student_firstname.data,
            "student_patronymic": s_form.student_patronymic.data,
            "student_birthdate": s_form.student_birthdate.data,
            "citizenship": s_form.citizenship.data,
            "student_position": s_form.student_position.data,
            "education": s_form.education.data,
            "institute_name": s_form.institute_name.data,
            "diploma_seriesnumber": s_form.diploma_seriesnumber.data,
            "diploma_date": s_form.diploma_date.data,
            "diploma_lastname": s_form.diploma_lastname.data,
            "snils": s_form.snils.data,
            "student_telephone": s_form.student_telephone.data,
            "student_email": s_form.student_email.data,
            "diploma_delivery": s_form.diploma_delivery.data,
            "delivery_address": s_form.delivery_address.data,
            "fire_safety_document_type": s_form.fire_safety_document_type.data,
            "fire_institution": s_form.fire_institution.data,
            "fire_series": s_form.fire_series.data,
            "fire_number": s_form.fire_number.data,
            "fire_date": s_form.fire_date.data,
            "student_categories": s_categories,
        })

    return org_data, students_data


@apply_bp.route("/programs/<study_form>/<direction>")
def programs_view(study_form: str, direction: str):
    """Страница выбора конкретной категории перед переходом к заполнению бланка."""
    valid_forms = [StudyForm.DISTANT.value, StudyForm.OCHNO.value]
    valid_directions = [d.value for d in TrainingDirection]

    if study_form not in valid_forms or direction not in valid_directions:
        flash("Некорректная форма или направление обучения", "danger")
        return redirect(url_for("main.index"))

    programs = get_programs_list(direction, study_form)
    return render_template(
        "apply/programs.html",
        study_form=study_form,
        direction=direction,
        study_form_label=StudyForm.label(study_form),
        direction_label=TrainingDirection.label(direction),
        programs=programs
    )


@apply_bp.route("/<study_form>/<direction>", methods=["GET", "POST"])
def form_view(study_form: str, direction: str):
    # Валидация параметров URL
    valid_forms = [StudyForm.DISTANT.value, StudyForm.OCHNO.value]
    valid_directions = [d.value for d in TrainingDirection]

    if study_form not in valid_forms or direction not in valid_directions:
        flash("Некорректная форма или направление обучения", "danger")
        return redirect(url_for("main.index"))

    # Направления, где в заявке обязательно должна быть одна выбранная программа
    needs_intermediate_selection = (
        (study_form == StudyForm.OCHNO.value and direction == TrainingDirection.GOCHS.value)
        or direction in [TrainingDirection.FIRE.value, TrainingDirection.CALL112.value]
    )

    category_code = request.args.get("category") or request.form.get("fixed_category_code")

    # Если требуется предварительный выбор, но категория не передана в GET — перенаправляем на выбор
    if needs_intermediate_selection and not category_code and request.method == "GET":
        return redirect(url_for("apply.programs_view", study_form=study_form, direction=direction))

    fixed_program = None
    if category_code:
        fixed_program = Program.query.filter_by(code=category_code).first()
    elif direction == TrainingDirection.ANTITERROR.value:
        fixed_program = Program.query.filter_by(direction=direction, is_active=True).first()
    elif direction == TrainingDirection.SPECIALIST.value:
        fixed_program = Program.query.filter_by(direction=direction, is_active=True).first()

    form = ApplicationForm()
    choices = get_program_choices(direction, study_form)
    if fixed_program:
        fixed_tuple = (fixed_program.code, f"{fixed_program.title} ({fixed_program.hours} ч.)")
        if fixed_tuple not in choices:
            choices.append(fixed_tuple)

    for student_form in form.students:
        for cat_form in student_form.student_categories:
            cat_form.category.choices = choices
            if fixed_program and not cat_form.category.data:
                cat_form.category.data = fixed_program.code

    if request.method == "POST":
        is_valid = form.validate_on_submit()
        if direction == TrainingDirection.FIRE.value:
            for s_form in form.students:
                if not s_form.fire_safety_document_type.data:
                    add_field_error(s_form.fire_safety_document_type, "Выберите основание пожарного образования.")
                    is_valid = False
                if not s_form.fire_series.data or not s_form.fire_series.data.strip():
                    add_field_error(s_form.fire_series, "Укажите серию документа.")
                    is_valid = False
                if not s_form.fire_number.data or not s_form.fire_number.data.strip():
                    add_field_error(s_form.fire_number, "Укажите номер документа.")
                    is_valid = False
                if not s_form.fire_date.data:
                    add_field_error(s_form.fire_date, "Укажите дату выдачи документа.")
                    is_valid = False

        if is_valid:
            try:
                org_data, students_data = extract_form_data(form)

                # Если программа зафиксирована, гарантируем ее установку для всех слушателей
                if fixed_program:
                    for s in students_data:
                        for c in s.get("student_categories", []):
                            if not c.get("category"):
                                c["category"] = fixed_program.code

                # Сохраняем черновик заявки
                application = ApplicationService.create_application_draft(
                    org_data=org_data,
                    students_data=students_data,
                    direction=direction,
                    study_form=study_form
                )

                flash(f"Заявка № {application.app_number} успешно сформирована!", "success")
                return redirect(url_for("apply.status_view", token=application.secret_token, download="1"))

            except Exception as e:
                flash(f"Ошибка при сохранении заявки: {str(e)}", "danger")

    return render_template(
        "apply/form.html",
        form=form,
        is_edit=False,
        study_form=study_form,
        direction=direction,
        study_form_label=StudyForm.label(study_form),
        direction_label=TrainingDirection.label(direction),
        program_choices=choices,
        fixed_program=fixed_program
    )


@apply_bp.route("/edit/<token>", methods=["GET", "POST"])
def edit_view(token: str):
    """Маршрут редактирования заявки: позволяет вернуться с шага 2 на шаг 1 и скорректировать данные."""
    application = Application.query.filter_by(secret_token=token).first_or_404()
    choices = get_program_choices(application.direction, application.study_form)

    # Определяем фиксированную программу (если заявка была создана по одной категории)
    fixed_program = None
    if application.direction in [TrainingDirection.ANTITERROR.value, TrainingDirection.SPECIALIST.value]:
        fixed_program = Program.query.filter_by(direction=application.direction, is_active=True).first()
    elif (
        (application.study_form == StudyForm.OCHNO.value and application.direction == TrainingDirection.GOCHS.value)
        or application.direction in [TrainingDirection.FIRE.value, TrainingDirection.CALL112.value]
    ):
        if application.listeners and application.listeners[0].courses:
            fixed_program = application.listeners[0].courses[0].program

    if fixed_program:
        fixed_tuple = (fixed_program.code, f"{fixed_program.title} ({fixed_program.hours} ч.)")
        if fixed_tuple not in choices:
            choices.append(fixed_tuple)

    if request.method == "POST":
        form = ApplicationForm()
        for student_form in form.students:
            for cat_form in student_form.student_categories:
                cat_form.category.choices = choices

        is_valid = form.validate_on_submit()
        if application.direction == TrainingDirection.FIRE.value:
            for s_form in form.students:
                if not s_form.fire_safety_document_type.data:
                    add_field_error(s_form.fire_safety_document_type, "Выберите основание пожарного образования.")
                    is_valid = False
                if not s_form.fire_series.data or not s_form.fire_series.data.strip():
                    add_field_error(s_form.fire_series, "Укажите серию документа.")
                    is_valid = False
                if not s_form.fire_number.data or not s_form.fire_number.data.strip():
                    add_field_error(s_form.fire_number, "Укажите номер документа.")
                    is_valid = False
                if not s_form.fire_date.data:
                    add_field_error(s_form.fire_date, "Укажите дату выдачи документа.")
                    is_valid = False

        if is_valid:
            try:
                org_data, students_data = extract_form_data(form)
                if fixed_program:
                    for s in students_data:
                        for c in s.get("student_categories", []):
                            if not c.get("category"):
                                c["category"] = fixed_program.code

                ApplicationService.update_application_draft(
                    token=token,
                    org_data=org_data,
                    students_data=students_data
                )
                flash(f"Заявка № {application.app_number} успешно обновлена! Сформирован обновленный бланк.", "success")
                return redirect(url_for("apply.status_view", token=token, download="1"))
            except Exception as e:
                current_app.logger.error(f"Error updating application {token}: {e}", exc_info=True)
                flash(f"Ошибка при обновлении заявки: {str(e)}", "danger")
    else:
        # GET-запрос: предзаполняем форму сохраненными данными из БД
        init_data = ApplicationService.get_application_form_data(application)
        form = ApplicationForm(data=init_data)
        for student_form in form.students:
            for cat_form in student_form.student_categories:
                cat_form.category.choices = choices

    return render_template(
        "apply/form.html",
        form=form,
        is_edit=True,
        application=application,
        study_form=application.study_form,
        direction=application.direction,
        study_form_label=StudyForm.label(application.study_form),
        direction_label=TrainingDirection.label(application.direction),
        program_choices=choices,
        fixed_program=fixed_program
    )


@apply_bp.route("/status/<token>", methods=["GET", "POST"])
def status_view(token: str):
    application = Application.query.filter_by(secret_token=token).first_or_404()
    upload_form = ScanUploadForm()

    if upload_form.validate_on_submit():
        try:
            ApplicationService.attach_signed_scan(
                token=token,
                file_storage=upload_form.scan_file.data,
                upload_folder=current_app.config["SCANS_FOLDER"]
            )
            flash("Скан заявления успешно прикреплен! Ваша заявка передана в учебный отдел на обработку.", "success")
            return redirect(url_for("apply.success_view", token=token))
        except Exception as e:
            flash(f"Ошибка при загрузке скана: {str(e)}", "danger")

    auto_download = request.args.get("download") == "1"

    return render_template(
        "apply/upload_scan.html",
        application=application,
        upload_form=upload_form,
        auto_download=auto_download
    )


@apply_bp.route("/download/<token>")
def download_docx(token: str):
    application = Application.query.filter_by(secret_token=token).first_or_404()

    # Собираем данные организации из заявки
    org_data = {
        "full_name": application.org_full_name,
        "short_name": application.org_short_name,
        "boss_lastname": application.boss_lastname,
        "boss_firstname": application.boss_firstname,
        "boss_patronymic": application.boss_patronymic,
        "boss_position": application.boss_position,
        "boss_authority": application.boss_authority,
        "ogrn": application.ogrn,
        "inn": application.inn,
        "kpp": application.kpp or "",
        "bank_name": application.bank_name,
        "account_number": application.account_number,
        "bik": application.bik,
        "actual_address": application.actual_address,
        "legal_address": application.legal_address,
        "phone": application.phone,
        "email": application.email,
        "executor_fio": application.executor_fio,
        "executor_position": application.executor_position,
        "executor_phone": application.executor_phone,
        "executor_email": application.executor_email,
    }

    # Собираем данные слушателей
    listeners_data = []
    for l in application.listeners:
        p = l.person
        courses = []
        for c in l.courses:
            courses.append({
                "title": c.program.title if c.program else "",
                "start_date": c.start_date,
                "end_date": c.end_date,
            })

        listeners_data.append({
            "lastname": p.lastname,
            "firstname": p.firstname,
            "patronymic": p.patronymic,
            "birthdate": p.birthdate,
            "citizenship": p.citizenship,
            "education_level": p.education_level,
            "institute_name": p.institute_name,
            "diploma_series_number": p.diploma_series_number,
            "diploma_date": p.diploma_date,
            "diploma_lastname": p.diploma_lastname,
            "snils": p.formatted_snils,
            "position": l.position,
            "phone": p.phone,
            "email": p.email,
            "diploma_delivery": l.diploma_delivery,
            "delivery_address": l.delivery_address or "",
            "fire_safety_document_type": p.fire_safety_document_type,
            "fire_institution": p.fire_institution,
            "fire_series": p.fire_series,
            "fire_number": p.fire_number,
            "fire_date": p.fire_date,
            "courses": courses,
        })

    templates_dir = current_app.config["DOCX_TEMPLATES_FOLDER"]
    stream = DocxService.generate_docx_stream(
        org_data=org_data,
        listeners_data=listeners_data,
        study_form=application.study_form,
        direction=application.direction,
        templates_dir=templates_dir
    )

    clean_org = application.org_short_name.replace('"', '').replace("'", "").strip()
    download_filename = f"Заявка_{application.app_number}_{clean_org}.docx"

    return send_file(
        stream,
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        as_attachment=True,
        download_name=download_filename
    )


@apply_bp.route("/success/<token>")
def success_view(token: str):
    application = Application.query.filter_by(secret_token=token).first_or_404()
    return render_template("apply/success.html", application=application)
