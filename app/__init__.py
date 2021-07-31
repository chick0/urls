from threading import Thread

from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()
migrate = Migrate()


def create_app():
    app = Flask(__name__)

    from . import config
    app.config.from_object(config)

    # database init
    __import__("app.models")
    db.init_app(app)
    migrate.init_app(app, db)

    # blueprint init
    from . import views
    for view in views.__all__:
        app.register_blueprint(getattr(getattr(getattr(__import__(f"app.views.{view}"), "views"), view), "bp"))

    # background task
    from . import task
    Thread(target=task.loop, args=(app,), daemon=True).start()

    return app
