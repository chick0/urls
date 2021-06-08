from sys import exit
from random import choice
from base64 import b64decode
from asyncio import sleep
from secrets import token_bytes
from sqlite3 import IntegrityError
from argparse import ArgumentParser
from configparser import ConfigParser

from sanic import Sanic
from sanic.exceptions import SanicException, Unauthorized
from sanic.response import html, redirect
from aiosqlite import connect
from jinja2 import Environment, PackageLoader, select_autoescape


app = Sanic(__name__)
env = Environment(
    loader=PackageLoader("urls", "templates", "utf-8"),
    autoescape=select_autoescape()
)

# Short URL Cache
cache = {}


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
        return redirect(to="/")

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
        return redirect(to="/")

    if request.method == "GET":
        if request.args.get("delete", "no") == "yes":
            if code in cache.keys():
                del cache[code]

            await cur.execute(
                "DELETE FROM urls WHERE code=? AND magic=?",
                (code, magic)
            )
            await db.commit()

        await db.close()

        template = env.get_template("manage.html")
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
            cache[code] = new_url

        await db.close()
        return redirect(
            to=app.url_for("url_manage", code=code, magic=magic)
        )


@app.route("/superuser")
async def superuser(request):
    if len(args.username) == 0 or len(args.password) == 0:
        return redirect(to="/")

    auth = request.headers.get("Authorization", None)

    if auth is None:
        raise Unauthorized("Auth required", scheme="Basic", realm="Auth required")
    else:
        type_, value_ = auth.split()
        if type_.lower() == "basic":
            username, password = b64decode(value_).decode().split(":")
            if username == args.username and password == args.password:
                db = await get_db()
                cur = await db.cursor()

                c = await cur.execute(
                    "SELECT * FROM urls"
                )

                all_url = [
                    {
                        "code": ctx[0],
                        "url": ctx[1],
                        "magic": app.url_for("url_manage", code=ctx[0], magic=ctx[2])
                    } for ctx in await c.fetchall()
                ]

                template = env.get_template("superuser.html")
                return html(
                    body=template.render(all_url=all_url)
                )

    return redirect(to="/")


@app.route("/<code:string>")
async def warp(request, code: str):
    if code not in cache.keys():
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
        cache[code] = url
    else:
        url = cache[code]

    if url.startswith("http://") or url.startswith("https://"):
        return redirect(to=url)
    else:
        raise SanicException("URL does not start with http or https!", 400)


async def clean_up():
    def get_limit():
        try:
            return int(args.limit)
        except ValueError:
            return 2500  # default

    while get_limit() < len(cache):
        del cache[choice(list(cache.keys()))]

    await sleep(60)
    await clean_up()


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

    parser.add_argument("--username",
                        help="set superuser username",
                        action="store", type=str, default="")
    parser.add_argument("--password",
                        help="set superuser password",
                        action="store", type=str, default="")

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

    try:
        config = ConfigParser()
        config.read("config.ini")

        args.host = config.get("app", "host", fallback=args.host)
        args.port = config.get("app", "port", fallback=args.port)
        args.limit = config.get("cache", "limit", fallback=args.limit)
        args.username = config.get("superuser", "username", fallback=args.username)
        args.password = config.get("superuser", "password", fallback=args.password)
    except (FileNotFoundError, KeyError):
        pass

    app.add_task(clean_up)
    app.run(
        host=args.host,
        port=args.port,
        debug=False
    )
