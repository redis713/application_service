import os
from flask import (
    render_template,
    request,
    redirect,
    url_for,
    flash,
    send_file,
    abort,
    current_app,
)
from sqlalchemy import or_, func
from app.blueprints.internal import internal_bp
from app.utils.host_helpers import is_internal_request
from app.models.application import Application, ApplicationListener
from app.models.person import Person
from app.constants import (
    ApplicationStatus,
    StudyForm,
    TrainingDirection,
    FIRE_DOCUMENT_LABELS,
)
from app.services.docx_service import DocxService
from app.services.application_service import ApplicationService
from app.extensions import db


@internal_bp.before_request
def require_internal_access():
    """
    Ограничивает доступ к служебному разделу:
    Разрешено только при обращении через внутренний домен (contractmaker.umcgochs.local)
    или во внутренней сети. Внешние запросы из интернета получают HTTP 404 Not Found.
    """
    if not is_internal_request():
        abort(404)


@internal_bp.route("")
@internal_bp.route("/")
def applications_list():
    """
    Реестр всех заявок для сотрудников:
    поиск, фильтрация по статусу, направлению, форме обучения, наличию скана,
    статистические сводки и пагинация.
    """
    query = Application.query

    # Параметры фильтрации и поиска
    q = (request.args.get("q") or "").strip()
    status = (request.args.get("status") or "").strip()
    direction = (request.args.get("direction") or "").strip()
    study_form = (request.args.get("study_form") or "").strip()
    scan = (request.args.get("scan") or "").strip()

    if q:
        q_term = f"%{q}%"
        query = query.filter(
            or_(
                Application.app_number.ilike(q_term),
                Application.org_short_name.ilike(q_term),
                Application.org_full_name.ilike(q_term),
                Application.inn.ilike(q_term),
                Application.executor_fio.ilike(q_term),
                Application.listeners.any(
                    ApplicationListener.person.has(
                        or_(
                            Person.lastname.ilike(q_term),
                            Person.firstname.ilike(q_term),
                            Person.snils.ilike(q_term),
                        )
                    )
                ),
            )
        )

    if status == ApplicationStatus.IN_REVIEW.value:
        query = query.filter(Application.status.in_([ApplicationStatus.IN_REVIEW.value, ApplicationStatus.DRAFT.value]))
    elif status:
        query = query.filter(Application.status == status)

    if direction:
        query = query.filter(Application.direction == direction)

    if study_form:
        query = query.filter(Application.study_form == study_form)

    if scan == "with_scan":
        query = query.filter(Application.signed_scan_path.isnot(None), Application.signed_scan_path != "")
    elif scan == "no_scan":
        query = query.filter(or_(Application.signed_scan_path.is_(None), Application.signed_scan_path == ""))

    # Сортировка: сначала самые новые
    query = query.order_by(Application.created_at.desc(), Application.id.desc())

    page = request.args.get("page", 1, type=int)
    per_page = 20
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    # Сводная статистика
    stats = {
        "total": Application.query.count(),
        "in_review": Application.query.filter(Application.status.in_([ApplicationStatus.IN_REVIEW.value, ApplicationStatus.DRAFT.value])).count(),
        "approved": Application.query.filter_by(status=ApplicationStatus.APPROVED.value).count(),
        "correction": Application.query.filter_by(status=ApplicationStatus.NEEDS_CORRECTION.value).count(),
        "submitted": Application.query.filter_by(status=ApplicationStatus.SUBMITTED.value).count(),
        "accepted": Application.query.filter_by(status=ApplicationStatus.ACCEPTED.value).count(),
        "total_students": db.session.query(func.count(ApplicationListener.id)).scalar() or 0,
    }

    statuses = [(s.value, ApplicationStatus.label(s.value)) for s in ApplicationStatus]
    directions = [(d.value, TrainingDirection.label(d.value)) for d in TrainingDirection]
    study_forms = [(sf.value, StudyForm.label(sf.value)) for sf in StudyForm]

    current_filters = {
        "q": q,
        "status": status,
        "direction": direction,
        "study_form": study_form,
        "scan": scan,
    }

    return render_template(
        "internal/applications_list.html",
        pagination=pagination,
        applications=pagination.items,
        stats=stats,
        statuses=statuses,
        directions=directions,
        study_forms=study_forms,
        current_filters=current_filters,
    )


@internal_bp.route("/<int:app_id>")
def application_detail(app_id: int):
    """
    Детальный просмотр заявки:
    все реквизиты организации, руководитель, ответственный исполнитель,
    список слушателей со сведениями для ФИС ФРДО и курсами, прикрепленный скан заявления.
    """
    application = Application.query.get_or_404(app_id)

    scan_exists = bool(
        application.signed_scan_path and os.path.exists(application.signed_scan_path)
    )

    scan_size_str = ""
    scan_ext = ""
    if scan_exists:
        try:
            size_bytes = os.path.getsize(application.signed_scan_path)
            if size_bytes < 1024 * 1024:
                scan_size_str = f"{size_bytes / 1024:.1f} КБ"
            else:
                scan_size_str = f"{size_bytes / (1024 * 1024):.2f} МБ"
            scan_ext = application.signed_scan_path.rsplit(".", 1)[-1].lower() if "." in application.signed_scan_path else ""
        except Exception:
            pass

    return render_template(
        "internal/application_detail.html",
        application=application,
        scan_exists=scan_exists,
        scan_size_str=scan_size_str,
        scan_ext=scan_ext,
        FIRE_DOCUMENT_LABELS=FIRE_DOCUMENT_LABELS,
    )


@internal_bp.route("/<int:app_id>/docx")
def download_application_docx(app_id: int):
    """
    Скачивание сгенерированного официального заявления в формате Microsoft Word (.docx).
    """
    application = Application.query.get_or_404(app_id)

    templates_dir = current_app.config["DOCX_TEMPLATES_FOLDER"]
    stream, download_filename = DocxService.generate_docx_for_application(
        application=application,
        templates_dir=templates_dir
    )

    return send_file(
        stream,
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        as_attachment=True,
        download_name=download_filename,
    )


@internal_bp.route("/<int:app_id>/scan")
def view_application_scan(app_id: int):
    """
    Просмотр или скачивание прикрепленного скана заявления с подписью и печатью.
    Если передан параметр ?download=1 — файл отдается как вложение.
    Иначе — inline в браузере (для удобного быстрого просмотра PDF или картинок).
    """
    application = Application.query.get_or_404(app_id)

    if not application.signed_scan_path or not os.path.exists(application.signed_scan_path):
        flash("Скан-копия заявления еще не прикреплена заявителем или файл отсутствует на сервере.", "warning")
        return redirect(url_for("internal.application_detail", app_id=app_id))

    ext = application.signed_scan_path.rsplit(".", 1)[-1].lower() if "." in application.signed_scan_path else ""
    mime_map = {
        "pdf": "application/pdf",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "tif": "image/tiff",
        "tiff": "image/tiff",
    }
    mimetype = mime_map.get(ext, "application/octet-stream")
    as_attachment = request.args.get("download") == "1"
    download_name = application.signed_scan_filename or f"scan_{application.app_number}.{ext}"

    return send_file(
        application.signed_scan_path,
        mimetype=mimetype,
        as_attachment=as_attachment,
        download_name=download_name,
    )


@internal_bp.route("/<int:app_id>/approve", methods=["POST"])
def approve_application(app_id: int):
    """Одобрение заявки договорным отделом."""
    try:
        application = ApplicationService.approve_application(app_id, reviewer="договорной отдел")
        flash(f"Заявка № {application.app_number} успешно одобрена! Теперь заявитель может загрузить подписанный скан заявления.", "success")
    except Exception as e:
        current_app.logger.error(f"Error approving application #{app_id}: {e}", exc_info=True)
        flash(f"Ошибка при одобрении заявки: {str(e)}", "danger")

    return redirect(url_for("internal.application_detail", app_id=app_id))


@internal_bp.route("/<int:app_id>/return_for_correction", methods=["POST"])
def return_application(app_id: int):
    """Возврат заявки заявителю на доработку с указанием замечаний."""
    comment = (request.form.get("comment") or "").strip()
    if not comment:
        flash("Пожалуйста, впишите замечания к заявке перед отправкой на доработку.", "danger")
        return redirect(url_for("internal.application_detail", app_id=app_id))

    try:
        application = ApplicationService.return_for_correction(app_id, comment=comment, reviewer="договорной отдел")
        flash(f"Заявка № {application.app_number} возвращена на доработку заявителю с замечаниями.", "warning")
    except Exception as e:
        current_app.logger.error(f"Error returning application #{app_id}: {e}", exc_info=True)
        flash(f"Ошибка при отправке заявки на доработку: {str(e)}", "danger")

    return redirect(url_for("internal.application_detail", app_id=app_id))


@internal_bp.route("/<int:app_id>/reject", methods=["POST"])
def reject_application(app_id: int):
    """Отклонение заявки договорным отделом."""
    reason = (request.form.get("reason") or "").strip()
    try:
        application = ApplicationService.reject_application(app_id, reason=reason, reviewer="договорной отдел")
        flash(f"Заявка № {application.app_number} отклонена.", "danger")
    except Exception as e:
        current_app.logger.error(f"Error rejecting application #{app_id}: {e}", exc_info=True)
        flash(f"Ошибка при отклонении заявки: {str(e)}", "danger")

    return redirect(url_for("internal.application_detail", app_id=app_id))


@internal_bp.route("/<int:app_id>/reset_review", methods=["POST"])
def reset_application_review(app_id: int):
    """Сброс статуса заявки обратно в 'На рассмотрении'."""
    application = Application.query.get_or_404(app_id)
    application.status = ApplicationStatus.IN_REVIEW.value
    application.reviewed_by = None
    application.reviewed_at = None
    db.session.commit()
    flash(f"Статус заявки № {application.app_number} возвращен в «На рассмотрении».", "info")
    return redirect(url_for("internal.application_detail", app_id=app_id))
