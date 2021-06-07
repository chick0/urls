from secrets import token_bytes
from sqlite3 import IntegrityError

from sanic import Sanic
from sanic.exceptions import SanicException
from sanic.response import html, redirect
from aiosqlite import connect
from jinja2 import Environment, PackageLoader, select_autoescape


app = Sanic(__name__)
env = Environment(
    loader=PackageLoader("urls", "templates", "utf-8"),
    autoescape=select_autoescape()
)


async def get_db():
    db = await connect("urls/urls.db")
    return db


@app.route("/")
async def index(request):
    template = env.get_template("index.html")
    return html(
        body=template.render()
    )


@app.route("/url/create", methods=['POST'])
async def url_create(request):
    url = request.form.get("url", None)
    if url is None:
        return redirect(
            to=app.url_for("index")
        )

    db = await get_db()
    cur = await db.cursor()

    async def retry():
        code_ = token_bytes(3).hex()
        try:
            await cur.execute(
                "INSERT INTO urls(code, url, magic) VALUES(?, ?, ?)",
                (code_, url, magic)
            )
            return code_
        except IntegrityError:
            return await retry()

    magic = token_bytes(128).hex()
    code = await retry()

    await db.commit()
    await db.close()

    return redirect(
        to=app.url_for("url_manage", code=code, magic=magic),
        headers={
            "code": code,
            "magic": magic
        }
    )


@app.route("/url/<code:string>/<magic:string>", methods=['GET', 'POST'])
async def url_manage(request, code: str, magic: str):
    db = await get_db()
    cur = await db.cursor()

    c = await cur.execute(
        "SELECT * FROM urls WHERE code=? AND magic=?",
        (code, magic)
    )
    ctx = await c.fetchone()
    if ctx is None:
        return redirect(
            to=app.url_for("index")
        )

    if request.method == "GET":
        if request.args.get("delete", "no") == "yes":
            await cur.execute(
                "DELETE FROM urls WHERE code=? AND magic=?",
                (code, magic)
            )
            await db.commit()

        await db.close()

        template = env.get_template("url.manage.html")
        return html(
            body=template.render(
                is_deleted=request.args.get("delete", "no"),

                code=code,
                url=ctx[1],
                magic=magic,

                warp_url=app.url_for("warp", code=code),
                delete_url=app.url_for("url_manage", code=code, magic=magic, delete="yes")
            )
        )
    elif request.method == "POST":
        new_url = request.form.get("url", None)
        if new_url is not None:
            await cur.execute(
                "UPDATE urls SET url=? WHERE code=? AND magic=?",
                (new_url, code, magic)
            )
            await db.commit()

        await db.close()
        return redirect(
            to=app.url_for("url_manage", code=code, magic=magic),
        )


@app.route("/<code:string>")
async def warp(request, code: str):
    db = await get_db()
    cur = await db.cursor()

    c = await cur.execute(
        "SELECT url FROM urls WHERE code=?",
        (code,)
    )
    ctx = await c.fetchone()
    await db.close()

    if ctx is None:
        raise SanicException("URL Not Found", 404)

    url = ctx[0]
    if url.startswith("http://") or url.startswith("https://"):
        return redirect(
            to=url
        )
    else:
        raise SanicException("URL does not start with http or https!", 400)


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8000,
        debug=False
    )
