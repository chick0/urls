from time import sleep

from . import db
from .models import Url
from .models import Used


def loop(app):
    while True:
        with app.app_context():
            for target in Used.query.filter_by(
                used=False
            ).limit(200).all():
                url = Url.query.filter_by(
                    code=target.code
                ).first()
                if url is None:
                    db.session.delete(target)
                else:
                    if url.date <= target.date:
                        target.used = True
                        url.used += 1
                    else:
                        db.session.delete(target)

                db.session.commit()

        sleep(80)
