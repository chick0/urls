from sys import exit
from random import choice
from base64 import b64decode
from urllib.parse import urlparse
from asyncio import sleep
from secrets import token_bytes
from sqlite3 import IntegrityError
from sqlite3 import OperationalError
from argparse import ArgumentParser
from configparser import ConfigParser

from sanic import Sanic
from sanic.exceptions import abort
from sanic.exceptions import Unauthorized
from sanic.response import html
from sanic.response import text
from sanic.response import json
from sanic.response import redirect
from aiosqlite import connect
from jinja2 import Environment
from jinja2 import PackageLoader
from jinja2 import select_autoescape


app = Sanic(__name__)
env = Environment(
    loader=PackageLoader("urls", "templates", "utf-8"),
    autoescape=select_autoescape()
)

# Short URL Cache
cache = {}

#
db = None


class SuperUser:
    def __init__(self, username: str = "", password: str = ""):
        self._username = username.replace(" ", "")
        self._password = password.replace(" ", "")

    def is_enabled(self):
        return not (len(self._username) == 0 or len(self._password) == 0)

    def check(self, username: str = "", password: str = ""):
        return self._username == username and self._password == password

    def parse(self, authorization):
        if authorization is None:
            raise Unauthorized(
                "Auth required",
                scheme="Basic",
                realm="Auth required"
            )
        else:
            method, value_ = authorization.split()
            if method.lower() == "basic":
                username, password = b64decode(value_).decode().split(":")
                return self.is_enabled() and self.check(username=username, password=password)

        return False


class UrlVerifyFail(Exception):
    def __init__(self, message):
        super().__init__(message)


def url_verifier(url: str) -> str:
    if len(url) > 2000:
        raise UrlVerifyFail(message="URL is too long. Please try again less than 2000 characters.")

    url = urlparse(url=url)
    allow_schemes = [
        "http",
        "https",
    ]

    if url.scheme not in allow_schemes:
        raise UrlVerifyFail(message=f"'{url.scheme}' is an unacceptable scheme.")

    return url.geturl()


@app.route("/")
async def index(request):
    template = env.get_template("index.html")
    return html(
        body=template.render()
    )


@app.route("/robots.txt")
async def robots(request):
    return text(
        body="User-agent: *\n"
             "Allow: /$\n"
             "Disallow: /\n"
             "Disallow: /url"
    )


@app.route("/url/create", methods=['POST'])
async def url_create(request):
    url = url_verifier(url=request.form.get("url", ""))
    if url is None:
        return redirect(to="/")

    cur = await getattr(db, "cursor")()

    async def retry(length: int = 2, try_count: int = 0):
        if length > 20:
            abort(500, "Fail to generate URL Code")

        code_ = token_bytes(length).hex()
        try:
            await cur.execute(
                "INSERT INTO urls(code, url, magic) VALUES(?, ?, ?)",
                (code_, url, magic)
            )
            return code_
        except IntegrityError:
            pass

        try_count += 1
        if try_count % 2 == 0:
            length += 1

        return await retry(length, try_count)

    magic = token_bytes(128).hex()
    code = await retry()

    cache[code] = url
    await getattr(db, "commit")()

    if request.headers.get("User-Agent", "").startswith("curl"):
        return json(
            body={
                "code": code,
                "magic": magic
            },
            status=201
        )

    return redirect(to=app.url_for("url_manage", code=code, magic=magic))


@app.route("/url/<code:string>/<magic:string>", methods=['GET', 'POST'])
async def url_manage(request, code: str, magic: str):
    cur = await getattr(db, "cursor")()

    c = await cur.execute(
        "SELECT * FROM urls WHERE code=? AND magic=?",
        (code, magic)
    )
    ctx = await c.fetchone()
    if ctx is None:
        return redirect(to="/")

    if request.method == "GET":
        if request.args.get("magicC", "no") == "yes":
            new_magic = token_bytes(128).hex()
            await cur.execute(
                "UPDATE urls SET magic=? WHERE code=? AND magic=?",
                (new_magic, code, magic)
            )
            await getattr(db, "commit")()

            return redirect(to=app.url_for("url_manage", code=code, magic=new_magic))

        if request.args.get("delete", "no") == "yes":
            if code in cache.keys():
                del cache[code]

            await cur.execute(
                "DELETE FROM urls WHERE code=? AND magic=?",
                (code, magic)
            )
            await getattr(db, "commit")()

        template = env.get_template("manage.html")
        return html(
            body=template.render(
                is_deleted=request.args.get("delete", "no"),
                code=code,
                url=ctx[1],
            )
        )
    elif request.method == "POST":
        try:
            new_url = url_verifier(url=request.form.get("url", ""))

            await cur.execute(
                "UPDATE urls SET url=? WHERE code=? AND magic=?",
                (new_url, code, magic)
            )
            await getattr(db, "commit")()
            cache[code] = new_url
        except UrlVerifyFail:
            pass

        return redirect(
            to=app.url_for("url_manage", code=code, magic=magic)
        )


@app.route("/superuser")
async def superuser(request):
    if user.parse(request.headers.get("Authorization", None)):
        if request.args.get("db", "") == "connect":
            if getattr(db, "_connection") is None:
                await db_setup()
            return redirect(to=app.url_for("superuser"))

        if request.args.get("db", "") == "close":
            if getattr(db, "_connection") is not None:
                await getattr(db, "close")()
            return redirect(to=app.url_for("superuser"))

        superuser_db = db
        if getattr(db, "_connection") is None:
            superuser_db = await connect("urls/urls.db")

        code = request.args.get("delete", None)
        if code is not None:
            if code in cache.keys():
                del cache[code]

            await superuser_db.execute(
                "DELETE FROM urls WHERE code=?",
                (code,)
            )
            await superuser_db.commit()
            return redirect(to=app.url_for("superuser"))

        cur = await superuser_db.cursor()
        c = await cur.execute(
            "SELECT * FROM urls"
        )

        template = env.get_template("superuser.html")
        return html(
            body=template.render(
                db_status="online" if getattr(db, "_connection") is not None else "offline",
                db_url="?db=close" if getattr(db, "_connection") is not None else "?db=connect",
                all_url=[
                    {
                        "code": ctx[0],
                        "url": ctx[1],
                        "magic": app.url_for("url_manage", code=ctx[0], magic=ctx[2])
                    } for ctx in await c.fetchall()
                ]
            )
        )

    raise Unauthorized("Auth required", scheme="Basic", realm="Auth required")


@app.route("/<code:string>")
async def warp(request, code: str):
    if code not in cache.keys():
        cur = await getattr(db, "cursor")()

        c = await cur.execute(
            "SELECT url FROM urls WHERE code=?",
            (code,)
        )
        ctx = await c.fetchone()

        if ctx is None:
            abort(404)

        url = ctx[0]
        cache[code] = url
    else:
        url = cache[code]

    if url.startswith("http://") or url.startswith("https://"):
        return redirect(to=url)
    else:
        abort(400, "Error: URL does not start with http:// or https://")


async def clean_up(limit: int or str):
    if isinstance(limit, str):
        try:
            limit = int(limit)
        except ValueError:
            limit = 2500  # default

    while limit < len(cache):
        del cache[choice(list(cache.keys()))]

    await sleep(60)
    await clean_up(limit)


async def db_setup():
    global db
    db = await connect("urls/urls.db")


async def db_is_busy(request, exception):
    abort(503, "Database is busy. Try again in 3 minute.")


async def url_verifier_fail(request, exception):
    abort(400, message=exception)


if __name__ == "__main__":
    parser = ArgumentParser(
        description="simple URL Shorter"
    )

    parser.add_argument("--reset",
                        help="reset config file",
                        action="store_const", const=True)

    parser.add_argument("--host",
                        help="set host ip address",
                        action="store", type=str, default="127.0.0.1")
    parser.add_argument("--port",
                        help="set port number",
                        action="store", type=int, default=8000)

    parser.add_argument("--limit",
                        help="set cache limit for url cache",
                        action="store", type=int, default=2500)

    args = parser.parse_args()

    if args.reset:
        config = ConfigParser()
        config.add_section("app")
        config.set("app", "host", "127.0.0.1")
        config.set("app", "port", "8000")
        config.add_section("cache")
        config.set("cache", "limit", "2500")
        config.add_section("superuser")
        config.set("superuser", "username", "")
        config.set("superuser", "password", "")

        config.write(open("config.ini", mode="w", encoding="utf-8"))
        print("config.ini reset"), exit(0)

    config = ConfigParser()
    config.read("config.ini")

    host = config.get("app", "host", fallback=args.host)
    port = config.get("app", "port", fallback=args.port)
    limit_ = config.get("cache", "limit", fallback=args.limit)
    user = SuperUser(
        username=config.get("superuser", "username", fallback=""),
        password=config.get("superuser", "password", fallback="")
    )
    del args, config

    app.add_task(db_setup)
    app.add_task(clean_up(limit=limit_))
    del limit_

    app.error_handler.add(OperationalError, db_is_busy)
    app.error_handler.add(ValueError, db_is_busy)
    app.error_handler.add(UrlVerifyFail, url_verifier_fail)

    app.run(
        host=host,
        port=port,
        debug=False
    )
