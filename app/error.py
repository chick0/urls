
from flask import render_template

from app.custom_error import *


def not_found(e):
    return render_template(
        "error.html",
        error_message="target not found"
    ), 404


def url_verify_fail(e):
    return render_template(
        "error.html",
        error_message=e.args[0]
    ), 400


def fail_to_create(e):
    return render_template(
        "error.html",
        error_message="Fail to create short url"
    ), 500


# error map
error_map = {
    404: not_found,

    # custom error
    UrlVerifyFail: url_verify_fail,
    FailToCreate: fail_to_create,
}
