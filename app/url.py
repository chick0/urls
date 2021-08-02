from urllib.parse import urlparse

from app.custom_error import UrlVerifyFail


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
