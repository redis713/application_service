import os
from flask import Flask, render_template
from app.config import Config
from app.extensions import db, csrf, migrate

def create_app(config_class=Config):
    flask_app = Flask(__name__)
    flask_app.config.from_object(config_class)

    # Убеждаемся, что каталоги для загрузок созданы
    os.makedirs(flask_app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(flask_app.config["SCANS_FOLDER"], exist_ok=True)

    # Инициализация расширений
    db.init_app(flask_app)
    csrf.init_app(flask_app)
    migrate.init_app(flask_app, db)

    # Поддержка работы за обратным прокси (Apache ProxyPass)
    from werkzeug.middleware.proxy_fix import ProxyFix
    flask_app.wsgi_app = ProxyFix(flask_app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    # Иркутский часовой пояс (UTC+8) для отображения времени в шаблонах
    from datetime import timezone, timedelta
    IRKUTSK_TZ = timezone(timedelta(hours=8))

    @flask_app.template_filter("irkutsk_time")
    def irkutsk_time_filter(dt, fmt="%d.%m.%Y %H:%M"):
        if not dt:
            return ""
        if hasattr(dt, "tzinfo"):
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            dt = dt.astimezone(IRKUTSK_TZ)
        elif hasattr(dt, "year") and hasattr(dt, "hour"):
            dt = dt.replace(tzinfo=timezone.utc).astimezone(IRKUTSK_TZ)
        if hasattr(dt, "strftime"):
            return dt.strftime(fmt)
        return str(dt)

    # Регистрация Blueprints
    from app.blueprints.main import main_bp
    from app.blueprints.apply import apply_bp
    from app.blueprints.internal import internal_bp

    flask_app.register_blueprint(main_bp)
    flask_app.register_blueprint(apply_bp)
    flask_app.register_blueprint(internal_bp)

    # Автоматическое создание таблиц и первичное наполнение программами
    with flask_app.app_context():
        # Импортируем модели для регистрации в SQLAlchemy
        from app.models import (
            Person,
            Program,
            Application,
            ApplicationListener,
            ListenerCourse,
            ApplicationAttachment,
        )
        if flask_app.config.get("TESTING"):
            db.create_all()

        from app.data.programs_seed import seed_programs
        try:
            seeded = seed_programs()
            flask_app.logger.info(f"Seeded {seeded} programs")
        except Exception as e:
            flask_app.logger.warning(f"Could not seed programs: {e}")

    # Обработчики ошибок
    @flask_app.errorhandler(404)
    def not_found_error(error):
        return render_template("errors/404.html"), 404

    @flask_app.errorhandler(413)
    def request_entity_too_large(error):
        return render_template("errors/413.html"), 413

    @flask_app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template("errors/500.html"), 500

    return flask_app
