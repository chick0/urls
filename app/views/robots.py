
from flask import Blueprint
from flask import Response


bp = Blueprint(
    name="robots",
    import_name="robots",
    url_prefix="",
)


@bp.get("/robots.txt")
def txt():
    return Response(
        mimetype="text/plain",
        response="\n".join([
            "User-agent: *",
            "Allow: /$",
            "Disallow: /",
        ]),
    )
