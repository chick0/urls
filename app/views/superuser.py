
from flask import Blueprint
from flask import request
from flask import redirect
from flask import url_for
from flask import Response

from flask import render_template

from app import db
from app.models import Url
from config import superuser


bp = Blueprint(
    name="superuser",
    import_name="superuser",
    url_prefix="/superuser",
)


def get_login_required():
    return Response(
        response="<h1>SuperUser Login Required</h1>",
        status=401,
        headers={
            "WWW-Authenticate": 'Basic realm="SuperUser Login Required"'
        }
    )


def authorization():
    sections = superuser.sections()
    if 'superuser' in sections:
        if request.authorization is None:
            return get_login_required()

        username = superuser['superuser'].get("username", None)
        password = superuser['superuser'].get("password", None)

        if username == request.authorization.username and password == request.authorization.password:
            return None
        else:
            return get_login_required()
    else:
        return "Superuser Dashboard is disabled!", 403


@bp.get("")
def dashboard():
    auth_result = authorization()
    if auth_result is not None:
        return auth_result

    url = Url.query.all()
    return render_template(
        "superuser.html",
        all_url=url
    )


@bp.get("/delete")
def delete():
    code = request.args.get("code", None)
    if code is not None:
        url = Url.query.filter_by(
            code=code,
        ).first()
        if url is not None:
            db.session.delete(url)
            db.session.commit()

    return redirect(url_for("superuser.dashboard"))
