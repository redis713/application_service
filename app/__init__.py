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

    # Регистрация Blueprints
    from app.blueprints.main import main_bp
    from app.blueprints.apply import apply_bp

    flask_app.register_blueprint(main_bp)
    flask_app.register_blueprint(apply_bp)

    # Автоматическое создание таблиц и первичное наполнение программами
    with flask_app.app_context():
        # Импортируем модели для регистрации в SQLAlchemy
        from app.models import (
            Organization,
            Person,
            Program,
            Application,
            ApplicationListener,
            ListenerCourse,
            ApplicationAttachment,
        )
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
