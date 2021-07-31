from secrets import token_bytes

from flask import Blueprint
from flask import request
from flask import redirect
from flask import url_for
from flask import render_template

from app import db
from app.models import Url
from app.url import url_verifier


bp = Blueprint(
    name="dashboard",
    import_name="dashboard",
    url_prefix="/dashboard",
)


@bp.get("/<string:code>/<string:magic>")
def show(code: str, magic: str):
    url = Url.query.filter_by(
        code=code,
        magic=magic
    ).first()
    if url is None:
        return render_template("delete.html"), 404

    return render_template(
        "dashboard.html",
        code=url.code,
        url=url.url,
        used=url.used,

        update=url_for("url.dashboard.update", code=code, magic=magic),
        delete=url_for("url.dashboard.delete", code=code, magic=magic),
    )


@bp.post("/<string:code>/<string:magic>")
def edit(code: str, magic: str):
    url = Url.query.filter_by(
        code=code,
        magic=magic
    ).first()
    if url is None:
        return render_template("delete.html"), 404

    url.url = url_verifier(url=request.form.get("url", ""))
    db.session.commit()

    return redirect(url_for("url.dashboard.show", code=code, magic=magic))


@bp.get("/<string:code>/<string:magic>/update")
def update(code: str, magic: str):
    url = Url.query.filter_by(
        code=code,
        magic=magic
    ).first()
    if url is None:
        return render_template("delete.html"), 404

    url.magic = token_bytes(128).hex()
    db.session.commit()
    return redirect(url_for("url.dashboard.show", code=code, magic=url.magic))


@bp.get("/<string:code>/<string:magic>/delete")
def delete(code: str, magic: str):
    url = Url.query.filter_by(
        code=code,
        magic=magic
    ).first()
    if url is None:
        return render_template("delete.html"), 404

    db.session.delete(url)
    db.session.commit()
    return render_template("delete.html")
