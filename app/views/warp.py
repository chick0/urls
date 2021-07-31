from threading import Thread

from flask import Blueprint
from flask import redirect
from flask import current_app

from app import db
from app.models import Url
from app.models import Used


bp = Blueprint(
    name="warp",
    import_name="warp",
    url_prefix="",
)


def add_used(context, code: str):
    with context():
        used = Used()
        used.code = code

        db.session.add(used)
        db.session.commit()


@bp.get("/<string:code>")
def go(code: str):
    url = Url.query.filter_by(
        code=code
    ).first()
    if url is None:
        return "not found", 404

    if url.url.startswith("http://") or url.url.startswith("https://"):
        Thread(target=add_used, args=(current_app.app_context, url.code,)).start()
        return redirect(url.url)
    else:
        return "Error: Short URL does not start with http:// or https://", 400
