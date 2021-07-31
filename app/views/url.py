from secrets import token_bytes

from flask import Blueprint
from flask import request
from flask import redirect
from flask import url_for
from flask import render_template
from sqlalchemy.exc import IntegrityError

from . import dashboard
from . import warp
from app import db
from app.models import Url
from app.url import url_verifier

bp = Blueprint(
    name="url",
    import_name="url",
    url_prefix="/",
)
bp.register_blueprint(blueprint=dashboard.bp)
bp.register_blueprint(blueprint=warp.bp)


@bp.get("")
def form():
    return render_template(
        "form.html"
    )


@bp.post("")
def create():
    url = Url()
    url.code = token_bytes(2).hex()
    url.url = url_verifier(url=request.form.get("url", ""))
    url.used = 0
    url.magic = token_bytes(128).hex()

    # commit to database
    success = False
    for length in range(2, 11):
        try:
            db.session.add(url)
            db.session.commit()

            success = True
            break
        except IntegrityError:
            url.code = token_bytes(length).hex()

    if success is False:
        return "Fail to create short url", 500

    return redirect(url_for("url.dashboard.show", code=url.code, magic=url.magic))
