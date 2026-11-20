from flask import Flask, render_template
from config import config_map
from .extensions import db, migrate, login_manager, socketio, mail, celery


def create_app(config_name="dev"):
    app = Flask(__name__)
    app.config.from_object(config_map[config_name])

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    socketio.init_app(app)
    mail.init_app(app)
    celery.conf.update(
        broker_url=app.config["CELERY_BROKER_URL"],
        result_backend=app.config["CELERY_RESULT_BACKEND"],
    )

    from . import models  # noqa: F401  (register models)

    from .blueprints.auth import bp as auth_bp
    from .blueprints.candidate import bp as candidate_bp
    from .blueprints.company import bp as company_bp
    from .blueprints.jobs import bp as jobs_bp
    from .blueprints.chat import bp as chat_bp
    from .blueprints.admin import bp as admin_bp
    from .blueprints.api import bp as api_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(candidate_bp, url_prefix="/candidate")
    app.register_blueprint(company_bp, url_prefix="/company")
    app.register_blueprint(jobs_bp)
    app.register_blueprint(chat_bp, url_prefix="/chat")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(api_bp, url_prefix="/api")

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500

    return app
