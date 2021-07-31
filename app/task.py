from time import sleep
from threading import Thread

from . import db
from .models import Url
from .models import Used


def core(app):
    while True:
        Thread(
            target=url_used_update,
            args=(app,)
        ).start()

        sleep(1 * 60)


def url_used_update(app):
    with app.app_context():
        for target in Used.query.filter_by(
            used=False
        ).limit(200).all():
            url = Url.query.filter_by(
                code=target.code
            ).first()
            if url is None:
                # target is deleted
                db.session.delete(target)
            else:
                if url.date < target.date:
                    target.used = True
                    url.used += 1
                else:
                    db.session.delete(target)

            db.session.commit()
