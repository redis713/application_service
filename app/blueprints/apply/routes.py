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

def get_program_choices(direction: str, study_form: str):
    """Возвращает список доступных программ для выбора в форме."""
    query = Program.query.filter_by(is_active=True)
    if direction in [d.value for d in TrainingDirection]:
        query = query.filter(Program.direction == direction)
    
    programs = query.order_by(Program.id).all()
    choices = [("", "Выберите категорию обучения")]
    for p in programs:
        choices.append((p.code, f"{p.title} ({p.hours} ч.)" if p.hours else p.title))
    return choices


@apply_bp.route("/<study_form>/<direction>", methods=["GET", "POST"])
def form_view(study_form: str, direction: str):
    # Валидация параметров URL
    valid_forms = [StudyForm.DISTANT.value, StudyForm.OCHNO.value]
    valid_directions = [d.value for d in TrainingDirection]

    if study_form not in valid_forms or direction not in valid_directions:
        flash("Некорректная форма или направление обучения", "danger")
        return redirect(url_for("main.index"))

    form = ApplicationForm()

    # Заполняем варианты программ для всех категорий
    choices = get_program_choices(direction, study_form)
    for student_form in form.students:
        for cat_form in student_form.student_categories:
            cat_form.category.choices = choices

    if form.validate_on_submit():
        try:
            # Извлекаем очищенные данные организации
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

            # Извлекаем очищенные данные слушателей
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
                    "student_categories": s_categories,
                })

            # Сохраняем черновик заявки
            application = ApplicationService.create_application_draft(
                org_data=org_data,
                students_data=students_data,
                direction=direction,
                study_form=study_form
            )

            flash(f"Заявка № {application.app_number} успешно сформирована!", "success")
            # Перенаправляем на страницу статуса и загрузки скана с флагом авто-скачивания docx
            return redirect(url_for("apply.status_view", token=application.secret_token, download="1"))

        except Exception as e:
            flash(f"Ошибка при сохранении заявки: {str(e)}", "danger")

    return render_template(
        "apply/form.html",
        form=form,
        study_form=study_form,
        direction=direction,
        study_form_label=StudyForm.label(study_form),
        direction_label=TrainingDirection.label(direction),
        program_choices=choices
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

    # Собираем данные организации из модели
    org = application.organization
    org_data = {
        "full_name": org.full_name,
        "short_name": org.short_name,
        "boss_lastname": org.boss_lastname,
        "boss_firstname": org.boss_firstname,
        "boss_patronymic": org.boss_patronymic,
        "boss_position": org.boss_position,
        "boss_authority": org.boss_authority,
        "ogrn": org.ogrn,
        "inn": org.inn,
        "kpp": org.kpp or "",
        "bank_name": org.bank_name,
        "account_number": org.account_number,
        "bik": org.bik,
        "actual_address": org.actual_address,
        "legal_address": org.legal_address,
        "phone": org.phone,
        "email": org.email,
        "executor_fio": org.executor_fio,
        "executor_position": org.executor_position,
        "executor_phone": org.executor_phone,
        "executor_email": org.executor_email,
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
            "courses": courses,
        })

    templates_dir = current_app.config["DOCX_TEMPLATES_FOLDER"]
    stream = DocxService.generate_docx_stream(
        org_data=org_data,
        listeners_data=listeners_data,
        study_form=application.study_form,
        templates_dir=templates_dir
    )

    clean_org = org.short_name.replace('"', '').replace("'", "").strip()
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
